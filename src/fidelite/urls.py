from django.urls import path
from . import views

urlpatterns = [
    # name="trouver_client" : un nom qu'on peut réutiliser (ex. dans redirect()),
    # au lieu de réécrire l'adresse en dur partout.
    path("", views.trouver_client, name="trouver_client"),
]