# ADR-0002 — Annuler une transaction


## Contexte
Le patron veut annuler une transaction faite par erreur, et savoir après coup qui l'a annulée et quand. Dans notre v1, supprimer une transaction dans l'admin la fait disparaître sans trace, et le compteur de la carte prépayée reste faux (voir la rétrospective). Deux zones grises : que faire si l'achat annulé était la 10e étampe et que le client a déjà bu le café gratuit qu'elle lui avait donné, et jusqu'à quand peut-on annuler.

## Décision
Nous allons annuler **sans jamais supprimer** : la transaction reste dans le journal, avec la date d'annulation (`annulee_le`) et la personne qui l'a annulée (`annulee_par`). Les soldes ignorent les transactions annulées. Seul le gérant peut annuler. Nous refusons l'annulation si elle rendrait le journal incohérent :
- annuler un achat payé est refusé si, en l'enlevant, un café gratuit déjà pris n'aurait plus de récompense derrière lui (le message demande d'annuler d'abord le café gratuit) ;
- annuler la vente d'une carte est refusé si des cafés ont déjà été pris dessus (il faut d'abord annuler ces cafés).
Il n'y a **pas de limite d'âge** : on peut annuler une transaction d'il y a trois mois, tant que le journal reste cohérent. Pour vérifier la cohérence, on rejoue le journal du client sans la transaction.

## Options écartées
- **Supprimer la transaction.** Elle disparaîtrait des rapports sans laisser de trace de qui l'a fait, ce qui est justement le défaut de la v1.
- **Annuler en créant une transaction « inverse ».** C'est une pratique comptable courante, mais elle complique le calcul des étampes et des rapports.
- **Accepter toutes les annulations et corriger le client ensuite.** Un client pourrait se retrouver avec un café gratuit bu sans l'avoir gagné.
- **Limiter l'annulation à 24 heures.** Le patron veut corriger une erreur découverte plus tard (par exemple par le comptable).

## Conséquences
- **Facile :** on sait toujours qui a annulé quoi et quand, et le solde du client est correct après l'annulation.
- **Difficile :** le gérant peut recevoir un refus et doit annuler dans le bon ordre (le café gratuit d'abord, puis l'achat).
- **Coût :** il faut rejouer le journal à chaque annulation. Pour un petit café, c'est négligeable.
- L'annulation d'un café tiré d'une carte recalcule le compteur de la carte à partir du journal.