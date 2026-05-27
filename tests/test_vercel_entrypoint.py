from fastapi import FastAPI

from app import app


def test_vercel_entrypoint_exports_fastapi_app():
    assert isinstance(app, FastAPI)

