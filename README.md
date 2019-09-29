# Pruefungsamtprojekt

This project was started to digitze the numbers in front of the exam office of the TU Berlin.

It was expanded and is now able to collect OCR-input from multiple recognizers into a database for display.

## Operation
The project is distributed via Ansible as 3+n Docker-containers:
- 1-n * Recognizer
- Frontend + mysql

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

Additionally, there is a mysql container for the database of django
Reverseproxy is done separately, the frontend expects http on port 8003.

## Setup New
You deploy the setup with ansible using ssh-key/passwords

- setup secrets in the gitlab-ci variables and put them into ansible/secrets as:
  - SECRET_DJANGO_SECRET_KEY / django_secret_key
  - SECRET_MYSQL_PASSWORD / mysql_password
  - SECRET_RECOGNIZER_AUTH / recognizer_auth

- there is a ansible/setup_pi.sh to burn an image to a SD-Card and enable ssh+keys 

- with a ssh-key of the recognizers and the webserver(s), use the ansible-playbook site.yml 
   to deploy the entire thing initially/periodically OR
- use the ansible-playbook recognizers.yml and webserver.yml to deploy those seperately

- If the secrets change, redeploy.

## Prerequisites
- edit hosts to reflect your infrastructure. Apt is used here for package management, so consider using Debian hosts.
- the ssh-key Ansible uses has to work on all hosts (root, for package-installation)
- edit ansible variables for mainly `server_url`.
- Setup a reverseproxy on the webserver to forward to 8003.
- install Ansible

## Run
Run `ansible-playbook playbooks/site.yml`

Please note this project was neither started nor converted to be plug&play. 
It needs to be adapted for your use case, so understanding the operation is necessary 
for installation and configuration.
Please see the READMEs in the respective source directories. 

## TODOs:
- subscription via SMS?