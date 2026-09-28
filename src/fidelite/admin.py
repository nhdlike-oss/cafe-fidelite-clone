# On importe l'outil admin de Django.
from django.contrib import admin

# On importe nos 3 modeles et notre formulaire valide.
from .forms import ClientForm
from .models import Client, CartePrepayee, Transaction


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Meme validation que l'ecran du comptoir (nom, telephone, courriel).
    form = ClientForm
    list_display = ("nom", "telephone", "courriel")
    search_fields = ("nom", "telephone", "courriel")


@admin.register(CartePrepayee)
class CartePrepayeeAdmin(admin.ModelAdmin):
    # "expire_le" et "expiree" sont des calculs du modele, pas des colonnes en base.
    list_display = ("client", "cafes_restants", "creee_le", "expire_le", "expiree")
    search_fields = ("client__nom",)

    # @admin.display permet de choisir le titre de la colonne et l'icone oui/non.
    @admin.display(boolean=True, description="Expirée")
    def expiree(self, carte):
        return carte.est_expiree


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("client", "type", "cree_le")
    list_filter = ("type",)
    search_fields = ("client__nom",)