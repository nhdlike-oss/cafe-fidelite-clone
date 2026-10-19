# Rétrospective de la v1

## 1. Est-ce que notre v1 pouvait faire les six demandes du patron ?

| Demande | Possible en v1 ? | Pourquoi |

| 3.1 Annuler une transaction | À moitié | Dans l'admin, on pouvait supprimer une transaction. Pour un achat payé le solde se corrigeait seul. Mais pour un café pris sur une carte, le nombre de cafés restants ne changeait pas. De plus, la suppression ne gardait aucune trace de qui avait annulé ni quand. |
| 3.2 Rapports | À moitié | On pouvait compter par type de transaction dans l'admin, mais il n'y avait aucun filtre par date. Impossible de répondre à « combien de cafés mardi passé ». |
| 3.3 Changer la règle du café gratuit | Non | Le chiffre 10 était écrit directement dans le code, et le calcul (un modulo) ne marche plus si la règle change en cours de route. |
| 3.4 Effacer un client | Non | Supprimer un client dans l'admin supprime aussi toutes ses transactions (testé : le total est passé de 42 à 36 pour un client de 6 achats). Les statistiques du patron changent, ce qui est interdit. Il n'y avait pas de moyen d'effacer l'identité en gardant les transactions. |
| 3.5 Fusionner deux fiches | Non | Rien ne permettait de déplacer les transactions et les cartes d'une fiche vers une autre. |
| 3.6 Employés et permissions | Non | Il n'y avait pas de connexion, et les transactions ne gardaient pas le nom de la personne qui les avait faites. |

## 2. Ce qui nous a surpris

- Notre journal des transactions nous a beaucoup aidés, même si on ne l'avait pas prévu. Les soldes se calculent à partir de lui, donc plusieurs demandes se règlent en travaillant sur le journal.
- La carte prépayée garde un nombre de cafés restants à côté du journal. On a donc deux endroits qui disent la même chose. Si les deux ne s'accordent plus, on ne sait pas lequel croire.
- Certaines demandes semblent se contredire : le patron veut garder les statistiques, mais aussi effacer l'identité d'un client.
- En testant notre v1, nous avons découvert que supprimer un café pris sur une carte laisse le solde faux. Nous pensions que le journal réglait tout, alors que le compteur de la carte le contredit.

## 3. Une décision qu'on prendrait autrement

On ne garderait pas le nombre de cafés restants sur la carte. Dans notre v1, cette information est écrite à deux endroits : dans le journal des transactions et dans un compteur sur la carte. Quand on supprime une transaction dans l'admin, le journal change mais pas le compteur, et les deux ne disent plus la même chose. On calculerait plutôt le nombre de cafés restants à partir du journal, pour qu'il n'y ait qu'une seule source.