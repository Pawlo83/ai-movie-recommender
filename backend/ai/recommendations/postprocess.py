from services.tmdb import tmdb_movie_exists, tmdb_search_by_title, get_providers
from utils import normalize_date


def validate_enrich_recommendations(raw_recs: list[dict]) -> list[dict]:
    """
    Odpowiada za normalizację, walidację oraz wzbogacenie rekomendacji
    zwróconych przez model AI.

    Funkcja:
    - weryfikuje istnienie filmów w TMDB oraz uzupełnia brakujące dane,
    - filtruje niepoprawne lub niezweryfikowane rekordy,
    - przygotowuje finalną strukturę danych gotową do użycia w aplikacji.

    Jest to warstwa post-processingu, w której odpowiedź modelu
    zostaje przekształcona z formatu „AI-output” do formatu wynikowego.
    """
    clean_recs = []
    for item in raw_recs:
        if not isinstance(item, dict):
            continue
        # podstawowy tytuł (wymagany)
        title = item["title"]
        if not title or not isinstance(title, str):
            # pomijamy brak tytułu
            continue
        title = title.strip()

        raw_tmdb = item["candidate_tmdb_id"]
        tmdb_id = int(raw_tmdb) if raw_tmdb else None

        raw_date = item["candidate_release_date"]
        release_date = normalize_date(raw_date)

        overview = item["overview"]

        verification = item["tmdb_id_verification"]
        confidence = item["confidence"]

        synthesized = item["synthesis"]
        if synthesized is None:
            synthesized = True  # domyślnie: film został wygenerowany

        selection_reason = item["selection_reason"]

        # WALIDACJA
        if tmdb_id is not None:
            # jeśli mamy tmdb_id, sprawdź czy istnieje
            movie = tmdb_movie_exists(tmdb_id, title)
            if movie:
                resolved_tmdb_id = int(tmdb_id)
                resolved_release_date = movie["release_date"]
                resolved_poster_path = movie["poster_path"]
                resolved_providers = get_providers(tmdb_id)
            else:
                # jeśli podany id nie istnieje, spróbuj wyszukać po tytule i dacie
                resolved_tmdb_id, resolved_release_date, resolved_poster_path, resolved_providers = tmdb_search_by_title(
                    title,
                    release_date
                )
        else:
            # brak tmdb_id — spróbuj wyszukać po tytule i dacie
            resolved_tmdb_id, resolved_release_date, resolved_poster_path, resolved_providers = tmdb_search_by_title(
                title,
                release_date
            )

        # jeśli po weryfikacji/wykryciu nie mamy tmdb_id, pomiń rekord
        if not resolved_tmdb_id:
            continue
        # Jeżeli nie mamy potwierdzonego release_date, zostaw przybliżony
        if not resolved_release_date:
            resolved_release_date = release_date

        clean_recs.append({
            "title": title,
            "tmdb_id": resolved_tmdb_id,
            "overview": overview,
            "release_date": resolved_release_date,
            "poster_path": resolved_poster_path,
            "providers": resolved_providers,
            "synthesized": bool(synthesized),
            "selection_reason": selection_reason,
            "_meta": {
                "raw_tmdb": raw_tmdb,
                "raw_release_date": raw_date,
                "verification": verification,
                "confidence": confidence
            }
        })

    return clean_recs