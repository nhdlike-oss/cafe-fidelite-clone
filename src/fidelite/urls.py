from django.urls import path
from . import views

urlpatterns = [
    # name="trouver_client" : un nom qu'on peut réutiliser (ex. dans redirect()),
    # au lieu de réécrire l'adresse en dur partout.
    path("", views.trouver_client, name="trouver_client"),

    # <int:client_id> capture un nombre dans l'adresse (ex: /cafe/achat/3/)
    # et l'envoie a la vue comme argument client_id.
    path("achat/<int:client_id>/", views.enregistrer_achat, name="enregistrer_achat"),
]