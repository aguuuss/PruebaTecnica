from datetime import UTC, datetime

from app.models import ImportLog
from app.services.slack import SlackImportSummary, SlackNotifier


def test_build_import_payload_includes_counts_fallback_and_scraped_names():
    log = ImportLog(
        id=1,
        source="Tucuman Turismo",
        status="success",
        items_found=3,
        created_count=2,
        updated_count=1,
        duplicate_count=1,
        error_message="Source returned no items, used mock dataset",
        started_at=datetime.now(UTC),
    )
    notifier = SlackNotifier(webhook_url="", preview_limit=2)

    payload = notifier.build_import_payload(
        SlackImportSummary(
            log=log,
            scraped_names=["Bar Uno", "Bar Dos", "Bar Tres"],
            source_items_found=0,
            used_fallback=True,
            fallback_reason="Source returned no items, used mock dataset",
        )
    )

    text = payload["text"]
    assert "Scrapeados desde fuente: 0" in text
    assert "Procesados: 3" in text
    assert "Creados: 2" in text
    assert "Actualizados: 1" in text
    assert "Fallback usado: si" in text
    assert "Items fallback: 3" in text
    assert "Que se scrapeo/proceso: Bar Uno, Bar Dos y 1 mas" in text


def test_build_import_payload_reports_error_without_scraped_items():
    log = ImportLog(
        id=2,
        source="Tucuman Turismo",
        status="error",
        items_found=0,
        created_count=0,
        updated_count=0,
        duplicate_count=0,
        error_message="database unavailable",
        started_at=datetime.now(UTC),
    )
    notifier = SlackNotifier(webhook_url="", preview_limit=10)

    payload = notifier.build_import_payload(SlackImportSummary(log=log, scraped_names=[]))

    text = payload["text"]
    assert "[ERROR]" in text
    assert "Scrapeados desde fuente: 0" in text
    assert "Procesados: 0" in text
    assert "Error: database unavailable" in text
    assert "Que se scrapeo/proceso: sin items" in text
