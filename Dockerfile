# Image de l'application (production). Construite par `docker compose up --build`.
# Image de base précise (version de Python + distribution), jamais « latest ».
FROM python:3.13-slim-bookworm

# Pas de fichiers .pyc, journaux immédiats sur la sortie standard, pip sans cache.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Utilisateur NON root : si quelqu'un exploite l'application, il n'est pas administrateur.
RUN useradd --create-home --uid 1000 app

WORKDIR /app

# Les dépendances d'abord : cette couche est réutilisée tant que requirements.txt ne change pas.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app src/ .

# Dossier des fichiers statiques (voir ADR-0014) : créé ici pour que le volume nommé
# qui s'y branche appartienne à l'utilisateur « app ».
RUN mkdir -p /app/staticfiles && chown app:app /app/staticfiles

USER app
EXPOSE 8000

# Serveur d'application de production (jamais `runserver`). Les journaux vont sur stdout.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--error-logfile", "-"]
