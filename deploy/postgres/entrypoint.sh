#!/bin/bash

psql -U ${POSTGRES_USER} <<-END
    CREATE USER ${DJANGO_POSTGRES_USER} WITH PASSWORD '${DJANGO_POSTGRES_PASSWORD}';
    CREATE DATABASE ${DJANGO_POSTGRES_DB} OWNER ${DJANGO_POSTGRES_USER};
END

psql -U ${POSTGRES_USER} ${DJANGO_POSTGRES_DB} -c 'CREATE EXTENSION IF NOT EXISTS hstore;'