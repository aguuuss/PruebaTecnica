from app.core.logging import configure_logging
from app.db import SessionLocal, init_db
from app.services.importer import PlaceImporter


def main() -> None:
    configure_logging()
    init_db()
    db = SessionLocal()
    try:
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
    finally:
        db.close()


if __name__ == "__main__":
    main()
