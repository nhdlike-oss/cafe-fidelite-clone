import re
from datetime import timedelta

from django.db import models
from django.utils import timezone

# Un cafe gratuit expire 30 jours apres le jour ou il a ete gagne.
DUREE_EXPIRATION_JOURS = 30

# Nombre d'achats payes necessaires pour gagner un cafe gratuit.
ACHATS_POUR_GRATUIT = 10

# NOUVEAU : une carte prepayee expire 30 jours apres sa vente.
DUREE_CARTE_JOURS = 30


class Client(models.Model):
    nom = models.CharField(max_length=100)
    # unique=True = deux clients ne peuvent PAS avoir le meme numero.
    telephone = models.CharField(max_length=15, unique=True)
    # blank=True = champ facultatif. Pas unique : une famille peut partager un courriel.
    courriel = models.EmailField(blank=True)
    # auto_now_add=True = Django remplit la date tout seul, une fois, a la creation.
    cree_le = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # S'execute a chaque enregistrement : on garde seulement les chiffres.
        # "418-555-1234" devient "4185551234".
        self.telephone = re.sub(r"\D", "", self.telephone)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.telephone})"

    # ---------- Calculs de fidelite (a partir du journal Transaction) ----------

    @property
    def achats_payes(self):
        # Nombre total de cafes payes normalement par ce client.
        return self.transactions.filter(type=Transaction.Type.ACHAT_PAYE).count()

    @property
    def gratuits_utilises(self):
        # Nombre total de cafes gratuits deja pris (information seulement).
        return self.transactions.filter(type=Transaction.Type.CAFE_GRATUIT).count()

    def recompenses_disponibles(self):
        # Renvoie la liste des DATES D'EXPIRATION des cafes gratuits encore valides,
        # du plus ancien au plus recent.
        duree = timedelta(days=DUREE_EXPIRATION_JOURS)
        payes = 0
        recompenses = []  # dates d'obtention, la plus ancienne en premier

        # On rejoue toute l'histoire du client, dans l'ordre chronologique.
        for t in self.transactions.order_by("cree_le", "id"):
            if t.type == Transaction.Type.ACHAT_PAYE:
                payes += 1
                # Chaque 10e achat paye (10, 20, 30...) gagne un cafe gratuit.
                if payes % ACHATS_POUR_GRATUIT == 0:
                    recompenses.append(t.cree_le)

            elif t.type == Transaction.Type.CAFE_GRATUIT:
                # On retire d'abord les recompenses expirees AU MOMENT de cette utilisation.
                while recompenses and recompenses[0] + duree < t.cree_le:
                    recompenses.pop(0)
                # Puis on consomme la plus ancienne encore valide.
                if recompenses:
                    recompenses.pop(0)

        # Enfin, on garde seulement celles qui ne sont pas expirees MAINTENANT.
        maintenant = timezone.now()
        return [d + duree for d in recompenses if d + duree >= maintenant]

    @property
    def gratuits_disponibles(self):
        # Combien de cafes gratuits le client peut utiliser aujourd'hui.
        return len(self.recompenses_disponibles())

    @property
    def prochaine_expiration(self):
        # Date d'expiration du cafe gratuit le plus proche (ou None s'il n'y en a pas).
        expirations = self.recompenses_disponibles()
        return expirations[0] if expirations else None

    # ---------- NOUVEAU : cartes prepayees ----------

    def cartes_valides(self):
        # Cartes NON expirees qui ont encore des cafes, la plus ancienne d'abord
        # (celle qui expire en premier est utilisee en premier).
        cartes = self.cartes.filter(cafes_restants__gt=0).order_by("creee_le")
        return [c for c in cartes if not c.est_expiree]

    @property
    def carte_active(self):
        # La carte a utiliser en premier, ou None si le client n'en a aucune de valide.
        cartes = self.cartes_valides()
        return cartes[0] if cartes else None

    @property
    def cafes_prepayes_restants(self):
        # Total des cafes utilisables sur TOUTES les cartes valides du client.
        # Une carte expiree ne compte pas : son compte "revient a 0".
        return sum(c.cafes_restants for c in self.cartes_valides())


class CartePrepayee(models.Model):
    # La carte de 11 cafes vendue au prix de 10.
    # L'argent est encaisse a la caisse, hors de ce systeme (voir 2.6 de l'enonce).

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cartes")
    cafes_restants = models.PositiveSmallIntegerField(default=11)
    creee_le = models.DateTimeField(auto_now_add=True)

    @property
    def expire_le(self):
        # Date d'expiration = date de vente + 30 jours.
        return self.creee_le + timedelta(days=DUREE_CARTE_JOURS)

    @property
    def est_expiree(self):
        # Vrai si la date d'expiration est passee.
        return timezone.now() > self.expire_le

    @property
    def cafes_utilisables(self):
        # Cafes reellement utilisables : 0 si la carte est expiree.
        return 0 if self.est_expiree else self.cafes_restants

    def __str__(self):
        return f"Carte de {self.client.nom} ({self.cafes_utilisables} utilisables)"


class Transaction(models.Model):
    # Le journal : CHAQUE evenement lie a la fidelite est enregistre ici.

    class Type(models.TextChoices):
        ACHAT_PAYE = "ACHAT_PAYE", "Achat paye"
        ACHAT_CARTE = "ACHAT_CARTE", "Cafe pris sur une carte prepayee"
        CAFE_GRATUIT = "CAFE_GRATUIT", "Cafe gratuit (recompense)"
        VENTE_CARTE = "VENTE_CARTE", "Vente d'une carte prepayee"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="transactions")
    type = models.CharField(max_length=20, choices=Type.choices)
    carte = models.ForeignKey(CartePrepayee, null=True, blank=True, on_delete=models.SET_NULL)
    cree_le = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_type_display()} - {self.client.nom}"