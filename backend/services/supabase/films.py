from typing import Any, Dict, List, Optional
import logging

from clients import supabase
from utils import chunk_list

logger = logging.getLogger(__name__)

def count_films_with_tags(and_tags: List[str], or_tags: List[str]) -> int:
    """
    Zwraca dokładną liczbę filmów w bazie, które spełniają podane kryteria tagów.
    """
    resp = supabase.rpc("count_films_by_tags", {"p_and_tags": and_tags, "p_or_tags": or_tags}).execute()
    count_val = int(resp.data) if resp.data is not None else 0
    logger.info(f"Filmów w count: {count_val} dla AND: {and_tags}, OR: {or_tags}")
    return count_val

def get_taged_films(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Zwraca listę filmów wraz z przypisanymi tagami.

    Funkcja:
    - pobiera filmy z tabeli `films`,
    - pobiera relacje film–tag z tabeli `films_tags`,
    - mapuje identyfikatory tagów na ich nazwy,
    - zwraca listę filmów wzbogaconą o pole `tags`.

    Dane pobierane są partiami w celu ograniczenia liczby zapytań
    i zachowania wydajności.
    """
    try:
        q = (
            supabase
            .table("films")
            .select("id,name,release_date,director,tmdb_id")
            .eq("is_valid", True)
            .order("release_date", desc=True)
        )
        if limit is not None:
            q = q.limit(limit)
        if offset is not None:
            q = q.offset(offset)

        resp = q.execute()
        films = resp.data or []
    except Exception:
        logger.exception("Błąd przy pobieraniu filmów z bazy Supabase")
        raise

    if not films:
        return []

    film_ids = [str(f["id"]) for f in films if f.get("id")]

    ft_rows = []
    for batch in chunk_list(film_ids, 25):
        try:
            r = (
                supabase
                .table("films_tags")
                .select("film_id,tag_id")
                .in_("film_id", batch)
                .execute()
            )
            if r.data:
                ft_rows.extend(r.data)
        except Exception:
            logger.exception("Błąd przy pobieraniu filmów z bazy Supabase")

    if not ft_rows:
        return [{**f, "tags": []} for f in films]

    tag_ids = list({str(r["tag_id"]) for r in ft_rows if r.get("tag_id")})
    tag_map: Dict[str, str] = {}

    for batch in chunk_list(tag_ids, 200):
        try:
            r = (
                supabase
                .table("tags")
                .select("id,tag_name")
                .in_("id", batch)
                .execute()
            )
            for t in r.data or []:
                tag_map[str(t["id"])] = t["tag_name"]
        except Exception:
            logger.exception("Błąd przy pobieraniu filmów z bazy Supabase")

    film_to_tags = {fid: [] for fid in film_ids}
    for r in ft_rows:
        fid, tid = str(r["film_id"]), str(r["tag_id"])
        if tid in tag_map:
            film_to_tags[fid].append(tag_map[tid])

    return [
        {
            **f,
            "tags": film_to_tags.get(str(f["id"]), [])
        }
        for f in films
    ]

def get_taged_films_with_tags(
    and_tags: Optional[List[str]] = None,
    or_tags: Optional[List[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """get_taged_films_with_tags
    Zwraca listę filmów wraz z przypisanymi tagami przefiltrowaną przez logikę AND/OR dla tagów.

    Funkcja:
    - wyołuje procedurę RPC w Supabase, aby otrzymać ID przefiltrowanych filmów,
    - pobiera filmy z tabeli `films` dla otrzymanych ID,
    - pobiera relacje film–tag z tabeli `films_tags`,
    - mapuje identyfikatory tagów na ich nazwy,
    - zwraca listę filmów wzbogaconą o pole `tags`.

    Dane pobierane są partiami w celu ograniczenia liczby zapytań
    i zachowania wydajności.
    """
    and_tags = and_tags or []
    or_tags = or_tags or []

    try:
        rpc_resp = supabase.rpc("get_filtered_film_ids", {
            "p_and_tags": and_tags,
            "p_or_tags": or_tags,
            "p_limit": limit,
            "p_offset": offset
        }).execute()
        
        matched_ids = [str(row["id"]) for row in rpc_resp.data or []]
        
    except Exception:
        logger.exception("Błąd przy pobieraniu wyfiltrowanych ID z RPC")
        raise

    if not matched_ids:
        return []

    try:
        q = (
            supabase
            .table("films")
            .select("id,name,release_date,director,tmdb_id")
            .in_("id", matched_ids)
            .order("release_date", desc=True)
        )
        resp = q.execute()
        films = resp.data or []
        films.sort(key=lambda f: matched_ids.index(str(f["id"])))

    except Exception:
        logger.exception("Błąd przy pobieraniu metadanych filmów z bazy Supabase")
        raise

    if not films:
        return []

    film_ids = [str(f["id"]) for f in films if f.get("id")]

    ft_rows = []
    for batch in chunk_list(film_ids, 25):
        try:
            r = (
                supabase
                .table("films_tags")
                .select("film_id,tag_id")
                .in_("film_id", batch)
                .execute()
            )
            if r.data:
                ft_rows.extend(r.data)
        except Exception:
            logger.exception("Błąd przy pobieraniu relacji z films_tags")

    if not ft_rows:
        return [{**f, "tags": []} for f in films]

    tag_ids = list({str(r["tag_id"]) for r in ft_rows if r.get("tag_id")})
    tag_map: Dict[str, str] = {}

    for batch in chunk_list(tag_ids, 200):
        try:
            r = (
                supabase
                .table("tags")
                .select("id,tag_name")
                .in_("id", batch)
                .execute()
            )
            for t in r.data or []:
                tag_map[str(t["id"])] = t["tag_name"]
        except Exception:
            logger.exception("Błąd przy pobieraniu nazw tagów z bazy Supabase")

    film_to_tags = {fid: [] for fid in film_ids}
    for r in ft_rows:
        fid, tid = str(r["film_id"]), str(r["tag_id"])
        if tid in tag_map:
            film_to_tags[fid].append(tag_map[tid])

    return [
        {
            **f,
            "tags": film_to_tags.get(str(f["id"]), [])
        }
        for f in films
    ]

def get_rand_movies(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Zwraca losową listę filmów z bazy danych.

    Funkcja wykorzystuje procedurę RPC po stronie Supabase
    do losowego wyboru rekordów i zwraca podstawowe metadane
    niezbędne do generowania domyślnych rekomendacji.
    """
    resp = supabase.rpc("get_random_films", {}).execute()
    rows = resp.data or []

    if limit:
        rows = rows[:limit]

    return [
        {"name": r["name"], "release_date": r["release_date"], "tmdb_id" : r["tmdb_id"]}
        for r in rows
    ]

def check_existing_tmdb_ids(tmdb_ids: list[int]) -> set[int]:
    """
    Weryfikuje, które z podanych identyfikatorów TMDB znajdują się już w naszej bazie danych.
    """
    if not tmdb_ids:
        return set()
    try:
        string_ids = [str(tid) for tid in tmdb_ids]
        response = supabase.table('films').select('tmdb_id').in_('tmdb_id', string_ids).execute()
        if response.data:
            return {int(item['tmdb_id']) for item in response.data}
        return set()
    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania istniejących tmdb_id w bazie: {e}")
        return set()