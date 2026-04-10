"""
Compatibility shim — do not add routes here.

The canonical runtime is app.app_v2.  This module exists only so that any
legacy import of ``app.app`` continues to resolve to the same FastAPI
instance.  All routes, middleware, and configuration live in app_v2.
"""

from .app_v2 import app, create_app  # noqa: F401

__all__ = ["app", "create_app"]
