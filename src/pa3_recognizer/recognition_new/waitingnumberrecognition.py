#!/usr/bin/env python3

import time
import logging
import requests
from base64 import b64decode

import cv2
import base64
import numpy as np

from imagecreation import ImageCreator
from recognition.imagerecognitionTUB import ImageRecognitor

logging.getLogger("requests").setLevel(logging.WARNING)


class Configuration():
    def __init__(self, server_conf):
        self.valid_ranges = server_conf.get('ranges', [])
        self.previous_numbers = [number.get('number', -1) for number in server_conf.get('current_numbers', [])]

        self.rotate = server_conf.get('rotate', 0)
        # How many numbers are (vertically) on the table?
        self.number_of_numbers = len(self.valid_ranges)

        self.template_digit = self.decode_template(server_conf.get('template_digit'))
        self.template_whole = self.decode_template(server_conf.get('template_whole'))

    @staticmethod
    def decode_template(template_encoded):
        template_encoded_numpy = np.fromstring(b64decode(template_encoded), dtype=np.uint8)
        if template_encoded_numpy is not None:
            template = cv2.imdecode(template_encoded_numpy, cv2.IMREAD_COLOR)
            return cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) if len(template.shape) != 2 else template
        else:
            logging.error("Template malformed!")


class WaitingNumberRecognition:

    def __init__(self, user='', client_password='', server_url='', camera='', image_directory=''):
        self.url = server_url
        self.user = user
        self.password = client_password
        logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s', level=logging.INFO)

        self.image_creator = ImageCreator(user=user, filesystem_dir=image_directory, camera_id=camera)

        config = self.get_config()
        self.image_recognitor = ImageRecognitor(config)

    def get_config(self):
        config_url = 'https://{}/get_config'.format(self.url)
                                                                                         # TODO: remove in production
        ret = requests.post(config_url, data={'user': self.user, 'password': self.password}, verify=False)
        return Configuration(ret.json())

    def spin(self, idle_time=0):
        while True:
            begin = time.time()
            image = self.image_creator.get_image()
            if image is not None and image.any():
                processing_begin = time.time()

                recognized_numbers = self.image_recognitor.recognize(image)
                logging.info('Recognized numbers: {}'.format(recognized_numbers))

                self.upload(recognized_numbers, processing_begin)

            rest = idle_time-(time.time()-begin)
            if rest > 0.0:
                time.sleep(rest)

    def upload(self, numbers, processing_begin):
            data = {'user': self.user, 'password': self.password, 'ts': int(time.time()),
                    'numbers': [], 'begin': int(processing_begin)}
            files = {}

            for i, num in enumerate(numbers):
                data['numbers'].append(num.number)

                if num.new:
                    _, img_encoded = cv2.imencode('.jpg', num.image)
                    files['image_{}'.format(i)] = ('{}.jpeg'.format(self.user),
                                                   img_encoded.tostring(),
                                                   'image/jpeg',
                                                   {'Expires': '0'})
            try:
                requests.post("https://{}/write".format(self.url), data=data, files=files, verify=False)
            except Exception as e:
                logging.exception("Failed to submit request: {0}".format(e))


if __name__ == '__main__':
    from os import path, access, W_OK, R_OK, environ
    import argparse

    def argcheck_dir(string):
        if path.isdir(string) and access(string, W_OK) and access(string, R_OK):
            return path.abspath(string)
        raise argparse.ArgumentTypeError('%s is no directory or isn\'t writeable' % string)


    argparser = argparse.ArgumentParser(description="Program to take \
                                                     webcam pictures, run seven-segment OCR over \
                                                     it and upload the results.",
                                        epilog='Created and Maintained by Kai Sisterhenn \
                                                under GPLv3, kais@freitagsrunde.org, since 2012')

    argparser.add_argument('--device', '-d', default=-1, type=int,
                           help='Set the device number (/dev/videoX). Default is -1 (first it can find)')
    argparser.add_argument('--wait', '-w', default=0, type=int,
                           help='Set the time to sleep between captures')
    argparser.add_argument('--image_directory', '-i', type=str,
                           help='Set if there is a directory to get the images from')
    argparser.add_argument('--server_url', '-S', type=str,
                           help='Set the url to reach the server')
    argparser.add_argument('--user', '-u',
                           help='Set the name of the pruefungsamt to recognize, if in not the hostname')
    argparser.add_argument('--client_password', '-P', type=str,
                           help='Set the password to submit the results')

    pd = vars(argparser.parse_args())
    client_password_ = pd['client_password']
    if not client_password_:
        with open("/run/secrets/recognizer_auth") as f:
            client_password_ = f.read().strip()

    server_url_ = pd['server_url']
    if not server_url_:
        server_url_ = environ.get('SERVER_URL')

    image_directory_ = pd['image_directory']
    if not image_directory_:
        image_directory_ = environ.get('IMAGE_DIRECTORY')

    camera_ = pd['device']
    if camera_ < 0:
        camera_ = environ.get('CAMERA', -1)

    recognition = WaitingNumberRecognition(user=pd['user'], client_password=client_password_,
                                           server_url=server_url_, camera=camera_, image_directory=image_directory_)
    recognition.spin(idle_time=pd['wait'])
