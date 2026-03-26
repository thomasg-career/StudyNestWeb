from flask import Blueprint, jsonify, request

try:
    from backend.supabase_client import sb
except ModuleNotFoundError:
    from supabase_client import sb

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    POST /api/auth/signup
    Body: { email, password, full_name }
    """
    body = request.get_json() or {}
    email     = body.get('email', '').strip()
    password  = body.get('password', '')
    full_name = body.get('full_name', '').strip()

    if not email or not password or not full_name:
        return jsonify({"error": "email, password, and full_name are required"}), 400

    try:
        resp = sb.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}}
        })
        return jsonify({
            "message": "Signup successful! Check your email to confirm.",
            "user_id": resp.user.id if resp.user else None
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Body: { email, password }
    Returns: { access_token, refresh_token, user }
    """
    body     = request.get_json() or {}
    email    = body.get('email', '').strip()
    password = body.get('password', '')

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        resp = sb.auth.sign_in_with_password({"email": email, "password": password})
        return jsonify({
            "access_token":  resp.session.access_token,
            "refresh_token": resp.session.refresh_token,
            "user": {
                "id":    resp.user.id,
                "email": resp.user.email,
                "name":  resp.user.user_metadata.get("full_name", "")
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /api/auth/logout
    Header: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            # Create user-scoped client and sign out
            try:
                from backend.supabase_client import user_sb
            except ModuleNotFoundError:
                from supabase_client import user_sb
            user_sb(token).auth.sign_out()
        except Exception:
            pass  # still return success
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route('/me', methods=['GET'])
def me():
    """
    GET /api/auth/me
    Header: Authorization: Bearer <token>
    Returns current user info.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not authenticated"}), 401
    token = auth_header.split(" ", 1)[1]
    try:
        resp = sb.auth.get_user(token)
        return jsonify({
            "id":    resp.user.id,
            "email": resp.user.email,
            "name":  resp.user.user_metadata.get("full_name", "")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401
