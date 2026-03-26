from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import request, jsonify
from supabase import Client, create_client
import os

load_dotenv(Path(__file__).with_name(".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Shared Supabase client (anon key — used for auth operations)
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def require_auth(f):
    """
    Decorator — every protected route calls this first.
    Expects:  Authorization: Bearer <supabase_access_token>
    Injects:  g.user_id  into the request context.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            # Verify the JWT with Supabase and get the user
            resp = sb.auth.get_user(token)
            if not resp or not resp.user:
                return jsonify({"error": "Invalid or expired token"}), 401
            g.user_id = resp.user.id
            g.access_token = token
        except Exception as e:
            return jsonify({"error": "Auth failed", "detail": str(e)}), 401

        return f(*args, **kwargs)
    return decorated


def user_sb(access_token: str) -> Client:
    """
    Returns a Supabase client authenticated as the current user.
    RLS policies will enforce data isolation automatically.
    """
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Inject the user JWT so RLS kicks in
    client.postgrest.auth(access_token)
    return client
