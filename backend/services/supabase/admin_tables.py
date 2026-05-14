from typing import Any, Dict, List, Tuple, Optional
from clients import supabase


def tables() -> List[Dict[str, str]]:
    """
    Zwraca listę tabel dostępnych w bazie danych.

    Funkcja pobiera nazwy tabel z bazy danych i filtruje
    wewnętrzne tabele systemowe niewymagane w panelu administracyjnym.
    """
    resp = supabase.rpc("get_all_tables", {}).execute()
    return [
        {"name": t["table_name"]}
        for t in resp.data or []
        if t["table_name"] != "films_tags"
    ]


def table_data(table_name: str) -> List[Dict[str, Any]]:
    """
    Zwraca pełne dane wskazanej tabeli.

    Funkcja pobiera wszystkie rekordy z tabeli
    określonej przez parametr table_name.
    """
    if not table_name:
        raise ValueError("table_name required")

    resp = supabase.table(table_name).select("*").execute()
    return resp.data or []


def modify_controller(
    *,
    table: str,
    operation: str,
    record_id: Optional[Any] = None,
    values: Dict[str, Any] | None = None,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Wykonuje operacje modyfikacji danych w tabelach.

    Funkcja obsługuje operacje:
    - add (dodanie rekordu),
    - update (aktualizacja rekordu),
    - delete (usunięcie rekordu).
    """
    pk = "id"
    values = values or {}

    if operation == "add":
        resp = supabase.table(table).insert(values).execute()
    elif operation == "update":
        resp = supabase.table(table).update(values).eq(pk, record_id).execute()
    elif operation == "delete":
        resp = supabase.table(table).delete().eq(pk, record_id).execute()
    else:
        return False, {"error": "Invalid operation"}

    if getattr(resp, "error", None):
        return False, {"error": resp.error.message}

    return True, {
        "affected_rows": len(resp.data or []),
        "data": resp.data,
    }