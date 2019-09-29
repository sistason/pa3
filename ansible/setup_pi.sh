#!/bin/bash

if (( $# != 3 )); then printf "Too little arguemnts!\n %s: HOSTNAME IMAGE /dev/SDCARD\n" "$0"; exit 1; fi

# Sanatation
HOSTNAME=$1

IMAGE=$2
if [ -z "${IMAGE}" ]; then echo "Image does not exist!"; exit 1; fi

SDCARD=$3
if (( $(fdisk -l "${SDCARD}" | head -n1 | grep -o "[[:digit:]]* bytes" | wc -c) > 18 )); then
  echo "${SDCARD} has more than 100GB storage! are you sure this is the SD-Card?"
  exit 1
fi

if [[ $(read -p "Burn image?" burn) == "[yY]*" ]]; then
  echo burn
  sleep 5
  # Burn image
  dd if="${IMAGE}" of="${SDCARD}" bs=1M status=progress

  sync

  partprobe
fi
# Setup SD-Card

umount /tmp/setup_pi_temp/* 2>/dev/null
rm -r /tmp/setup_pi_temp
mkdir /tmp/setup_pi_temp /tmp/setup_pi_temp/boot /tmp/setup_pi_temp/slash 2>/dev/null

set +e
if [[ "${SDCARD}" == *mmcblk* ]]; then
  mount "${SDCARD}p1" /tmp/setup_pi_temp/boot
  mount "${SDCARD}p2" /tmp/setup_pi_temp/slash
elif [[ "${SDCARD}" == *sd* ]]; then
  mount "${SDCARD}1" /tmp/setup_pi_temp/boot
  mount "${SDCARD}2" /tmp/setup_pi_temp/slash
else
  echo "unknown partition"
fi

touch /tmp/setup_pi_temp/boot/SSH
umount /tmp/setup_pi_temp/boot

mkdir /tmp/setup_pi_temp/slash/root/.ssh/ || true
echo "$(</home/sistason/.ssh/pa3_client_key.pub)" > /tmp/setup_pi_temp/slash/root/.ssh/authorized_keys
sed -i "/^pi*\$/d" /tmp/setup_pi_temp/slash/etc/passwd
echo "pi:x:1000:1000:,,,:/home/pi:/bin/false" >> /tmp/setup_pi_temp/slash/etc/passwd
echo "${HOSTNAME}" > /tmp/setup_pi_temp/slash/etc/hostname
sed -i "s/raspberrypi/${HOSTNAME}/g" /tmp/setup_pi_temp/slash/etc/hosts
umount /tmp/setup_pi_temp/slash

rmdir /tmp/setup_pi_temp/slash /tmp/setup_pi_temp/boot /tmp/setup_pi_temp
sync