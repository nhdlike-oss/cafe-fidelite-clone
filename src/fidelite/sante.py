from django.db import connection
from django.http import HttpResponse


class SanteMiddleware:
    """Repond a /sante/ pour les healthchecks Docker (ADR-0013, exigence C8).

    Place AVANT tous les autres middlewares : la reponse ne depend ni de ALLOWED_HOSTS
    ni de la connexion. Elle verifie que la base de donnees repond.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/sante/":
            try:
                connection.ensure_connection()
            except Exception:
                return HttpResponse("base de donnees indisponible", status=503,
                                    content_type="text/plain")
            return HttpResponse("ok", content_type="text/plain")
        return self.get_response(request)
