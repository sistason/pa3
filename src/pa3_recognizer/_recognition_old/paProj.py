#!/usr/bin/env python
from imgRec import ImageRecognitor
from imgCrt import ImageCreator
from time import sleep, time
from os import path, access, W_OK, R_OK, uname, environ
from re import search
import logging


class PruefungsamtProjekt():
    def __init__(self, user='', client_password='', server_url='', camera='', image_directory=''):
        logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s', level=logging.INFO)
        user = user if user else self.get_pa_number()

        self.img_crt = ImageCreator(user, filesystem_dir=image_directory, camera_id=camera)
        self.img_rec = ImageRecognitor(user, client_password=client_password, server_url=server_url)

    def spin(self, idle_time=0):
        while True:
            begin = time()
            image = self.img_crt.get_image()
            if image is not None and image.any():
                self.img_rec.work_image(image)

            rest = idle_time-(time()-begin)
            if rest > 0.0:
                sleep(rest)

    @staticmethod
    def get_pa_number():
        hostname = uname()[1]   # NOTE: UNIX-only solution, not on Windows.
        try:
            return search("recognizer_(.+)", hostname).group(1)
        except IndexError:
            logging.error("Cannot determine own pa_number, please make sure\
                     the number is in the hostname or specify it via '-p'")
            exit(1)


def argcheck_dir(string):
    if path.isdir(string) and access(string, W_OK) and access(string, R_OK):
        return path.abspath(string)
    raise argparse.ArgumentTypeError('%s is no directory or isn\'t writeable'%string)


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description="Program to take \
                        webcam pictures, run seven-segment OCR over \
                        it and upload the results somewhere.",
                epilog='Created and Maintained by Kai Sisterhenn \
                    under GPLv3, kais@freitagsrunde.org, since 2012')
    argparser.add_argument('--pa_user', '-p',
                           help='Set the name of the pruefungsamt to recognize')
    argparser.add_argument('--client_password', '-P', type=str,
                           help='Set the password to submit the results')
    argparser.add_argument('--server_url', '-S', type=str,
                           help='Set the url to reach the server')
    argparser.add_argument('--image_directory', '-i', type=str,
                           help='Set if there is a directory to get the images from')
    argparser.add_argument('--camera', '-C', type=int, default=-1,
                           help='Set to use the camera, if any')
    argparser.add_argument('--wait', '-w', default=1, type=int, 
                            help='Set the time to sleep between captures')

    pd = vars(argparser.parse_args())
    client_password_ = pd['client_password']
    if not client_password_:
        with open(path.join("/run", "secrets", "recognizer_auth")) as f:
            client_password_ = f.read().strip()

    server_url_ = pd['server_url']
    if not server_url_:
        server_url_ = environ.get('SERVER_URL')

    image_directory_ = pd['image_directory']
    if not image_directory_:
        image_directory_ = environ.get('IMAGE_DIRECTORY')

    camera_ = pd['camera']
    if camera_ < 0:
        camera_ = environ.get('CAMERA', -1)

    pa_proj = PruefungsamtProjekt(user=pd['pa_user'], client_password=client_password_,
                                  server_url=server_url_, camera=camera_, image_directory=image_directory_)
    pa_proj.spin(idle_time=pd['wait'])
