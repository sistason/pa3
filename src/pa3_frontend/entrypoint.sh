#!/bin/bash

project_directory="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

python3 "${project_directory}/pa3_django/manage.py" collectstatic --noinput

echo "Make migrations"
python3 "${project_directory}/pa3_django/manage.py" makemigrations
python3 "${project_directory}/pa3_django/manage.py" migrate

echo "Start cron"
/usr/sbin/cron

echo "Start Apache2"
/usr/sbin/apache2ctl -D FOREGROUND
