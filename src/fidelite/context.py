from .services import est_gerant, est_proprietaire, succursale_courante, succursales_permises


def roles(request):
    contexte = {"est_gerant": est_gerant(request.user),
                "est_proprietaire": est_proprietaire(request.user)}
    if request.user.is_authenticated:
        contexte["succursale_courante"] = succursale_courante(request)
        contexte["plusieurs_succursales"] = succursales_permises(request.user).count() > 1
    return contexte
