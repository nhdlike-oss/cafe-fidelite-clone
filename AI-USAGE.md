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


---
---

# Devoir 3

## Outil utilisé
Claude (Anthropic), via l'application Claude, tout au long du devoir 3.

## Ce que l'IA a fait
- **Code :** modèle `Succursale` et migrations 0005 à 0007, permissions par succursale (`services.py`), choix du café, rapports par café, `balances --succursale`, commandes `importer_sqlite` et `demo_v3`, page de santé `/sante/`.
- **Conteneurs :** `Dockerfile`, `compose.yaml`, `compose.dev.yaml`, `docker/nginx.conf`, `.env.example`, configuration par variables d'environnement.
- **Tests :** `tests_v3.py` (succursales, permissions, rapports, migration v2 vers v3).
- **Documentation :** première version des ADR 0008 à 0015, de `retrospective-v2.md`, de la section v3 de `conception.md`, de `migration.md` et du README.
- **Explications :** Docker, WSL, PostgreSQL et les migrations, en langage simple.

## Ce que l'IA n'a pas pu faire
Elle n'a pas pu lancer `docker compose` dans son environnement. Le démarrage des conteneurs et du proxy a été vérifié sur ma machine.

## Ce qui vient de nous
- J'ai installé Docker Desktop et WSL sur Windows, créé mon `.env` avec ma propre clé secrète, et lancé la v3 avec `docker compose up --build`.
- J'ai chargé la démonstration et signalé l'erreur de `demo_v3` (transactions sans succursale), que l'IA a corrigée.
- J'ai fait expliquer les ADR en langage simple jusqu'à les comprendre, puis j'ai validé les décisions des ADR 0008 à 0015.

## Vérification
J'ai lancé `docker compose run --rm web python manage.py test` dans mes conteneurs : 59 tests, tous réussis, contre PostgreSQL. Les quatre services démarrent en bon état (`docker compose ps`) et la démonstration se charge sans erreur.

## Limites de l'usage
Le contenu généré n'est pas considéré comme correct par défaut : il doit être relu, exécuté et adapté. Les limites connues sont dans `docs/conception.md` (Version 3, section 8).