from __future__ import annotations

import os
import pytest

from app import create_app


@pytest.fixture(scope="function")
def app():
    # Use SQLite in-memory database for tests
    os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
    application = create_app(os.environ["DATABASE_URL"])
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
