# ADR-0008 — Comment on connaît le café d'une transaction



## Contexte
Les deux cafés se connectent au même serveur. Chaque transaction doit appartenir à une succursale, et une barista peut faire des quarts dans les deux cafés. L'application ne peut pas deviner où elle se trouve : elle ne tourne plus sur la machine du comptoir.

## Décision
Chaque employé est **rattaché** à une ou plusieurs succursales (`Succursale.personnel`). Au moment d'enregistrer, la succursale est :
- son seul café, s'il n'en a qu'un (aucun choix à faire) ;
- sinon celle qu'il **choisit à l'écran** (« Dans quel café êtes-vous ? »), mémorisée dans sa session, et modifiable avec le lien « changer » en haut de page.
Le serveur vérifie que le café choisi fait partie de ceux de l'utilisateur (sinon erreur). Le propriétaire (super-utilisateur) a accès à tous les cafés. Une personne rattachée à aucun café ne peut rien enregistrer. Le nom du premier café (« Café 1 ») est provisoire : on peut le renommer dans l'administration, sans toucher au code.

## Options écartées
- **Déduire le café de l'adresse du poste ou du réseau :** fragile, et ne marche plus quand le serveur est sur le Web.
- **Un seul café par employé, sans choix :** empêche la barista qui travaille dans les deux cafés.
- **Choisir le café à chaque transaction :** trop lent au comptoir, et facile à oublier.

## Conséquences
- **Facile :** ajouter un café = une ligne dans l'administration, puis rattacher des employés.
- **Difficile :** une barista qui change de café doit penser à cliquer « changer » ; sinon ses transactions vont au mauvais café. La succursale est donc affichée en haut de chaque page.
- Chaque transaction stocke sa succursale (clé étrangère protégée : on ne peut pas supprimer un café qui a des transactions).
