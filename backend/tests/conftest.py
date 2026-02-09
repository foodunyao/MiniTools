import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """Creates a test client for FastAPI"""
    return TestClient(app)
