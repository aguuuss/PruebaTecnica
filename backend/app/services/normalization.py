import re
import unicodedata


FILLER_WORDS = {
    "bar",
    "bares",
    "restaurant",
    "restaurante",
    "restaurantes",
    "tucuman",
    "san",
    "miguel",
    "de",
    "la",
    "el",
    "los",
    "las",
}


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_text(value: str | None, *, remove_fillers: bool = False) -> str:
    if not value:
        return ""
    text = strip_accents(value).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [word for word in text.split() if word]
    if remove_fillers:
        words = [word for word in words if word not in FILLER_WORDS]
    return " ".join(words)


def dedupe_key(name: str, address: str | None = None) -> str:
    name_part = normalize_text(name, remove_fillers=True)
    address_part = normalize_text(address)
    return f"{name_part}|{address_part}".strip("|")
