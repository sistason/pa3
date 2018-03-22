#!/bin/bash

python3 manage.py collectstatic --noinput

python manage.py migrate

/usr/sbin/apache2ctl -D FOREGROUND
