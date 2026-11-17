# Système de fidélité pour un café

Devoirs 1 à 3, 8INF228 : Adaptation et qualité des applications. **Version 3.**

Application web (Python + Django + PostgreSQL) utilisée au comptoir d'un petit réseau de cafés. Elle gère les clients, le programme du café gratuit (étampes), la vente de cartes prépayées, les annulations, les rapports, plusieurs succursales et des rôles (barista, gérant, propriétaire). Elle ne traite **aucun paiement**.

Les choix de conception sont dans [`docs/conception.md`](docs/conception.md) et les décisions dans [`docs/adr/`](docs/adr/).

## Prérequis
- **Docker** avec Docker Compose (Docker Desktop sous Windows). Vérifier : `docker --version` et `docker compose version`.
- Git. (Python n'est nécessaire que pour générer la clé secrète, voir plus bas.)

## Installation neuve de la v3

```
git clone https://github.com/nhdlike-oss/cafe-fidelite-clone.git
cd cafe-fidelite-clone
git checkout v3.0.0
cp .env.example .env
```
Sous Windows (invite de commandes) : `copy .env.example .env`.

Ouvrir `.env` et remplacer les deux valeurs « CHANGEZ » :
- `SECRET_KEY` : générer une valeur avec `python -c "import secrets; print(secrets.token_urlsafe(50))"`.
- `DB_PASSWORD` : n'importe quel mot de passe.

Puis, **une seule commande** :
```
docker compose up --build
```
L'application est sur **http://localhost:8000**. Au premier démarrage, le service `migrate` crée les tables et rassemble les fichiers statiques, puis l'application démarre (comptez une à deux minutes).

Dans un deuxième terminal, charger les données de démonstration :
```
docker compose exec web python manage.py demo_v3
```

Pour arrêter : `Ctrl+C`, ou `docker compose down` (les données sont **conservées** dans le volume `pgdata`). `docker compose down -v` supprime aussi les données.

## Comptes de démonstration (créés par `demo_v3`)

| Compte | Mot de passe | Rôle | Cafés |
|---|---|---|---|
| `barista` | `barista123` | Barista | Café 1 et Café 2 (choisit son café à l'écran) |
| `gerant` | `gerant123` | Gérant | Café 1 seulement |
| `gerant2` | `gerant2123` | Gérant | Café 2 seulement |
| `proprietaire` | `proprietaire123` | Propriétaire (tout, y compris `/admin/`) | Tous |

Les données incluent : deux succursales, **Camille Deux-Cafés** (étampes gagnées au Café 1, café gratuit réclamé au Café 2), **David Café2** (carte prépayée du Café 2), deux fiches « Louise Tremblay » à fusionner, un client à effacer (« Marc Aleatoire »), des achats de « Sophie Erreur » à annuler, et des transactions réparties sur plusieurs jours. Ces mots de passe sont **pour la démonstration seulement**.

## Adresses

| Adresse | Contenu |
|---|---|
| http://localhost:8000/ | Redirige vers la recherche de clients (connexion demandée) |
| http://localhost:8000/cafe/ | Trouver ou créer un client |
| http://localhost:8000/cafe/achat/&lt;id&gt;/ | Enregistrer un achat |
| http://localhost:8000/cafe/rapports/ | Rapports par café ou pour le réseau (gérant, propriétaire) |
| http://localhost:8000/cafe/regle/ | Règle du café gratuit (gérant) |
| http://localhost:8000/admin/ | Administration : ajouter un café, rattacher des employés (propriétaire) |
| http://localhost:8000/sante/ | Contrôle de santé (utilisé par Docker) |

**Ajouter un café sans toucher au code :** `/admin/` → Succursales → Ajouter, puis choisir son personnel.

## Tests (contre PostgreSQL)

```
docker compose run --rm web python manage.py test
```
Lance les tests des trois devoirs (règles de fidélité, annulation, rapports, règle avec date, effacement, fusion, rôles, succursales, permissions par café, migration v2 → v3).

## Soldes : la commande `balances`

```
docker compose exec web python manage.py balances
docker compose exec web python manage.py balances --succursale "Café 2"
```
Sans option : les soldes du **réseau** (étampes, cafés gratuits en réserve, cafés sur carte). Avec `--succursale` : ce qui s'est passé dans ce café (voir ADR-0012).

## Migrer une base de la v2 (SQLite)

Voir [`docs/migration.md`](docs/migration.md), pas à pas, avec nos soldes avant et après.

## Mode développement (pas la production)

```
docker compose -f compose.yaml -f compose.dev.yaml up --build
```
Active `DEBUG=True`, `runserver` et le rechargement automatique (le code de `src/` est monté dans le conteneur). La production, elle, n'utilise ni l'un ni l'autre.

## Configuration

Toute la configuration vient de variables d'environnement, documentées une par une dans [`.env.example`](.env.example) : `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `USE_HTTPS`, `LOG_LEVEL`, `DB_*`. Aucun secret n'est dans le dépôt ni dans l'image. Les journaux vont sur la sortie standard : `docker compose logs`.

## Les conteneurs

| Service | Rôle |
|---|---|
| `db` | PostgreSQL 16, volume `pgdata` |
| `migrate` | Tâche unique : migrations et fichiers statiques |
| `web` | Gunicorn + Django, `DEBUG=False`, non exposé |
| `proxy` | nginx : le seul service exposé (`localhost:8000`) |

## Structure du dépôt

```
cafe-fidelite/
├── README.md
├── AI-USAGE.md            déclaration d'usage de l'IA générative
├── .env.example           chaque variable d'environnement documentée
├── compose.yaml           les conteneurs (compose.dev.yaml : mode développement)
├── Dockerfile
├── requirements.txt
├── docker/nginx.conf
├── docs/
│   ├── conception.md      conception (v1, v2, v3 + diagramme de déploiement)
│   ├── retrospective-v1.md, retrospective-v2.md
│   ├── migration.md       v1 → v2 et v2 → v3
│   └── adr/               décisions (0001 à 0015)
└── src/                   projet Django (manage.py, config/, fidelite/)
```

## Auteurs

Khaled Hamdaoui et Hassy Diallo
