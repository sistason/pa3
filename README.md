# Pruefungsamtprojekt

This project was started to digitze the numbers in front of the exam office of the TU Berlin.

It was expanded and is now able to collect OCR-input from multiple recognizers into a database for display.

## Operation
The project is distributed via Ansible as 4 Docker-containers:
- Recognizer
- Frontend
  - frontend_mysql
  - frontend_proxy

### Recognizer
The recognizer is located on a device with a camera or with access to the images it needs to run OCR on.

The recognition is opencv-python software specifically designed to recognize the seven-segment displays at TU-Berlin, although it can easily be exchanged or customized.

The recogniition POSTs its results via https to the frontend.

### Frontend
The Frontend is located on a device with a public IP/DNS for the user interaction.

The software consists of a python-django framework, which:
- collects results of the recognition
- displays the results to users
- provides an API
- Optional: Interfaces services of notifications for the users

Additionally, there is a mysql container for the database of django and a proxy container
for redirecting to https and handling the Let's Encrypt certificate verification process.

## Prerequisites
- edit hosts to reflect your infrastructure. Apt is used here for package management, so consider using Debian hosts.
- the ssh-key Ansible uses has to work on all hosts (root, for package-installation)
- edit playbook.yml for `server_url` and `frontend_directry`.
- Docker needs port 80 and 443 on the web-host. If the ports are used, consider ProxyPass/etc. with either reconfiguring the frontend-ports in src/pa3_frontend/playbook.yml or use a virtual machine for the frontend.
- install Ansible

## Run
Run `ansible-playbook -i hosts playbook.yml`

Please note this project was neither started nor converted to be plug&play. 
It needs to be adapted for your use case, so understanding the operation is necessary 
for installation and configuration.
Please see the READMEs in the respective source directories. 

## TODOs:
- subscription via SMS?
- rewrite/refactor number_recognition to py3

