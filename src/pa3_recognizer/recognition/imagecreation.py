#!/ust/bin/env python3

import cv2
import os
import time
import logging


class ImageCreator():
    """ Captures images from a webcam or directory

    Returns the image from the directory supplied."""

    def __init__(self, user='', filesystem_dir='', camera_id=-1):
        self.USER = user

        self.camera_id = camera_id
        self.cam = self._init_cam() if camera_id != -1 else None
        self.filesystem_dir = filesystem_dir

    def get_image(self):
        if self.filesystem_dir:
            return self.get_image_filesystem()
        if self.cam is not None:
            return self.get_image_webcam()

    def get_image_filesystem(self):
        try:
            image_location = os.path.join(self.filesystem_dir, '{}.next.jpeg'.format(self.USER))
            while not os.path.exists(image_location):
                time.sleep(0.1)

            image_location_edit = os.path.join(self.filesystem_dir, '{}.jpeg'.format(self.USER))
            os.rename(image_location, image_location_edit)
            return cv2.imread(image_location_edit)
        except Exception as e:
            logging.exception('Error while getting image, was: {0}'.format(e))
            return

    def get_image_webcam(self):
        try:
            cam_result = self.cam.read()
            if cam_result[0]:
                return cam_result[1]
            self.cam = self._init_cam()
        except Exception as e:
            logging.exception('Error while getting image, was: {0}'.format(e))

    def _init_cam(self):
        try:
            cam_ = cv2.VideoCapture(self.camera_id)
            cam_.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cam_.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            return cam_
        except Exception as e:
            logging.exception('Error while initializing camera, was: {0}'.format(e))
