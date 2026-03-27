try:
    from backend.supabase_client import user_sb
except ModuleNotFoundError:
    from supabase_client import user_sb


def ist_today() -> str:
    from datetime import datetime, timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d")


def _format_local_date(date_str: str):
    from datetime import date
    return date.fromisoformat(date_str)


def sync_daily_stats(access_token: str, user_id: str, date_str: str | None = None):
    from datetime import timedelta

    date_str = date_str or ist_today()
    client = user_sb(access_token)

    tasks_resp = (client.from_("tasks").select("*").eq("user_id", user_id)
                  .gte("created_at", f"{date_str}T00:00:00+05:30")
                  .lt("created_at", f"{date_str}T23:59:59+05:30")
                  .execute())
    tasks = tasks_resp.data or []

    habits_resp = client.from_("habits").select("*").eq("user_id", user_id).execute()
    habits = habits_resp.data or []

    logs_resp = (client.from_("habit_logs").select("*")
                 .eq("user_id", user_id)
                 .eq("log_date", date_str)
                 .execute())
    habit_logs = logs_resp.data or []

    mood_resp = (client.from_("mood_logs").select("mood,energy").eq("user_id", user_id)
                 .gte("created_at", f"{date_str}T00:00:00+05:30")
                 .lte("created_at", f"{date_str}T23:59:59+05:30")
                 .order("created_at", desc=True)
                 .limit(1)
                 .execute())
    mood_entry = (mood_resp.data or [{}])[0]

    payload = {
        "user_id": user_id,
        "date": date_str,
        "tasks_done": sum(1 for task in tasks if task.get("completed")),
        "tasks_total": len(tasks),
        "habits_done": len(habit_logs),
        "habits_total": len(habits),
        "mood": mood_entry.get("mood", 0),
        "energy": mood_entry.get("energy", 0),
    }

    client.from_("daily_stats").upsert(payload, on_conflict="user_id,date").execute()

    current_year = int(date_str[:4])
    previous_year = current_year - 1

    current_year_resp = (client.from_("daily_stats").select("date,tasks_done,habits_done")
                         .eq("user_id", user_id)
                         .gte("date", f"{current_year}-01-01")
                         .lte("date", f"{current_year}-12-31")
                         .execute())

    previous_year_resp = (client.from_("daily_stats").select("date,tasks_done,habits_done")
                          .eq("user_id", user_id)
                          .gte("date", f"{previous_year}-01-01")
                          .lte("date", f"{previous_year}-12-31")
                          .execute())

    active_dates = set()
    for resp in [current_year_resp, previous_year_resp]:
        for entry in (resp.data or []):
            if (entry.get("tasks_done", 0) or 0) > 0 or (entry.get("habits_done", 0) or 0) > 0:
                active_dates.add(str(entry["date"])[:10])

    if payload["tasks_done"] > 0 or payload["habits_done"] > 0:
        active_dates.add(date_str)

    streak = 0
    cursor = _format_local_date(date_str)

    if date_str not in active_dates:
        cursor -= timedelta(days=1)

    while True:
        cursor_str = cursor.isoformat()
        if cursor_str not in active_dates:
            break
        streak += 1
        cursor -= timedelta(days=1)

    client.from_("profiles").update({"current_streak": streak}).eq("id", user_id).execute()

    return {
        "daily_stats": payload,
        "current_streak": streak
    }
