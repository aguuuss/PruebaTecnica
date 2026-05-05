from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


client = TestClient(app)


def test_run_import_requires_configured_token(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "import_run_token", None)

    response = client.post("/imports/run")

    assert response.status_code == 503
    assert response.json()["detail"] == "Import token is not configured"


def test_run_import_rejects_missing_or_invalid_token(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "import_run_token", "secret-token")

    missing = client.post("/imports/run")
    invalid = client.post("/imports/run", headers={"Authorization": "Bearer nope"})

    assert missing.status_code == 401
    assert missing.json()["detail"] == "Missing bearer token"
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid bearer token"
