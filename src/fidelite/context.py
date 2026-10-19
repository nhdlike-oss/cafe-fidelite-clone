from .services import est_gerant


def roles(request):
    return {"est_gerant": est_gerant(request.user)}
