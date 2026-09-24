# ModelForm : un formulaire qui se construit automatiquement à partir d'un modèle.
from django import forms
from .models import Client


class ClientForm(forms.ModelForm):
    # La classe interne "Meta" donne des options au formulaire.
    class Meta:
        # Sur quel modèle ce formulaire est basé.
        model = Client
        # Quels champs du modèle apparaissent dans le formulaire.
        # (On exclut "cree_le" : il se remplit tout seul.)
        fields = ["nom", "telephone", "courriel"]