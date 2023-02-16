#!/bin/bash

psql -U postgres <<-END
    CREATE USER dev WITH PASSWORD '9SEEk57rnu';
    CREATE DATABASE utmcraft_opensource OWNER dev;
END

psql -U postgres utmcraft_opensource -c 'CREATE EXTENSION IF NOT EXISTS hstore;'
