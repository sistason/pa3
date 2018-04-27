import unittest
from hamcrest import *

from recognition.imagerecognitionTUB import Number


class NumberShould(unittest.TestCase):

    def setUp(self):
        pass

    def test_confidence_basic(self):
        number = Number(0,[])
        number.add_digit(0, 75)

        assert_that(number.confidence, equal_to(75))
        del number

    def test_confidence_computation(self):
        number = Number(0, [])
        number.add_digit(0, 75)
        number.add_digit(0, 50)

        assert_that(number.confidence, equal_to(62.5))
        del number


if __name__ == "__main__":
    unittest.main()