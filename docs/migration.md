# Migration de la v1 vers la v2

## Ce qui change dans la base
La v2 **ajoute** des colonnes et des tables. Elle ne supprime rien et ne modifie aucune migration de la v1 (`0001` et `0002` sont intactes).

- `0003_v2_annulation_regle_audit` : ajoute l'annulation et l'auteur des transactions, l'état « annulée » d'une carte, l'état « effacé » d'un client, et deux nouvelles tables (règles du café gratuit, journal d'audit). Toutes les nouvelles colonnes ont une valeur par défaut : les données existantes restent valides.
- `0004_donnees_initiales_v2` : crée la règle initiale (10 étampes, depuis toujours) et les rôles barista et gérant.

**Rien n'est reconstitué** : la v1 gardait déjà un journal complet des transactions, donc tous les soldes se calculent comme avant. La règle initiale de 10 étampes reproduit exactement le calcul de la v1.

## Procédure pas à pas

**A. Partir de la v1**
1. `git checkout v1.0.0`
2. Créer l'environnement : `py -m venv .venv`, l'activer, puis `python -m pip install -r requirements.txt`
3. `cd src`, puis `python manage.py migrate`
4. Charger les données de démonstration v1 : `python manage.py loaddata ../docs/donnees-demo-v1.json` (ce fichier se trouve dans le dépôt de la v2 ; le copier dans `docs/` au besoin)
5. Noter les soldes de la v1 :
   `python manage.py shell -c "from fidelite.models import Client; [print(c.nom, c.achats_payes, c.gratuits_disponibles, c.cafes_prepayes_restants) for c in Client.objects.all()]"`

**B. Passer à la v2 sur la même base**
6. `git checkout v2.0.0` (ne pas supprimer `db.sqlite3`)
7. `python -m pip install -r requirements.txt`
8. `python manage.py migrate` (applique `0003` et `0004` par-dessus la base existante)
9. `python manage.py balances`
10. Comparer avec l'étape 5.

## Notre vérification (données de démonstration de la v1)

| Client | Achats payés | Gratuits en réserve | Cafés sur carte | Avant (v1) | Après (v2) |
|---|---|---|---|---|---|
| hassy | 5 | 0 | 0 | 5 / 0 / 0 | 5 / 0 / 0 |
| Alice | 10 | 1 | 0 | 10 / 1 / 0 | 10 / 1 / 0 |
| Bruce | 14 | 0 | 0 | 14 / 0 / 0 | 14 / 0 / 0 |
| Neene | 0 | 0 | 7 | 0 / 0 / 7 | 0 / 0 / 7 |
| Diop | 6 | 0 | 0 | 6 / 0 / 0 | 6 / 0 / 0 |
| Fifi | 7 | 0 | 0 | 7 / 0 / 0 | 7 / 0 / 0 |

Les trois nombres sont : achats payés / cafés gratuits en réserve / cafés sur carte. Résultat : **tous les soldes sont identiques**. Les cafés gratuits expirent 30 jours après leur obtention : si la vérification est refaite plus de 30 jours après la création des données, le gratuit d'Alice et la carte de Neene seront expirés à la fois avant et après la migration, et les deux listes restent identiques.

## Point d'attention
La commande `balances` n'existe qu'en v2. À l'étape 5, on utilise donc la commande `shell` de Django, qui calcule les mêmes nombres.