#!/bin/bash

project_directory="$(dirname $0)"

# Secrets come via ENV
mkdir /run/secrets
echo "$SECRET_RECOGNIZER_AUTH" > /run/secrets/recognizer_auth
echo "$SECRET_MYSQL_PASSWORD" > /run/secrets/mysql_password
echo "$SECRET_DJANGO_SECRET_KEY" > /run/secrets/django_secret_key
chown www-data:www-data /run/secrets/*

python3 "${project_directory}/pa3_django/manage.py" collectstatic --noinput

# Wait for database

i=5
while sleep 5; do
    if echo "show databases;" | python3 "${project_directory}/pa3_django/manage.py" dbshell 2>/dev/null; then
        break
    elif [ $i -ge 60 ]; then
        break
    fi
    echo "$(date) - Waiting $i/60s for database connectivity..."
    i=$((i+5))
done

echo "Make migrations"

python3 "${project_directory}/pa3_django/manage.py" makemigrations pa3 pa3_web
python3 "${project_directory}/pa3_django/manage.py" migrate

echo "Start cron"
/usr/sbin/crond

echo "Start Gunicorn"
su www-data -c "gunicorn pa3.wsgi:application --bind 0.0.0.0:8003"