import unittest
from hamcrest import *
import os
from base64 import b64encode
from cv2 import imread

from imagerecognitionTUB import ImageRecognitor
from waitingnumberrecognition import Configuration


class ImageRecognitionTUBShould(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        template_dir = os.path.join(self.base_dir, "images/whole/templates/")
        template_path = os.path.join(self.base_dir, "images/mask.png")
        self.digit_mask = self.get_template(template_path)
        self.templates = dict(((i.rsplit('.', 1)[0],
                               self.get_template(os.path.join(template_dir, i),
                                                 gray=True)) for i in os.listdir(template_dir)))

    def get_template(self, template_path, gray=False):
        with open(template_path, 'rb') as f:
            return Configuration.decode_template(b64encode(f.read()).decode('utf-8'), gray=gray)

    def test_recognize_all_images(self):
        test_dir = os.path.join(self.base_dir, "images/whole/")
        for whole_image_file in os.listdir(test_dir):
            whole_image_path = os.path.join(test_dir, whole_image_file)
            if not os.path.isfile(whole_image_path):
                continue
            whole_image = imread(whole_image_path)

            filename, extension = whole_image_file.split('.')
            numbers, type_ = filename.split('_', 1)

            expected = [int(number) for number in numbers.split(',')]
            _c = {'ranges':[[i-10, i+10] for i in expected], 'current_numbers': [{'number': e} for e in expected], 'digits': 3}

            config = Configuration(_c)
            config.digit_mask = self.digit_mask
            config.template = self.templates.get(type_)
            image_recognitor = ImageRecognitor(config)

            actual = [n.number for n in image_recognitor.recognize(whole_image)]
            assert_that(actual, equal_to(expected))

if __name__ == "__main__":
    unittest.main()