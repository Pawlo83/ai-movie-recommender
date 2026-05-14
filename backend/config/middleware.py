import logging

logger = logging.getLogger('django.request')

class LogHostHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        logger.debug(f"Host header received: {host}")
        response = self.get_response(request)
        return response
