from django.contrib import admin
from django.urls import include, path   # include = brancher les adresses d'une autre app

urlpatterns = [
    path("admin/", admin.site.urls),        # /admin/ -> l'interface d'administration
    path("cafe/", include("fidelite.urls")) # /cafe/... -> le plan de ton app fidelite
]