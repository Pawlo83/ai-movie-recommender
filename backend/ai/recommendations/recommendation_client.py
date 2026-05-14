import json
import logging
from pprint import pformat

from services.supabase.gpt_cache import get_cached_gpt_response, save_gpt_response
from utils import unique_by_title

from ai import extract_recommendations, build_database_movies, validate_enrich_recommendations
from ai.prompts import build_system_prompt, build_instruction_prompt, build_functions_schema, build_message_prompt

from clients import openai_client

logger = logging.getLogger(__name__)
MIN_DB_MOVIES_SEND = 50
MAX_DB_MOVIES_SEND = 150

def get_or_call_openai_recommendations(original_criterions: list[dict], db_mapped_criterions: list[dict], description: str) -> dict:
    """
    Główna funkcja wejściowa do systemu rekomendacji filmów.

    Działanie:
    1. Sprawdza, czy dla przekazanego payloadu (kryteriów użytkownika)
       istnieje już zapisana odpowiedź modelu w cache (Supabase).
    2. Jeżeli cache istnieje – zwraca go bez wykonywania zapytania do OpenAI.
    3. Jeżeli cache nie istnieje – wywołuje OpenAI, zapisuje wynik w Supabase
       i zwraca świeżo wygenerowane rekomendacje.
    """
    cached_response = get_cached_gpt_response(original_criterions)
    if cached_response is not None:
        logger.info("Wysyłam dane z bazy do użytkownika")
        return {
            "recommendations": cached_response,
            "error": None,
            "from_cache": True,
        }

    validated_recommendations = _call_openai_recommendations(original_criterions, db_mapped_criterions)

    if validated_recommendations.get("error") is False:
        recommendations = validated_recommendations.get("recommendations", [])
        save_gpt_response(original_criterions, description, recommendations)

    validated_recommendations["from_cache"] = False
    return validated_recommendations


def _call_openai_recommendations(original_criterions: list[dict], db_mapped_criterions: list[dict]) -> dict:
    """
    Bezpośrednio komunikuje się z OpenAI w celu wygenerowania rekomendacji.

    Funkcja:
    - pobiera z bazy danych odfiltrowaną pulę filmów
    - buduje payload wejściowy (system prompt, instrukcje, dane z bazy filmów),
    - wywołuje model OpenAI z mechanizmem function calling,
    - parsuje surową odpowiedź modelu,
    - waliduje i wzbogaca końcowy wynik.
    """
    try:
        logger.info(pformat(original_criterions, sort_dicts=False))

        movies_from_db = build_database_movies(db_mapped_criterions, MIN_DB_MOVIES_SEND, MAX_DB_MOVIES_SEND)
        #movies_from_db = build_database_movies(limit=MAX_DB_MOVIES_SEND)

        system = build_system_prompt()
        msg_payload = build_instruction_prompt(movies_from_db, original_criterions)
        msg = build_message_prompt(original_criterions)
        function_schema = build_functions_schema()

        messages: list = [
            system,
            {
                "role": "user",
                "content": "Dane z bazy (JSON) z instrukcjami:\n\n" + json.dumps(
                    msg_payload,
                    ensure_ascii=False
                )
            },
            msg
        ]

        logger.info("Wysłano do AI.")

        completion = openai_client.chat.completions.create(
            model="gpt-5-mini",
            messages=messages,
            functions=function_schema,
            function_call="auto"
        )

        logger.info("Odpowiedź od AI - PRZED obróbką:")

        raw_recommendations = extract_recommendations(completion)
        logger.info(pformat(raw_recommendations, width=160, sort_dicts=False))


        logger.info("Odpowiedź PO obróbce:")

        validated_recommendations = validate_enrich_recommendations(raw_recommendations)
        validated_recommendations = unique_by_title(validated_recommendations)
        logger.info(json.dumps(validated_recommendations, indent=2, ensure_ascii=False))
        return {"error": False, "recommendations": validated_recommendations}

    except Exception as e:
        logger.exception("Błąd w rekomendacji AI")
        return {"error": str(e), "recommendations": []}