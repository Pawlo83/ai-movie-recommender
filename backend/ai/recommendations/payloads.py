from services.supabase.films import get_taged_films_with_tags, count_films_with_tags, get_taged_films
import logging

logger = logging.getLogger(__name__)

def build_database_movies(db_mapped_criterions: list[dict], min_limit: int, max_limit: int) -> list[dict]:
    """
    Przygotowuje i normalizuje listę filmów pochodzących z bazy danych
    do postaci przekazywanej w payloadzie do modelu.

    Funkcja:
    - sortuje tagi od najwyżej ocenianego
    - ogranicza liczbę filmów poprzez dostosowanie ilości użytych filtrów 
    - mapuje wewnętrzną strukturę danych na uproszczony format wejściowy modelu,

    Odpowiada za przygotowanie danych wejściowych do modelu.
    """

    try:
        sorted_tags = sorted(db_mapped_criterions, key=lambda x: x.get('rating', 0), reverse=True)
        tags_only = [t['tag'] for t in sorted_tags]

        if not tags_only:
            logger.info("Brak zmapowanych tagów. Pobieranie domyślnej listy filmów.")
            database_movies = get_taged_films(limit=((max_limit+min_limit)//2))
        else:
            current_and_tags = [tags_only[0]]
            current_or_tags = []
            i = 1
            count = count_films_with_tags(current_and_tags, current_or_tags)

            if count < min_limit and len(tags_only) > 1:
                logger.info(f"Główny tag daje {count} filmów, przechodzę w PURE OR.")
                last_tag = current_and_tags.pop()
                current_or_tags = [last_tag]
            else:
                while i < len(tags_only) and count > max_limit:
                    current_and_tags.append(tags_only[i])
                    count = count_films_with_tags(current_and_tags, current_or_tags)
                    i += 1
                    if count < min_limit:
                        last_tag = current_and_tags.pop()
                        current_or_tags = [last_tag]
                        break 
            count_and = count_films_with_tags(current_and_tags, []) 

            while i < len(tags_only) and count < min_limit:
                current_or_tags.append(tags_only[i])
                count = count_films_with_tags(current_and_tags, current_or_tags)
                
                if count >= min_limit:
                    break
                elif count > max_limit and i+1 < len(tags_only):
                    current_or_tags.pop()
                i += 1
            
            count = count_films_with_tags(current_and_tags, current_or_tags)
            if count < min_limit:
                if current_and_tags and count_and >= min_limit:
                    logger.info(f"OR zwrócił za mało filmów, wracam do czystego AND.")
                    current_or_tags = []
                    count = count_and
                else:
                    logger.info(f"Za mało filmów, wykorzystuje dopełnianie.")
            logger.info(f"Ostateczne filtry bazy ({count} filmów) - AND: {current_and_tags}, OR: {current_or_tags}")
            
            database_movies = get_taged_films_with_tags(current_and_tags, current_or_tags, max_limit)
            movies = [
                {
                    "id": f["id"],
                    "title": f["name"],
                    "release_date": f["release_date"],
                    "director": f["director"],
                    "tmdb_id": f["tmdb_id"],
                    "tags": f["tags"]
                }
                for f in database_movies
            ]     

            if len(movies) < min_limit:
                missing_amount = ((min_limit+max_limit)//2) - len(movies)
                logger.info(f"Wynik poniżej minimum ({len(movies)}). Dobieram {missing_amount} domyślnych filmów.")
                padding_raw = get_taged_films(limit=missing_amount + len(movies))
                
                existing_ids = {m["id"] for m in movies}
                added = 0
                for f in padding_raw:
                    if f["id"] not in existing_ids:
                        movies.append({
                            "id": f["id"],
                            "title": f["name"],
                            "release_date": f.get("release_date", ""),
                            "director": f.get("director", ""),
                            "tmdb_id": f.get("tmdb_id", ""),
                            "tags": f.get("tags", [])
                        })
                        existing_ids.add(f["id"])
                        added += 1
                    if added >= missing_amount:
                        break
  
        return movies[:max_limit]

    except Exception as e:
        logger.exception("Nie udało się pobrać filmów z bazy danych (Preagregacja): %s", e)
        return []