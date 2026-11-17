# ADR-0013 — Les migrations s'appliquent par un service qui se termine, avant l'application


## Contexte
Il faut que les migrations s'appliquent de façon fiable, et que l'application ne démarre pas sur une base pas prête ou pas à jour. Question : automatiquement au démarrage, ou par une commande explicite ?

## Décision
Un service `migrate` de `compose.yaml` s'exécute **une seule fois**, après que la base est saine (healthcheck), puis se termine : il lance `python manage.py migrate --noinput` puis `collectstatic` (ADR-0014). Le service `web` ne démarre que lorsque `migrate` s'est terminé avec succès (`service_completed_successfully`). La commande peut aussi être lancée à la main : `docker compose run --rm migrate`.

## Options écartées
- **Migrer dans le conteneur de l'application, à chaque démarrage :** quand il y aura plusieurs instances (ce qui est prévu plus tard), elles migreraient en même temps.
- **Migrer à la main seulement :** facile à oublier après une mise à jour ; l'application démarrerait sur un ancien schéma.

## Conséquences
- **Facile :** un `docker compose up --build` suffit ; si une migration échoue, l'application ne démarre pas et l'erreur est visible dans `docker compose logs migrate`.
- **Difficile :** un service de plus dans `compose.yaml`.
