import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Client

# ---- Expressions régulières (compilées une seule fois, ici) ----

# NOM : des lettres (accents permis), séparées par UN espace, tiret ou apostrophe.
# Accepte : "Sara", "Marie-Ève", "O'Brien", "Jean Tremblay"
# Refuse  : "k1", "--", "Sara  ", "123"
# À-Ö, Ø-ö, ø-ÿ = toutes les lettres accentuées (sans les symboles × et ÷).
REGEX_NOM = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '’\-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$")

# TÉLÉPHONE, étape 1 : ce que le barista a le droit de taper.
# Chiffres, espaces, tirets, points, parenthèses, et un "+" au début.
REGEX_TEL_SAISIE = re.compile(r"^\+?[\d\s().\-]+$")

# TÉLÉPHONE, étape 2 : le numéro nettoyé (10 chiffres, format nord-américain).
# [2-9]\d{2} = indicatif régional (ne commence jamais par 0 ou 1)
# [2-9]\d{6} = le reste du numéro (le poste ne commence jamais par 0 ou 1 non plus)
REGEX_TEL_NA = re.compile(r"^[2-9]\d{2}[2-9]\d{6}$")

# COURRIEL : texte@domaine.extension, avec une extension d'au moins 2 lettres.
# Refuse "sara@gmail" (pas d'extension) et "sara@.com".
REGEX_COURRIEL = re.compile(
    r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$"
)


class ClientForm(forms.ModelForm):
    # On redéclare le champ téléphone pour permettre de taper "+1 (418) 555-1234"
    # (17 caractères) : le max_length=15 du modèle aurait refusé ça avant même
    # que notre validation s'exécute. On nettoie le numéro plus bas.
    telephone = forms.CharField(
        max_length=20,
        label="Téléphone",
        widget=forms.TextInput(attrs={"placeholder": "418-555-1234", "inputmode": "tel"}),
    )

    class Meta:
        model = Client
        fields = ["nom", "telephone", "courriel"]

    # Django appelle automatiquement clean_<nom_du_champ>() pour chaque champ.
    # Si on lève une ValidationError, le formulaire est refusé et le message
    # s'affiche en rouge sous le champ.

    def clean_nom(self):
        # split() puis join() : enlève les espaces au début, à la fin et les doubles.
        nom = " ".join(self.cleaned_data["nom"].split())

        if len(nom) < 2:
            raise ValidationError("Le nom doit contenir au moins 2 lettres.")

        if not REGEX_NOM.match(nom):
            raise ValidationError(
                "Nom invalide : lettres seulement (espace, tiret et apostrophe permis)."
            )

        # Refuse "kk", "aaa" : il faut au moins 2 lettres différentes.
        # set() garde les valeurs uniques : set("kk") = {"k"}, set("Sara") = {"s","a","r"}.
        lettres = re.sub(r"[^A-Za-zÀ-ÿ]", "", nom).lower()
        if len(set(lettres)) < 2:
            raise ValidationError("Ce nom ne semble pas valide.")

        return nom

    def clean_telephone(self):
        brut = self.cleaned_data["telephone"].strip()

        # Étape 1 : pas de lettres ni de symboles bizarres.
        if not REGEX_TEL_SAISIE.match(brut):
            raise ValidationError(
                "Téléphone invalide : chiffres, espaces, tirets ou parenthèses seulement."
            )

        # Étape 2 : on garde seulement les chiffres.
        chiffres = re.sub(r"\D", "", brut)

        # Un "1" devant (indicatif du Canada) est permis : 14185551234 -> 4185551234.
        if len(chiffres) == 11 and chiffres.startswith("1"):
            chiffres = chiffres[1:]

        # Étape 3 : il doit rester exactement un numéro nord-américain valide.
        if not REGEX_TEL_NA.match(chiffres):
            raise ValidationError("Numéro invalide : il faut 10 chiffres (ex. 418-555-1234).")

        # IMPORTANT : on retourne les chiffres seulement. Comme ça, Django vérifie
        # l'unicité sur "4185551234" et non sur "418-555-1234". Sans ça, un doublon
        # écrit avec des tirets passerait le contrôle et ferait planter l'enregistrement.
        return chiffres

    def clean_courriel(self):
        # Le courriel est facultatif : s'il est vide, on n'a rien à vérifier.
        courriel = self.cleaned_data.get("courriel", "").strip().lower()

        if courriel and not REGEX_COURRIEL.match(courriel):
            raise ValidationError("Courriel invalide (ex. sara@exemple.com).")

        # En minuscules : "Sara@Gmail.com" et "sara@gmail.com" sont la même adresse.
        return courriel