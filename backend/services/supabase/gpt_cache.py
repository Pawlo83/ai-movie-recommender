import json
from typing import Any, Dict, List, Optional
import logging

from clients import supabase
from utils import normalize_request

logger = logging.getLogger(__name__)


def get_cached_gpt_response(
    request_payload: list[dict],
) -> Optional[List[Dict[str, Any]]]:
    """
    Pobiera z cache zapisany wynik rekomendacji AI
    dla znormalizowanego zestawu kryteriów użytkownika.

    Funkcja:
    - normalizuje payload zapytania,
    - wyszukuje najnowszą, aktualną odpowiedź w tabeli gpt_response,
    - zwraca listę rekomendacji lub None, jeżeli cache nie istnieje
      lub wystąpił błąd odczytu.
    """
    if supabase is None:
        return None

    try:
        norm_request = normalize_request(request_payload)
        serialized = json.dumps(
            sorted(norm_request, key=lambda c: (c["tag"].lower(), c["rating"])),
            ensure_ascii=False
        )

        result = (
            supabase
            .table("gpt_response")
            .select("response")
            .eq("request", serialized)
            .eq("is_valid", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as e:
        logger.warning("Błąd odczytu cache z Supabase: %s", e)
        return None

    if not result.data:
        return None

    return result.data[0].get("response")


def save_gpt_response(
    request_payload: list[dict],
    description: str,
    response_payload: List[Dict[str, Any]],
) -> None:
    """
    Zapisuje odpowiedź modelu AI do cache w bazie danych.

    Funkcja:
    - normalizuje zapytanie użytkownika,
    - zapisuje wynik rekomendacji wraz z opisem,
    - oznacza wpis jako aktualny (is_valid = True).
    """
    if supabase is None or not response_payload:
        return

    try:
        norm_request = normalize_request(request_payload)

        supabase.table("gpt_response").insert({
            "request": sorted(norm_request, key=lambda c: (c["tag"].lower(), c["rating"])),
            "response": response_payload,
            "description": description,
            "is_valid": True,
        }).execute()
    except Exception as e:
        logger.warning("Błąd zapisu cache do Supabase: %s", e)


def cache_film(movie: dict, tag_id_map):
    """
    Zapisuje film wygenerowany przez AI do bazy danych
    wraz z przypisanymi tagami.

    Funkcja:
    - wykonuje upsert filmu do tabeli films (is_valid = False),
    - mapuje nazwy tagów na ich identyfikatory,
    - zapisuje relacje film–tag w tabeli films_tags.

    Funkcja wykorzystywana jest do asynchronicznego
    wzbogacania bazy danych na podstawie wyników AI.
    """

    film_payload = {
        "name": movie["title"],
        "tmdb_id": str(movie["tmdb_id"]),
        "release_date": movie["release_date"],
        "director": ", ".join(movie["directors"]),
        "is_valid": False
    }

    film_res = (
        supabase
        .table("films")
        .upsert(film_payload)
        .execute()
    )

    film_id = film_res.data[0]["id"]


    relations = []
    for tag_name in movie["tags"]:
        tag_id = tag_id_map.get(tag_name)
        if not tag_id:
            continue

        relations.append({
            "film_id": film_id,
            "tag_id": tag_id
        })

    supabase.table("films_tags").upsert(
        relations,
        on_conflict="film_id,tag_id"
    ).execute()