# Déclaration d'usage de l'IA générative

Devoir 1, système de fidélité pour un café.

## Outil utilisé

Claude (Anthropic), via l'interface de conversation claude.ai, tout au long du devoir.

## Ce que l'IA a fait

| Domaine | Usage |
|---|---|
| Mise en place | Aide pour créer l'environnement virtuel, installer Django, lier le dépôt à GitHub, créer une branche personnelle, faire des commits, créer un tag |
| Apprentissage | Explications de Django (requêtes, URL, vues, modèles, gabarits, migrations), de Python et de HTTP, avec des exemples |
| Code | Rédaction du code de départ des modèles (`Client`, `CartePrepayee`, `Transaction`), des vues, du formulaire, des gabarits HTML, du CSS et de la configuration de l'administration, avec des commentaires explicatifs |
| Conception | Discussion des zones grises de l'énoncé : l'IA a proposé des options et leurs conséquences (journal unique ou héritage de classes, café gratuit en réserve, identification par téléphone) |
| Validation | Rédaction des expressions régulières de validation du nom, du téléphone et du courriel |
| Dépannage | Lecture des messages d'erreur et propositions de correctifs (gabarits, environnement virtuel, Git) |
| Schémas | Diagramme du trajet d'une requête et diagramme de classes |
| Documentation | Rédaction de la première version du `README.md`, de `docs/conception.md` et de ce fichier, à partir des décisions prises pendant la conversation |

## Ce qui vient de moi

- La décision finale sur chaque zone grise. Par exemple : le café gratuit et la carte prépayée expirent tous deux après un mois ; la recherche porte aussi sur le courriel ; un client peut commander plusieurs cafés à la fois ; la fidélité suit celui qui paie ; les saisies doivent être validées avec des expressions régulières.
- Les scénarios réels qui ont fait évoluer le produit (clients homonymes, carte oubliée, amies dont on paie les cafés, achat de plusieurs cafés).
- L'exécution du code, les tests dans le navigateur et le choix de ce qui a été conservé, modifié ou rejeté.
- Le versionnement Git et la remise.

## Vérification

Le code produit avec l'IA a été exécuté sur ma machine et essayé dans le navigateur : recherche, création de client, enregistrement d'achats, carte prépayée et administration. Plusieurs erreurs rencontrées en cours de route (gabarits, environnement virtuel) ont été diagnostiquées à partir des messages d'erreur réels.

## Limites de l'usage

Le contenu généré n'est pas considéré comme correct par défaut : il a été relu, exécuté et adapté à mes décisions. Les limites connues de la solution sont documentées dans `docs/conception.md`, section 4.
