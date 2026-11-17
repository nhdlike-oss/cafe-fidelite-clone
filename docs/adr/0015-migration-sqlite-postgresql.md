# ADR-0015 — Passer de SQLite à PostgreSQL par une commande d'import



## Contexte
La v2 tourne sur SQLite ; la v3 sur PostgreSQL. Il faut transférer les données sans perdre un seul solde, et la procédure doit être scriptée ou documentée pas à pas.

## Décision
Une commande Django, `python manage.py importer_sqlite <fichier>`, fait tout : elle **copie** la base SQLite (l'original n'est jamais modifié), applique dessus les migrations de la v3 (0005 à 0007), exporte les données avec `dumpdata` (clés naturelles, sans les types de contenu ni les permissions que Django recrée), vide les données de départ de PostgreSQL, charge le tout avec `loaddata`, puis compare le nombre de lignes de chaque table. Elle refuse de s'exécuter si PostgreSQL contient déjà des clients, sauf avec `--ecraser`. La vérification des soldes se fait avec `balances` avant et après (voir `docs/migration.md`).

## Options écartées
- **pgloader ou un outil externe :** une installation de plus, et il ne connaît pas nos migrations ni nos règles.
- **Un script SQL à la main :** les clés étrangères et les séquences de PostgreSQL se règlent facilement mal.
- **Migrer d'abord dans PostgreSQL puis copier les tables :** il faudrait recopier les clés une à une ; `dumpdata` et `loaddata` les conservent telles quelles.

## Conséquences
- **Facile :** une seule commande, répétable, avec un contrôle intégré.
- **Difficile :** `loaddata` charge tout en mémoire, ce qui convient à un café mais pas à des millions de lignes.
- La commande est utile **une seule fois** par café ; elle pourra être retirée après la migration réelle.
