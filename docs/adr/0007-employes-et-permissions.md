
## Contexte
Le patron a engagé deux étudiants. Il ne veut pas que n'importe qui annule des transactions ou efface des clients. Question : un barista qui vient de se tromper peut-il annuler sa propre erreur ?

## Décision
Il y a deux rôles :
- **Barista :** chercher et créer des clients, enregistrer des achats, donner un café gratuit, vendre une carte.
- **Gérant :** tout ce que fait un barista, plus annuler, les rapports, changer la règle, effacer et fusionner.

Chaque personne a son propre compte. Toutes les pages du comptoir demandent une connexion. Chaque transaction garde la personne qui l'a faite. Le compte administrateur Django de la v1 compte comme gérant.

Un barista **ne peut pas** annuler, même sa propre dernière erreur : il va chercher le gérant.

## Options écartées
- **Laisser le barista annuler sa dernière entrée :** c'est pratique, mais il faut gérer un délai, et un barista pourrait cacher une erreur ou une fraude.
- **Un seul compte partagé :** impossible de savoir qui a fait quoi.

## Conséquences
- **Facile :** la règle est simple à expliquer et à vérifier.
- **Difficile :** le gérant doit être présent pour corriger une erreur.
- Les transactions de la v1 n'ont pas d'auteur (elles ont été faites avant les comptes).