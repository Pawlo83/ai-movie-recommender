from typing import Any, Dict, List, Optional
from clients import supabase


def get_tag_id_by_name(tag_name: str) -> Optional[str]:
    """
    Zwraca identyfikator tagu na podstawie jego nazwy.

    Funkcja wyszukuje tag w tabeli `tags` i zwraca jego ID
    lub None, jeżeli tag nie istnieje.
    """
    resp = (
        supabase
        .table("tags")
        .select("id")
        .eq("tag_name", tag_name)
        .single()
        .execute()
    )

    if getattr(resp, "error", None):
        return None

    return resp.data.get("id")


def get_tag_usage(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Zwraca statystyki użycia tagów w systemie.

    Funkcja pobiera zagregowane dane dotyczące liczby
    przypisań tagów do filmów i zwraca je w formacie JSON.
    """
    resp = supabase.rpc("get_tag_usage", {}).execute()
    rows = resp.data or []

    if limit:
        rows = rows[:limit]

    return [
        {"tag_name": r["tag_name"], "uses": r["uses"]}
        for r in rows
    ]

def get_tags(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Zwraca listę dostępnych tagów.

    Funkcja pobiera unikalne nazwy tagów wykorzystywanych
    w systemie, bez informacji o liczbie ich użyć.
    """
    resp = supabase.rpc("get_tag_usage", {}).execute()
    rows = resp.data or []

    if limit:
        rows = rows[:limit]

    return [
        {"tag_name": r["tag_name"]}
        for r in rows
    ]

def get_tag_id_map():
    """
    Zwraca mapowanie nazw tagów na ich identyfikatory.

    Funkcja wykorzystywana jest do szybkiej konwersji
    nazw tagów na ID podczas zapisu relacji film–tag.
    """
    res = supabase.table("tags").select("id, tag_name").execute()
    return {row["tag_name"]: row["id"] for row in res.data}