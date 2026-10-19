from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="trouver_client")),
    path("admin/", admin.site.urls),
    # v2 : connexion obligatoire pour les ecrans du comptoir.
    path("connexion/", auth_views.LoginView.as_view(template_name="fidelite/connexion.html"),
         name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
    path("cafe/", include("fidelite.urls")),
]
