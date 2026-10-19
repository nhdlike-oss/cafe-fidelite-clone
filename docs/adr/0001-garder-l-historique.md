# ADR-0001 — Garder l'historique (le journal fait foi)
## Contexte
Notre v1 calcule presque tout à partir du journal des transactions : les achats payés, les cafés gratuits et leur expiration. Une seule exception : la carte prépayée a un compteur `cafes_restants`, stocké à côté du journal. Nos tests sur la v1 ont montré le problème : si on supprime une transaction, le journal change mais pas le compteur, et les deux se contredisent. Les demandes du patron mettent ce choix à l'épreuve : annuler, faire des rapports par date, changer la règle et fusionner des fiches demandent l'historique, alors qu'effacer un client demande de le protéger.

## Décision
Nous allons **confirmer** le choix de l'historique : le journal fait foi. Chaque événement est une transaction, et on ne supprime jamais une transaction : on l'annule (qui et quand sont gardés). Les soldes se calculent en rejouant le journal. Le compteur de la carte reste dans la base pour ne pas modifier la structure d'une base déjà en production, mais ce n'est qu'un **cache** : on le recalcule à partir du journal à chaque annulation, et si les deux se contredisent, le journal a raison.

## Options écartées
- **Garder seulement l'état actuel (des compteurs).** Annuler une transaction d'hier serait impossible sans journal, et « combien de cafés mardi passé » aussi.
- **Garder les deux, sans règle sur lequel a raison.** C'est exactement le défaut de notre v1.
- **Supprimer complètement le compteur de la carte.** C'est plus propre, mais cela change la structure d'une base en production. Le risque de modifier les soldes pendant la migration nous a semblé trop grand pour le gain.

## Conséquences
- **Facile :** annuler, faire des rapports par période, changer la règle selon la date et fusionner des fiches se font en travaillant sur le journal. Les soldes ne peuvent pas « dériver ».
- **Difficile :** l'effacement d'un client est plus délicat, parce que son historique doit rester pour les statistiques. On anonymise le client au lieu de le supprimer (voir ADR-0005).
- **Coût :** le solde d'un client se calcule en parcourant toutes ses transactions. Pour un client qui vient tous les jours depuis trois ans (environ mille transactions), c'est encore très rapide pour un petit café. Si cela devenait lent, on pourrait ajouter un cache, toujours recalculable à partir du journal.
- Les migrations de la v2 ne touchent à aucune donnée existante, donc tous les soldes de la v1 restent identiques.