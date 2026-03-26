from flask import Blueprint, g, jsonify, request

from datetime import date, timedelta
import calendar

try:
    from backend.supabase_client import require_auth, user_sb
except ModuleNotFoundError:
    from supabase_client import require_auth, user_sb

stats_bp = Blueprint('stats', __name__)


def _ist_today() -> str:
    """Return today's date as YYYY-MM-DD in IST (UTC+5:30)."""
    from datetime import datetime, timezone, timedelta as td
    ist = timezone(td(hours=5, minutes=30))
    return datetime.now(ist).strftime('%Y-%m-%d')


@stats_bp.route('/today', methods=['GET'])
@require_auth
def today_stats():
    """
    GET /api/stats/today
    Fetches live data for today from tasks, habits, habit_logs, mood_logs.
    Does NOT rely on the daily_stats archive table — always fresh.
    """
    today_str = request.args.get('date') or _ist_today()
    client    = user_sb(g.access_token)

    # Tasks
    tasks_resp = (client.from_('tasks').select('*').eq('user_id', g.user_id)
                  .gte('created_at', f"{today_str}T00:00:00+05:30")
                  .lt('created_at',  f"{today_str}T23:59:59+05:30")
                  .execute())
    tasks = tasks_resp.data or []

    # Habits & logs
    habits_resp = client.from_('habits').select('*').eq('user_id', g.user_id).execute()
    habits      = habits_resp.data or []
    logs_resp   = (client.from_('habit_logs').select('*')
                   .eq('user_id', g.user_id).eq('log_date', today_str).execute())
    habit_logs  = logs_resp.data or []

    # Mood (latest of the day)
    mood_resp = (client.from_('mood_logs').select('*').eq('user_id', g.user_id)
                 .gte('created_at', f"{today_str}T00:00:00+05:30")
                 .lte('created_at', f"{today_str}T23:59:59+05:30")
                 .order('created_at', desc=True).limit(1).execute())
    mood_entry = (mood_resp.data or [None])[0]

    tasks_done    = sum(1 for t in tasks if t['completed'])
    tasks_total   = len(tasks)
    habits_done   = len(habit_logs)
    habits_total  = len(habits)
    total_done     = tasks_done + habits_done
    total_expected = tasks_total + habits_total
    percent = round((total_done / total_expected) * 100) if total_expected else 0

    return jsonify({
        "date":           today_str,
        "tasks_done":     tasks_done,
        "tasks_total":    tasks_total,
        "tasks_pending":  tasks_total - tasks_done,
        "habits_done":    habits_done,
        "habits_total":   habits_total,
        "habits_pending": habits_total - habits_done,
        "mood":           mood_entry['mood']   if mood_entry else 0,
        "energy":         mood_entry['energy'] if mood_entry else 0,
        "progress_pct":   percent,
        "tasks":          tasks,
        "habits":         habits,
        "habit_logs":     habit_logs,
    }), 200


@stats_bp.route('/weekly', methods=['GET'])
@require_auth
def weekly_stats():
    """
    GET /api/stats/weekly
    Returns daily_stats rows for the current Mon–Sun week
    plus live data for today merged in.
    """
    today_str = _ist_today()
    today_dt  = date.fromisoformat(today_str)

    # Monday of current week
    monday = today_dt - timedelta(days=(today_dt.weekday()))
    sunday = monday + timedelta(days=6)

    client = user_sb(g.access_token)
    resp   = (client.from_('daily_stats').select('*').eq('user_id', g.user_id)
              .gte('date', str(monday)).lte('date', str(sunday))
              .order('date').execute())

    rows    = {str(r['date'])[:10]: r for r in (resp.data or [])}
    profile = (client.from_('profiles').select('current_streak')
               .eq('id', g.user_id).single().execute())
    streak  = profile.data.get('current_streak', 0) if profile.data else 0

    days = []
    for i in range(7):
        d     = monday + timedelta(days=i)
        d_str = str(d)
        days.append(rows.get(d_str, {"date": d_str, "tasks_done": 0, "tasks_total": 0,
                                     "habits_done": 0, "habits_total": 0,
                                     "mood": 0, "energy": 0}))

    return jsonify({"week_start": str(monday), "week_end": str(sunday),
                    "streak": streak, "days": days}), 200


@stats_bp.route('/monthly', methods=['GET'])
@require_auth
def monthly_stats():
    """
    GET /api/stats/monthly?year=YYYY&month=M
    Returns daily_stats rows for the given month (defaults to current).
    """
    today_str = _ist_today()
    today_dt  = date.fromisoformat(today_str)
    year  = request.args.get('year',  type=int, default=today_dt.year)
    month = request.args.get('month', type=int, default=today_dt.month)

    first_day = date(year, month, 1)
    last_day  = date(year, month, calendar.monthrange(year, month)[1])

    client = user_sb(g.access_token)
    resp   = (client.from_('daily_stats').select('*').eq('user_id', g.user_id)
              .gte('date', str(first_day)).lte('date', str(last_day))
              .order('date').execute())
    rows   = resp.data or []

    profile = (client.from_('profiles').select('current_streak')
               .eq('id', g.user_id).single().execute())
    streak  = profile.data.get('current_streak', 0) if profile.data else 0

    # Aggregate totals
    total_done     = sum((r.get('tasks_done', 0) or 0) + (r.get('habits_done', 0) or 0) for r in rows)
    total_expected = sum((r.get('tasks_total', 0) or 0) + (r.get('habits_total', 0) or 0) for r in rows)
    moods          = [r['mood']   for r in rows if r.get('mood')]
    energies       = [r['energy'] for r in rows if r.get('energy')]

    return jsonify({
        "year":        year,
        "month":       month,
        "streak":      streak,
        "progress_pct": round((total_done / total_expected) * 100) if total_expected else 0,
        "avg_mood":    round(sum(moods)    / len(moods),    1) if moods    else 0,
        "avg_energy":  round(sum(energies) / len(energies), 1) if energies else 0,
        "days":        rows,
    }), 200


@stats_bp.route('/yearly', methods=['GET'])
@require_auth
def yearly_stats():
    """
    GET /api/stats/yearly?year=YYYY
    Returns daily_stats rows for the full year (defaults to current year).
    """
    today_str = _ist_today()
    today_dt  = date.fromisoformat(today_str)
    year      = request.args.get('year', type=int, default=today_dt.year)

    client = user_sb(g.access_token)
    resp   = (client.from_('daily_stats').select('*').eq('user_id', g.user_id)
              .gte('date', f"{year}-01-01").lte('date', f"{year}-12-31")
              .order('date').execute())
    rows   = resp.data or []

    profile = (client.from_('profiles').select('current_streak')
               .eq('id', g.user_id).single().execute())
    streak  = profile.data.get('current_streak', 0) if profile.data else 0

    total_done     = sum((r.get('tasks_done', 0) or 0) + (r.get('habits_done', 0) or 0) for r in rows)
    total_expected = sum((r.get('tasks_total', 0) or 0) + (r.get('habits_total', 0) or 0) for r in rows)
    moods          = [r['mood']   for r in rows if r.get('mood')]
    energies       = [r['energy'] for r in rows if r.get('energy')]

    # Group by month for charts
    monthly = {}
    for r in rows:
        m = str(r['date'])[:7]  # YYYY-MM
        if m not in monthly:
            monthly[m] = {"tasks_done": 0, "tasks_total": 0,
                          "habits_done": 0, "habits_total": 0,
                          "mood_sum": 0, "energy_sum": 0, "days": 0}
        monthly[m]["tasks_done"]   += r.get('tasks_done', 0)  or 0
        monthly[m]["tasks_total"]  += r.get('tasks_total', 0) or 0
        monthly[m]["habits_done"]  += r.get('habits_done', 0) or 0
        monthly[m]["habits_total"] += r.get('habits_total', 0) or 0
        monthly[m]["mood_sum"]     += r.get('mood', 0)   or 0
        monthly[m]["energy_sum"]   += r.get('energy', 0) or 0
        monthly[m]["days"]         += 1

    return jsonify({
        "year":        year,
        "streak":      streak,
        "progress_pct": round((total_done / total_expected) * 100) if total_expected else 0,
        "avg_mood":    round(sum(moods)    / len(moods),    1) if moods    else 0,
        "avg_energy":  round(sum(energies) / len(energies), 1) if energies else 0,
        "monthly":     monthly,
        "days":        rows,
    }), 200


@stats_bp.route('/archive', methods=['POST'])
@require_auth
def archive_today():
    """
    POST /api/stats/archive
    Manually triggers archiving today's live data into daily_stats.
    (The cron job calls Supabase Edge Function; this is the Flask equivalent.)
    """
    today_str = _ist_today()
    client    = user_sb(g.access_token)

    # Fetch live counts
    tasks_resp  = (client.from_('tasks').select('*').eq('user_id', g.user_id)
                   .gte('created_at', f"{today_str}T00:00:00+05:30")
                   .lt('created_at',  f"{today_str}T23:59:59+05:30").execute())
    tasks       = tasks_resp.data or []
    habits_resp = client.from_('habits').select('*').eq('user_id', g.user_id).execute()
    habits      = habits_resp.data or []
    logs_resp   = (client.from_('habit_logs').select('*')
                   .eq('user_id', g.user_id).eq('log_date', today_str).execute())
    habit_logs  = logs_resp.data or []
    mood_resp   = (client.from_('mood_logs').select('mood,energy').eq('user_id', g.user_id)
                   .gte('created_at', f"{today_str}T00:00:00+05:30")
                   .lte('created_at', f"{today_str}T23:59:59+05:30")
                   .order('created_at', desc=True).limit(1).execute())
    mood_entry  = (mood_resp.data or [{}])[0]

    payload = {
        "user_id":      g.user_id,
        "date":         today_str,
        "tasks_done":   sum(1 for t in tasks if t['completed']),
        "tasks_total":  len(tasks),
        "habits_done":  len(habit_logs),
        "habits_total": len(habits),
        "mood":         mood_entry.get('mood', 0),
        "energy":       mood_entry.get('energy', 0),
    }

    # Upsert — safe to call multiple times
    client.from_('daily_stats').upsert(payload, on_conflict='user_id,date').execute()
    return jsonify({"message": "Archived", "data": payload}), 200
