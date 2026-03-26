try:
    from backend.supabase_client import user_sb
except ModuleNotFoundError:
    from supabase_client import user_sb


def ist_today() -> str:
    from datetime import datetime, timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).strftime("%Y-%m-%d")


def sync_daily_stats(access_token: str, user_id: str, date_str: str | None = None):
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
    return payload
