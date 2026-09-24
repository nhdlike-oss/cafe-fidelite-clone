# On importe l'outil admin de Django.
from django.contrib import admin

# On importe notre modèle Client depuis models.py.
# Le "." veut dire "dans ce même dossier".
from .models import Client


# @admin.register(Client) est un "décorateur" : une ligne qui commence par @
# et qui modifie ce qui suit. Ici, elle dit à Django :
# "affiche le modèle Client dans l'interface d'administration,
# en utilisant les options définies juste en dessous".
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # list_display = quelles colonnes montrer dans la liste des clients.
    list_display = ("nom", "telephone", "courriel")

    # search_fields = ajoute une barre de recherche qui cherche dans ces champs.
    search_fields = ("nom", "telephone","courriel")