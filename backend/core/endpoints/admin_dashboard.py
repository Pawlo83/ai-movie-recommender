import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from authentication import jwt_required
from services.supabase.admin_tables import modify_controller, table_data, tables
from services.supabase.film_tags import film_tags_controller

logger = logging.getLogger(__name__)

@jwt_required
@require_GET
def get_tables(request):
    """
    Zwraca listę dostępnych tabel w bazie danych.

    Endpoint udostępnia nazwy tabel przeznaczonych do zarządzania
    danymi w warstwie administracyjnej aplikacji.
    """
    data = tables()
    return JsonResponse({"tables": data})


@jwt_required
@require_GET
def get_table_data(request):
    """
    Zwraca dane wskazanej tabeli.

    Funkcja:
    - parsuje nazwę tabeli z treści żądania,
    - pobiera dane tabeli z warstwy Supabase,
    - zwraca wynik w formacie JSON.
    """
    try:
        table_name_raw = request.GET.get("table_name")
    except Exception:
        logger.exception("Błąd parsowania request body w get_table_data")
        table_name_raw = ""

    data = table_data(table_name_raw)

    return JsonResponse({"data": data})


@jwt_required
@require_POST
def modify_table_data(request):
    """
    Wykonuje operacje modyfikacji danych w tabelach.

    Endpoint obsługuje operacje CRUD przekazane w treści żądania
    i deleguje ich wykonanie do warstwy serwisowej.
    """
    try:
        payload = json.loads(request.body)
        success, result = modify_controller(
            table=payload.get("table"),
            operation=payload.get("operation"),
            record_id=payload.get("id"),
            values=payload.get("values")
        )
        if not success:
            return JsonResponse(
                {"success": False, **result},
                status=400
            )

        return JsonResponse(
            {"success": True, "result": result}
        )

    except Exception:
        return JsonResponse(
            {"success": False, "error": "Internal server error"},
            status=500
        )


@jwt_required
@require_GET
def me(request):
    """
    Zwraca podstawowe informacje o aktualnie uwierzytelnionym użytkowniku.

    Dane użytkownika pobierane są z payloadu tokena JWT
    dołączonego do żądania.
    """
    try:
        payload = request.jwt_payload
    except Exception:
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    return JsonResponse({
        "user": {
            "username": payload.get("sub"),
        }
    })


@jwt_required
@require_POST
def film_tags(request):
    """
    Zarządza przypisaniem tagów do filmów.

    Endpoint:
    - obsługuje dodawanie i usuwanie tagów,
    - deleguje logikę do warstwy serwisowej,
    - zwraca wynik operacji w formacie JSON.
    """
    try:
        payload = json.loads(request.body)
    except Exception:
        return JsonResponse({"detail": "Invalid request body"}, status=400)

    success, result = film_tags_controller(
        action=payload.get("action") if request.method == "POST" else "get",
        film_id=payload.get("film_id"),
        tag_name=payload.get("tag_name"),
    )

    if not success:
        return JsonResponse(result, status=400)

    return JsonResponse(result, safe=False)
