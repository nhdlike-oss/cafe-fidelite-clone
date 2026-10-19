from django.db import transaction as db
from django.utils import timezone

from .models import Audit, CartePrepayee, Client, Transaction, rejouer

GROUPE_GERANT = "gerant"
GROUPE_BARISTA = "barista"


class ErreurMetier(Exception):
    """Une regle d'affaires refuse l'operation (le message est montre au gerant)."""


def est_gerant(user):
    # Un super-utilisateur Django (ex. le compte cree en v1) compte comme gerant.
    return bool(user and user.is_authenticated
                and (user.is_superuser or user.groups.filter(name=GROUPE_GERANT).exists()))


def annuler_transaction(tx, user):
    """Annule une transaction (ADR-0002). Refuse si le journal devenait incoherent."""
    with db.atomic():
        if tx.est_annulee:
            raise ErreurMetier("Cette transaction est déjà annulée.")

        if tx.type == Transaction.Type.VENTE_CARTE and tx.carte_id:
            if tx.carte.transaction_set.filter(
                    type=Transaction.Type.ACHAT_CARTE, annulee_le__isnull=True).exists():
                raise ErreurMetier(
                    "Des cafés ont déjà été pris sur cette carte : annulez-les d'abord.")

        elif tx.type == Transaction.Type.ACHAT_PAYE:
            # On rejoue le journal SANS cette transaction : si un cafe gratuit
            # n'a plus de recompense derriere lui, l'annulation est refusee.
            reste = [t for t in tx.client.journal_actif() if t.pk != tx.pk]
            if not rejouer(reste).coherent:
                raise ErreurMetier(
                    "Annulation impossible : cet achat a donné un café gratuit "
                    "qui a déjà été bu. Annulez d'abord le café gratuit.")

        tx.annulee_le = timezone.now()
        tx.annulee_par = user
        tx.save(update_fields=["annulee_le", "annulee_par"])

        if tx.carte_id:
            if tx.type == Transaction.Type.VENTE_CARTE:
                tx.carte.annulee = True
                tx.carte.save(update_fields=["annulee"])
            else:
                tx.carte.recalculer()
    return tx


def effacer_client(client, user):
    """Anonymise le client (ADR-0005). Les transactions restent pour les rapports."""
    with db.atomic():
        if client.efface:
            raise ErreurMetier("Ce client est déjà effacé.")
        Audit.objects.create(
            action=Audit.Action.EFFACEMENT, par=user, details=f"client #{client.pk}")
        client.anonymiser()


def fusionner_clients(a, b, user):
    """Fusionne deux fiches (ADR-0006). La plus ancienne survit. Retourne la survivante."""
    with db.atomic():
        if a.pk == b.pk:
            raise ErreurMetier("Choisissez deux fiches différentes.")
        if a.efface or b.efface:
            raise ErreurMetier("Impossible de fusionner un client effacé.")
        garde, absorbe = sorted([a, b], key=lambda c: (c.cree_le, c.pk))

        combine = Transaction.objects.filter(
            client__in=[garde, absorbe], annulee_le__isnull=True).order_by("cree_le", "id")
        if not rejouer(combine).coherent:
            raise ErreurMetier(
                "Fusion refusée : l'historique combiné serait incohérent "
                "(un café gratuit n'aurait plus de récompense valide).")

        Transaction.objects.filter(client=absorbe).update(client=garde)
        CartePrepayee.objects.filter(client=absorbe).update(client=garde)
        Audit.objects.create(
            action=Audit.Action.FUSION, par=user,
            details=f"fiche #{absorbe.pk} fusionnée dans la fiche #{garde.pk}")
        absorbe.delete()  # plus aucune transaction ni carte : rien n'est perdu
    return garde
