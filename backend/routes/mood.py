from flask import Blueprint, g, jsonify, request

try:
    from backend.supabase_client import require_auth, user_sb
    from backend.routes.daily_stats_sync import sync_daily_stats
except ModuleNotFoundError:
    from supabase_client import require_auth, user_sb
    from .daily_stats_sync import sync_daily_stats

habits_bp = Blueprint('habits', __name__)


@habits_bp.route('/', methods=['GET'])
@require_auth
def get_habits():
    """GET /api/habits/ — list all habits for the current user"""
    client = user_sb(g.access_token)
    resp = client.from_('habits').select('*').eq('user_id', g.user_id).execute()
    return jsonify(resp.data), 200


@habits_bp.route('/', methods=['POST'])
@require_auth
def create_habit():
    """
    POST /api/habits/
    Body: { name }
    """
    body = request.get_json() or {}
    name = body.get('name', '').strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    client = user_sb(g.access_token)
    resp = client.from_('habits').insert({
        "user_id": g.user_id,
        "name": name,
        "streak": 0
    }).execute()

    sync_daily_stats(g.access_token, g.user_id)
    return jsonify(resp.data[0] if resp.data else {}), 201


@habits_bp.route('/<habit_id>', methods=['DELETE'])
@require_auth
def delete_habit(habit_id):
    """DELETE /api/habits/<habit_id>"""
    client = user_sb(g.access_token)
    client.from_('habits').delete().eq('id', habit_id).eq('user_id', g.user_id).execute()
    sync_daily_stats(g.access_token, g.user_id)
    return jsonify({"message": "Habit deleted"}), 200


@habits_bp.route('/logs', methods=['GET'])
@require_auth
def get_habit_logs():
    """
    GET /api/habits/logs?date=YYYY-MM-DD
    Returns habit_logs for the given date.
    """
    date = request.args.get('date')
    client = user_sb(g.access_token)
    query = client.from_('habit_logs').select('*').eq('user_id', g.user_id)
    if date:
        query = query.eq('log_date', date)
    resp = query.execute()
    return jsonify(resp.data), 200


@habits_bp.route('/logs', methods=['POST'])
@require_auth
def log_habit():
    """
    POST /api/habits/logs
    Body: { habit_id, log_date }
    """
    body = request.get_json() or {}
    habit_id = body.get('habit_id')
    log_date = body.get('log_date')
    if not habit_id or not log_date:
        return jsonify({"error": "habit_id and log_date are required"}), 400

    client = user_sb(g.access_token)
    try:
        resp = client.from_('habit_logs').insert({
            "user_id": g.user_id,
            "habit_id": habit_id,
            "log_date": log_date
        }).execute()
        sync_daily_stats(g.access_token, g.user_id, log_date)
        return jsonify(resp.data[0] if resp.data else {}), 201
    except Exception as e:
        sync_daily_stats(g.access_token, g.user_id, log_date)
        return jsonify({"message": "Already logged", "detail": str(e)}), 200


@habits_bp.route('/logs/<log_id>', methods=['DELETE'])
@require_auth
def unlog_habit(log_id):
    """DELETE /api/habits/logs/<log_id>"""
    client = user_sb(g.access_token)
    existing = (client.from_('habit_logs').select('log_date')
                .eq('id', log_id)
                .eq('user_id', g.user_id)
                .limit(1)
                .execute())
    rows = existing.data or []
    log_date = rows[0].get('log_date') if rows else None

    client.from_('habit_logs').delete().eq('id', log_id).eq('user_id', g.user_id).execute()
    sync_daily_stats(g.access_token, g.user_id, log_date)
    return jsonify({"message": "Habit unlogged"}), 200
