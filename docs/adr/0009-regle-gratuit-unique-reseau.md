# ADR-0009 — Une seule règle du café gratuit pour tout le réseau


## Contexte
Les étampes valent dans tous les cafés. Question : chaque café peut-il avoir sa propre règle (10 étampes ici, 12 là), ou une promotion d'ouverture (deux étampes pour un achat le premier jour) ?

## Décision
Il y a **une seule règle pour tout le réseau**, celle de l'ADR-0004 (nombre d'étampes et date d'entrée en vigueur). La table `RegleFidelite` n'a pas de succursale. Il n'y a **pas de promotion par café** pour l'instant.

## Options écartées
- **Une règle par café :** un client pourrait gagner son café gratuit à 10 étampes au Café 1 et à 12 au Café 2 ; ses étampes ne voudraient plus rien dire, puisqu'elles se cumulent d'un café à l'autre.
- **Étampes doubles un jour donné :** le rejeu du journal compterait une étampe par achat. Il faudrait ajouter un poids à chaque achat, et décider quoi faire si on l'annule. Trop gros pour ce devoir.

## Conséquences
- **Facile :** les soldes restent calculés d'un seul bloc, comme en v2. Le comportement est le même partout.
- **Difficile :** le nouveau café ne peut pas faire de promotion d'ouverture. Si le patron la veut, un nouvel ADR devra remplacer celui-ci.
