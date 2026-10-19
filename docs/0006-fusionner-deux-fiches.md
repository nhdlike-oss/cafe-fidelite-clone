
## Contexte
Une cliente a deux fiches (deux numéros de téléphone). Le patron veut en faire une seule, sans rien perdre. Questions : quelle fiche survit ? 6 étampes plus 7 étampes font 13, le client gagne-t-il un café tout de suite ? Peut-on revenir en arrière ?

## Décision
La fiche **la plus ancienne** survit, avec son nom et son téléphone. Les transactions et les cartes de l'autre fiche sont déplacées vers elle, puis l'autre fiche disparaît.

Les étampes se calculent dans l'ordre des dates sur le journal combiné. Donc 6 + 7 = 13 étampes : le client gagne un café gratuit tout de suite (au moment de sa 10e étampe).

On refuse la fusion si l'historique combiné devenait incohérent. Le gérant doit confirmer, et on garde une trace de la fusion (numéros de fiches seulement).

## Options écartées
- **Garder la fiche la plus récente :** on perdrait l'historique le plus long comme identité.
- **Laisser le gérant choisir la fiche :** plus de risque d'erreur pour peu d'avantage.
- **Permettre de défaire la fusion :** il faudrait se souvenir de quelle transaction venait de quelle fiche.

## Conséquences
- **Facile :** le client garde tout (étampes, récompenses, cartes, historique).
- **Difficile :** une fusion par erreur **ne peut pas être défaite**. L'écran avertit le gérant avant de confirmer.
- Le téléphone de l'autre fiche est perdu.