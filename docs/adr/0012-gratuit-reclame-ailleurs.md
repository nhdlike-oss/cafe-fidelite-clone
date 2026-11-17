# ADR-0012 — Où apparaît un café gratuit réclamé dans un autre café



## Contexte
Un client gagne ses étampes au Café 1 et réclame son café gratuit au Café 2. Dans le rapport de quel café apparaît-il ? La même question se pose pour la commande `balances` par succursale.

## Décision
Chaque transaction compte dans **le café où elle a lieu**. Un café gratuit apparaît donc dans le rapport du café où il est **réclamé** (c'est là que le café est servi et que le coût est payé). Les achats comptent dans le café où ils sont faits. Les rapports par café s'additionnent exactement au rapport du réseau.
Pour `balances` : sans option, la commande affiche les soldes du **réseau** (étampes, gratuits en réserve, cafés sur carte : ils valent partout, donc identiques à la v2) ; avec `--succursale`, elle affiche pour chaque client ce qui s'est passé dans ce café (achats payés, gratuits pris, cafés sur carte, cartes vendues), en excluant les transactions annulées.

## Options écartées
- **Rattacher le gratuit au café où les étampes ont été gagnées :** les étampes d'un gratuit viennent de plusieurs cafés ; on ne saurait pas lequel choisir.
- **Partager le coût entre les cafés :** demande un calcul de répartition que le patron n'a pas demandé.

## Conséquences
- **Facile :** un rapport = un filtre sur `succursale`, les totaux s'additionnent.
- **Difficile :** le café qui vend le plus d'étampes ne voit pas les gratuits qu'il a « financés » ; seul le rapport du réseau montre l'ensemble.
- La rétroactivité de l'ADR-0003 continue de s'appliquer : annuler une transaction change le rapport de sa période et de son café.
