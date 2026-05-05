from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.models import ImportLog


@dataclass
class SlackImportSummary:
    log: ImportLog
    scraped_names: list[str]
    source_items_found: int | None = None
    used_fallback: bool = False
    fallback_reason: str | None = None


class SlackNotifier:
    def __init__(self, webhook_url: str | None = None, preview_limit: int | None = None) -> None:
        settings = get_settings()
        self.webhook_url = webhook_url if webhook_url is not None else settings.slack_webhook_url
        self.preview_limit = preview_limit if preview_limit is not None else settings.slack_scrape_preview_limit

    def notify_import_finished(self, summary: SlackImportSummary) -> None:
        if not self.webhook_url:
            return

        payload = self.build_import_payload(summary)
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
        except Exception:
            return

    def build_import_payload(self, summary: SlackImportSummary) -> dict[str, str]:
        log = summary.log
        status_label = "OK" if log.status == "success" else "ERROR"
        fallback_label = "si" if summary.used_fallback else "no"

        lines = [
            f"[{status_label}] Importacion de lugares",
            f"Fuente: {log.source}",
            f"Estado: {log.status}",
            f"Scrapeados desde fuente: {summary.source_items_found if summary.source_items_found is not None else log.items_found}",
            f"Procesados: {log.items_found}",
            f"Creados: {log.created_count}",
            f"Actualizados: {log.updated_count}",
            f"Duplicados: {log.duplicate_count}",
            f"Fallback usado: {fallback_label}",
        ]

        if summary.used_fallback:
            lines.append(f"Items fallback: {len(summary.scraped_names)}")

        if summary.fallback_reason:
            lines.append(f"Motivo fallback/error: {summary.fallback_reason}")
        elif log.error_message:
            lines.append(f"Error: {log.error_message}")

        lines.append(f"Que se scrapeo/proceso: {self._format_names(summary.scraped_names)}")
        return {"text": "\n".join(lines)}

    def _format_names(self, names: list[str]) -> str:
        if not names:
            return "sin items"

        visible = names[: self.preview_limit]
        suffix = ""
        hidden_count = len(names) - len(visible)
        if hidden_count > 0:
            suffix = f" y {hidden_count} mas"
        return ", ".join(visible) + suffix
