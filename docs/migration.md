# Migration de la v2 vers la v3

## Ce qui change dans la base
La v3 **ajoute** une table et une colonne, sans rien supprimer. Aucune migration de la v1 ou de la v2 n'est modifiée (`0001` à `0004` sont intactes).

- `0005_v3_succursale` : crée la table `Succursale` et ajoute `Transaction.succursale`, encore **facultative**.
- `0006_donnees_initiales_v3` : crée le premier café (« Café 1 »), lui rattache **toutes** les transactions existantes, et rattache au Café 1 les employés (baristas et gérants) de la v2.
- `0007_succursale_obligatoire` : la colonne devient obligatoire, maintenant que chaque transaction a un café.

Trois migrations séparées : PostgreSQL refuse de modifier une colonne dans la même transaction que la mise à jour de ses données. Rien n'est reconstitué : le journal contenait déjà tout, donc les soldes se calculent comme avant.

Le passage de **SQLite** (v2) à **PostgreSQL** (v3) se fait avec la commande `python manage.py importer_sqlite` (ADR-0015) : elle copie la base (l'original n'est jamais touché), applique les migrations de la v3 sur la copie, exporte, charge dans PostgreSQL, et compare le nombre de lignes de chaque table.

## Procédure pas à pas (Windows, PowerShell)

**A. Créer une base v2 avec les données de démonstration**
1. `git checkout v2.0.0`
2. `py -m venv .venv`, l'activer (`.venv\Scripts\activate`), puis `python -m pip install -r requirements.txt`
3. `cd src`
4. `python manage.py migrate`
5. `python manage.py demo_v2`
6. Noter les soldes : `python manage.py balances > ..\balances-v2.txt`
7. Copier la base : `mkdir ..\v2` puis `copy db.sqlite3 ..\v2\db.sqlite3`
8. Retourner à la racine : `cd ..`

**B. Passer à la v3 (conteneurs)**
9. `git checkout v3.0.0` (le dossier `v2/` et `balances-v2.txt` ne sont pas versionnés : ils restent)
10. `copy .env.example .env`, puis remplir `SECRET_KEY` et `DB_PASSWORD` (voir le README)
11. `docker compose up --build -d` (attendre que tout soit « healthy » : `docker compose ps`)
12. Importer la base v2 :
    ```
    docker compose run --rm -v "${PWD}/v2:/v2:ro" web python manage.py importer_sqlite /v2/db.sqlite3
    ```
    La commande affiche, pour chaque table, le nombre de lignes source et cible : tout doit dire `ok`.
13. Les nouveaux soldes : `docker compose exec web python manage.py balances > balances-v3.txt`
14. Comparer : `fc balances-v2.txt balances-v3.txt` (sous Linux/Mac : `diff`). Aucune différence attendue.
15. Les transactions par café : `docker compose exec web python manage.py balances --succursale "Café 1"` montre toutes les transactions existantes, et `--succursale "Café 2"` n'en montre aucune.

## Notre vérification (données de démonstration de la v2)

Mesurée avec `demo_v2` sur la v2, puis après l'import dans PostgreSQL (version 16) :

| Client | Achats payés | Étampes (cycle) | Gratuits en réserve | Cafés sur carte | Avant (v2, SQLite) | Après (v3, PostgreSQL) |
|---|---|---|---|---|---|---|
| Louise Tremblay (#1) | 6 | 6 | 0 | 0 | 6 / 6 / 0 / 0 | 6 / 6 / 0 / 0 |
| Louise Tremblay (#2) | 7 | 7 | 0 | 0 | 7 / 7 / 0 / 0 | 7 / 7 / 0 / 0 |
| Marc Aleatoire (#3) | 1 | 1 | 0 | 8 | 1 / 1 / 0 / 8 | 1 / 1 / 0 / 8 |
| Jean Gratuit (#4) | 10 | 0 | 1 | 0 | 10 / 0 / 1 / 0 | 10 / 0 / 1 / 0 |
| Sophie Erreur (#5) | 2 | 2 | 0 | 0 | 2 / 2 / 0 / 0 | 2 / 2 / 0 / 0 |

Les quatre nombres sont : achats payés / étampes du cycle / gratuits en réserve / cafés sur carte. Résultat : **tous les soldes sont identiques**, et les 30 transactions de la démonstration appartiennent au Café 1. Les nombres de lignes (5 clients, 1 carte, 30 transactions, 1 règle, 2 utilisateurs, 2 groupes) sont identiques dans la source et la cible.

Les cafés gratuits et les cartes expirent après 30 jours : si la vérification est refaite plus de 30 jours après la création des données, le gratuit de Jean et la carte de Marc seront expirés **avant et après**, et les deux listes restent identiques.

## Ce que nous avons appris en migrant
- **Une migration de données doit écrire dans la base qu'elle migre.** Notre première version de `0006` utilisait la base « par défaut » : en migrant la copie SQLite pendant que PostgreSQL était la base par défaut, elle n'a rien rempli dans la copie et la migration `0007` a échoué (`NOT NULL constraint failed`). Corrigé avec `.using(schema_editor.connection.alias)`. La migration `0004` de la v2, déjà livrée, a le même défaut (`Group.objects.get_or_create` sans `.using`) : elle fonctionne dans notre procédure parce qu'elle est déjà appliquée sur la copie, mais elle n'est pas modifiable (règle du devoir).
- **L'import est refusé sur une base qui contient déjà des clients** (sauf `--ecraser`), pour ne jamais vider de vraies données par accident.
- Aucune donnée de la démonstration n'a été refusée par PostgreSQL. Nos données passent les validations de formulaire, donc elles respectent déjà les tailles de colonnes que SQLite ne vérifie pas.

---

# Migration de la v1 vers la v2 (devoir 2)

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