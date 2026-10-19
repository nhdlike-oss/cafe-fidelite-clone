from django.urls import path
from . import views

urlpatterns = [
    path("", views.trouver_client, name="trouver_client"),
    path("achat/<int:client_id>/", views.enregistrer_achat, name="enregistrer_achat"),
    # Reservees au gerant :
    path("transaction/<int:transaction_id>/annuler/", views.annuler, name="annuler"),
    path("rapports/", views.rapports, name="rapports"),
    path("regle/", views.regle, name="regle"),
    path("client/<int:client_id>/effacer/", views.effacer, name="effacer"),
    path("client/<int:client_id>/fusionner/", views.fusionner, name="fusionner"),
    path("client/<int:client_id>/fusionner/<int:autre_id>/", views.fusionner, name="fusionner_avec"),
]
