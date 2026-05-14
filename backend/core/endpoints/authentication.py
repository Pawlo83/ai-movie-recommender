import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from authentication import create_access_token, create_refresh_token, decode_token

IS_PROD = not settings.DEBUG


@require_POST
def generate_token(request):
    """
    Endpoint logowania użytkownika i generowania tokenów JWT.

    Funkcja:
    - weryfikuje dane logowania przesłane w treści żądania,
    - generuje access oraz refresh token JWT,
    - zapisuje tokeny w ciasteczkach httpOnly,
    - zwraca prostą odpowiedź potwierdzającą poprawne uwierzytelnienie.
    """
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"detail": "Invalid request body"}, status=400)
    username = data["username"]
    password = data["password"]
    if (
        username != settings.APP_LOGIN_USERNAME or
        password != settings.APP_LOGIN_PASSWORD
    ):
        return JsonResponse({"detail": "Invalid credentials"}, status=401)

    access = create_access_token(username)
    refresh = create_refresh_token(username)

    response = JsonResponse({"ok": True})

    response.set_cookie(
        "access_token",
        access,
        httponly=True,
        secure=True,
        samesite='None',
        max_age=settings.JWT_ACCESS_TTL,
    )

    response.set_cookie(
        "refresh_token",
        refresh,
        httponly=True,
        secure=True,
        samesite='None',
        max_age=settings.JWT_REFRESH_TTL,
    )
    return response


@require_POST
def token_refresh(request):
    """
    Endpoint odświeżania access token JWT.

    Funkcja:
    - odczytuje refresh token z ciasteczka,
    - weryfikuje jego poprawność i typ,
    - generuje nowy access token,
    - zapisuje go w ciasteczku httpOnly.
    """
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except Exception:
        return JsonResponse({"detail": "Invalid refresh token"}, status=401)

    user = payload["sub"]

    access = create_access_token(user)

    response = JsonResponse({"ok": True})
    response.set_cookie(
        "access_token",
        access,
        httponly=True,
        secure=True,
        samesite='None',
        max_age=settings.JWT_ACCESS_TTL,
    )

    return response


@require_POST
def logout(request):
    response = JsonResponse({"ok": True})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response