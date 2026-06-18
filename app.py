"""Vercel / WSGI entrypoint — exposes Flask app at a default location."""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.chat_server import app  # noqa: E402, F401

__all__ = ["app"]
