import os
from typing import Any, Dict, Optional
import logging

from integrations import safe_request
from utils import normalize_title, similarity, TITLE_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

def tmdb_movie_exists(tmdb_id: int, expected_title: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Weryfikuje istnienie filmu w TMDB na podstawie tmdb_id.

    Działanie:
    - wykonuje bezpośrednie zapytanie do endpointu /movie/{id},
    - w przypadku poprawnej odpowiedzi (200) zwraca dane filmu,
    - jeżeli podano expected_title, dodatkowo weryfikuje zgodność tytułu
      przy użyciu porównania rozmytego (fuzzy matching).

    Weryfikacja tytułu:
    - porównywane są różne warianty tytułu zwrócone przez TMDB
      (title, original_title, name, original_name),
    - tytuły są normalizowane przed porównaniem,
    - ostateczna decyzja podejmowana jest na podstawie
      progu TITLE_SIMILARITY_THRESHOLD.
    """
    if not TMDB_API_KEY or tmdb_id is None:
        logger.info("brak TMDB_API_KEY lub tmdb_id is None")
        return None

    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}"
        resp = safe_request(url, params= {"api_key": TMDB_API_KEY}, use_bearer=True)
        if resp.status_code == 200:
            movie = resp.json()

            # jeśli nie podano oczekiwanego tytułu — zwracamy dane
            if not expected_title:
                return movie

            # pobierz najlepszy tytuł z odpowiedzi TMDB do porównania
            tmdb_title_candidates = []
            if movie.get("title"):
                tmdb_title_candidates.append(movie.get("title"))
            if movie.get("original_title"):
                tmdb_title_candidates.append(movie.get("original_title"))
            if movie.get("name"):
                tmdb_title_candidates.append(movie.get("name"))
            if movie.get("original_name"):
                tmdb_title_candidates.append(movie.get("original_name"))


            expected_norm = normalize_title(expected_title)
            best_sim = 0.0
            best_candidate = None
            for cand in tmdb_title_candidates:
                cand_norm = normalize_title(cand)
                sim = similarity(expected_norm, cand_norm)
                if sim > best_sim:
                    best_sim = sim
                    best_candidate = cand

            if best_sim >= TITLE_SIMILARITY_THRESHOLD:
                return movie

            return None

        if resp.status_code == 404:
            logger.error("Nie istnieje")
            return None

        logger.error("Fetch nieudany")
        return None

    except Exception:
        # nie przerywamy całego procesu z powodu błędu sieciowego — traktujemy jak "brak"
        return None

def tmdb_search_by_title(title: str, year: str):
    """
    Wyszukuje film w TMDB na podstawie tytułu i roku produkcji
    i zwraca podstawowe metadane wraz z informacją o streamingach.

    Działanie:
    - wykonuje zapytanie do endpointu /search/movie,
    - filtruje wyniki po roku,
    - preferuje dokładne dopasowanie tytułu,
    - wybiera najlepszego kandydata i pobiera dla niego informacje o streamingach.
    """
    if not TMDB_API_KEY or not title:
        return None, None, None, None

    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {
            "api_key": TMDB_API_KEY,
            "query": title,
            "page": 1,
        }

        resp = safe_request(url, params=params, use_bearer=True)
        if resp.status_code != 200:
            return None, None, None, None

        data = resp.json()
        results = data.get("results") or []
        if not results:
            return None, None, None, None

        # --- normalizacja roku z wejścia ---
        target_year = None
        if isinstance(year, str) and len(year) >= 4:
            try:
                target_year = int(year[:4])
            except ValueError:
                target_year = None

        title_lower = title.strip().lower()
        candidates = []

        for r in results:
            r_title = (r.get("title") or "").strip().lower()
            r_date = r.get("release_date") or ""

            # jeśli podano rok – sprawdzamy zgodność
            if target_year and len(r_date) >= 4:
                try:
                    r_year = int(r_date[:4])
                except ValueError:
                    continue

                if r_year != target_year:
                    continue  # NIEZGODNY ROK → odrzucamy

            # preferuj dokładne dopasowanie tytułu
            score = 2 if r_title == title_lower else 1
            candidates.append((score, r))

        # jeśli po filtrze nie ma kandydatów → ODRZUCAMY FILM
        if not candidates:
            return None, None, None, None

        # sortowanie: najpierw dokładny tytuł, potem reszta
        candidates.sort(key=lambda x: x[0], reverse=True)
        selected_movie = candidates[0][1]

        movie_id = selected_movie.get("id")
        release_date = selected_movie.get("release_date")
        poster_path = selected_movie.get("poster_path")

        providers_list = []

        if movie_id:
            providers_list = get_providers(movie_id)

        if movie_id:
            return int(movie_id), release_date, poster_path, providers_list

        return None, None, None, None

    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        return None, None, None, None


def get_providers(tmdb_id):
    """
    Pobiera listę dostępnych serwisów streamingowych (watch providers)
    dla danego filmu na podstawie jego TMDB ID.

    Funkcja:
    - wykonuje zapytanie do endpointu /watch/providers,
    - ogranicza wynik do rynku PL,
    - zwraca wyłącznie providerów dostępnych w modelu flatrate
      (abonamentowym).
      """
    if not TMDB_API_KEY or not tmdb_id:
        return None
    providers_list = []
    try:
        prov_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/watch/providers"
        prov_resp = safe_request(prov_url, params = {"api_key": TMDB_API_KEY}, use_bearer=True)

        if prov_resp.status_code == 200:
            prov_data = prov_resp.json()
            pl_data = prov_data.get("results", {}).get("PL", {})
            flatrate = pl_data.get("flatrate", [])
            providers_list = [
                {"name": p.get("provider_name"), "logo_path": p.get("logo_path")}
                for p in flatrate
            ]
    except Exception:
        logger.warning("Nie ma movie_id")
        providers_list = []

    return providers_list


def get_director(tmdb_id):
    """
    Pobiera listę reżyserów dla danego filmu na podstawie jego TMDB ID.

    Funkcja:
    - wykonuje zapytanie do endpointu /credits,
    - przeszukuje listę 'crew' w poszukiwaniu osób z job='Director',
    - zwraca listę słowników z imieniem i nazwiskiem (oraz id) reżysera(ów).
    """
    if not TMDB_API_KEY or not tmdb_id:
        return None

    directors_names = []
    try:
        credits_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits"
        cred_resp = safe_request(credits_url, params={"api_key": TMDB_API_KEY}, use_bearer=True)

        if cred_resp.status_code == 200:
            cred_data = cred_resp.json()
            crew = cred_data.get("crew", [])

            # Wyciągamy wszystkich, którzy mają "job": "Director"
            directors_names = [
                member.get("name")
                for member in crew
                if member.get("job") == "Director"
            ]

    except Exception as e:
        logger.warning(f"Błąd pobierania reżyserów dla filmu {tmdb_id}: {e}")
        directors_names = []

    return directors_names


def get_movie_overview(tmdb_id: int, language: str = "en-US") -> Optional[str]:
    """
    Pobiera opis fabuły (overview) filmu z serwisu TMDB.

    Funkcja:
    - wykonuje zapytanie do endpointu /movie/{id},
    - pobiera opis w zadanym języku,
    - zwraca tekst opisu lub None, jeżeli opis nie jest dostępny
      lub wystąpił błąd podczas komunikacji z API.
    """
    if not TMDB_API_KEY or tmdb_id is None:
        logger.info("brak TMDB_API_KEY lub tmdb_id")
        return None

    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}"
        params = {"language": language, "api_key": TMDB_API_KEY}

        resp = safe_request(url, params=params, use_bearer=True)

        if resp.status_code == 200:
            data = resp.json()
            overview = data.get("overview")

            if not overview:
                return None

            return overview

        if resp.status_code == 404:
            return None

        return None

    except Exception as e:
        return None