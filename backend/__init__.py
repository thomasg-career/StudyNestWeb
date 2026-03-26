try:
    from backend.app import create_app
except ModuleNotFoundError:
    from app import create_app

__all__ = ["create_app"]
