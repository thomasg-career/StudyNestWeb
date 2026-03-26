from flask import Blueprint, g, jsonify, request

try:
    from backend.supabase_client import require_auth, user_sb
except ModuleNotFoundError:
    from supabase_client import require_auth, user_sb

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/', methods=['GET'])
@require_auth
def get_profile():
    """GET /api/profile/ — fetch current user's profile"""
    client = user_sb(g.access_token)
    resp   = (client.from_('profiles').select('*')
              .eq('id', g.user_id).single().execute())
    if not resp.data:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(resp.data), 200


@profile_bp.route('/', methods=['PATCH'])
@require_auth
def update_profile():
    """
    PATCH /api/profile/
    Body: { full_name?, avatar_url?, current_streak? }
    """
    body    = request.get_json() or {}
    allowed = {k: v for k, v in body.items() if k in ('full_name', 'avatar_url', 'current_streak')}
    if not allowed:
        return jsonify({"error": "No updatable fields provided"}), 400

    client = user_sb(g.access_token)
    resp   = (client.from_('profiles')
              .update(allowed)
              .eq('id', g.user_id)
              .execute())
    return jsonify(resp.data[0] if resp.data else {}), 200
