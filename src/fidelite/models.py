# "import" veut dire : on va chercher du code écrit ailleurs, pour l'utiliser ici.
# "re" est un module de Python qui sait travailler avec du texte (chercher, remplacer).
import re

# On importe "models", l'outil de Django pour décrire des données.
from django.db import models


# "class" crée un nouveau type d'objet. Ici, le type "Client".
# "(models.Model)" veut dire : Client HÉRITE de models.Model,
# donc il reçoit gratuitement tout ce que Django sait faire avec les modèles.
class Client(models.Model):

    # Chaque ligne ci-dessous décrit UNE colonne dans la table "Client".
    # nom_variable = type_de_champ(options)

    nom = models.CharField(max_length=100)
    # CharField = texte court.
    # max_length=100 = obligatoire pour CharField, la longueur maximale acceptée.

    telephone = models.CharField(max_length=15, unique=True)
    # unique=True = deux clients ne peuvent PAS avoir le même numéro.
    # Django refusera d'enregistrer un doublon.

    courriel = models.EmailField(blank=True)
    # EmailField = comme CharField, mais vérifie que ça ressemble à un courriel.
    # blank=True = ce champ est FACULTATIF dans les formulaires.

    cree_le = models.DateTimeField(auto_now_add=True)
    # DateTimeField = une date ET une heure.
    # auto_now_add=True = Django remplit cette date TOUT SEUL, une fois, à la création.

    # "def" crée une fonction. Ici, une méthode (une fonction qui appartient à la classe).
    # "self" représente "cet objet-ci", le client précis sur lequel on travaille.
    def save(self, *args, **kwargs):
        # Cette méthode s'exécute CHAQUE FOIS qu'on enregistre un client.
        # On la réécrit pour nettoyer le numéro de téléphone avant de le stocker.

        # re.sub(motif, remplacement, texte) : remplace dans "texte" tout ce qui
        # correspond au "motif" par "remplacement".
        # r"\D" = un motif qui veut dire "tout caractère qui N'EST PAS un chiffre".
        # On remplace ces caractères par rien ("").
        # Résultat : "418-555-1234" devient "4185551234".
        self.telephone = re.sub(r"\D", "", self.telephone)

        # On appelle ensuite la vraie méthode save() de Django (celle qu'on a
        # "écrasée"), pour qu'elle fasse le travail réel d'enregistrement.
        # "super()" veut dire : va chercher cette méthode chez le parent (models.Model).
        super().save(*args, **kwargs)

    # __str__ (deux tirets bas de chaque côté) est une méthode spéciale de Python.
    # Elle dit à Python comment AFFICHER cet objet sous forme de texte.
    # Sans elle, un client s'afficherait "Client object (1)", pas très utile.
    def __str__(self):
        # f"..." est une "f-string" : elle permet d'insérer des variables dans
        # du texte avec des accolades {}.
        return f"{self.nom} ({self.telephone})"