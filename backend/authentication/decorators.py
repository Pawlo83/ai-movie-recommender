from functools import wraps
from django.http import JsonResponse
from authentication import decode_token

def jwt_required(view_func):
    """
    Dekorator zabezpieczający endpointy API przy użyciu JWT.

    Działanie:
    - Odczytuje access_token z httpOnly cookie.
    - Dekoduje i weryfikuje token.
    - W przypadku sukcesu dopuszcza wykonanie widoku.
    - W przypadku błędu zwraca 401 Unauthorized.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = request.COOKIES.get("access_token")

        if not token:
            return JsonResponse({"detail": "Unauthorized"}, status=401)

        try:
            payload = decode_token(token, expected_type="access")
            request.jwt_payload = payload

        except Exception:
            return JsonResponse({"detail": "Invalid token"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper
