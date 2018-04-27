import unittest
from cv2 import imread, IMREAD_GRAYSCALE
from numpy import ndarray
from hamcrest import *
import os
from base64 import b64encode

from recognition.imagerecognitionTUB import ImageRecognitor, Number
from waitingnumberrecognition import Configuration


class RecognitorTUBShould(unittest.TestCase):

    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))

        config = Configuration({})
        template_path = os.path.join(self.base_dir, "images/mask.png")
        with open(template_path, 'rb') as f:
            config.digit_mask = config.decode_template(b64encode(f.read()).decode('utf-8'))

        self.image_recognitor = ImageRecognitor(config)

    def test_read_template(self):
        image_whole = imread(os.path.join(self.base_dir, "images/whole/056_pa_02.jpeg"))
        template_path = os.path.join(self.base_dir, "images/whole/templates/pa_02.jpeg")
        with open(template_path, 'rb') as f:
            template = self.image_recognitor.config.decode_template(b64encode(f.read()).decode('utf-8'))
        self.image_recognitor.config.template = template

        assert_that(type(self.image_recognitor.preprocess_image(image_whole)), equal_to(ndarray))
        assert_that(type(self.image_recognitor.config.template), equal_to(ndarray))

    def test_recognize_digits(self):
        digits_dir = os.path.join(self.base_dir, "images/digits/")
        for digit_file in os.listdir(digits_dir):
            digit_path = os.path.join(digits_dir, digit_file)
            expected_digit_int = int(digit_file.split('_')[0])

            image_digit = imread(digit_path, IMREAD_GRAYSCALE)
            height, width = image_digit.shape

            if width > 35:
                image_digit = self.image_recognitor.utils.scale_image(image_digit, 35.0 / width)

            actual_digit_int = self.image_recognitor.recognize_single_seven_segment_digit(image_digit, debug=False)[0]

            print('{}: {}'.format(expected_digit_int, actual_digit_int))
            # assert_that(actual_digit_int, equal_to(expected_digit_int))
"""
    def test_recognize_numbers(self):
        numbers_dir = os.path.join(self.base_dir, "images/single_numbers/")
        for number_file in os.listdir(numbers_dir):
            expected_number = int(number_file.split('_')[0])
            number_path = os.path.join(numbers_dir, number_file)
            image_number = imread(number_path, IMREAD_GRAYSCALE)
            height, width = image_number.shape

            if width > 100:
                image_number = self.image_recognitor.utils.scale_image(image_number, 100.0 / width)

            actual_number = Number(expected_number, [expected_number, expected_number])
            for digit in self.image_recognitor.find_all_digits_from_single_number(image_number):
                digit_, confidence_ = self.image_recognitor.recognize_single_seven_segment_digit(digit)
                actual_number.add_digit(digit_, confidence_)

            actual_number.validate()
            assert_that(actual_number.number, equal_to(expected_number))
"""

if __name__ == "__main__":
    unittest.main()