from django.shortcuts import render, redirect
from .models import Client
from .forms import ClientForm


def trouver_client(request):
    # request.GET contient ce qui est écrit après un "?" dans l'adresse,
    # par exemple /cafe/?q=tremblay
    # .get("q", "") veut dire : prends la valeur de "q", ou "" si elle n'existe pas.
    recherche = request.GET.get("q", "")

    if recherche:
        # Client.objects.filter(...) cherche PLUSIEURS clients qui correspondent.
        # nom__icontains="tremblay" veut dire :
        #   "nom" CONTIENT "tremblay", peu importe les majuscules (le "i").
        # Le | veut dire "OU" : on cherche dans le nom OU dans le téléphone.
        resultats = Client.objects.filter(
            nom__icontains=recherche
        ) | Client.objects.filter(
            telephone__icontains=recherche
        )
    else:
        # Si la barre de recherche est vide, on affiche tous les clients.
        resultats = Client.objects.all()

    if request.method == "POST":
        # POST = le barista a rempli le formulaire et cliqué "Enregistrer".
        # On construit le formulaire à partir des données envoyées.
        formulaire = ClientForm(request.POST)

        # is_valid() vérifie que les données respectent les règles du modèle
        # (par exemple : le téléphone n'est pas déjà pris par un autre client).
        if formulaire.is_valid():
            # save() enregistre le nouveau client dans la base de données.
            formulaire.save()
            # redirect() renvoie le navigateur vers cette même page,
            # ce qui vide le formulaire et évite un double-envoi si on
            # rafraîchit la page par erreur.
            return redirect("trouver_client")
    else:
        # GET = la page s'affiche normalement, sans envoi de formulaire.
        # On prépare un formulaire vide.
        formulaire = ClientForm()

    # "context" est un dictionnaire : il rassemble tout ce que le gabarit
    # HTML pourra afficher.
    context = {
        "resultats": resultats,
        "formulaire": formulaire,
        "recherche": recherche,
    }
    return render(request, "fidelite/trouver_client.html", context)