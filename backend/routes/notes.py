from flask import Blueprint, g, jsonify, request

try:
    from backend.supabase_client import require_auth, user_sb
except ModuleNotFoundError:
    from supabase_client import require_auth, user_sb

notes_bp = Blueprint('notes', __name__)


@notes_bp.route('/', methods=['GET'])
@require_auth
def get_notes():
    """GET /api/notes/ — all notes for current user, newest first"""
    client = user_sb(g.access_token)
    resp = (client.from_('notes')
            .select('*')
            .eq('user_id', g.user_id)
            .order('created_at', desc=True)
            .execute())
    return jsonify(resp.data), 200


@notes_bp.route('/', methods=['POST'])
@require_auth
def create_note():
    """
    POST /api/notes/
    Body: { content }
    """
    body    = request.get_json() or {}
    content = body.get('content', '').strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    client = user_sb(g.access_token)
    resp = client.from_('notes').insert({
        "user_id": g.user_id,
        "content": content
    }).execute()
    return jsonify(resp.data[0] if resp.data else {}), 201


@notes_bp.route('/<note_id>', methods=['GET'])
@require_auth
def get_note(note_id):
    """GET /api/notes/<note_id> — single note"""
    client = user_sb(g.access_token)
    resp = (client.from_('notes')
            .select('*')
            .eq('id', note_id)
            .eq('user_id', g.user_id)
            .single()
            .execute())
    if not resp.data:
        return jsonify({"error": "Note not found"}), 404
    return jsonify(resp.data), 200


@notes_bp.route('/<note_id>', methods=['PATCH'])
@require_auth
def update_note(note_id):
    """
    PATCH /api/notes/<note_id>
    Body: { content }
    """
    body    = request.get_json() or {}
    content = body.get('content', '').strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    client = user_sb(g.access_token)
    resp = (client.from_('notes')
            .update({"content": content})
            .eq('id', note_id)
            .eq('user_id', g.user_id)
            .execute())
    return jsonify(resp.data[0] if resp.data else {}), 200


@notes_bp.route('/<note_id>', methods=['DELETE'])
@require_auth
def delete_note(note_id):
    """DELETE /api/notes/<note_id>"""
    client = user_sb(g.access_token)
    client.from_('notes').delete().eq('id', note_id).eq('user_id', g.user_id).execute()
    return jsonify({"message": "Note deleted"}), 200
