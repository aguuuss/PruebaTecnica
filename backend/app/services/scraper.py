from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapedPlace:
    name: str
    address: str | None
    city: str | None
    contact: str | None
    opening_hours: str | None
    services: str | None
    source: str
    source_url: str


class TucumanTurismoScraper:
    source = "Tucuman Turismo"

    def fetch(self, url: str) -> list[ScrapedPlace]:
        headers = {
            "User-Agent": "TucumanPlacesAutomator/1.0 (+technical-test; non-aggressive)"
        }
        with httpx.Client(timeout=20, headers=headers, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        return self.parse(response.text, url)

    def parse(self, html: str, url: str) -> list[ScrapedPlace]:
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(".card, article, .item, .contenido")
        candidates = cards or soup.select("li, tr")
        results: list[ScrapedPlace] = []

        for node in candidates:
            text = " ".join(node.get_text(" ", strip=True).split())
            if len(text) < 8:
                continue

            name_node = node.select_one("h1, h2, h3, h4, strong, b, a")
            name = name_node.get_text(" ", strip=True) if name_node else text.split(" - ")[0]
            if not name or len(name) > 120:
                continue

            lowered = text.lower()
            if not any(word in lowered for word in ("bar", "restaurant", "restaurante", "cafe", "café", "comida", "parrilla")):
                continue

            results.append(
                ScrapedPlace(
                    name=name,
                    address=self._extract_after(text, ["Direccion:", "Dirección:", "Domicilio:", "Ubicacion:", "Ubicación:"]),
                    city=self._extract_after(text, ["Localidad:", "Ciudad:"]),
                    contact=self._extract_after(text, ["Telefono:", "Teléfono:", "Contacto:", "WhatsApp:"]),
                    opening_hours=self._extract_after(text, ["Horario:", "Horarios:"]),
                    services=self._extract_after(text, ["Servicios:", "Servicio:"]),
                    source=self.source,
                    source_url=url,
                )
            )

        unique: dict[str, ScrapedPlace] = {}
        for place in results:
            unique.setdefault(place.name.lower(), place)
        return list(unique.values())

    def _extract_after(self, text: str, labels: list[str]) -> str | None:
        for label in labels:
            if label in text:
                tail = text.split(label, 1)[1]
                for stop in [" Direccion:", " Dirección:", " Localidad:", " Telefono:", " Teléfono:", " Horario:", " Servicios:"]:
                    tail = tail.split(stop, 1)[0]
                return tail.strip(" -") or None
        return None
