import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from services.supabase.films import get_rand_movies
from services.tmdb import get_providers
from services.tmdb.tmdb_service import tmdb_movie_exists, tmdb_search_by_title, get_movie_overview

logger = logging.getLogger(__name__)

@require_GET
def get_default_recommendations(request):
    """
    Zwraca losową listę rekomendacji filmowych.

    Funkcja:
    - losuje filmy z bazy danych,
    - weryfikuje ich istnienie w serwisie TMDB,
    - uzupełnia brakujące dane (opis, plakaty, dostawcy),
    - zwraca gotową listę rekomendacji w formacie JSON.

    Endpoint pełni rolę domyślnych rekomendacji filmowych przy uruchomieniu aplikacji.
    """
    rand_recs = []

    try:
        movie_info = get_rand_movies()

        for item in movie_info:
            tmdb_id = item["tmdb_id"]
            movie = tmdb_movie_exists(tmdb_id, item["name"])
            if movie:
                resolved_tmdb_id = int(tmdb_id)
                resolved_release_date = movie["release_date"]
                resolved_poster_path = movie["poster_path"]
                resolved_providers = get_providers(tmdb_id)

            else:
                resolved_tmdb_id, resolved_release_date, resolved_poster_path, resolved_providers = tmdb_search_by_title(
                    item["name"],
                    item["release_date"]
                )
            resolved_overview = get_movie_overview(resolved_tmdb_id)


            rand_recs.append({
                "title": item["name"],
                "tmdb_id": resolved_tmdb_id,
                "overview": resolved_overview,
                "release_date": resolved_release_date,
                "poster_path": resolved_poster_path,
                "providers": resolved_providers,
                "synthesized": False
            })

    except Exception:
        logger.exception("Błąd przy odczytywaniu losowych rekomendacji")
        return JsonResponse({
            "recommendations" : None
        })

    return JsonResponse({
        "recommendations": rand_recs
    })

