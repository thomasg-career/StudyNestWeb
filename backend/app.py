from flask import Flask
from flask_cors import CORS

try:
    from backend.routes.auth import auth_bp
    from backend.routes.habits import habits_bp
    from backend.routes.mood import mood_bp
    from backend.routes.notes import notes_bp
    from backend.routes.stats import stats_bp
    from backend.routes.tasks import tasks_bp
    from backend.routes.user_profile import profile_bp
except ModuleNotFoundError:
    from routes.auth import auth_bp
    from routes.habits import habits_bp
    from routes.mood import mood_bp
    from routes.notes import notes_bp
    from routes.stats import stats_bp
    from routes.tasks import tasks_bp
    from routes.user_profile import profile_bp


def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(habits_bp, url_prefix="/api/habits")
    app.register_blueprint(mood_bp, url_prefix="/api/mood")
    app.register_blueprint(notes_bp, url_prefix="/api/notes")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
