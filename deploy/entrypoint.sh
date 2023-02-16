#!/bin/sh
echo "Waiting for Postgres..."

while ! nc -z $DJANGO_POSTGRES_HOST $DJANGO_POSTGRES_PORT; do
  sleep 0.1
done

echo "PostgreSQL started"

exec "$@"