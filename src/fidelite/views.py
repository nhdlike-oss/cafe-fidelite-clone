import re
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction as db
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import ClientForm, RegleForm
from .models import (ACHATS_POUR_GRATUIT, Audit, CartePrepayee, Client, RegleFidelite,
                     Succursale, Transaction)
from .services import (SESSION_SUCCURSALE, ErreurMetier, annuler_transaction, effacer_client,
                       est_gerant, exiger_gestion_clients, fusionner_clients,
                       succursale_courante, succursales_gerees, succursales_permises)


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
def choisir_succursale(request):
    # v3 (ADR-0008) : la personne choisit dans quel cafe elle se trouve.
    permises = succursales_permises(request.user)
    suivant = request.GET.get("next") or request.POST.get("next") or ""
    if not suivant.startswith("/") or suivant.startswith("//"):
        suivant = "/cafe/"
    if request.method == "POST":
        # On verifie cote serveur que ce cafe fait partie de ceux de l'utilisateur.
        cafe = get_object_or_404(permises, pk=request.POST.get("succursale"))
        request.session[SESSION_SUCCURSALE] = cafe.pk
        return redirect(suivant)
    return render(request, "fidelite/choisir_succursale.html", {
        "succursales": permises, "suivant": suivant})


@login_required
def enregistrer_achat(request, client_id):
    client = get_object_or_404(Client, id=client_id, efface=False)
    carte_active = client.carte_active

    succursale = succursale_courante(request)
    if succursale is None:
        if succursales_permises(request.user).exists():
            return redirect(f"{reverse('choisir_succursale')}?next={request.path}")
        messages.error(request, "Votre compte n'est rattaché à aucune succursale : "
                                "demandez au propriétaire de vous en attribuer une.")
        return redirect("trouver_client")

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
                        client=client, type=Transaction.Type.ACHAT_PAYE, cree_par=par,
                        succursale=succursale)

            elif action == "gratuit" and client.gratuits_disponibles > 0:
                Transaction.objects.create(
                    client=client, type=Transaction.Type.CAFE_GRATUIT, cree_par=par,
                    succursale=succursale)
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
                            carte=carte, cree_par=par, succursale=succursale)
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
                    carte=nouvelle, cree_par=par, succursale=succursale)

        return redirect("enregistrer_achat", client_id=client.id)

    historique = (client.transactions.select_related("cree_par", "annulee_par", "succursale")
                  .order_by("-cree_le", "-id")[:30])
    try:
        exiger_gestion_clients(request.user, client)
        peut_gerer_fiche = True
    except PermissionDenied:
        peut_gerer_fiche = False
    return render(request, "fidelite/enregistrer_achat.html", {
        "client": client, "carte_active": carte_active, "historique": historique,
        "cafes_geres": set(succursales_gerees(request.user).values_list("pk", flat=True)),
        "peut_gerer_fiche": peut_gerer_fiche})


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

    # v3 (ADR-0003, ADR-0010, ADR-0012) : le rapport vaut pour UNE succursale ou pour
    # l'ensemble de celles que l'utilisateur gere (tout le reseau pour le proprietaire).
    gerees = succursales_gerees(request.user)
    choix = request.GET.get("succursale", "")
    if choix:
        cafe = get_object_or_404(Succursale, pk=choix) if choix.isdigit() else None
        if cafe is None:
            raise PermissionDenied
        if not gerees.filter(pk=cafe.pk).exists():
            raise PermissionDenied   # un gerant ne voit pas l'autre cafe
        portee = Transaction.objects.filter(succursale=cafe)
        titre_portee = cafe.nom
    else:
        portee = Transaction.objects.filter(succursale__in=gerees)
        titre_portee = "Tout le réseau" if request.user.is_superuser else "Mes succursales"

    # Les transactions annulees sont exclues. Un cafe gratuit compte dans le cafe
    # ou il est RECLAME (ADR-0012).
    periode = portee.filter(cree_le__date__gte=debut, cree_le__date__lte=fin)
    comptes = {r["type"]: r["n"] for r in
               periode.filter(annulee_le__isnull=True).values("type").annotate(n=Count("id"))}
    T = Transaction.Type
    contexte = {
        "debut": debut, "fin": fin,
        "succursales": gerees, "choix": choix, "titre_portee": titre_portee,
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
    exiger_gestion_clients(request.user, client)
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
    exiger_gestion_clients(request.user, client, *([autre] if autre else []))

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
