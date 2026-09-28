from django.shortcuts import render, redirect, get_object_or_404
from .models import Client, CartePrepayee, Transaction
from .forms import ClientForm


def trouver_client(request):
    # request.GET contient ce qui est écrit après un "?" dans l'adresse,
    # par exemple /cafe/?q=tremblay
    # .strip() enlève les espaces au début et à la fin ("  " compte comme vide).
    recherche = request.GET.get("q", "").strip()

    if recherche:
        # icontains = contient, peu importe majuscules/minuscules (le "i").
        # Le | veut dire "OU" : on cherche dans le nom, le telephone, OU le courriel.
        resultats = (
            Client.objects.filter(nom__icontains=recherche)
            | Client.objects.filter(telephone__icontains=recherche)
            | Client.objects.filter(courriel__icontains=recherche)
        )
    else:
        # Sans recherche, on n'affiche AUCUN client.
        resultats = Client.objects.none()

    if request.method == "POST":
        # POST = le barista a rempli le formulaire et cliqué "Enregistrer".
        formulaire = ClientForm(request.POST)

        # is_valid() vérifie nom, téléphone et courriel (voir forms.py).
        if formulaire.is_valid():
            # save() renvoie le client qu'on vient de créer.
            nouveau = formulaire.save()
            # On envoie le barista directement sur la page d'achat du nouveau client.
            return redirect("enregistrer_achat", client_id=nouveau.id)
    else:
        # GET = la page s'affiche normalement, sans envoi de formulaire.
        formulaire = ClientForm()

    context = {
        "resultats": resultats,
        "formulaire": formulaire,
        "recherche": recherche,
    }
    return render(request, "fidelite/trouver_client.html", context)


def enregistrer_achat(request, client_id):
    # On va chercher le client par son id, ou on affiche une 404 s'il n'existe pas.
    client = get_object_or_404(Client, id=client_id)

    # CHANGE : la carte active vient du modele et ignore les cartes expirees.
    # Vaut None si le client n'a aucune carte valide avec des cafes restants.
    carte_active = client.carte_active

    if request.method == "POST":
        # request.POST.get("action") lit quel bouton a ete clique dans le gabarit.
        action = request.POST.get("action")

        # Nombre de cafes demande (1 par defaut si le champ est vide ou invalide).
        try:
            quantite = int(request.POST.get("quantite", 1))
        except ValueError:
            quantite = 1

        # On empeche une quantite absurde (0, negative, ou trop grande).
        quantite = max(1, min(quantite, 20))

        if action == "payer":
            # Une transaction PAR cafe demande : chaque ligne du journal = un cafe.
            for _ in range(quantite):
                Transaction.objects.create(client=client, type=Transaction.Type.ACHAT_PAYE)

        elif action == "gratuit" and client.gratuits_disponibles > 0:
            Transaction.objects.create(client=client, type=Transaction.Type.CAFE_GRATUIT)

        elif action == "carte" and carte_active:
            # CHANGE : on puise dans les cartes valides, la plus ancienne d'abord,
            # jusqu'a ce que la quantite demandee soit servie.
            a_servir = quantite
            for carte in client.cartes_valides():
                if a_servir <= 0:
                    break
                # On ne prend pas plus que ce qui reste sur cette carte.
                a_retirer = min(a_servir, carte.cafes_restants)
                for _ in range(a_retirer):
                    carte.cafes_restants -= 1
                    Transaction.objects.create(
                        client=client,
                        type=Transaction.Type.ACHAT_CARTE,
                        carte=carte,
                    )
                carte.save()
                a_servir -= a_retirer

        elif action == "vendre_carte":
            nouvelle_carte = CartePrepayee.objects.create(client=client)
            Transaction.objects.create(
                client=client,
                type=Transaction.Type.VENTE_CARTE,
                carte=nouvelle_carte,
            )

        # On recharge la meme page pour voir les infos a jour.
        return redirect("enregistrer_achat", client_id=client.id)

    context = {
        "client": client,
        "carte_active": carte_active,
    }
    return render(request, "fidelite/enregistrer_achat.html", context)