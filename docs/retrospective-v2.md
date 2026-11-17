# Rétrospective de la v2

*Écrite avant de coder la v3.*

## 1. Ce que nous n'avions pas vu venir
Nous n'avions pas vu à quel point l'idée « un seul café » était **implicite** : elle n'était écrite nulle part, donc nous ne pouvions pas la chercher. En relisant le code, elle se cache à cinq endroits :
- **Le modèle :** `Transaction` n'a aucun champ qui dit où elle a eu lieu.
- **Les rapports :** la vue `rapports` compte toutes les transactions de la base, sans filtre.
- **Les permissions :** `est_gerant` répond « oui ou non » pour tout le système ; un gérant est gérant partout.
- **La configuration :** `DEBUG = True`, une `SECRET_KEY` écrite dans `settings.py`, SQLite dans un fichier à côté du code : tout cela suppose notre propre machine.
- **Les commandes :** `balances` et `demo_v2` supposent un seul café.

Nous n'avions pas non plus prévu que la **fiche client** soulèverait une question : effacer ou fusionner un client qui a des transactions dans deux cafés (zone grise de la demande 2.3).

## 2. Pouvait-on ajouter une succursale à un seul endroit ?
Non. Il faudra ajouter la succursale sur les transactions mais aussi corriger les rapports, les permissions, `balances` et les données de démonstration. Le journal des transactions nous aide, par contre : comme toute l'activité y est déjà, il suffit d'ajouter une colonne à cette seule table pour savoir où chaque chose s'est passée. Si nous avions gardé des compteurs, il aurait fallu les découper par café.

## 3. Ce que nous ferions autrement
Nous aurions dû poser la question « dans quel café ? » dès la v1, même avec un seul café. Une colonne de plus coûtait presque rien au début ; l'ajouter maintenant, sur des données réelles, oblige à une migration prudente (ajouter la colonne facultative, remplir, puis la rendre obligatoire).
