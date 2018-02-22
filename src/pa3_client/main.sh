#!/bin/bash

HOST=root@141.23.57.145
HOST_PORT=9022
HOST_PATH=current_images
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
image_dir=$DIR/image_directory

_t=$(ip addr show dev eth0 | egrep -o "inet 130\.149\.233\.[0-9]{1,3}")
_last_octet=${_t#inet 130.149.233.}

if [[ $_last_octet == 82 ]]; then
    PA_NR=10
elif [[ $_last_octet == 83 ]]; then
    PA_NR=13
elif [[ $_last_octet == 84 ]]; then
    PA_NR=23
elif [[ $_last_octet == 85 ]]; then
    PA_NR=02
    ROTATE="--rotate 180"
else
    echo "Pruefungsamt number not recognized by IP address"
    exit 1
fi


mkdir $image_dir
sshfs -o"IdentityFile=~/.ssh/pa3_client_key" -o"StrictHostKeyChecking=no" -o"port=$HOST_PORT" $HOST:$HOST_PATH $image_dir

while true; do
    fswebcam -l 1 -d /dev/video0 -r 1280x720 --no-banner \
      $ROTATE $image_dir/${PA_NR}_tmp.jpeg \
      --exec "mv $image_dir/${PA_NR}_tmp.jpeg $image_dir/$PA_NR.jpeg"

    sleep 5
done

