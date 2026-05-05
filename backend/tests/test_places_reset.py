from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db import SessionLocal
from app.main import app
from app.models import ImportLog, Place


client = TestClient(app)


def test_reset_places_requires_token(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "import_run_token", "secret-token")

    response = client.delete("/places/reset")

    assert response.status_code == 401


def test_reset_places_deletes_places_and_logs(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "import_run_token", "secret-token")

    db = SessionLocal()
    try:
        place = Place(
            name="Reset Test Place",
            normalized_name="reset test place",
            address="Test 123",
            normalized_address="test 123",
            city="Tucuman",
            category="bar",
            source="manual",
            source_url="manual",
            is_active=True,
            fetched_at=datetime.now(UTC),
        )
        log = ImportLog(source="test", status="success")
        db.add(place)
        db.add(log)
        db.commit()

        response = client.delete("/places/reset", headers={"Authorization": "Bearer secret-token"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert response.json()["deleted_places"] >= 1
        assert response.json()["deleted_logs"] >= 1
    finally:
        db.close()
