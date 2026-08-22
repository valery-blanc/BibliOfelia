# BibliOfelia — image multi-arch (arm64 pour Pi 5, amd64 pour dev)
# Build : docker buildx build --platform linux/amd64,linux/arm64 -t ofelia/bibliofelia:dev .

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

# Dépendances système : SQLite, fontconfig, gettext (i18n), curl (healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
        sqlite3 \
        gcc \
        gettext \
        curl \
        tini \
        fontconfig \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt

# -----------------------------------------------------------------------------
FROM base AS dev

RUN pip install -r requirements-dev.txt

COPY . /app
RUN chmod +x /app/scripts/*.sh \
    && mkdir -p /app/data /app/media /app/staticfiles

EXPOSE 8001
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]

# -----------------------------------------------------------------------------
FROM base AS prod

COPY . /app
RUN chmod +x /app/scripts/*.sh \
    && mkdir -p /app/data /app/media /app/staticfiles \
    && python manage.py collectstatic --noinput \
    && python manage.py compilemessages || true

# Healthcheck : /pairing/info est public (pas d'auth) et touche la BD.
# /api/v1/health exige un JWT (contrat OfeliaScan §6.10), donc inadapté ici.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8001/api/v1/pairing/info || exit 1

EXPOSE 8001
ENTRYPOINT ["/usr/bin/tini", "--", "/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8001", \
     "--workers", "3", \
     "--worker-class", "sync", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
