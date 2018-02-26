cd /root/pa3_django; python manage.py collectstatic --noinput
uwsgi --uid uwsgi --http-auto-chunked --http-keepalive
