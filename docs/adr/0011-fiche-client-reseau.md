# ADR-0011 — La fiche client appartient au réseau


## Contexte
Un client peut avoir des transactions dans les deux cafés. Le gérant du Café 1 peut-il effacer ou fusionner une fiche qui a aussi des transactions au Café 2 ? À qui appartient la fiche ?

## Décision
La fiche appartient au **réseau**, pas à un café : c'est ce qui permet d'accumuler des étampes d'un café à l'autre (ADR-0009). Règle : le propriétaire peut toujours effacer ou fusionner ; un gérant le peut **seulement si toutes les transactions du ou des clients sont dans les cafés qu'il gère**. Un client sans transaction peut être effacé par n'importe quel gérant. Pour une fusion, la règle s'applique aux deux fiches. Cela complète les ADR-0005 et ADR-0006 sans les modifier.

## Options écartées
- **Une fiche par café :** casse « une étampe, c'est une étampe ».
- **Laisser le gérant agir quand même, en prévenant l'autre café :** effacer une identité est définitif ; le gérant du Café 1 modifierait les statistiques et la fidélité du Café 2.

## Conséquences
- **Facile :** la vérification est une seule comparaison d'ensembles de cafés.
- **Difficile :** un client fidèle aux deux cafés ne peut être effacé que par le propriétaire, ce qui l'oblige à demander au propriétaire.
- La recherche de clients reste celle du réseau : un gérant retrouve un client même s'il n'a jamais acheté dans son café.
