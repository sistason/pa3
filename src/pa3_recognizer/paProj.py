#!/usr/bin/env python
from imgRec import ImageRecognitor
from imgCrt import ImageCreator
from time import sleep, time
from os import path, access, W_OK, R_OK, uname
from re import search
import logging


class PruefungsamtProjekt():
    def __init__(self, pa_number=0):
        logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s', 
                                                        level=logging.INFO)
        pa_number = pa_number if pa_number else self.get_pa_number()
        pa_number = "{:02}".format(pa_number)

        current_dir = path.abspath(path.dirname(__file__))
        self.img_crt = ImageCreator(pa_number, path.join(current_dir, 'current_images'))
        self.img_rec = ImageRecognitor(pa_number)

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
        hostname=uname()[1]   #NOTE: UNIX-only solution, not on Windows.
        try:
            return int(search("recognizer_(\d\d)", hostname).group(1))
        except (IndexError, ValueError):
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
    argparser.add_argument('--pa_number', '-p', default=0, type=int, 
                            help='Set the number of the pruefungsamt to recognize')
    argparser.add_argument('--wait', '-w', default=1, type=int, 
                            help='Set the time to sleep between captures')

    pd=vars(argparser.parse_args())

    pa_proj = PruefungsamtProjekt(pa_number=pd['pa_number'])
    pa_proj.spin(idle_time=pd['wait'])
