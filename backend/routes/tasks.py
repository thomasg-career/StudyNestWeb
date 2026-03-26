from flask import Blueprint, g, jsonify, request

try:
    from backend.supabase_client import require_auth, user_sb
    from backend.daily_stats_sync import sync_daily_stats
except ModuleNotFoundError:
    from supabase_client import require_auth, user_sb
    from daily_stats_sync import sync_daily_stats

tasks_bp = Blueprint('tasks', __name__)


@tasks_bp.route('/', methods=['GET'])
@require_auth
def get_tasks():
    """
    GET /api/tasks/
    Query params: date (YYYY-MM-DD) — optional, filters by IST date
    Returns all tasks for the current user (optionally filtered by date).
    """
    date = request.args.get('date')  # e.g. 2025-03-24
    client = user_sb(g.access_token)

    query = client.from_('tasks').select('*').eq('user_id', g.user_id)

    if date:
        query = (query
                 .gte('created_at', f"{date}T00:00:00+05:30")
                 .lt('created_at',  f"{date}T23:59:59+05:30"))

    resp = query.order('created_at', desc=False).execute()
    return jsonify(resp.data), 200


@tasks_bp.route('/', methods=['POST'])
@require_auth
def create_task():
    """
    POST /api/tasks/
    Body: { text }
    Creates a new incomplete task for the current user.
    """
    body = request.get_json() or {}
    text = body.get('text', '').strip()
    if not text:
        return jsonify({"error": "text is required"}), 400

    client = user_sb(g.access_token)
    resp = client.from_('tasks').insert({
        "user_id":   g.user_id,
        "text":      text,
        "completed": False
    }).execute()
    sync_daily_stats(g.access_token, g.user_id)

    return jsonify(resp.data[0] if resp.data else {}), 201


@tasks_bp.route('/<task_id>', methods=['PATCH'])
@require_auth
def update_task(task_id):
    """
    PATCH /api/tasks/<task_id>
    Body: { completed: bool }  or  { text: str }
    Toggles completion or updates text.
    """
    body = request.get_json() or {}
    allowed = {k: v for k, v in body.items() if k in ('completed', 'text')}
    if not allowed:
        return jsonify({"error": "No updatable fields provided"}), 400

    client = user_sb(g.access_token)
    resp = (client.from_('tasks')
            .update(allowed)
            .eq('id', task_id)
            .eq('user_id', g.user_id)
            .execute())
    sync_daily_stats(g.access_token, g.user_id)

    return jsonify(resp.data[0] if resp.data else {}), 200


@tasks_bp.route('/<task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    """
    DELETE /api/tasks/<task_id>
    Deletes the task (only if owned by current user — enforced by RLS too).
    """
    client = user_sb(g.access_token)
    client.from_('tasks').delete().eq('id', task_id).eq('user_id', g.user_id).execute()
    sync_daily_stats(g.access_token, g.user_id)
    return jsonify({"message": "Task deleted"}), 200
