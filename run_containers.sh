#!/bin/bash

NAME=pa3
RECOGNIZER=${NAME}_recognizer
FRONTEND=${NAME}_frontend
BACKEND=${NAME}_backend

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR=${DIR}/data/
if [ ! -e ${DATA_DIR} ]; then mkdir -p ${DATA_DIR}; fi

echo "Stopping containers..."
docker container stop ${RECOGNIZER}_{02,10,13,23} $FRONTEND $BACKEND ${NAME}_mysql

echo "rebuilding secrets..."
if [ ! -e ${DATA_DIR}/secrets ]; then mkdir -p ${DATA_DIR}/secrets; fi
for pwfile in ${DATA_DIR}/secrets/{mysql,pa_02,pa_10,pa_13,pa_23,djangokey}_pw.txt; do
    if [ ! -e $pwfile ]; then
        echo $(pwgen 31 1) > $pwfile
    fi
done

echo "rebuilding containers..."
docker build -t $RECOGNIZER --file $DIR/Dockerfile_recognizer $DIR
docker build -t $FRONTEND --file $DIR/Dockerfile_frontend $DIR
docker build -t $BACKEND --file $DIR/Dockerfile_backend $DIR

NET=${NAME}-net
if ! docker inspect $NET &>/dev/null; then
    docker network create -o "com.docker.network.bridge.name=br-docker-pa3" --subnet 172.17.0.16/28 $NET
fi


mkdir -p "${DATA_DIR}/mysql/" 2>/dev/null
docker run --rm -dit --name ${NAME}_mysql --net $NET -h ${NAME}_mysql \
    -e MYSQL_ROOT_PASSWORD="$(<${DATA_DIR}/secrets/mysql_pw.txt)" \
    -e MYSQL_DATABASE="${NAME}_django" \
    --mount type="bind",source="${DATA_DIR}/mysql",destination="/var/lib/mysql" \
    mysql

cp ${DATA_DIR}/secrets/* $DIR/src/pa3_frontend/pa3_django/secrets/  #TODO: remove on production
mkdir -p "${DATA_DIR}/frontend_bindfs/" 2>/dev/null    #TODO: remove on production
umount "${DATA_DIR}/frontend_bindfs/" 2>/dev/null
bindfs "$DIR/src/pa3_frontend/pa3_django" "${DATA_DIR}/frontend_bindfs" -o "force-user=0,force-group=0"  #TODO: remove on production
docker run --rm -dit --name $FRONTEND -h $BACKEND -p 9080:80 -p 9433:443 --net $NET \
    --mount type="bind",source="${DATA_DIR}/frontend_bindfs",destination="/root/pa3_django" \
    ${FRONTEND}

if [ ! -e "${DATA_DIR}/current_images/" ]; then mkdir -p "${DATA_DIR}/current_images/"; fi
docker run --rm -dit --name $BACKEND -h $BACKEND -p 9022:22 \
    --cap-add=NET_ADMIN --cap-add=NET_RAW --net $NET \
    --mount type="bind",source="${DATA_DIR}/current_images/",destination="/root/current_images/" \
    ${BACKEND}

for pa_client in 02 10 13 23; do
    _name=${RECOGNIZER}_${pa_client}
    echo $_name
    docker run --rm -dit --name ${_name} --network=${NET} --hostname=${_name} \
    --mount type="bind",source="$DATA_DIR/current_images/",destination="/root/current_images/" \
    ${RECOGNIZER}
done

