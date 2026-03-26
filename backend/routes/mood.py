from flask import Blueprint, g, jsonify, request

try:
    from backend.supabase_client import require_auth, user_sb
    from backend.daily_stats_sync import sync_daily_stats
except ModuleNotFoundError:
    from supabase_client import require_auth, user_sb
    from daily_stats_sync import sync_daily_stats

mood_bp = Blueprint('mood', __name__)


@mood_bp.route('/', methods=['GET'])
@require_auth
def get_mood_logs():
    """
    GET /api/mood/?date=YYYY-MM-DD
    Returns mood logs for the given IST date.
    Optional: ?limit=1 to get only the latest entry.
    """
    date   = request.args.get('date')
    limit  = request.args.get('limit', type=int)
    client = user_sb(g.access_token)

    query = client.from_('mood_logs').select('*').eq('user_id', g.user_id)

    if date:
        query = (query
                 .gte('created_at', f"{date}T00:00:00+05:30")
                 .lte('created_at', f"{date}T23:59:59+05:30"))

    query = query.order('created_at', desc=True)

    if limit:
        query = query.limit(limit)

    resp = query.execute()
    return jsonify(resp.data), 200


@mood_bp.route('/', methods=['POST'])
@require_auth
def log_mood():
    """
    POST /api/mood/
    Body: { mood: int(0-100), energy: int(0-100), happiness: int(0-100) }
    Saves a new mood/energy snapshot for the current user.
    """
    body = request.get_json() or {}

    mood      = body.get('mood')
    energy    = body.get('energy')
    happiness = body.get('happiness')

    if mood is None or energy is None:
        return jsonify({"error": "mood and energy are required"}), 400

    # Basic range validation
    for name, val in [('mood', mood), ('energy', energy)]:
        if not (0 <= int(val) <= 100):
            return jsonify({"error": f"{name} must be between 0 and 100"}), 400

    payload = {
        "user_id": g.user_id,
        "mood":    int(mood),
        "energy":  int(energy),
    }
    if happiness is not None:
        payload["happiness"] = int(happiness)

    client = user_sb(g.access_token)
    resp = client.from_('mood_logs').insert(payload).execute()
    sync_daily_stats(g.access_token, g.user_id)
    return jsonify(resp.data[0] if resp.data else {}), 201


@mood_bp.route('/<log_id>', methods=['DELETE'])
@require_auth
def delete_mood_log(log_id):
    """DELETE /api/mood/<log_id>"""
    client = user_sb(g.access_token)
    client.from_('mood_logs').delete().eq('id', log_id).eq('user_id', g.user_id).execute()
    sync_daily_stats(g.access_token, g.user_id)
    return jsonify({"message": "Mood log deleted"}), 200
