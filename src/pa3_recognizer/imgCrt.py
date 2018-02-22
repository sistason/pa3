#!/ust/bin/env python 

from cv2 import imread
import os
import time
import logging

class ImageCreator():
    """ Captures images from a webcam or directory

    Returns the image from the directory supplied."""
    
    def __init__(self, pa_number, image_directory):
        self.IMAGE_DIR = image_directory
        self.PA = "{:02}".format(pa_number)

    def get_image(self):
        try:
            image_location = os.path.join(self.IMAGE_DIR, '{}.jpeg'.format(self.PA))
            while not os.path.exists(image_location):
                time.sleep(0.1)

            image_location_edit = os.path.join(self.IMAGE_DIR, '{}.edit.jpeg'.format(self.PA))
            os.rename(image_location, image_location_edit)
            img = imread(image_location_edit)
            os.remove(image_location_edit)
            return img
        except Exception as e:
            logging.exception('Error while getting image, was: {0}'.format(e))
            return
