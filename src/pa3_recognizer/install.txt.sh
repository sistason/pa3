#!/bin/bash
#
# <new rasbian>
# copy private_key and authorized_keys to /root/.ssh

passwd -d pi

apt-get update
# apt-get install -y vim screen tcpdump xinetd check-mk-agent # Optional

# TODO: expand file system here
raspi-config

# sed -i "s/disable[$'\t' ]*=[$'\t' ]*yes/disable = no/" /etc/xinetd.d/check_mk
# service xinetd restart

reboot
