# ADR-0010 — Rôles barista, gérant et propriétaire, par succursale



## Contexte
La gérante du nouveau café ne doit pas pouvoir annuler les transactions de l'autre café ni voir ses rapports. En v2 (ADR-0007), un gérant était gérant pour tout le système. Cet ADR **complète** l'ADR-0007 sans le remplacer : les rôles barista et gérant gardent leur sens, on ajoute le périmètre.

## Décision
Trois rôles :
- **Barista :** comme en v2, dans les cafés auxquels il est rattaché.
- **Gérant :** comme en v2, **mais seulement dans les cafés auxquels il est rattaché** (annuler, rapports, règle, effacer, fusionner).
- **Propriétaire :** le super-utilisateur Django. Il agit dans tous les cafés, y compris l'administration (ajouter un café, rattacher des employés).
Toutes les vérifications passent par les mêmes fonctions de `services.py` (`succursales_gerees`, `peut_gerer`, `exiger_gestion`, `exiger_gestion_clients`), appelées **à deux endroits** : dans les vues (erreur 403) et dans les services eux-mêmes (`annuler_transaction`, `effacer_client`, `fusionner_clients`). Même si une vue oubliait la vérification, le service refuserait. Les boutons « Annuler » ne sont affichés que pour les cafés gérés, mais ce n'est qu'un confort : la vraie barrière est côté serveur. Le compte administrateur de la v1/v2 devient le propriétaire.

## Options écartées
- **Cacher les boutons seulement :** contournable en tapant l'adresse.
- **Un groupe Django distinct par café :** il faudrait créer des groupes et des droits à chaque nouveau café, alors qu'ajouter une succursale doit se faire sans modifier le code.
- **Un groupe « propriétaire » séparé du super-utilisateur :** le propriétaire a besoin de l'administration pour ajouter un café ; le super-utilisateur Django fait déjà exactement cela.

## Conséquences
- **Facile :** nouveau café = rattacher des personnes, aucun code.
- **Difficile :** le rôle (barista ou gérant) est global, mais le périmètre est par café : on ne peut pas être gérant au Café 1 et simple barista au Café 2.
- Une action refusée renvoie 403. Les tests essaient d'attaquer l'autre café (voir `tests_v3.py`).
