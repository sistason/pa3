# Recognition

The recognizer is deployed on a host with a webcam or with access to images it should run OCR on.

#### Ansible Playbook
You can change the `server_url` to where the recognition POSTs its results to, 
and the `camera-id` (/dev/videoX) in the ansible-playbook.

#### Dockerfile
The Dockerfile just builds a opencv-ready container and adds the secrets, the recognition-src and the entrypoint.

#### Recognition
CLI-Arguments are located in the main-pythonfile. Arguments overwrite the ENV-variables, 
which are used by ansible to control the operation.

For a detailled description of the algorithm, see chapter Implementation in 
https://www.sistason.de/media/masterthesis.pdf