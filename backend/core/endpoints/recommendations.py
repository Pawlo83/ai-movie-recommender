import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from semantic_tagger import analyze_text, map_tags_to_db
from ai import get_or_call_openai_recommendations, tagger
from concurrent.futures import ThreadPoolExecutor
from services.supabase.films import check_existing_tmdb_ids

from services.tmdb.tmdb_service import get_director

executor = ThreadPoolExecutor(max_workers=4)
logger = logging.getLogger(__name__)

@require_POST
def recommendations_json(request):
    """
    Główny endpoint generowania rekomendacji filmowych.

    Funkcja:
    - parsuje kryteria użytkownika oraz opis tekstowy zapytania,
    - uzupełnia kryteria o tagi wykryte automatycznie (NLP),
    - wywołuje silnik rekomendacji oparty o model AI,
    - asynchronicznie uruchamia proces tagowania filmów wygenerowanych przez model,
    - zwraca listę rekomendowanych filmów w formacie JSON.
    """
    try:
        payload = json.loads(request.body)
    except Exception:
        logger.exception("Błąd parsowania request body w recommendations_json")
        payload = {}

    req = payload["req"]
    criterions_raw = req["criterions"] or []
    description = req["description"] or ""

    original_criterions = []
    for c in criterions_raw:
        if not isinstance(c, dict):
            continue
        tag = c["value"]
        rating = c["rating"]

        original_criterions.append({"tag": tag.strip(), "rating": rating})

    if description:
        tags_from_description = analyze_text(description)

        existing_tags = {item['tag'] for item in original_criterions}

        for c in tags_from_description:
            if not isinstance(c, dict):
                continue
            
            tag = c["tag"]
            rating = c["rating"]

            if tag not in existing_tags:
                original_criterions.append({"tag": tag, "rating": rating})
                existing_tags.add(tag)

    if not original_criterions:
        return JsonResponse({
            "error": True,
            "recommendations": []
        })

    db_mapped_criterions = map_tags_to_db(original_criterions)
    db_mapped_criterions_positive = [c for c in db_mapped_criterions if c['rating'] > 0]

    resp = get_or_call_openai_recommendations(original_criterions, db_mapped_criterions_positive, description)

    if resp["recommendations"] and not resp["from_cache"]:
        movies_to_save = []
        synthesized_movies = [m for m in resp["recommendations"] if m.get("synthesized")]
        if synthesized_movies:
            existing_ids = check_existing_tmdb_ids([m["tmdb_id"] for m in synthesized_movies])
            for movie in synthesized_movies:
                tmdb_id = movie["tmdb_id"]
                if tmdb_id not in existing_ids:
                    directors_list = get_director(tmdb_id)
                    movie_data = {
                        "title": movie["title"],
                        "release_date": movie["release_date"],
                        "tmdb_id": tmdb_id,
                        "directors": directors_list
                    }
                    movies_to_save.append(movie_data)

        if len(movies_to_save) > 0:
            logger.info("Wysyłam %d wygenerowanych przez AI filmów do taggera", len(movies_to_save))
            executor.submit(tagger, movies_to_save)
        else:
            logger.info("Wszystkie wygenerowane filmy są już zapisane w bazie danych.")

    return JsonResponse({
        "error": resp["error"],
        "recommendations": resp["recommendations"]
    })

