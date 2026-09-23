#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ] && [ "$POSTGRES_HOST" != "sqlite" ]; then
    echo "Waiting for postgres at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
    while ! nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
        sleep 0.5
    done
    echo "PostgreSQL started"
fi

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Seeding demo data..."
python manage.py seed_demo || true

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

exec "$@"
