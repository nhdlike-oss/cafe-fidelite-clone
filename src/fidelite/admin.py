from django.contrib import admin

from .forms import ClientForm
from .models import Audit, CartePrepayee, Client, RegleFidelite, Transaction


class SansSuppression(admin.ModelAdmin):
    # Supprimer un client ou une transaction detruirait le journal et fausserait les
    # rapports : on annule / efface plutot depuis l'ecran du gerant.
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Client)
class ClientAdmin(SansSuppression):
    form = ClientForm
    list_display = ("nom", "telephone", "courriel", "efface")
    search_fields = ("nom", "telephone", "courriel")


@admin.register(CartePrepayee)
class CartePrepayeeAdmin(SansSuppression):
    list_display = ("client", "cafes_restants", "creee_le", "expire_le", "expiree", "annulee")
    search_fields = ("client__nom",)
    readonly_fields = ("cafes_restants",)

    @admin.display(boolean=True, description="Expirée")
    def expiree(self, carte):
        return carte.est_expiree


@admin.register(Transaction)
class TransactionAdmin(SansSuppression):
    # Lecture seule : toute correction passe par l'annulation (qui est tracee).
    list_display = ("client", "type", "cree_le", "cree_par", "annulee_le", "annulee_par")
    list_filter = ("type",)
    search_fields = ("client__nom",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RegleFidelite)
class RegleAdmin(SansSuppression):
    list_display = ("etampes_requises", "en_vigueur_le", "cree_par")


@admin.register(Audit)
class AuditAdmin(SansSuppression):
    list_display = ("action", "details", "par", "cree_le")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
