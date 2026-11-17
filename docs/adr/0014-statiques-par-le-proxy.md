# ADR-0014 — Les fichiers statiques sont servis par le proxy nginx


## Contexte
Avec `DEBUG = False`, Django ne sert plus les fichiers statiques (feuilles de style de l'application et de l'administration). Qui doit les servir : Django, le proxy, ou un conteneur à part ?

## Décision
`collectstatic` écrit dans un volume nommé (`static`), rempli par le service `migrate`. Le proxy nginx monte ce volume en lecture seule et sert `/static/` directement. L'application ne sert aucun fichier statique.

## Options écartées
- **WhiteNoise dans Django :** simple, mais ajoute du code et une dépendance pour un travail que le proxy fait déjà, plus vite.
- **Un conteneur nginx de plus, réservé aux statiques :** un conteneur pour presque rien.

## Conséquences
- **Facile :** pas de code, le proxy est déjà là ; fichiers mis en cache 7 jours.
- **Difficile :** après une mise à jour qui change le CSS, il faut relancer `migrate` (ce que fait `docker compose up --build`).
