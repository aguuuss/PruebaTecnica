from datetime import datetime
from difflib import SequenceMatcher
import logging

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ImportLog, Place
from app.services.ai import PlaceAI
from app.services.mock_data import MOCK_PLACES
from app.services.normalization import dedupe_key, normalize_text
from app.services.scraper import ScrapedPlace, TucumanTurismoScraper
from app.services.slack import SlackImportSummary, SlackNotifier

logger = logging.getLogger(__name__)


class PlaceImporter:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.scraper = TucumanTurismoScraper()
        self.ai = PlaceAI()
        self.slack = SlackNotifier()

    def run(self) -> ImportLog:
        log = ImportLog(source=self.scraper.source, status="running")
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        scraped_names: list[str] = []
        source_items_found = 0
        used_fallback = False
        fallback_reason = None

        try:
            scrape_warning = None
            try:
                scraped = self.scraper.fetch(self.settings.source_url)
                source_items_found = len(scraped)
                logger.info(
                    "Scraper fetch completed source_items_found=%s names=%s",
                    source_items_found,
                    [item.name for item in scraped[:20]],
                )
            except Exception as exc:
                scrape_warning = f"Source unavailable, used mock dataset: {exc}"
                logger.exception("Scraper fetch failed")
                scraped = []
            if not scraped:
                used_fallback = True
                fallback_reason = scrape_warning or "Source returned no items, used mock dataset"
                scraped = [ScrapedPlace(**item) for item in MOCK_PLACES]
                log.error_message = fallback_reason
                logger.warning(
                    "Using fallback dataset fallback_reason=%s fallback_count=%s",
                    fallback_reason,
                    len(scraped),
                )
            log.items_found = len(scraped)
            scraped_names = [item.name for item in scraped]

            for item in scraped:
                raw = item.__dict__
                enriched = self.ai.enrich(raw)
                existing = self._find_duplicate(raw)
                payload = {
                    "name": item.name,
                    "normalized_name": normalize_text(item.name, remove_fillers=True),
                    "address": item.address,
                    "normalized_address": normalize_text(item.address),
                    "city": item.city,
                    "category": enriched["category"],
                    "source": item.source,
                    "source_url": item.source_url,
                    "contact": item.contact,
                    "opening_hours": item.opening_hours,
                    "services": item.services,
                    "description": enriched["description"],
                    "is_active": True,
                    "fetched_at": datetime.utcnow(),
                }

                if existing:
                    for key, value in payload.items():
                        if value is not None:
                            setattr(existing, key, value)
                    log.updated_count += 1
                    log.duplicate_count += 1
                else:
                    self.db.add(Place(**payload))
                    log.created_count += 1

            log.status = "success"
            logger.info(
                "Import completed items_found=%s created_count=%s updated_count=%s duplicate_count=%s",
                log.items_found,
                log.created_count,
                log.updated_count,
                log.duplicate_count,
            )
        except Exception as exc:
            log.status = "error"
            log.error_message = str(exc)
            logger.exception("Import failed")
        finally:
            log.finished_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(log)
            self.slack.notify_import_finished(
                SlackImportSummary(
                    log=log,
                    scraped_names=scraped_names,
                    source_items_found=source_items_found,
                    used_fallback=used_fallback,
                    fallback_reason=fallback_reason,
                )
            )

        return log

    def _find_duplicate(self, item: dict) -> Place | None:
        incoming_key = dedupe_key(item["name"], item.get("address"))
        places = self.db.query(Place).all()

        for place in places:
            existing_key = dedupe_key(place.name, place.address)
            if incoming_key and incoming_key == existing_key:
                return place
            score = SequenceMatcher(None, incoming_key, existing_key).ratio()
            if score >= 0.88:
                return place
        return None
