
## Contexte
Le patron veut passer de 10 à 12 étampes à partir du 1er novembre, sans qu'on modifie le code. Question : la nouvelle règle s'applique-t-elle aux étampes déjà accumulées ? Un client à 10 étampes le 31 octobre perd-il son café gratuit le 1er novembre ?

## Décision
Le gérant enregistre une règle : un nombre d'étampes et une date d'entrée en vigueur. La date ne peut pas être dans le passé. Sans règle enregistrée, c'est 10.

Chaque achat est jugé avec la règle **en vigueur à la date de cet achat**. Les étampes déjà accumulées comptent pour la nouvelle règle. Donc :
- Un client qui a 10 étampes le 31 octobre a déjà gagné son café gratuit. Il le garde.
- Un client qui a 8 étampes le 31 octobre doit en avoir 12 au total pour son café gratuit.

## Options écartées
- **Remettre les étampes à zéro au changement :** ce serait injuste pour les clients.
- **Appliquer la nouvelle règle à tout le passé :** des cafés gratuits déjà gagnés disparaîtraient.
- **Garder le chiffre dans le code :** le patron ne peut pas le changer.

## Conséquences
- **Facile :** le gérant change la règle sans programmeur. L'historique reste cohérent.
- **Difficile :** les étampes ne se calculent plus avec un simple « modulo 10 ». Il faut parcourir le journal dans l'ordre.