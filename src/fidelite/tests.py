from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import ClientForm, RegleForm
from .models import Audit, CartePrepayee, Client, RegleFidelite, Transaction
from .services import (ErreurMetier, annuler_transaction, effacer_client,
                       fusionner_clients)

T = Transaction.Type


# ---------- Outils de test ----------

def ajouter(client, type_, jours=0, carte=None, par=None):
    # Cree une transaction "il y a N jours" (cree_le est automatique, on le recule apres).
    t = Transaction.objects.create(client=client, type=type_, carte=carte, cree_par=par)
    if jours:
        Transaction.objects.filter(pk=t.pk).update(cree_le=timezone.now() - timedelta(days=jours))
        t.refresh_from_db()
    return t


def acheter(client, n, jours=0, par=None):
    return [ajouter(client, T.ACHAT_PAYE, jours, par=par) for _ in range(n)]


def vendre_carte(client, jours=0, utilises=0):
    carte = CartePrepayee.objects.create(client=client)
    if jours:
        CartePrepayee.objects.filter(pk=carte.pk).update(
            creee_le=timezone.now() - timedelta(days=jours))
        carte.refresh_from_db()
    ajouter(client, T.VENTE_CARTE, jours, carte=carte)
    for _ in range(utilises):
        ajouter(client, T.ACHAT_CARTE, 0, carte=carte)
        carte.cafes_restants -= 1
    carte.save()
    return carte


class BaseTest(TestCase):
    def setUp(self):
        self.barista = User.objects.create_user("barista", password="x")
        self.barista.groups.add(Group.objects.get(name="barista"))
        self.gerant = User.objects.create_user("gerant", password="x")
        self.gerant.groups.add(Group.objects.get(name="gerant"))
        self.cl = Client.objects.create(nom="Sara Martin", telephone="4185550001")


# ---------- Regles de la v1 ----------

class ReglesV1(BaseTest):
    def test_dixieme_achat_donne_un_cafe_gratuit(self):
        acheter(self.cl, 9)
        self.assertEqual(self.cl.gratuits_disponibles, 0)
        acheter(self.cl, 1)
        self.assertEqual(self.cl.gratuits_disponibles, 1)

    def test_cafe_gratuit_expire_apres_30_jours(self):
        acheter(self.cl, 10, jours=31)
        self.assertEqual(self.cl.gratuits_disponibles, 0)

    def test_cafe_gratuit_pris_est_consomme(self):
        acheter(self.cl, 10)
        ajouter(self.cl, T.CAFE_GRATUIT)
        self.assertEqual(self.cl.gratuits_disponibles, 0)

    def test_carte_prepayee_11_cafes_et_ne_compte_pas_pour_les_achats(self):
        vendre_carte(self.cl, utilises=4)
        self.assertEqual(self.cl.cafes_prepayes_restants, 7)
        self.assertEqual(self.cl.achats_payes, 0)

    def test_carte_prepayee_expire_apres_30_jours(self):
        vendre_carte(self.cl, jours=31)
        self.assertEqual(self.cl.cafes_prepayes_restants, 0)

    def test_validation_du_formulaire_client(self):
        bon = ClientForm({"nom": "Marie-Ève", "telephone": "+1 (418) 555-1234", "courriel": ""})
        self.assertTrue(bon.is_valid(), bon.errors)
        self.assertEqual(bon.cleaned_data["telephone"], "4185551234")
        self.assertFalse(ClientForm({"nom": "k1", "telephone": "4185551234"}).is_valid())
        self.assertFalse(ClientForm({"nom": "Sara", "telephone": "123"}).is_valid())
        self.assertFalse(ClientForm(
            {"nom": "Sara", "telephone": "4185551234", "courriel": "sara@gmail"}).is_valid())

    def test_recherche_par_telephone_avec_tirets(self):
        self.client.force_login(self.barista)
        rep = self.client.get(reverse("trouver_client"), {"q": "418-555"})
        self.assertIn(self.cl, list(rep.context["resultats"]))


# ---------- 3.1 Annuler ----------

class Annulation(BaseTest):
    def test_annuler_un_achat_corrige_le_solde_et_garde_la_trace(self):
        tx = acheter(self.cl, 1)[0]
        annuler_transaction(tx, self.gerant)
        tx.refresh_from_db()
        self.assertEqual(self.cl.achats_payes, 0)
        self.assertEqual(tx.annulee_par, self.gerant)
        self.assertIsNotNone(tx.annulee_le)
        self.assertTrue(Transaction.objects.filter(pk=tx.pk).exists())  # jamais supprimee

    def test_zone_grise_10e_etampe_dont_le_gratuit_est_deja_bu(self):
        achats = acheter(self.cl, 10)
        gratuit = ajouter(self.cl, T.CAFE_GRATUIT)
        with self.assertRaises(ErreurMetier):
            annuler_transaction(achats[-1], self.gerant)
        self.assertEqual(self.cl.achats_payes, 10)          # rien n'a change
        annuler_transaction(gratuit, self.gerant)           # d'abord le gratuit...
        annuler_transaction(achats[-1], self.gerant)        # ...puis l'achat
        self.assertEqual(self.cl.achats_payes, 9)
        self.assertEqual(self.cl.gratuits_disponibles, 0)

    def test_zone_grise_on_peut_annuler_une_transaction_de_3_mois(self):
        tx = ajouter(self.cl, T.ACHAT_PAYE, jours=90)
        annuler_transaction(tx, self.gerant)
        self.assertEqual(self.cl.achats_payes, 0)

    def test_annuler_un_cafe_sur_carte_remet_le_cafe(self):
        carte = vendre_carte(self.cl, utilises=4)
        tx = Transaction.objects.filter(type=T.ACHAT_CARTE).first()
        annuler_transaction(tx, self.gerant)
        carte.refresh_from_db()
        self.assertEqual(carte.cafes_restants, 8)

    def test_annuler_la_vente_d_une_carte(self):
        carte = vendre_carte(self.cl, utilises=1)
        vente = Transaction.objects.get(type=T.VENTE_CARTE)
        with self.assertRaises(ErreurMetier):               # un cafe a deja ete pris
            annuler_transaction(vente, self.gerant)
        annuler_transaction(Transaction.objects.get(type=T.ACHAT_CARTE), self.gerant)
        annuler_transaction(vente, self.gerant)
        self.assertEqual(self.cl.cafes_prepayes_restants, 0)

    def test_on_ne_peut_pas_annuler_deux_fois(self):
        tx = acheter(self.cl, 1)[0]
        annuler_transaction(tx, self.gerant)
        with self.assertRaises(ErreurMetier):
            annuler_transaction(tx, self.gerant)


# ---------- 3.2 Rapports ----------

class Rapports(BaseTest):
    def lire(self, jour):
        rep = self.client.get(reverse("rapports"), {"debut": jour.isoformat(), "fin": jour.isoformat()})
        return rep.context

    def test_rapport_par_periode_et_transactions_annulees_exclues(self):
        acheter(self.cl, 8, jours=20)                        # 8 etampes plus anciennes
        passes = acheter(self.cl, 2, jours=3)                # 10e etampe il y a 3 jours
        acheter(self.cl, 3)
        ajouter(self.cl, T.CAFE_GRATUIT)
        vendre_carte(self.cl, utilises=2)
        self.client.force_login(self.gerant)

        aujourdhui = timezone.localdate()
        ctx = self.lire(aujourdhui)
        self.assertEqual((ctx["payes"], ctx["gratuits"], ctx["sur_carte"], ctx["cartes"]), (3, 1, 2, 1))

        mardi = aujourdhui - timedelta(days=3)
        self.assertEqual(self.lire(mardi)["payes"], 2)
        # Zone grise : annuler aujourd'hui un achat d'un jour passe change le rapport de ce jour.
        annuler_transaction(passes[0], self.gerant)
        ctx = self.lire(mardi)
        self.assertEqual(ctx["payes"], 1)
        self.assertEqual(ctx["annulees"], 1)

    def test_les_cafes_d_un_client_efface_restent_comptes(self):
        acheter(self.cl, 3)
        self.client.force_login(self.gerant)
        avant = self.lire(timezone.localdate())["payes"]
        effacer_client(self.cl, self.gerant)
        self.assertEqual(self.lire(timezone.localdate())["payes"], avant)


# ---------- 3.3 Regle ----------

class ChangementDeRegle(BaseTest):
    def setUp(self):
        super().setUp()
        # 12 etampes, en vigueur depuis il y a 2 jours.
        RegleFidelite.objects.create(
            etampes_requises=12, en_vigueur_le=timezone.localdate() - timedelta(days=2))

    def test_zone_grise_un_gratuit_deja_gagne_est_conserve(self):
        acheter(self.cl, 10, jours=5)                       # 10 etampes AVANT le changement
        self.assertEqual(self.cl.gratuits_disponibles, 1)

    def test_zone_grise_les_etampes_accumulees_comptent_pour_la_nouvelle_regle(self):
        acheter(self.cl, 8, jours=5)
        acheter(self.cl, 3)
        self.assertEqual(self.cl.gratuits_disponibles, 0)   # 11 etampes < 12
        acheter(self.cl, 1)
        self.assertEqual(self.cl.gratuits_disponibles, 1)   # 12e etampe

    def test_la_date_ne_peut_pas_etre_dans_le_passe(self):
        hier = timezone.localdate() - timedelta(days=1)
        self.assertFalse(RegleForm({"etampes_requises": 12, "en_vigueur_le": hier}).is_valid())
        demain = timezone.localdate() + timedelta(days=1)
        self.assertTrue(RegleForm({"etampes_requises": 12, "en_vigueur_le": demain}).is_valid())

    def test_le_gerant_change_la_regle_sans_code(self):
        self.client.force_login(self.gerant)
        demain = timezone.localdate() + timedelta(days=1)
        rep = self.client.post(reverse("regle"), {"etampes_requises": 15, "en_vigueur_le": demain})
        self.assertEqual(rep.status_code, 302)
        self.assertTrue(RegleFidelite.objects.filter(etampes_requises=15).exists())
        self.assertTrue(Audit.objects.filter(action=Audit.Action.REGLE).exists())


# ---------- 3.4 Effacer ----------

class Effacement(BaseTest):
    def test_effacer_anonymise_garde_les_transactions_et_ne_laisse_aucune_trace(self):
        client = Client.objects.create(nom="Jean Dupont", telephone="4185559999",
                                       courriel="jean@exemple.com")
        acheter(client, 3)
        effacer_client(client, self.gerant)
        client.refresh_from_db()
        for champ in (client.nom, client.telephone, client.courriel):
            self.assertNotIn("Dupont", champ)
            self.assertNotIn("9999", champ)
            self.assertNotIn("jean", champ)
        self.assertTrue(client.efface)
        self.assertEqual(client.transactions.count(), 3)    # statistiques intactes
        for a in Audit.objects.all():                       # le journal d'audit non plus
            self.assertNotIn("Dupont", a.details)
            self.assertNotIn("9999", a.details)

    def test_un_client_efface_n_est_plus_trouvable_ni_utilisable(self):
        client = Client.objects.create(nom="Jean Dupont", telephone="4185559999")
        effacer_client(client, self.gerant)
        self.client.force_login(self.barista)
        rep = self.client.get(reverse("trouver_client"), {"q": "Dupont"})
        self.assertEqual(len(rep.context["resultats"]), 0)
        self.assertEqual(self.client.get(reverse("enregistrer_achat", args=[client.pk])).status_code, 404)

    def test_effacer_deux_fois_est_refuse(self):
        effacer_client(self.cl, self.gerant)
        with self.assertRaises(ErreurMetier):
            effacer_client(self.cl, self.gerant)

    def test_la_carte_restante_est_signalee_avant_l_effacement(self):
        vendre_carte(self.cl, utilises=4)
        self.client.force_login(self.gerant)
        rep = self.client.get(reverse("effacer", args=[self.cl.pk]))
        self.assertContains(rep, "7")
        self.assertContains(rep, "perdus")


# ---------- 3.5 Fusionner ----------

class Fusion(BaseTest):
    def test_6_plus_7_etampes_donnent_un_gratuit_et_tout_est_conserve(self):
        a = self.cl                                          # fiche la plus ancienne
        b = Client.objects.create(nom="Sara M.", telephone="4185550002")
        acheter(a, 6, jours=10)
        acheter(b, 7, jours=8)
        vendre_carte(b, utilises=2)
        self.assertEqual((a.gratuits_disponibles, b.gratuits_disponibles), (0, 0))

        garde = fusionner_clients(b, a, self.gerant)         # l'ordre des arguments n'a pas d'importance
        self.assertEqual(garde.pk, a.pk)                     # la plus ancienne survit
        self.assertEqual(garde.achats_payes, 13)
        self.assertEqual(garde.gratuits_disponibles, 1)      # 13 etampes : gratuit tout de suite
        self.assertEqual(garde.cafes_prepayes_restants, 9)   # la carte a suivi
        self.assertFalse(Client.objects.filter(pk=b.pk).exists())
        audit = Audit.objects.get(action=Audit.Action.FUSION)
        self.assertNotIn("Sara", audit.details)

    def test_fusionner_une_fiche_avec_elle_meme_est_refuse(self):
        with self.assertRaises(ErreurMetier):
            fusionner_clients(self.cl, self.cl, self.gerant)

    def test_fusion_via_l_ecran_du_gerant(self):
        b = Client.objects.create(nom="Autre", telephone="4185550002")
        self.client.force_login(self.gerant)
        rep = self.client.post(reverse("fusionner_avec", args=[self.cl.pk, b.pk]))
        self.assertEqual(rep.status_code, 302)
        self.assertFalse(Client.objects.filter(pk=b.pk).exists())


# ---------- 3.6 Roles ----------

class Permissions(BaseTest):
    def test_les_ecrans_du_comptoir_demandent_une_connexion(self):
        rep = self.client.get(reverse("trouver_client"))
        self.assertEqual(rep.status_code, 302)
        self.assertIn("/connexion/", rep["Location"])

    def test_le_barista_enregistre_un_achat_et_son_nom_est_retenu(self):
        self.client.force_login(self.barista)
        self.client.post(reverse("enregistrer_achat", args=[self.cl.pk]),
                         {"action": "payer", "quantite": "2"})
        txs = Transaction.objects.filter(client=self.cl)
        self.assertEqual(txs.count(), 2)
        self.assertTrue(all(t.cree_par == self.barista for t in txs))

    def test_le_barista_ne_peut_ni_annuler_ni_voir_les_rapports_ni_effacer_ni_fusionner(self):
        tx = acheter(self.cl, 1, par=self.barista)[0]
        self.client.force_login(self.barista)
        self.assertEqual(self.client.post(reverse("annuler", args=[tx.pk])).status_code, 403)
        tx.refresh_from_db()
        self.assertIsNone(tx.annulee_le)                    # même sa propre erreur (ADR-0007)
        for nom, args in (("rapports", []), ("regle", []), ("effacer", [self.cl.pk]),
                          ("fusionner", [self.cl.pk])):
            self.assertEqual(self.client.get(reverse(nom, args=args)).status_code, 403, nom)

    def test_le_gerant_annule_via_l_ecran(self):
        tx = acheter(self.cl, 1, par=self.barista)[0]
        self.client.force_login(self.gerant)
        self.client.post(reverse("annuler", args=[tx.pk]))
        tx.refresh_from_db()
        self.assertEqual(tx.annulee_par, self.gerant)
        self.assertEqual(self.client.get(reverse("rapports")).status_code, 200)

    def test_les_roles_et_la_regle_initiale_existent_apres_migration(self):
        self.assertTrue(Group.objects.filter(name="barista").exists())
        self.assertTrue(Group.objects.filter(name="gerant").exists())
        self.assertTrue(RegleFidelite.objects.filter(etampes_requises=10).exists())


# ---------- Migration : commande des soldes ----------

class Soldes(BaseTest):
    def test_commande_balances(self):
        acheter(self.cl, 10)
        sortie = StringIO()
        call_command("balances", stdout=sortie)
        self.assertIn("Sara Martin", sortie.getvalue())
