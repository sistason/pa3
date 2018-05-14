#!/usr/bin/env python3
from imagerecognition_utilities import ImageRecognitionUtilities


class AbstractNumber(object):
    """ Base class for storing the resulting number in """
    number = -1
    previous = -1
    confidence = -1

    _digits = None
    _confidences = None
    valid_range = []

    valid = False
    new = False

    image = None

    def __init__(self, previous, valid_range):
        self._digits = []
        self._confidences = []
        self.valid_range = valid_range
        self.previous = previous

    def add_digit(self, digit, confidence):
        self._digits.append(digit)
        self._confidences.append(confidence)
        self.confidence = sum(self._confidences)/len(self._confidences)

    def validate(self):
        raise NotImplementedError

    def __str__(self):
        return "{n.number}@{n.confidence}, {0}".format('valid' if self.valid else 'invalid', n=self)

    def __repr__(self):
        return self.__str__()
        

class AbstractImageRecognitor():
    """ Base class for any image recognition """

    def __init__(self, config):
        self.utils = ImageRecognitionUtilities()
        self.config = config

    def recognize(self, image):
        """ Follow the workflow preprocess -> process and return a list of recognized numbers """

        preprocessed_image = self.preprocess_image(image)
        return self.process_image(preprocessed_image)

    def preprocess_image(self, image):
        raise NotImplementedError

    def process_image(self, image):
        raise NotImplementedError
