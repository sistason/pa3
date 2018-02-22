#!/bin/bash

iptables -F INPUT
iptables -P INPUT DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

/usr/sbin/sshd -D
