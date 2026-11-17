import os
import shutil
import tempfile

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections

from fidelite.models import Client, Transaction


class Command(BaseCommand):
    help = ("Copie une base SQLite de la v2 dans la base actuelle (PostgreSQL dans les "
            "conteneurs). Le fichier SQLite d'origine n'est jamais modifié.")

    def add_arguments(self, parser):
        parser.add_argument("chemin", help="Chemin du fichier db.sqlite3 de la v2.")
        parser.add_argument("--ecraser", action="store_true",
                            help="Autorise à remplacer des clients déjà présents dans la base cible.")

    def handle(self, *args, **options):
        source = options["chemin"]
        if not os.path.isfile(source):
            raise CommandError(f"Fichier introuvable : {source}")

        cible = connections["default"]
        # Garde-fou : on ne vide jamais une base qui contient deja de vrais clients.
        if (Client.objects.exists() or Transaction.objects.exists()) and not options["ecraser"]:
            raise CommandError("La base cible contient déjà des clients ou des transactions. "
                               "Relancez avec --ecraser si vous voulez vraiment les remplacer.")

        with tempfile.TemporaryDirectory() as dossier:
            # 1. Travailler sur une COPIE : la base de la v2 reste intacte.
            copie = os.path.join(dossier, "v2.sqlite3")
            shutil.copy(source, copie)
            self.ajouter_alias_v2(copie)

            # 2. Mettre la copie au schema de la v3 (migrations 0005 a 0007, par-dessus la v2).
            self.stdout.write("1/4 Migrations de la v3 sur la copie de la base v2...")
            call_command("migrate", database="v2", interactive=False, verbosity=0)
            avant = self.compter("v2")

            # 3. Exporter. Les types de contenu et les permissions sont recrees par Django :
            #    on les exclut ; les liens vers eux passent par des cles « naturelles ».
            self.stdout.write("2/4 Export des données...")
            fichier = os.path.join(dossier, "donnees.json")
            call_command("dumpdata", database="v2", natural_foreign=True, natural_primary=True,
                         exclude=["contenttypes", "auth.permission", "sessions"],
                         output=fichier, verbosity=0)

            # 4. Vider les donnees de depart de la cible (regle, groupes, premier cafe),
            #    puisque la copie les contient deja, avec les memes identifiants.
            self.stdout.write(f"3/4 Import dans {cible.vendor}...")
            call_command("flush", database="default", interactive=False, verbosity=0)
            call_command("loaddata", fichier, database="default", verbosity=0)

        apres = self.compter("default")
        self.stdout.write("4/4 Vérification du nombre de lignes :")
        ok = True
        for nom, n in avant.items():
            m = apres[nom]
            etat = "ok" if n == m else "DIFFÉRENT"
            ok = ok and n == m
            self.stdout.write(f"   {nom:<28} source {n:>5}   cible {m:>5}   {etat}")
        if not ok:
            raise CommandError("Des lignes manquent : l'import n'est pas fiable.")
        self.stdout.write(self.style.SUCCESS(
            "Import terminé. Lancez maintenant `python manage.py balances` et comparez."))

    def ajouter_alias_v2(self, chemin):
        # Declare une deuxieme base (la copie SQLite) en plus de la base par defaut.
        config = {"ENGINE": "django.db.backends.sqlite3", "NAME": chemin}
        reglages = connections.configure_settings(
            {"default": connections.settings["default"], "v2": config})
        connections.settings["v2"] = reglages["v2"]

    def compter(self, alias):
        modeles = [m for m in apps.get_app_config("fidelite").get_models()]
        modeles += [apps.get_model("auth", "User"), apps.get_model("auth", "Group"),
                    apps.get_model("admin", "LogEntry")]
        return {f"{m._meta.app_label}.{m.__name__}": m.objects.using(alias).count()
                for m in modeles}
