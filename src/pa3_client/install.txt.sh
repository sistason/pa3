#!/bin/bash
#
# <new rasbian>
# copy private_key and authorized_keys to /root/.ssh
# copy main.sh + main_wrapper.sh to /root/

passwd -d pi

apt-get update
# apt-get install -y vim screen tcpdump xinetd check-mk-agent # Optional
apt-get install -y fswebcam tmux ferm imagemagick
echo "@reboot   root    /root/main_wrapper.sh" >> /etc/crontab


# TODO: expand file system here
raspi-config

# sed -i "s/disable[$'\t' ]*=[$'\t' ]*yes/disable = no/" /etc/xinetd.d/check_mk
# service xinetd restart

reboot
