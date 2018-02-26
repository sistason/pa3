#!/bin/bash

NAME=pa3
RECOGNIZER=${NAME}_recognizer
FRONTEND=${NAME}_frontend
BACKEND=${NAME}_backend

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR=/tmp/docker_${NAME}_tempdir/
if [ ! -e ${DATA_DIR} ]; then mkdir -p ${DATA_DIR}; fi

echo "Stopping containers..."
docker container stop ${RECOGNIZER}_{02,10,13,23} $FRONTEND $BACKEND

echo "rebuilding containers..."
docker build -t $RECOGNIZER --file $DIR/Dockerfile_recognizer $DIR
#docker build -t $FRONTEND --file $DIR/Dockerfile_frontend $DIR
docker build -t $BACKEND --file $DIR/Dockerfile_backend $DIR


NET=${NAME}-net
if ! docker inspect $NET &>/dev/null; then
    docker network create -o "com.docker.network.bridge.name=br-docker-pa3" --subnet 172.17.0.16/29 $NET
fi

#docker run -dit --name $FRONTEND -h $BACKEND -p 9080:80 -p 9433:443 $FRONTEND
docker run -d --name ${NAME}_mysql -e MYSQL_ROOT_PASSWORD= mysql
docker run --rm -dit --name $BACKEND -h $BACKEND -p 9022:22 \
    --cap-add=NET_ADMIN --cap-add=NET_RAW --net $NET \
    --mount type="bind",source="$DATA_DIR/current_images/",destination="/root/current_images/" \
    ${BACKEND}

for pa_client in 02 10 13 23; do
    _name=${RECOGNIZER}_${pa_client}
    echo $_name
    docker run --rm -dit --name ${_name} --network=${NET} --hostname=${_name} \
    --mount type="bind",source="$DATA_DIR/current_images/",destination="/root/current_images/" \
    ${RECOGNIZER}
done

