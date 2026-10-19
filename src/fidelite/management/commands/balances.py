from django.core.management.base import BaseCommand

from fidelite.models import Client


class Command(BaseCommand):
    help = "Affiche, pour chaque client : étampes, récompenses en réserve et cafés sur carte."

    def handle(self, *args, **options):
        self.stdout.write(
            f"{'id':>3}  {'nom':<22} {'achats payés':>12} {'étampes (cycle)':>16} "
            f"{'gratuits en réserve':>20} {'cafés sur cartes':>17}")
        for c in Client.objects.order_by("id"):
            self.stdout.write(
                f"{c.id:>3}  {c.nom:<22} {c.achats_payes:>12} {c.etampes_cycle:>16} "
                f"{c.gratuits_disponibles:>20} {c.cafes_prepayes_restants:>17}")