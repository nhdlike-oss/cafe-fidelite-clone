# Système de fidélité pour un café

Devoir 1, INF228 : Adaptation et qualité des applications.

Application web locale (Python + Django) utilisée au comptoir d'un petit café indépendant pour remplacer les cartes de fidélité en carton. Elle gère les clients, le programme du « 11e café gratuit » et la vente de cartes prépayées (11 cafés pour le prix de 10). Elle ne traite **aucun paiement** : l'argent change de mains à la caisse, hors du système.

## Fonctionnalités

- **Trouver ou créer un client** : recherche par nom, téléphone ou courriel (sans tenir compte des majuscules), création avec validation du nom, du téléphone et du courriel.
- **Enregistrer un achat** : un ou plusieurs cafés payés, café gratuit, café sur carte prépayée, vente d'une nouvelle carte.
- **Administration Django** : liste et création des clients, cartes prépayées et transactions.

Les choix de conception (zones grises de l'énoncé) sont expliqués dans [`docs/conception.md`](docs/conception.md).

## Prérequis

- Python 3.12 ou plus récent (développé avec Python 3.13)
- Git

## Installation et lancement

Sous **Windows** (invite de commandes) :

```
git clone https://github.com/Khaled-hamdaoui/cafe-fidelite.git
cd cafe-fidelite
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sous **Mac / Linux**, remplacer `py -m venv .venv` par `python3 -m venv .venv` et l'activation par `source .venv/bin/activate`.

Le dépôt privé demande d'être connecté à GitHub pour le `git clone`. La base de données (`db.sqlite3`) n'est pas versionnée : c'est la commande `migrate` qui la crée. `createsuperuser` crée le compte pour l'administration.

## Utilisation

| Adresse | Contenu |
|---|---|
| http://127.0.0.1:8000/ | Redirige vers la recherche de clients |
| http://127.0.0.1:8000/cafe/ | Écran 1 : trouver ou créer un client |
| http://127.0.0.1:8000/cafe/achat/&lt;id&gt;/ | Écran 2 : enregistrer un achat pour un client |
| http://127.0.0.1:8000/admin/ | Administration (compte créé avec `createsuperuser`) |

Pour arrêter le serveur : `Ctrl+C` dans la fenêtre du terminal.

## Règles de fidélité (résumé)

- Tous les 10 cafés **payés**, le client gagne un café gratuit, qu'il garde en réserve.
- Un café gratuit **expire 30 jours** après avoir été gagné.
- Une carte prépayée contient **11 cafés** et **expire 30 jours** après sa vente.
- Un café pris sur une carte prépayée **ne compte pas** pour les 10 achats payés.
- Un client est identifié par son **téléphone** (unique).

## Structure du dépôt

```
cafe-fidelite/
├── README.md
├── AI-USAGE.md            déclaration d'usage de l'IA générative
├── requirements.txt       dépendances Python
├── docs/
│   └── conception.md      document de conception
└── src/                   projet Django
    ├── manage.py
    ├── config/            réglages et adresses du projet
    └── fidelite/          l'application (modèles, vues, formulaires, gabarits)
```

## Auteurs

Khaled Hamdaoui et 
