from typing import Any, Tuple
from clients import supabase
from services.supabase.tags import get_tag_id_by_name


def film_tags_controller(
    *,
    action: str,
    film_id: str,
    tag_name: str | None = None,
) -> Tuple[bool, Any]:
    """
    Zarządza przypisaniem tagów do filmów.

    Funkcja obsługuje operacje:
    - get – pobranie listy tagów przypisanych do filmu,
    - add – dodanie tagu do filmu,
    - remove – usunięcie tagu z filmu.

    Wynik zwracany jest w postaci informacji o powodzeniu operacji lub błędzie.
    """
    if action == "get":
        resp = (
            supabase
            .table("films_tags")
            .select("tags(tag_name)")
            .eq("film_id", film_id)
            .execute()
        )
        tags = [
            r["tags"]["tag_name"]
            for r in resp.data or []
            if r.get("tags")
        ]
        return True, tags

    if action in {"add", "remove"}:
        if not tag_name:
            return False, {"error": "Missing tag_name"}

        tag_id = get_tag_id_by_name(tag_name)
        if not tag_id:
            return False, {"error": "Tag does not exist"}

        q = supabase.table("films_tags")

        if action == "add":
            q = q.insert({"film_id": film_id, "tag_id": tag_id})
        else:
            q = q.delete().eq("film_id", film_id).eq("tag_id", tag_id)

        res = q.execute()
        if getattr(res, "error", None):
            return False, {"error": res.error.message}

        return True, {"message": f"Tag {action}ed"}

    return False, {"error": "Unsupported action"}