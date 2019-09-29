FROM python:3.7-alpine
ENV PYTHONUNBUFFERED 1

ENV LANG de_DE.UTF-8
RUN apk update && apk add --virtual build-deps gcc musl-dev # python3-dev
RUN apk update && apk add gettext mariadb-client mariadb-dev libxml2-dev libxslt-dev

COPY requirements.txt /root
RUN pip install -r /root/requirements.txt

RUN apk del build-deps

#RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales gettext
#RUN sed -i -e 's/# ${LANG} UTF-8/${LANG} UTF-8/' /etc/locale.gen && \
#    dpkg-reconfigure --frontend=noninteractive locales && \
#    update-locale LANG=${LANG}

RUN adduser -DH www-data
RUN chown www-data:www-data /dev/shm

EXPOSE 8003

COPY crontab /etc/crontab
RUN touch /var/log/django_debug.log; chmod 777 /var/log/django_debug.log
COPY pa3_django /srv/pa3_django

COPY entrypoint.sh /srv/

WORKDIR /srv/pa3_django
ENTRYPOINT ["/bin/sh", "/srv/entrypoint.sh"]
