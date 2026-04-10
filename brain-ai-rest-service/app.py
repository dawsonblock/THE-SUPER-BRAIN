"""Compatibility shim — the canonical runtime is app.app_v2."""

from app.app_v2 import app, create_app  # noqa: F401

__all__ = ["app", "create_app"]
