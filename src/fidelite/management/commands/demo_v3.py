from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from fidelite.models import CartePrepayee, Client, Succursale, Transaction

T = Transaction.Type


class Command(BaseCommand):
    help = ("Données de démonstration v3 : deux succursales, un barista, un gérant par "
            "succursale, un propriétaire, un client présent dans les deux cafés.")

    def handle(self, *args, **options):
        # Les clients et transactions de la v2 (comptes barista/gerant inclus).
        call_command("demo_v2", verbosity=0)
        cafe1 = Succursale.objects.get(nom="Café 1")
        cafe2, _ = Succursale.objects.get_or_create(nom="Café 2")

        def compte(nom, groupe=None, super_=False):
            u, cree = User.objects.get_or_create(username=nom)
            if cree:
                u.set_password(f"{nom}123")
            if super_:
                u.is_superuser = u.is_staff = True
            u.save()
            if groupe:
                u.groups.add(Group.objects.get(name=groupe))
            return u

        barista = User.objects.get(username="barista")
        gerant1 = User.objects.get(username="gerant")       # gérant du Café 1 (v2)
        gerant2 = compte("gerant2", "gerant")                # gérant du Café 2
        proprio = compte("proprietaire", super_=True)        # propriétaire : tout
        cafe1.personnel.add(barista, gerant1)
        cafe2.personnel.add(gerant2, barista)                # le barista fait des quarts aux deux

        if not Client.objects.filter(telephone="4185550201").exists():
            now = timezone.now()

            def ajouter(c, type_, jours, cafe, par, carte=None):
                t = Transaction.objects.create(client=c, type=type_, carte=carte,
                                               cree_par=par, succursale=cafe)
                Transaction.objects.filter(pk=t.pk).update(cree_le=now - timedelta(days=jours))

            # Un client qui accumule des étampes au Café 1 et réclame son gratuit au Café 2
            c = Client.objects.create(nom="Camille Deux-Cafés", telephone="4185550201")
            for i in range(10):
                ajouter(c, T.ACHAT_PAYE, 12 - i, cafe1, barista)
            ajouter(c, T.ACHAT_PAYE, 1, cafe2, gerant2)
            ajouter(c, T.CAFE_GRATUIT, 0, cafe2, gerant2)

            # Un client du Café 2 seulement, avec une carte prépayée vendue là-bas
            d = Client.objects.create(nom="David Café2", telephone="4185550202")
            carte = CartePrepayee.objects.create(client=d)
            ajouter(d, T.VENTE_CARTE, 3, cafe2, gerant2, carte=carte)
            for j in (2, 1):
                ajouter(d, T.ACHAT_CARTE, j, cafe2, barista, carte=carte)
                carte.cafes_restants -= 1
            carte.save()
            ajouter(d, T.ACHAT_PAYE, 4, cafe2, gerant2)

        self.stdout.write(self.style.SUCCESS(
            "Démo v3 prête : barista/barista123 (2 cafés), gerant/gerant123 (Café 1), "
            "gerant2/gerant2123 (Café 2), proprietaire/proprietaire123 (tout)."))
