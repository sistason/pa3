#!/usr/bin/env python

import cv2
import os
import time
import logging


class ImageCreator():
    """ Captures images from a webcam or directory

    Returns the image from the directory supplied."""
    
    def __init__(self, pa_number, filesystem_dir=''):
        self.PA = pa_number

        self.cam = None
        self.filesystem_dir = filesystem_dir

    def get_image(self):
        if self.filesystem_dir:
            return self.get_image_filesystem()
        else:
            return self.get_image_webcam()

    def get_image_filesystem(self):
        try:
            image_location = os.path.join(self.filesystem_dir, '{}.next.jpeg'.format(self.PA))
            while not os.path.exists(image_location):
                time.sleep(0.1)

            image_location_edit = os.path.join(self.filesystem_dir, '{}.jpeg'.format(self.PA))
            os.rename(image_location, image_location_edit)
            return cv2.imread(image_location_edit)
        except Exception as e:
            logging.exception('Error while getting image, was: {0}'.format(e))
            return

    def get_image_webcam(self):
        if self.cam is None:
            self._init_cam()

        try:
            return self.cam.read()[1]
        except Exception as e:
            logging.exception('Error while getting image, was: {0}'.format(e))

    def _init_cam(self):
        try:
            self.cam = cv2.VideoCapture(0)
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
            self.cam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 720)
        except Exception as e:
            logging.exception('Error while initializing camera, was: {0}'.format(e))
