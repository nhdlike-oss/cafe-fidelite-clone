import re
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction as db
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ClientForm, RegleForm
from .models import (ACHATS_POUR_GRATUIT, Audit, CartePrepayee, Client, RegleFidelite,
                     Transaction)
from .services import (ErreurMetier, annuler_transaction, effacer_client, est_gerant,
                       fusionner_clients)


def gerant_requis(vue):
    # Connexion obligatoire, puis role gerant (sinon erreur 403).
    @wraps(vue)
    @login_required
    def enveloppe(request, *args, **kwargs):
        if not est_gerant(request.user):
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return enveloppe


@login_required
def trouver_client(request):
    recherche = request.GET.get("q", "").strip()

    if recherche:
        # Nom OU courriel OU telephone. Les numeros sont stockes en chiffres seulement :
        # on cherche donc sur les chiffres tapes ("418-555" trouve "418555...").
        condition = Q(nom__icontains=recherche) | Q(courriel__icontains=recherche)
        chiffres = re.sub(r"\D", "", recherche)
        if chiffres:
            condition |= Q(telephone__icontains=chiffres)
        resultats = Client.objects.filter(efface=False).filter(condition)
    else:
        resultats = Client.objects.none()

    if request.method == "POST":
        formulaire = ClientForm(request.POST)
        if formulaire.is_valid():
            nouveau = formulaire.save()
            return redirect("enregistrer_achat", client_id=nouveau.id)
    else:
        formulaire = ClientForm()

    return render(request, "fidelite/trouver_client.html", {
        "resultats": resultats, "formulaire": formulaire, "recherche": recherche})


@login_required
def enregistrer_achat(request, client_id):
    client = get_object_or_404(Client, id=client_id, efface=False)
    carte_active = client.carte_active

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            quantite = int(request.POST.get("quantite", 1))
        except ValueError:
            quantite = 1
        quantite = max(1, min(quantite, 20))
        par = request.user

        with db.atomic():
            if action == "payer":
                for _ in range(quantite):
                    Transaction.objects.create(
                        client=client, type=Transaction.Type.ACHAT_PAYE, cree_par=par)

            elif action == "gratuit" and client.gratuits_disponibles > 0:
                Transaction.objects.create(
                    client=client, type=Transaction.Type.CAFE_GRATUIT, cree_par=par)
                if quantite > 1:
                    messages.warning(request, "Un seul café gratuit est enregistré à la fois.")

            elif action == "carte" and carte_active:
                a_servir = quantite
                for carte in client.cartes_valides():
                    if a_servir <= 0:
                        break
                    a_retirer = min(a_servir, carte.cafes_restants)
                    for _ in range(a_retirer):
                        carte.cafes_restants -= 1
                        Transaction.objects.create(
                            client=client, type=Transaction.Type.ACHAT_CARTE,
                            carte=carte, cree_par=par)
                    carte.save()
                    a_servir -= a_retirer
                if a_servir > 0:
                    messages.warning(
                        request, f"Il ne restait pas assez de cafés sur la carte : "
                                 f"{a_servir} café(s) non enregistré(s).")

            elif action == "vendre_carte":
                nouvelle = CartePrepayee.objects.create(client=client)
                Transaction.objects.create(
                    client=client, type=Transaction.Type.VENTE_CARTE,
                    carte=nouvelle, cree_par=par)

        return redirect("enregistrer_achat", client_id=client.id)

    historique = (client.transactions.select_related("cree_par", "annulee_par")
                  .order_by("-cree_le", "-id")[:30])
    return render(request, "fidelite/enregistrer_achat.html", {
        "client": client, "carte_active": carte_active, "historique": historique})


@gerant_requis
def annuler(request, transaction_id):
    tx = get_object_or_404(Transaction, id=transaction_id)
    if request.method == "POST":
        try:
            annuler_transaction(tx, request.user)
            messages.success(request, "Transaction annulée.")
        except ErreurMetier as e:
            messages.error(request, str(e))
    if tx.client.efface:
        return redirect("trouver_client")
    return redirect("enregistrer_achat", client_id=tx.client_id)


@gerant_requis
def rapports(request):
    def lire(nom, defaut):
        try:
            return date.fromisoformat(request.GET.get(nom, ""))
        except ValueError:
            return defaut

    aujourdhui = timezone.localdate()
    debut = lire("debut", aujourdhui)
    fin = lire("fin", debut)
    if fin < debut:
        debut, fin = fin, debut

    # Les transactions annulees sont exclues (ADR-0003).
    periode = Transaction.objects.filter(cree_le__date__gte=debut, cree_le__date__lte=fin)
    comptes = {r["type"]: r["n"] for r in
               periode.filter(annulee_le__isnull=True).values("type").annotate(n=Count("id"))}
    T = Transaction.Type
    contexte = {
        "debut": debut, "fin": fin,
        "payes": comptes.get(T.ACHAT_PAYE, 0),
        "gratuits": comptes.get(T.CAFE_GRATUIT, 0),
        "sur_carte": comptes.get(T.ACHAT_CARTE, 0),
        "cartes": comptes.get(T.VENTE_CARTE, 0),
        "annulees": periode.filter(annulee_le__isnull=False).count(),
        "raccourcis": [
            ("Aujourd'hui", aujourdhui, aujourdhui),
            ("7 derniers jours", aujourdhui - timedelta(days=6), aujourdhui),
            ("Ce mois-ci", aujourdhui.replace(day=1), aujourdhui),
        ],
    }
    return render(request, "fidelite/rapports.html", contexte)


@gerant_requis
def regle(request):
    if request.method == "POST":
        formulaire = RegleForm(request.POST)
        if formulaire.is_valid():
            nouvelle = formulaire.save(commit=False)
            nouvelle.cree_par = request.user
            nouvelle.save()
            Audit.objects.create(action=Audit.Action.REGLE, par=request.user,
                                 details=str(nouvelle))
            messages.success(request, "Nouvelle règle enregistrée.")
            return redirect("regle")
    else:
        formulaire = RegleForm()
    return render(request, "fidelite/regle.html", {
        "formulaire": formulaire, "regles": RegleFidelite.objects.all(),
        "defaut": ACHATS_POUR_GRATUIT})


@gerant_requis
def effacer(request, client_id):
    client = get_object_or_404(Client, id=client_id, efface=False)
    if request.method == "POST":
        try:
            effacer_client(client, request.user)
            messages.success(request, "Client effacé : ses renseignements personnels ont disparu.")
            return redirect("trouver_client")
        except ErreurMetier as e:
            messages.error(request, str(e))
    return render(request, "fidelite/effacer.html", {"client": client})


@gerant_requis
def fusionner(request, client_id, autre_id=None):
    client = get_object_or_404(Client, id=client_id, efface=False)
    autre = get_object_or_404(Client, id=autre_id, efface=False) if autre_id else None

    if autre and request.method == "POST":
        try:
            garde = fusionner_clients(client, autre, request.user)
            messages.success(request, "Fiches fusionnées.")
            return redirect("enregistrer_achat", client_id=garde.id)
        except ErreurMetier as e:
            messages.error(request, str(e))

    recherche = request.GET.get("q", "").strip()
    candidats = Client.objects.none()
    if recherche and not autre:
        condition = Q(nom__icontains=recherche) | Q(courriel__icontains=recherche)
        chiffres = re.sub(r"\D", "", recherche)
        if chiffres:
            condition |= Q(telephone__icontains=chiffres)
        candidats = Client.objects.filter(efface=False).exclude(pk=client.pk).filter(condition)
    return render(request, "fidelite/fusionner.html", {
        "client": client, "autre": autre, "recherche": recherche, "candidats": candidats})
