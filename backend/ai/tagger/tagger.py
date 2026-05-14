import json
import logging
from pprint import pformat

from services.supabase.gpt_cache import cache_film
from services.supabase.tags import get_tags, get_tag_id_map
from ai.prompts import build_tagging_system_prompt, build_tagging_function_schema
from clients import openai_client

logger = logging.getLogger(__name__)

def tagger(movies: list[dict]):
    """
    Odpowiada za automatyczne przypisanie tagów do filmów
    z wykorzystaniem OpenAI API.

    Funkcja:
    - przekazuje listę filmów oraz słownik dozwolonych tagów do modelu AI,
    - wykorzystuje mechanizm function calling do uzyskania ustrukturyzowanej odpowiedzi,
    - mapuje wygenerowane tagi na filmy na podstawie identyfikatora TMDB,
    - zapisuje wzbogacone dane w bazie danych Supabase.

    Funkcja nie zwraca wartości — jej efektem jest dodanie do bazy
    danych filmów wraz z przypisanymi tagami.
    """
    try:
        logger.info("Filmy wejściowe:")
        logger.info(pformat(movies, width=160))

        tags_from_db = get_tags()

        system = build_tagging_system_prompt()

        payload = {
            "available_tags": tags_from_db,
            "movies": movies
        }

        user_msg = {
            "role": "user",
            "content": (
                "Na podstawie dostępnych tagów przypisz każdemu filmowi odpowiednie etykiety.\n\n"
                "Dane wejściowe (JSON):\n\n"
                + json.dumps(payload, ensure_ascii=False)
            )
        }

        completion = openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[system, user_msg],
            functions=build_tagging_function_schema(),
            function_call="auto"
        )

        raw = completion.choices[0].message.function_call.arguments
        parsed = json.loads(raw)

        logger.info("Odpowiedź AI (raw):")
        logger.info(json.dumps(parsed, indent=2, ensure_ascii=False))

        tags_by_tmdb = {
            m["tmdb_id"]: m["tags"]
            for m in parsed["movies"]
        }

        enriched = []
        for movie in movies:
            enriched.append({
                **movie,
                "tags": tags_by_tmdb.get(movie["tmdb_id"], [])
            })

        tag_map = get_tag_id_map()

        for movie in enriched:
            cache_film(movie, tag_map)

    except Exception:
        logger.exception("Błąd w tagowaniu filmów")
