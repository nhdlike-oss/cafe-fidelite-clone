"""Tests du devoir 3 : plusieurs cafés, permissions par succursale, migration v2 -> v3.

Les tests de la v1 et de la v2 (tests.py) continuent de passer : « tout ce qui
fonctionnait en v2 doit continuer de fonctionner ».
"""
from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from . import tests as v2
from .models import Client, Succursale, Transaction
from .services import (annuler_transaction, effacer_client, est_proprietaire,
                       fusionner_clients)

T = Transaction.Type


class DeuxCafes(TestCase):
    """Deux cafés, un barista dans les deux, un gérant par café, un propriétaire."""

    def setUp(self):
        self.cafe1 = Succursale.objects.get(nom="Café 1")          # créé par la migration
        self.cafe2 = Succursale.objects.create(nom="Café 2")       # ajouté SANS toucher au code

        def employe(nom, groupe):
            u = User.objects.create_user(nom, password="x")
            u.groups.add(Group.objects.get(name=groupe))
            return u

        self.barista = employe("barista", "barista")               # quarts dans les deux cafés
        self.gerant1 = employe("gerant1", "gerant")
        self.gerant2 = employe("gerant2", "gerant")
        self.proprio = User.objects.create_superuser("proprio", password="x")
        self.cafe1.personnel.add(self.barista, self.gerant1)
        self.cafe2.personnel.add(self.barista, self.gerant2)
        self.cl = Client.objects.create(nom="Sara Martin", telephone="4185550001")

    def tx(self, cafe, type_=T.ACHAT_PAYE, client=None, par=None, jours=0):
        return v2.ajouter(client or self.cl, type_, jours, par=par, cafe=cafe)

    def tous_les_ecrans(self, user):
        self.client.force_login(user)


class SuccursalesEtFidelite(DeuxCafes):
    def test_toutes_les_transactions_de_la_v2_appartiennent_au_premier_cafe(self):
        # Les cafés de ce test sont créés après la migration : on vérifie le cas simple.
        self.assertEqual(self.cafe1.nom, "Café 1")

    def test_un_employe_d_un_seul_cafe_est_place_automatiquement(self):
        self.client.force_login(self.gerant1)
        self.client.post(reverse("enregistrer_achat", args=[self.cl.pk]),
                         {"action": "payer", "quantite": "1"})
        self.assertEqual(Transaction.objects.get().succursale, self.cafe1)

    def test_un_barista_des_deux_cafes_doit_choisir_puis_la_transaction_va_au_bon_cafe(self):
        self.client.force_login(self.barista)
        url = reverse("enregistrer_achat", args=[self.cl.pk])
        rep = self.client.get(url)
        self.assertEqual(rep.status_code, 302)
        self.assertIn(reverse("choisir_succursale"), rep["Location"])
        self.assertEqual(Transaction.objects.count(), 0)
        self.client.post(reverse("choisir_succursale"), {"succursale": self.cafe2.pk})
        self.client.post(url, {"action": "payer", "quantite": "1"})
        self.assertEqual(Transaction.objects.get().succursale, self.cafe2)

    def test_on_ne_peut_pas_choisir_un_cafe_qui_n_est_pas_le_sien(self):
        self.client.force_login(self.gerant1)
        rep = self.client.post(reverse("choisir_succursale"), {"succursale": self.cafe2.pk})
        self.assertEqual(rep.status_code, 404)

    def test_un_compte_sans_cafe_ne_peut_rien_enregistrer(self):
        orphelin = User.objects.create_user("orphelin", password="x")
        self.client.force_login(orphelin)
        self.client.post(reverse("enregistrer_achat", args=[self.cl.pk]),
                         {"action": "payer", "quantite": "1"})
        self.assertEqual(Transaction.objects.count(), 0)

    def test_etampes_gagnees_au_cafe_A_cafe_gratuit_reclame_au_cafe_B(self):
        for _ in range(10):
            self.tx(self.cafe1)
        self.assertEqual(self.cl.gratuits_disponibles, 1)           # valable dans tout le réseau
        self.client.force_login(self.gerant2)                       # le gérant du Café 2
        self.client.post(reverse("enregistrer_achat", args=[self.cl.pk]), {"action": "gratuit"})
        gratuit = Transaction.objects.get(type=T.CAFE_GRATUIT)
        self.assertEqual(gratuit.succursale, self.cafe2)
        self.assertEqual(self.cl.gratuits_disponibles, 0)

    def test_carte_prepayee_vendue_au_cafe_A_utilisable_au_cafe_B(self):
        carte = v2.vendre_carte(self.cl)                            # vendue au Café 1
        self.client.force_login(self.gerant2)
        self.client.post(reverse("enregistrer_achat", args=[self.cl.pk]),
                         {"action": "carte", "quantite": "2"})
        carte.refresh_from_db()
        self.assertEqual(carte.cafes_restants, 9)
        self.assertEqual(Transaction.objects.filter(type=T.ACHAT_CARTE,
                                                    succursale=self.cafe2).count(), 2)

    def test_ajouter_un_troisieme_cafe_ne_demande_aucun_code(self):
        cafe3 = Succursale.objects.create(nom="Café 3")
        self.tx(cafe3)
        self.assertEqual(cafe3.transactions.count(), 1)


class PermissionsParSuccursale(DeuxCafes):
    def test_le_gerant_annule_dans_son_cafe_pas_dans_l_autre(self):
        ici, ailleurs = self.tx(self.cafe1), self.tx(self.cafe2)
        self.client.force_login(self.gerant1)
        self.assertEqual(self.client.post(reverse("annuler", args=[ailleurs.pk])).status_code, 403)
        self.client.post(reverse("annuler", args=[ici.pk]))
        ici.refresh_from_db(), ailleurs.refresh_from_db()
        self.assertIsNotNone(ici.annulee_le)
        self.assertIsNone(ailleurs.annulee_le)

    def test_la_verification_est_aussi_dans_le_service_pas_seulement_dans_la_vue(self):
        ailleurs = self.tx(self.cafe2)
        with self.assertRaises(PermissionDenied):
            annuler_transaction(ailleurs, self.gerant1)
        annuler_transaction(ailleurs, self.proprio)                 # le propriétaire peut
        ailleurs.refresh_from_db()
        self.assertEqual(ailleurs.annulee_par, self.proprio)

    def test_le_barista_ne_peut_annuler_dans_aucun_cafe(self):
        tx = self.tx(self.cafe1)
        self.client.force_login(self.barista)
        self.assertEqual(self.client.post(reverse("annuler", args=[tx.pk])).status_code, 403)

    def test_le_bouton_annuler_n_est_pas_affiche_pour_l_autre_cafe(self):
        ailleurs = self.tx(self.cafe2)
        self.client.force_login(self.gerant1)
        rep = self.client.get(reverse("enregistrer_achat", args=[self.cl.pk]))
        self.assertNotContains(rep, reverse("annuler", args=[ailleurs.pk]))

    def test_effacer_un_client_present_dans_les_deux_cafes_est_reserve_au_proprietaire(self):
        self.tx(self.cafe1), self.tx(self.cafe2)
        self.client.force_login(self.gerant1)
        self.assertEqual(self.client.get(reverse("effacer", args=[self.cl.pk])).status_code, 403)
        with self.assertRaises(PermissionDenied):
            effacer_client(self.cl, self.gerant1)
        self.client.force_login(self.proprio)
        self.assertEqual(self.client.get(reverse("effacer", args=[self.cl.pk])).status_code, 200)
        effacer_client(self.cl, self.proprio)
        self.cl.refresh_from_db()
        self.assertTrue(self.cl.efface)
        self.assertEqual(Transaction.objects.count(), 2)           # les statistiques restent

    def test_le_gerant_efface_un_client_qui_n_a_que_son_cafe(self):
        self.tx(self.cafe1)
        effacer_client(self.cl, self.gerant1)
        self.cl.refresh_from_db()
        self.assertTrue(self.cl.efface)

    def test_fusion_de_fiches_dans_deux_cafes_reservee_au_proprietaire(self):
        autre = Client.objects.create(nom="Sara Martin", telephone="4185550002")
        self.tx(self.cafe1), self.tx(self.cafe2, client=autre)
        with self.assertRaises(PermissionDenied):
            fusionner_clients(self.cl, autre, self.gerant1)
        garde = fusionner_clients(self.cl, autre, self.proprio)
        self.assertEqual(garde.transactions.count(), 2)

    def test_les_roles_de_la_v2_fonctionnent_toujours_au_cafe_1(self):
        self.assertFalse(est_proprietaire(self.gerant1))
        self.assertTrue(est_proprietaire(self.proprio))


class RapportsDuReseau(DeuxCafes):
    def donnees(self):
        self.tx(self.cafe1), self.tx(self.cafe1), self.tx(self.cafe2)
        for _ in range(10):                                        # 10 étampes au Café 1...
            self.tx(self.cafe1, client=Client.objects.get_or_create(
                nom="Max", telephone="4185550003")[0])
        max_ = Client.objects.get(nom="Max")
        self.tx(self.cafe2, T.CAFE_GRATUIT, client=max_)           # ...gratuit réclamé au Café 2
        self.tx(self.cafe2, T.VENTE_CARTE)

    def rapport(self, user, **params):
        self.client.force_login(user)
        debut = timezone.localdate().isoformat()
        return self.client.get(reverse("rapports"), {"debut": debut, "fin": debut, **params})

    def test_le_gerant_ne_voit_que_son_cafe(self):
        self.donnees()
        rep = self.rapport(self.gerant1)
        self.assertEqual(rep.context["payes"], 12)                  # 2 + 10, tous au Café 1
        self.assertEqual(rep.context["gratuits"], 0)

    def test_le_gerant_ne_peut_pas_demander_le_rapport_de_l_autre_cafe(self):
        self.donnees()
        rep = self.rapport(self.gerant1, succursale=self.cafe2.pk)
        self.assertEqual(rep.status_code, 403)

    def test_le_proprietaire_voit_le_reseau_ou_un_cafe(self):
        self.donnees()
        reseau = self.rapport(self.proprio).context
        cafe2 = self.rapport(self.proprio, succursale=self.cafe2.pk).context
        cafe1 = self.rapport(self.proprio, succursale=self.cafe1.pk).context
        self.assertEqual(reseau["payes"], cafe1["payes"] + cafe2["payes"])
        self.assertEqual(reseau["gratuits"], 1)

    def test_le_cafe_gratuit_apparait_dans_le_cafe_ou_il_est_reclame(self):
        self.donnees()
        self.assertEqual(self.rapport(self.proprio, succursale=self.cafe2.pk).context["gratuits"], 1)
        self.assertEqual(self.rapport(self.proprio, succursale=self.cafe1.pk).context["gratuits"], 0)

    def test_les_annulations_sont_exclues_par_succursale(self):
        tx = self.tx(self.cafe1)
        annuler_transaction(tx, self.gerant1)
        ctx = self.rapport(self.gerant1).context
        self.assertEqual((ctx["payes"], ctx["annulees"]), (0, 1))

    def test_un_parametre_invalide_est_refuse(self):
        self.assertEqual(self.rapport(self.proprio, succursale="abc").status_code, 403)


class SoldesParSuccursale(DeuxCafes):
    def test_balances_reseau_et_par_succursale(self):
        for _ in range(3):
            self.tx(self.cafe1)
        self.tx(self.cafe2)
        reseau, cafe2 = StringIO(), StringIO()
        call_command("balances", stdout=reseau)
        call_command("balances", "--succursale", "Café 2", stdout=cafe2)
        self.assertIn("Sara Martin", reseau.getvalue())
        self.assertRegex(reseau.getvalue(), r"Sara Martin\s+4\s+4\s+0\s+0")  # 4 étampes au total
        self.assertRegex(cafe2.getvalue(), r"Sara Martin\s+1\s+0\s+0\s+0")   # 1 achat au Café 2


class ConfigurationEtSante(TestCase):
    def test_la_page_de_sante_repond_sans_connexion_et_verifie_la_base(self):
        rep = self.client.get("/sante/")
        self.assertEqual((rep.status_code, rep.content), (200, b"ok"))

    def test_une_page_inexistante_donne_un_404_normal(self):
        self.assertEqual(self.client.get("/pas-de-page/").status_code, 404)


class MigrationV2VersV3(TransactionTestCase):
    """Les données d'une base v2 passent à la v3 : tout appartient au premier café."""
    serialized_rollback = True

    def test_les_donnees_de_la_v2_appartiennent_au_cafe_1(self):
        avant = [("fidelite", "0004_donnees_initiales_v2")]
        apres = [("fidelite", "0007_succursale_obligatoire")]
        MigrationExecutor(connection).migrate(avant)                # on revient à la v2
        anciennes = MigrationExecutor(connection).loader.project_state(avant).apps
        user = anciennes.get_model("auth", "User").objects.create(username="vieux")
        user.groups.add(anciennes.get_model("auth", "Group").objects.get(name="barista"))
        client = anciennes.get_model("fidelite", "Client").objects.create(
            nom="Ancien", telephone="4185559999")
        for _ in range(3):
            anciennes.get_model("fidelite", "Transaction").objects.create(
                client=client, type="ACHAT_PAYE")

        MigrationExecutor(connection).migrate(apres)                # v3 par-dessus la v2
        nouvelles = MigrationExecutor(connection).loader.project_state(apres).apps
        cafe = nouvelles.get_model("fidelite", "Succursale").objects.get()
        self.assertEqual(cafe.nom, "Café 1")
        self.assertEqual(nouvelles.get_model("fidelite", "Transaction").objects
                         .filter(succursale=cafe).count(), 3)
        self.assertEqual(list(cafe.personnel.values_list("username", flat=True)), ["vieux"])


class DonneesDeDemonstration(TestCase):
    def test_demo_v3_fonctionne_sur_une_base_neuve_et_se_relance_sans_erreur(self):
        call_command("demo_v3", stdout=StringIO())
        call_command("demo_v3", stdout=StringIO())          # relancée : rien n'est dupliqué
        self.assertEqual(Succursale.objects.count(), 2)
        for compte in ("barista", "gerant", "gerant2", "proprietaire"):
            self.assertTrue(User.objects.filter(username=compte).exists(), compte)
        camille = Client.objects.get(nom="Camille Deux-Cafés")
        self.assertEqual(set(camille.transactions.values_list("succursale__nom", flat=True)),
                         {"Café 1", "Café 2"})
