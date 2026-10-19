import re
from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

# Un cafe gratuit expire 30 jours apres le jour ou il a ete gagne.
DUREE_EXPIRATION_JOURS = 30

# Regle initiale (v1) : 10 achats payes = 1 cafe gratuit.
# En v2, la regle reelle vient de la table RegleFidelite (modifiable sans code).
ACHATS_POUR_GRATUIT = 10

# Une carte prepayee expire 30 jours apres sa vente et contient 11 cafes.
DUREE_CARTE_JOURS = 30
CAFES_PAR_CARTE = 11


class Client(models.Model):
    nom = models.CharField(max_length=100)
    # unique=True = deux clients ne peuvent PAS avoir le meme numero.
    telephone = models.CharField(max_length=15, unique=True)
    courriel = models.EmailField(blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    # v2 : un client efface est ANONYMISE (la ligne reste pour garder les rapports).
    efface = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # On garde seulement les chiffres, sauf pour un client efface
        # (son "telephone" est alors un marqueur unique : "efface-<id>").
        if not self.efface:
            self.telephone = re.sub(r"\D", "", self.telephone)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.telephone})"

    def anonymiser(self):
        # Remplace TOUT ce qui identifie le client. Le marqueur reste unique
        # (contrainte unique du telephone) mais ne contient aucune donnee personnelle.
        self.nom = "Client effacé"
        self.telephone = f"efface-{self.pk}"
        self.courriel = ""
        self.efface = True
        self.save()

    # ---------- Calculs de fidelite (a partir du journal Transaction) ----------

    def journal_actif(self):
        # Les transactions NON annulees, dans l'ordre chronologique.
        return self.transactions.filter(annulee_le__isnull=True).order_by("cree_le", "id")

    @property
    def achats_payes(self):
        return self.transactions.filter(
            type=Transaction.Type.ACHAT_PAYE, annulee_le__isnull=True
        ).count()

    @property
    def gratuits_utilises(self):
        return self.transactions.filter(
            type=Transaction.Type.CAFE_GRATUIT, annulee_le__isnull=True
        ).count()

    def etat(self):
        return rejouer(self.journal_actif())

    @property
    def etampes_cycle(self):
        # Etampes accumulees vers le prochain cafe gratuit.
        return self.etat().cycle

    def recompenses_disponibles(self):
        # Dates d'expiration des cafes gratuits encore valides, du plus ancien au plus recent.
        duree = timedelta(days=DUREE_EXPIRATION_JOURS)
        maintenant = timezone.now()
        return [d + duree for d in self.etat().recompenses if d + duree >= maintenant]

    @property
    def gratuits_disponibles(self):
        return len(self.recompenses_disponibles())

    @property
    def prochaine_expiration(self):
        expirations = self.recompenses_disponibles()
        return expirations[0] if expirations else None

    # ---------- Cartes prepayees ----------

    def cartes_valides(self):
        # Cartes non annulees, non expirees, avec des cafes restants (la plus ancienne d'abord).
        cartes = self.cartes.filter(cafes_restants__gt=0, annulee=False).order_by("creee_le")
        return [c for c in cartes if not c.est_expiree]

    @property
    def carte_active(self):
        cartes = self.cartes_valides()
        return cartes[0] if cartes else None

    @property
    def cafes_prepayes_restants(self):
        return sum(c.cafes_restants for c in self.cartes_valides())


class CartePrepayee(models.Model):
    # La carte de 11 cafes vendue au prix de 10 (l'argent est encaisse hors systeme).
    # cafes_restants est un CACHE : le journal fait foi (voir ADR-0001).
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="cartes")
    cafes_restants = models.PositiveSmallIntegerField(default=11)
    creee_le = models.DateTimeField(auto_now_add=True)
    # v2 : mise a True quand la vente de la carte est annulee.
    annulee = models.BooleanField(default=False)

    def recalculer(self):
        # Recalcule le cache a partir du journal : 11 - cafes pris (non annules).
        utilises = self.transaction_set.filter(
            type=Transaction.Type.ACHAT_CARTE, annulee_le__isnull=True
        ).count()
        self.cafes_restants = max(CAFES_PAR_CARTE - utilises, 0)
        self.save(update_fields=["cafes_restants"])

    @property
    def expire_le(self):
        return self.creee_le + timedelta(days=DUREE_CARTE_JOURS)

    @property
    def est_expiree(self):
        return timezone.now() > self.expire_le

    @property
    def cafes_utilisables(self):
        return 0 if (self.est_expiree or self.annulee) else self.cafes_restants

    def __str__(self):
        return f"Carte de {self.client.nom} ({self.cafes_utilisables} utilisables)"


class Transaction(models.Model):
    # Le journal : CHAQUE evenement lie a la fidelite est enregistre ici.
    # Une transaction n'est jamais supprimee : on l'ANNULE (annulee_le / annulee_par).

    class Type(models.TextChoices):
        ACHAT_PAYE = "ACHAT_PAYE", "Achat paye"
        ACHAT_CARTE = "ACHAT_CARTE", "Cafe pris sur une carte prepayee"
        CAFE_GRATUIT = "CAFE_GRATUIT", "Cafe gratuit (recompense)"
        VENTE_CARTE = "VENTE_CARTE", "Vente d'une carte prepayee"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="transactions")
    type = models.CharField(max_length=20, choices=Type.choices)
    carte = models.ForeignKey(CartePrepayee, null=True, blank=True, on_delete=models.SET_NULL)
    cree_le = models.DateTimeField(auto_now_add=True)
    # v2 : qui a fait la transaction (vide pour les transactions de la v1).
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    # v2 : annulation (qui et quand).
    annulee_le = models.DateTimeField(null=True, blank=True)
    annulee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    @property
    def est_annulee(self):
        return self.annulee_le is not None

    def __str__(self):
        return f"{self.get_type_display()} - {self.client.nom}"


class RegleFidelite(models.Model):
    # Nombre d'etampes pour un cafe gratuit, a partir d'une date (ADR-0004).
    etampes_requises = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    en_vigueur_le = models.DateField(unique=True)
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["en_vigueur_le"]

    def __str__(self):
        return f"{self.etampes_requises} étampes dès le {self.en_vigueur_le}"


class Audit(models.Model):
    # Trace des actions du gerant. NE CONTIENT JAMAIS de renseignement personnel
    # (seulement des numeros d'identifiant) : voir ADR-0005.
    class Action(models.TextChoices):
        FUSION = "FUSION", "Fusion de fiches"
        EFFACEMENT = "EFFACEMENT", "Effacement d'un client"
        REGLE = "REGLE", "Changement de règle"

    action = models.CharField(max_length=20, choices=Action.choices)
    par = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    cree_le = models.DateTimeField(auto_now_add=True)
    details = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.get_action_display()} - {self.details}"


# ---------- Rejeu du journal ----------

class Etat:
    def __init__(self):
        self.payes = 0
        self.cycle = 0          # etampes accumulees depuis le dernier gratuit gagne
        self.recompenses = []   # dates d'obtention des gratuits non consommes
        self.coherent = True    # False si un gratuit a ete pris sans recompense valide


def rejouer(transactions):
    # transactions : NON annulees, triees par (cree_le, id).
    # La regle appliquee a un achat est celle en vigueur a la DATE de cet achat.
    regles = list(RegleFidelite.objects.order_by("en_vigueur_le")
                  .values_list("en_vigueur_le", "etampes_requises"))
    duree = timedelta(days=DUREE_EXPIRATION_JOURS)

    def requis(quand):
        jour = timezone.localdate(quand)
        n = ACHATS_POUR_GRATUIT
        for debut, etampes in regles:
            if debut <= jour:
                n = etampes
        return n

    etat = Etat()
    for t in transactions:
        if t.type == Transaction.Type.ACHAT_PAYE:
            etat.payes += 1
            etat.cycle += 1
            if etat.cycle >= requis(t.cree_le):
                etat.recompenses.append(t.cree_le)
                etat.cycle = 0
        elif t.type == Transaction.Type.CAFE_GRATUIT:
            while etat.recompenses and etat.recompenses[0] + duree < t.cree_le:
                etat.recompenses.pop(0)
            if etat.recompenses:
                etat.recompenses.pop(0)
            else:
                etat.coherent = False
    return etat