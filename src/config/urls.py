from django.contrib import admin
# RedirectView renvoie automatiquement le navigateur vers une autre adresse.
from django.views.generic import RedirectView
# include = brancher les adresses d'une autre app.
from django.urls import include, path

urlpatterns = [
    # NOUVEAU : l'adresse vide "/" redirige vers la page "trouver_client".
    # pattern_name utilise le NOM de la route (defini dans fidelite/urls.py),
    # donc pas d'adresse ecrite en dur ici.
    path("", RedirectView.as_view(pattern_name="trouver_client")),

    # /admin/ -> l'interface d'administration.
    path("admin/", admin.site.urls),

    # /cafe/... -> le plan de l'app fidelite.
    path("cafe/", include("fidelite.urls")),
]