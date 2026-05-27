"""Vercel FastAPI entrypoint.

The application code lives in api.main for local uvicorn and tests. Vercel's
FastAPI detector expects one of a small set of root entrypoint names, so this
module re-exports the same app without duplicating any routes.
"""

from api.main import app

