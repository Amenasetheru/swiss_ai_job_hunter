#!/usr/bin/env bash
# Stop the script immediately when a command fails
set -euo pipefail

# Connect to the initialized database with the PostgreSQL administrator account
psql \
  --username "${POSTGRES_USER}" \
  --dbname "${POSTGRES_DB}" \
  --set app_db_user="${APP_DB_USER}" \
  --set app_db_password="${APP_DB_PASSWORD}" <<'SQL'
-- Create the application role without PostgreSQL superuser privileges
SELECT format(
    'CREATE ROLE %I WITH LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT',
    :'app_db_user',
    :'app_db_password'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_roles
    WHERE rolname = :'app_db_user'
)\gexec

-- Transfer database ownership to the dedicated application role
SELECT format(
    'ALTER DATABASE %I OWNER TO %I',
    current_database(),
    :'app_db_user'
)\gexec

-- Grant the application role permission to use and create objects in the public schema
SELECT format(
    'GRANT USAGE, CREATE ON SCHEMA public TO %I',
    :'app_db_user'
)\gexec

-- Transfer ownership of the public schema to the application role
SELECT format(
    'ALTER SCHEMA public OWNER TO %I',
    :'app_db_user'
)\gexec
SQL
