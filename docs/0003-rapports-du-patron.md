
## Contexte
Le comptable veut savoir combien de cafés ont été servis un jour donné, et combien de cartes ont été vendues ce mois-ci. Question : une transaction annulée compte-t-elle ? Et si on annule aujourd'hui un achat de mardi passé, le rapport de mardi doit-il changer ?

## Décision
Le gérant choisit une période (un jour, une semaine, un mois…). Le rapport affiche quatre nombres : cafés payés, cafés gratuits, cafés tirés d'une carte, cartes vendues. On compte des cafés et des cartes, jamais des dollars.

Les transactions **annulées ne sont pas comptées**. Donc si on annule un achat de mardi passé, le rapport de mardi change. Le rapport montre aussi combien de transactions ont été annulées sur la période.

## Options écartées
- **Compter les transactions annulées :** le rapport serait faux, puisque ces cafés n'ont pas vraiment été vendus.
- **Garder le rapport de mardi tel qu'il était :** il faudrait sauvegarder une copie de chaque rapport, ce qui est compliqué pour peu d'avantage.

## Conséquences
- **Facile :** le rapport montre toujours la réalité corrigée.
- **Difficile :** un rapport déjà donné au comptable peut changer si on annule après. Le nombre d'annulations affiché permet de comprendre pourquoi.
- Les cafés d'un client effacé restent comptés.