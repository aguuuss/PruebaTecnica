import logging

from app.core.logging import configure_logging
from app.db import SessionLocal, init_db
from app.services.importer import PlaceImporter
from app.services.scraper import TucumanTurismoScraper
from app.services.slack import SlackNotifier

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()
    notifier = SlackNotifier()
    scraper = TucumanTurismoScraper()
    db = None
    try:
        init_db()
        db = SessionLocal()
        log = PlaceImporter(db).run()
        print(
            {
                "status": log.status,
                "items_found": log.items_found,
                "created": log.created_count,
                "updated": log.updated_count,
                "duplicates": log.duplicate_count,
                "error": log.error_message,
            }
        )
    except Exception as exc:
        logger.exception("Import job failed before completion")
        notifier.notify_job_failure(source=scraper.source, error_message=str(exc))
        raise
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
