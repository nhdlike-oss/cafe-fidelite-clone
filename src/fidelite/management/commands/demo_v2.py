from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from fidelite.models import CartePrepayee, Client, Transaction
from fidelite.services import GROUPE_BARISTA, GROUPE_GERANT

T = Transaction.Type


class Command(BaseCommand):
    help = "Crée les comptes de démonstration (barista, gérant) et des données de démonstration v2."

    def handle(self, *args, **options):
        for nom, groupe in (("barista", GROUPE_BARISTA), ("gerant", GROUPE_GERANT)):
            u, cree = User.objects.get_or_create(username=nom)
            if cree:
                u.set_password(f"{nom}123")
                u.save()
            u.groups.add(Group.objects.get_or_create(name=groupe)[0])
        barista = User.objects.get(username="barista")
        now = timezone.now()

        def client(nom, tel, courriel=""):
            return Client.objects.get_or_create(telephone=tel, defaults={"nom": nom, "courriel": courriel})

        def ajouter(c, type_, jours, carte=None, heures=0):
            t = Transaction.objects.create(client=c, type=type_, carte=carte, cree_par=barista)
            quand = now - timedelta(days=jours, hours=heures)
            Transaction.objects.filter(pk=t.pk).update(cree_le=quand)
            return t, quand

        # Deux fiches à fusionner (6 + 7 = 13 étampes)
        a, cree_a = client("Louise Tremblay", "4185550101")
        b, cree_b = client("Louise Tremblay", "4185550102")
        if cree_a and cree_b:
            for i in range(6):
                ajouter(a, T.ACHAT_PAYE, 9 - i)
            for i in range(7):
                ajouter(b, T.ACHAT_PAYE, 8 - i, heures=2)

            # Un client à effacer, avec une carte à moitié utilisée
            e, _ = client("Marc Aleatoire", "4185550103", "marc@exemple.com")
            carte = CartePrepayee.objects.create(client=e)
            CartePrepayee.objects.filter(pk=carte.pk).update(creee_le=now - timedelta(days=4))
            ajouter(e, T.VENTE_CARTE, 4, carte=carte)
            for j in (3, 2, 1):
                ajouter(e, T.ACHAT_CARTE, j, carte=carte)
                carte.cafes_restants -= 1
            carte.save()
            ajouter(e, T.ACHAT_PAYE, 5)

            # Un client avec un café gratuit disponible
            g, _ = client("Jean Gratuit", "4185550105")
            for i in range(10):
                ajouter(g, T.ACHAT_PAYE, 10 - i)

            # Une transaction à annuler : le dernier achat de Sophie (mauvais client)
            s, _ = client("Sophie Erreur", "4185550104")
            ajouter(s, T.ACHAT_PAYE, 0)
            ajouter(s, T.ACHAT_PAYE, 0)

        self.stdout.write(self.style.SUCCESS(
            "Démo prête. Comptes : barista / barista123 et gerant / gerant123."))
