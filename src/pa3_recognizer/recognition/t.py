#!/usr/bin/env python3

import cv2
from imagerecognition_utilities import ImageRecognitionUtilities

img = cv2.imread("/home/sistason/t/number_2.jpeg", 0)

utils = ImageRecognitionUtilities()
bot, top, left, right = utils.get_contour_values(img)

cv2.imwrite('/home/sistason/t/t.jpeg', img[top:bot, left:right])

