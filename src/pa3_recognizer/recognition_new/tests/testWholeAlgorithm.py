import unittest
from hamcrest import *
import os
from cv2 import imread
from waitingnumberrecognition.imagecreation import ImageCreator
from waitingnumberrecognition.recognition.imagerecognition2015 import ImageRecognitor2015
from waitingnumberrecognition.waitingnumberrecognition import Configuration


class ImageRecognition2015Should(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.abspath(os.path.dirname(__file__))
        test_dir = os.path.join(base_dir, "images/whole/")
        self.template_dir = os.path.join(base_dir, "images/whole/templates/")
        self.image_creator = ImageCreator(path_=test_dir)

    def test_recognize_all_images(self):
        end = False
        while not end:
            image_name, image = self.image_creator.get_image(test=True)
            if image is None:
                end = True
                continue

            full_filename = image_name.split('/')[-1]
            filename, extension = full_filename.split('.')
            numbers, type_ = filename.split('_')

            template_image = imread(os.path.join(self.template_dir, type_+'.'+extension))

            expected = [int(number) for number in numbers.split(',')]
            _c = {'valid_ranges':[[i,i] for i in expected], 'previous_numbers':expected}
            _conf = Configuration(_c)
            _conf.set_template(template_image)
            image_recognitor = ImageRecognitor2015(_conf)

            actual = [n.number for n in image_recognitor.recognize(image)]
            assert_that(actual, equal_to(expected))

if __name__ == "__main__":
    unittest.main()