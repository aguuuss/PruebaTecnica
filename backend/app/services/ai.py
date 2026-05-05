import json
import logging

from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class PlaceAI:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def enrich(self, item: dict) -> dict:
        if not self.client:
            logger.info("AI disabled, using fallback name=%s", item.get("name"))
            return self._fallback(item)

        prompt = {
            "name": item.get("name"),
            "address": item.get("address"),
            "city": item.get("city"),
            "services": item.get("services"),
            "opening_hours": item.get("opening_hours"),
        }
        logger.info("AI request name=%s payload=%s", item.get("name"), json.dumps(prompt, ensure_ascii=False))
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Clasifica bares/restaurantes de Tucuman. "
                            "Responde solo JSON con category y description. "
                            "category debe ser una de: bar, restaurante, cafe, pizzeria, "
                            "heladeria, pasteleria, regional, boliche, otro."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            raw_content = response.choices[0].message.content or "{}"
            logger.info("AI response name=%s raw=%s", item.get("name"), raw_content)
            data = json.loads(raw_content)
            enriched = {
                "category": data.get("category") or self._fallback_category(item),
                "description": data.get("description") or self._fallback_description(item),
            }
            logger.info("AI enrichment applied name=%s result=%s", item.get("name"), enriched)
            return enriched
        except Exception:
            logger.exception("AI request failed, using fallback name=%s", item.get("name"))
            return self._fallback(item)

    def _fallback(self, item: dict) -> dict:
        fallback = {
            "category": self._fallback_category(item),
            "description": self._fallback_description(item),
        }
        logger.info("AI fallback result name=%s result=%s", item.get("name"), fallback)
        return fallback

    def _fallback_category(self, item: dict) -> str:
        text = " ".join(
            str(item.get(key) or "").lower()
            for key in ("name", "services", "opening_hours")
        )
        if "pizza" in text:
            return "pizzeria"
        if "helad" in text:
            return "heladeria"
        if "cafe" in text or "café" in text:
            return "cafe"
        if "pastel" in text or "panader" in text:
            return "pasteleria"
        if "regional" in text or "empanad" in text:
            return "regional"
        if "rest" in text or "parrilla" in text:
            return "restaurante"
        return "bar"

    def _fallback_description(self, item: dict) -> str:
        name = item.get("name") or "Lugar"
        city = item.get("city") or "Tucuman"
        category = self._fallback_category(item)
        return f"{name} es una opcion de tipo {category} ubicada en {city}."
