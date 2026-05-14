import difflib
from datetime import datetime
import re
from typing import Optional, List, Any, Generator

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TITLE_SIMILARITY_THRESHOLD = 0.8

def normalize_title(s: Optional[str]) -> str:
    """
    Normalizuje tytuł filmu na potrzeby porównań tekstowych.

    Funkcja:
    - zamienia tekst na lowercase,
    - usuwa znaki niealfanumeryczne,
    - redukuje wielokrotne spacje.
    """
    if not s:
        return ""
    s = s.lower().strip()

    s = re.sub(r"[^\w\s]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s)
    return s


def similarity(a: str, b: str) -> float:
    """
    Oblicza współczynnik podobieństwa dwóch ciągów znaków.

    Wykorzystywana do porównywania tytułów filmów.
    """
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def normalize_date(val):
    """
    Normalizuje datę do formatu YYYY-MM-DD.

    Funkcja akceptuje wyłącznie poprawne daty w formacie ISO
    i zwraca None dla wartości nieprawidłowych.
    """
    if isinstance(val, str):
        s = val.strip()
        # jeśli jest pełna data YYYY-MM-DD -> zaakceptuj po sprawdzeniu
        if DATE_RE.match(s):
            try:
                datetime.strptime(s, "%Y-%m-%d")
                return s
            except ValueError:
                return None
        return None
    return None


def chunk_list(lst: List[Any], chunk_size: int) -> Generator[list[Any], Any, None]:
    """
    Dzieli listę na mniejsze fragmenty (batch'e) o zadanym rozmiarze.

    Funkcja wykorzystywana do ograniczania wielkości zapytań
    do bazy danych.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def normalize_item(item: Any) -> Any:
    """
    Normalizuje pojedynczy element payloadu.

    Dla stringów usuwa zbędne spacje i zamienia na lowercase,
    pozostałe typy zwracane są bez zmian.
    """
    if isinstance(item, str):
        s = re.sub(r"\s+", " ", item).strip().lower()
        return s
    return item


def normalize_request(request_payload: List[Any]) -> List[Any]:
    """
    Normalizuje listę elementów zapytania użytkownika.

    Funkcja wykorzystywana jest do ujednolicania payloadu
    przed zapisem lub odczytem z cache.
    """
    return [normalize_item(x) for x in request_payload]


def unique_by_title(recommendations: list[dict]) -> list[dict]:
    """
    Usuwa duplikaty rekomendacji na podstawie tytułu filmu.

    Zachowuje pierwsze wystąpienie danego tytułu
    i usuwa kolejne duplikaty.
    """
    seen_titles = set()
    unique = []

    for rec in recommendations:
        title = rec.get("title")
        if title not in seen_titles:
            seen_titles.add(title)
            unique.append(rec)

    return unique
