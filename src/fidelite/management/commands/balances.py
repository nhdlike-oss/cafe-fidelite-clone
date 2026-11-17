from django.core.management.base import BaseCommand, CommandError

from fidelite.models import Client, Succursale, Transaction

T = Transaction.Type


class Command(BaseCommand):
    help = ("Affiche les soldes des clients. Sans option : soldes du RESEAU (étampes, gratuits "
            "en réserve, cafés sur carte). Avec --succursale : ce qui s'est passé dans ce café.")

    def add_arguments(self, parser):
        parser.add_argument("--succursale", help="Nom ou identifiant d'une succursale.")

    def handle(self, *args, **options):
        ref = options["succursale"]
        if ref:
            cafe = (Succursale.objects.filter(pk=ref).first() if ref.isdigit() else None) \
                or Succursale.objects.filter(nom__iexact=ref).first()
            if cafe is None:
                raise CommandError(f"Succursale introuvable : {ref}")
            return self.par_succursale(cafe)

        # Soldes du reseau : les etampes, gratuits et cartes valent dans tous les cafes.
        self.stdout.write(
            f"{'id':>3}  {'nom':<22} {'achats payés':>12} {'étampes (cycle)':>16} "
            f"{'gratuits en réserve':>20} {'cafés sur cartes':>17}")
        for c in Client.objects.order_by("id"):
            self.stdout.write(
                f"{c.id:>3}  {c.nom:<22} {c.achats_payes:>12} {c.etampes_cycle:>16} "
                f"{c.gratuits_disponibles:>20} {c.cafes_prepayes_restants:>17}")

    def par_succursale(self, cafe):
        # Transactions NON annulees faites dans ce cafe (un gratuit compte la ou il est reclame).
        self.stdout.write(f"Succursale : {cafe.nom}")
        self.stdout.write(
            f"{'id':>3}  {'nom':<22} {'achats payés':>12} {'gratuits pris':>14} "
            f"{'cafés sur carte':>16} {'cartes vendues':>15}")
        for c in Client.objects.order_by("id"):
            tx = c.transactions.filter(succursale=cafe, annulee_le__isnull=True)
            n = {t: tx.filter(type=t).count()
                 for t in (T.ACHAT_PAYE, T.CAFE_GRATUIT, T.ACHAT_CARTE, T.VENTE_CARTE)}
            if any(n.values()):
                self.stdout.write(
                    f"{c.id:>3}  {c.nom:<22} {n[T.ACHAT_PAYE]:>12} {n[T.CAFE_GRATUIT]:>14} "
                    f"{n[T.ACHAT_CARTE]:>16} {n[T.VENTE_CARTE]:>15}")
