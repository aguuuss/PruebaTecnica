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
    stop_markers = {
        "enlaces útiles",
        "casa de tucumán",
        "anexo ente tucumán turismo",
    }
    field_prefixes = (
        "dirección:",
        "direccion:",
        "domicilio:",
        "ubicación:",
        "ubicacion:",
        "localidad:",
        "ciudad:",
        "horarios de atención:",
        "horario de atención:",
        "horario:",
        "horarios:",
        "contacto:",
        "teléfono:",
        "telefono:",
        "whatsapp:",
        "servicios:",
        "servicio:",
    )

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
        results = self._parse_nodes(candidates, url)
        if len(results) <= 1:
            results = self._merge_results(results, self._parse_structured_text(soup, url))

        unique: dict[str, ScrapedPlace] = {}
        for place in results:
            key = f"{place.name.lower()}|{(place.address or '').lower()}"
            unique.setdefault(key, place)
        return list(unique.values())

    def _parse_nodes(self, candidates, url: str) -> list[ScrapedPlace]:
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
        return results

    def _parse_structured_text(self, soup: BeautifulSoup, url: str) -> list[ScrapedPlace]:
        lines = [
            " ".join(line.split())
            for line in soup.get_text("\n").splitlines()
            if " ".join(line.split())
        ]
        results: list[ScrapedPlace] = []
        current_name: str | None = None
        current_fields: dict[str, list[str] | str | None] = {
            "address": [],
            "city": None,
            "contact": [],
            "opening_hours": [],
            "services": [],
        }
        in_listing = False

        for line in lines:
            lowered = line.lower()
            if line == "Bares y Restaurantes":
                in_listing = True
                continue
            if not in_listing:
                continue
            if lowered in self.stop_markers:
                break
            if line == "Compartir" or line == "Conocé los principales bares y restaurantes de la provincia.":
                continue

            if self._is_name_line(line):
                if current_name:
                    place = self._build_place(current_name, current_fields, url)
                    if place:
                        results.append(place)
                current_name = line
                current_fields = {
                    "address": [],
                    "city": None,
                    "contact": [],
                    "opening_hours": [],
                    "services": [],
                }
                continue

            if not current_name:
                continue

            self._consume_field_line(current_fields, line)

        if current_name:
            place = self._build_place(current_name, current_fields, url)
            if place:
                results.append(place)

        return results

    def _consume_field_line(self, fields: dict[str, list[str] | str | None], line: str) -> None:
        lowered = line.lower()
        if lowered.startswith(("dirección:", "direccion:", "domicilio:", "ubicación:", "ubicacion:")):
            value = line.split(":", 1)[1].strip(" .")
            if value:
                address = fields["address"]
                if isinstance(address, list):
                    address.append(value)
        elif lowered.startswith(("localidad:", "ciudad:")):
            fields["city"] = line.split(":", 1)[1].strip(" .") or None
        elif lowered.startswith(("horarios de atención:", "horario de atención:", "horario:", "horarios:")):
            value = line.split(":", 1)[1].strip(" .")
            if value:
                opening_hours = fields["opening_hours"]
                if isinstance(opening_hours, list):
                    opening_hours.append(value)
        elif lowered.startswith(("contacto:", "teléfono:", "telefono:", "whatsapp:")):
            value = line.split(":", 1)[1].strip(" .")
            if value:
                contact = fields["contact"]
                if isinstance(contact, list):
                    contact.append(value)
        elif lowered.startswith(("servicios:", "servicio:")):
            value = line.split(":", 1)[1].strip(" .")
            if value:
                services = fields["services"]
                if isinstance(services, list):
                    services.append(value)

    def _build_place(self, name: str, fields: dict[str, list[str] | str | None], url: str) -> ScrapedPlace | None:
        if len(name) > 120:
            return None
        address = " | ".join(fields["address"]) if isinstance(fields["address"], list) else fields["address"]
        contact = " / ".join(fields["contact"]) if isinstance(fields["contact"], list) else fields["contact"]
        opening_hours = " / ".join(fields["opening_hours"]) if isinstance(fields["opening_hours"], list) else fields["opening_hours"]
        services = " / ".join(fields["services"]) if isinstance(fields["services"], list) else fields["services"]
        return ScrapedPlace(
            name=name,
            address=address or None,
            city=fields["city"] if isinstance(fields["city"], str) else None,
            contact=contact or None,
            opening_hours=opening_hours or None,
            services=services or None,
            source=self.source,
            source_url=url,
        )

    def _is_name_line(self, line: str) -> bool:
        lowered = line.lower()
        if len(line) < 3 or len(line) > 120:
            return False
        if lowered in self.stop_markers:
            return False
        if lowered.startswith(self.field_prefixes):
            return False
        if line in {"Bares y Restaurantes", "Compartir"}:
            return False
        if line.startswith("http") or line.startswith("www."):
            return False
        return True

    def _merge_results(self, primary: list[ScrapedPlace], fallback: list[ScrapedPlace]) -> list[ScrapedPlace]:
        merged: dict[str, ScrapedPlace] = {}
        for place in primary + fallback:
            key = f"{place.name.lower()}|{(place.address or '').lower()}"
            existing = merged.get(key)
            if not existing or self._completeness(place) > self._completeness(existing):
                merged[key] = place
        return list(merged.values())

    def _completeness(self, place: ScrapedPlace) -> int:
        return sum(
            1 for value in (place.address, place.city, place.contact, place.opening_hours, place.services) if value
        )

    def _extract_after(self, text: str, labels: list[str]) -> str | None:
        for label in labels:
            if label in text:
                tail = text.split(label, 1)[1]
                for stop in [" Direccion:", " Dirección:", " Localidad:", " Telefono:", " Teléfono:", " Horario:", " Servicios:"]:
                    tail = tail.split(stop, 1)[0]
                return tail.strip(" -") or None
        return None
