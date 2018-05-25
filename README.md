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

## Setup New
You deploy the setup once with ansible using ssh-key/password on your local machine.
Afterwards, 
- a gitlab-ci.yml is available to build new webserver-images
- web: a cron-script to get the images via the gitlab-repository
- rec: a cron-scirpt to pull the repo and rebuild/rerun the recognizer-image.

### Initial Setup
- setup secrets in the gitlab-ci variables and put them into ansible/secrets as:
  - SECRET_DJANGO_SECRET_KEY / django_secret_key
  - SECRET_MYSQL_ROOT_PASSWORD / mysql_root_password
  - SECRET_RECOGNIZER_AUTH / recognizer_auth
  - Create deploy key and put into secrets/gitlab-deploy-key

- with a ssh-key of the recognizers and the webserver(s), use the ansible-playbook site.yml 
   with the hosts-inventory to deploy the entire thing initially/periodically OR
- use the ansible-playbook recognizers.yml to deploy those and put the cron-update-script 
   manually to the webserver_host, so it pulls everything via the gitlab-ci+repository

- If the secrets change, you need to redeploy the recognizer-key manually, as the recognizers 
   just pull the repo (gitlab-ci crosscompiling for arm? nah...). 
   The webserver use gitlab-ci, which has the secrets available as variables and will update 
   via the cron-update-script on a push.


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