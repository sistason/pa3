FROM sgtwilko/rpi-raspbian-opencv
#FROM python:3.6

RUN mkdir -p /srv/pa3/current_images
RUN mkdir -p /run/secrets/

COPY requirements.txt /srv/pa3/
RUN pip3 install -r /srv/pa3/requirements.txt

COPY recognizer_auth /run/secrets/
COPY recognition/ /srv/pa3/recognition

WORKDIR /srv/pa3
CMD ["python3", "/srv/pa3/recognition/waitingnumberrecognition.py"]
