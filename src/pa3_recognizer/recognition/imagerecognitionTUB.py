#!/usr/bin/env python3

from imagerecognition import AbstractImageRecognitor, AbstractNumber

import cv2
import numpy as np
import math
import logging
import time


class Number(AbstractNumber):

    def validate(self):
        if not self._digits:
            return

        number_str = ''
        for digit in self._digits:
            number_str += str(digit) if type(digit) == int and digit != -1 else "?"

        if "?" in number_str:
            self.number = number_str
            logging.debug(' Number "{}" only partly recognized' .format(number_str))
            return

        number_ = int(number_str)

        if number_ < self.valid_range[0] or number_ > self.valid_range[1]:
            logging.debug(' Number "{}" not in range {}' .format(number_, self.valid_range))
            return

        # if history is empty OR number is successor of previous OR is at a range-switch
        number_seems_okay = ((self.previous == -1) or
                             (self.previous <= number_ <= self.previous+4) or
                             (self.previous >= self.valid_range[1]-4 and number_ <= self.valid_range[0]+4))

        if number_seems_okay:
            self.number = number_
            self.valid = True
            # New, different Numbers need high confidence to be accepted
            if number_ != self.previous and not [c for c in self._confidences if c<50]:
                self.new = True


class ImageRecognitor(AbstractImageRecognitor):
    """ Number Recognition on the whole picture
        
        Steps:
            1. Find Numbers in the whole picture
            2. Split image / self.NUMBERS to get single numbers
            3. Threshold image via kmeans
            4. Get single digits by splitting the number at the spaces between
            5. Recognize digits:
                5.1 Get outer edges (left,right)
                5.2 Compute position of the segments
                5.3 Check which segments are set (pixels/area)
            6. Combine digits and validate the resulting number"""

    template = None                         # Keep a copy of the template to modify for this algorithm
    iteration = 0                           # For state/logging purposescd
    position_of_number_table_in_image = []  # Optimization for not always recomputing the position of the number table

    def __init__(self, config):
        super().__init__(config)
        self.fail_histories = [0 for _ in range(config.number_of_numbers)]

    def preprocess_image(self, image):
        self.template = self.config.template.copy()

        # Make sure image is grayscaled
        if len(image.shape) != 2:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        image = self.utils.rotate_image(image, self.config.rotate)

        return image

    def process_image(self, image):
        self.iteration += 1
        numbers = []
        try:
            number_table = self.find_number_table_in_image(image, debug=False)

            for order in range(self.config.number_of_numbers):
                single_number = self.find_single_number_in_number_table(number_table, order, debug=False)
                digit_images = self.find_all_digits_from_single_number(single_number, debug=False)

                if self.fail_histories[order] > 10:
                    self.config.previous_numbers[order] = -1

                number = Number(self.config.previous_numbers[order], self.config.valid_ranges[order])
                for digit_image in digit_images:
                    digit, confidence = self.recognize_single_seven_segment_digit(digit_image)
                    number.add_digit(digit, confidence)

                number.image = single_number
                number.validate()
                if number.valid:
                    self.fail_histories[order] = 0
                    self.config.previous_numbers[order] = number.number
                else:
                    self.fail_histories[order] += 1

                numbers.append(number)

        except Exception as e:
            logging.info('Could not process the image due to an error!', e)
            return []

        return numbers

    def find_single_number_in_number_table(self, image, order, debug=False):
        # height/NUMBER_OF_NUMBERS gives the single numbers
        height, width = image.shape

        split_here = int(height / self.config.number_of_numbers)
        single_number = image.copy()[order*split_here: split_here*(1+order), :]

        if debug:
            print('Single_number: {}'.format(order))
            self.utils.show_image(single_number)
        return single_number

    def find_all_digits_from_single_number(self, single_number, debug=False, iterations=0):
        # ------ Find Area of Interest (the numbers only) ------------
        #       from the borders of the image to the center, checking the
        #       requirements. Saves a findContours and a sort for few pixel
        #       checks.
        image_thresholded = self.utils.threshold_image_simple(single_number)
        image_opened = self.utils.morph_open_image(image_thresholded, iterations=iterations)

        y_max, y_min, _, x_max = self.utils.get_contour_values(image_opened, digits=3)
        image = image_opened[y_min:y_max, :]

        if not x_max or not y_max:
            return []

        digit_images_to_return = self.split_digits_by_sliding_bar(debug, single_number[y_min:y_max, :],
                                                                  image, x_max)
        if len(digit_images_to_return) != self.config.number_of_digits and iterations <= 2:
            return self.find_all_digits_from_single_number(single_number, debug, iterations=iterations+1)

        return reversed(digit_images_to_return)

    def split_digits_by_sliding_bar(self, debug, single_number, image, x_max):
        # Cut out individual numbers by a sliding horizontal window
        digit_images_to_return = []

        height, width = image.shape
        met_empty_space = False
        current_right_edge = x_max
        bar_w = int(height / 30)
        sliding_bar_x = x_max - bar_w
        while sliding_bar_x - bar_w >= 0:
            if not self.utils.is_a_percentage_of_pixels_set(
                    image[:, sliding_bar_x - bar_w:sliding_bar_x + bar_w],
                    bar_w / 100.0):
                met_empty_space = True

            elif met_empty_space:
                single_digit_image = single_number[:, sliding_bar_x + bar_w:current_right_edge]
                if debug:
                    self.utils.show_image(single_digit_image)
                    time.sleep(2)

                digit_images_to_return.append(single_digit_image)

                current_right_edge = sliding_bar_x + bar_w
                met_empty_space = False

            if debug:
                image_temp = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2BGR)
                cv2.rectangle(image_temp, (sliding_bar_x - bar_w, 0), (sliding_bar_x + bar_w, height), (0, 0, 255))
                self.utils.show_image(image_temp)
                time.sleep(0.3)

            sliding_bar_x -= int(math.ceil(width / 200))
        digit_images_to_return.append(single_number[:, 0:current_right_edge])
        return digit_images_to_return

    def find_number_table_in_image(self, image, debug=False):
        """ Find the number table by matchTemplate, crop, scale and rotate it """
        if not self.position_of_number_table_in_image or (self.iteration % 60):
            try:
                # Find template
                result = cv2.matchTemplate(image, self.template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                template_height, template_width = self.template.shape
                self.position_of_number_table_in_image = (max_loc[0], max_loc[1],
                        max_loc[0]+template_width, max_loc[1]+template_height)
            except Exception as e:
                logging.warning('crop was false? camera moved?: {0}'.format(e))

        # Crop image
        logging.debug('Cropping image to: {0}'.format(str(self.position_of_number_table_in_image)))
        _t = self.position_of_number_table_in_image
        number_table = image[_t[1]:_t[3],
                             _t[0]:_t[2]]
        if debug:
            img_temp = cv2.cvtColor(image.copy(), cv2.COLOR_GRAY2BGR)
            cv2.rectangle(img_temp, (_t[0], _t[1]), (_t[2], _t[3]), (0, 255, 0))
            self.utils.show_image(img_temp)

        # Validate image
        height, width = number_table.shape
        if not (height or width):
            raise Exception('Could not find the number table!')

        # Wait for resizing until the template operations are done, since scaling one or the other disables matching
        if width > 200:
            number_table = self.utils.scale_image(number_table, 200.0 / width)

        return number_table

    @staticmethod
    def get_set_segment_percentage(image, digit_mask, color, set_pixels_segment):
        color_lower = np.array([i-5 if i else 0 for i in color])
        color_upper = np.array([i+5 if i else 0 for i in color])
        color_mask = cv2.inRange(digit_mask, color_lower, color_upper)

        set_pixels_image = cv2.countNonZero(cv2.bitwise_and(image, image, mask=color_mask))
        return set_pixels_image / set_pixels_segment

    def recognize_single_seven_segment_digit(self, single_digit, iterations=0, debug=False):

        image_thresholded = self.utils.threshold_image_simple(single_digit)
        image_opened = self.utils.morph_open_image(image_thresholded, iterations=iterations)
        y_max, y_min, _, x_max = self.utils.get_contour_values(image_opened)
        image = image_opened[y_min:y_max, :x_max]

        digit, confidence = self.get_digit_from_segments(image, image_thresholded)
        if digit == -1 and iterations <= 2:
            return self.recognize_single_seven_segment_digit(single_digit, iterations+1)

        return digit, confidence

    def get_digit_from_segments(self, image, image_thresholded):
        # Sanity Checks.
        height, width = image.shape
        if not image.any() or not height or not width or image.size < 0.5*image_thresholded.size:
            return -1, 100

        top_color_bgr = (0, 0, 255)
        top_left_color_bgr = (0, 127, 255)
        top_right_color_bgr = (0, 255, 127)
        mid_color_bgr = (0, 255, 0)
        bot_left_color_bgr = (255, 127, 0)
        bot_right_color_bgr = (127, 255, 0)
        bot_color_bgr = (255, 0, 0)

        seven_segment_positions = [(0, 1, 2, 4, 5, 6),
                                   (2, 5),
                                   (0, 2, 3, 4, 6),
                                   (0, 2, 3, 5, 6),
                                   (1, 2, 3, 5),
                                   (0, 1, 3, 5, 6),
                                   (0, 1, 3, 4, 5, 6),
                                   (0, 2, 5),
                                   (0, 1, 2, 3, 4, 5, 6),
                                   (0, 1, 2, 3, 5, 6)]
        seven_segment_positions_bool = [[True if i in ss_pos else False for i in range(7)]
                                        for ss_pos in seven_segment_positions]

        # add height top/bot until exact size
        mask_unscaled = self.config.digit_mask.copy()
        digit_mask = self.resize_mask_to_image(image, mask_unscaled)
        set_pixels_segment = cv2.countNonZero(cv2.cvtColor(digit_mask, cv2.COLOR_BGR2GRAY))/7

        f = lambda color: self.get_set_segment_percentage(image, digit_mask, color, set_pixels_segment)
        top = f(top_color_bgr)
        top_left = f(top_left_color_bgr)
        top_right = f(top_right_color_bgr)
        mid = f(mid_color_bgr)
        bot_left = f(bot_left_color_bgr)
        bot_right = f(bot_right_color_bgr)
        bot = f(bot_color_bgr)

        segments = [top, top_left, top_right, mid, bot_left, bot_right, bot]

        segments_set_thresholds = {100: 0.2, 75: 0.3, 50: 0.40, 25: 0.50}
        for confidence, threshold in segments_set_thresholds.items():
            segments_set = [seg >= threshold for seg in segments]

            ratings = [(False not in [segments_set[i] == segment_set for i, segment_set in enumerate(ss_pos)])
                       for ss_pos in seven_segment_positions_bool]

            if ratings.count(True) != 1:
                continue

            num = ratings.index(True)

            return num, confidence

        return -1, 0

    def resize_mask_to_image(self, image, mask):
        """
        Resizes the mask to match the image.shape.
        After scaling, the height could be off-by-one (float), so add/remove a row at the bottom.
        The width will be off, so add/remove empty columns left, so the mask gets aligned to the right of the image.
        """
        height, width = image.shape

        mask = self.utils.scale_image(mask, height / mask.shape[0])

        # Add/remove a row at the bottom, if necessary
        if mask.shape[0] > height:
            mask = mask[1:, :]
        if mask.shape[0] < height:
            row_shape = list(mask.shape)
            row_shape[0] = 1
            blank_row = np.zeros(row_shape, np.uint8)
            mask = np.concatenate((blank_row, mask), axis=0)

        # Add/remove columns left, until the mask.width == image.width
        column_shape = list(mask.shape)
        column_shape[1] = 1
        blank_column = np.zeros(column_shape, np.uint8)
        while mask.shape[1] != width:
            mask = mask[:, 1:] if mask.shape[1] > width else np.concatenate((blank_column, mask), axis=1)

        return mask


if __name__ == '__main__':
    import sys
    template = cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    img = cv2.imread(sys.argv[2])

    logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s', level=logging.INFO)

    from waitingnumberrecognition import Configuration
    c = {"valid_ranges": [[0, 999], [0, 999], [0, 999]], "previous_numbers": [448, 719, 71]}
    _config = Configuration(c)
    _config.template = template

    imgrec = ImageRecognitor2015(_config)
    print([str(num) for num in imgrec.recognize(img)])
