
## Contexte
Une cliente demande d'effacer ses renseignements (esprit de la Loi 25). Mais les statistiques du patron ne doivent pas changer : ses cafés restent comptés. Questions : effacer ou anonymiser ? Que devient sa carte prépayée à moitié utilisée ? Les anciennes valeurs restent-elles quelque part ?

## Décision
Nous allons **anonymiser** le client. Son nom devient « Client effacé », son téléphone devient « efface-numéro » (unique, mais sans donnée personnelle), et son courriel est vidé. Ses transactions restent, donc les rapports ne changent pas. Le client n'apparaît plus dans la recherche.

Sa carte prépayée restante est **perdue**. Avant de confirmer, le gérant voit un avertissement qui indique combien de cafés seront perdus.

Le journal d'actions du gérant ne contient que des numéros, jamais de nom, de téléphone ou de courriel. Nous n'avons pas d'historique des anciennes valeurs. Dans l'admin, la suppression d'un client est désactivée.

## Options écartées
- **Supprimer le client :** ses transactions disparaîtraient et les rapports changeraient (testé sur la v1).
- **Garder le nom et effacer seulement le téléphone :** la personne resterait identifiable.
- **Rembourser la carte :** le système ne traite aucun paiement.

## Conséquences
- **Facile :** les statistiques restent exactes et l'identité disparaît du système.
- **Difficile :** on ne peut pas revenir en arrière.
- **Limite connue :** les anciennes copies de sauvegarde de la base de données contiennent encore l'ancienne identité. Il faut aussi effacer ces copies.