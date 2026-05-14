import logging
import os
import time
from typing import Dict, Optional, Any

import requests

from clients import tmdb_session

logger = logging.getLogger(__name__)


TMDB_API_KEY = os.environ.get("TMDB_API_KEY")


def _build_tmdb_auth_headers() -> Dict[str, str]:
    """Zwraca nagłówki auth do TMDB."""
    if not TMDB_API_KEY:
        return {}
    key = TMDB_API_KEY.strip()
    bearer = f"Bearer {key}"
    return {"Authorization": bearer}


def safe_request(url: str, params: Optional[Dict[str, Any]] = None, use_bearer: bool = True, timeout: int = 6) -> Optional[requests.Response]:
    """
    Wykonuje zapytanie HTTP do API TMDB z podstawowym mechanizmem odporności
    na błędy sieciowe (retry + backoff).

    Funkcja:
    - próbuje wykonać request maksymalnie 3 razy,
    - używa autoryzacji Bearer,
    """
    attempts = 3
    backoff = 0.3
    for attempt in range(attempts):
        try:
            headers = {}
            if use_bearer:
                headers.update(_build_tmdb_auth_headers())

            resp = tmdb_session.get(url, params=params, headers=headers, timeout=timeout)
            return resp
        except requests.RequestException as e:
            time.sleep(backoff * (attempt + 1))
            backoff *= 2
            if attempt == attempts - 1:
                logger.error(f"Żądanie do TMDB zakończyło się błędem: {e}")
                return None
    return None