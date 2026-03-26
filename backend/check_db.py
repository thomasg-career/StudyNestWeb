import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).with_name(".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    try:
        resp = sb.from_('daily_stats').select('tasks_pending').limit(1).execute()
        print("tasks_pending exists!")
        print(resp)
    except Exception as e:
        print(f"Error selecting tasks_pending: {e}")
        
    try:
        resp = sb.from_('daily_stats').select('habits_pending').limit(1).execute()
        print("habits_pending exists!")
    except Exception as e:
        print(f"Error selecting habits_pending: {e}")

if __name__ == '__main__':
    main()
