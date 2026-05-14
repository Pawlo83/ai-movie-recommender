import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.middleware.csrf import get_token

from services.supabase.tags import get_tag_usage

logger = logging.getLogger(__name__)

@require_GET
@ensure_csrf_cookie
def ping(request):
    """
    Endpoint testowy służący do sprawdzania dostępności backendu.

    Zwraca prostą odpowiedź JSON potwierdzającą,
    że aplikacja jest uruchomiona i reaguje na żądania.
    """
    return JsonResponse({
        "status": "awake",
        "csrf_token": get_token(request)
    })


@require_GET
def tags_json(request):
    """
    Zwraca najczęściej używane tagów w bazie.

    Funkcja pobiera zagregowane dane dotyczące przypisania tagów
    do filmów i udostępnia je w formacie JSON.
    W przypadku błędu zwraca pustą listę tagów oraz loguje wyjątek.
    """
    data = []
    try:
        data = get_tag_usage()
    except Exception:
        logger.exception("Błąd podczas pobierania statystyk użycia tagów")

    return JsonResponse({"tags": data})