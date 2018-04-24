#!/usr/bin/env python3

from recognition.imagerecognition import AbstractImageRecognitor, AbstractNumber

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

    template_digit = template_whole = None  # Keep a copy of the template to modify for this algorithm
    iteration = 0                           # For state/logging purposes
    position_of_number_table_in_image = []  # Optimization for not always recomputing the position of the number table

    def __init__(self, config):
        super().__init__(config)
        self.fail_histories = [0 for _ in range(config.number_of_numbers)]

    def preprocess_image(self, image):
        self.template_digit = self.config.template_digit.copy()
        self.template_whole = self.config.template_whole.copy()

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
                digit_images.reverse()

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
        single_number = image.copy()[order*split_here : split_here*(1+order), :]

        single_number = self.utils.threshold_image(single_number)
        if debug:
            print('Single_number: {}'.format(order))
            self.utils.show_image(single_number)
        return single_number

    def find_all_digits_from_single_number(self, img, debug=False):
        # ------ Find Area of Interest (the numbers only) ------------
        # TODO: findContours not really neccessary, just manually iterate
        #       from the borders of the image to the center, checking the
        #       requirements. Saves a findContours and a sort for few pixel
        #       checks.
        height, width = img.shape
        STRIP = int(height/15)

        _, contours, hierarchy = cv2.findContours(img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        conts_combined = []
        [[conts_combined.extend(j) for j in i] for i in contours]
        # Sort 
        contour_pixels = sorted(conts_combined, key=lambda f:f[1])
        if not contour_pixels:
                logging.debug('No contour found! h:{0}, w:{1}'.format(height, width))
                return []

        # Get botmost pixel of a number by only selecting bot contours which 
        # are part of a bigger vertical pixel segment (i.e. a number)
        # Done by checking if a vertical strip of 10% img_height is set
        for contour in contour_pixels:
            if img[contour[1]+STRIP:contour[1],contour[0]].all():
                bot = contour[1]-1
                break
        else:
            # Bot is the first pixel, which is located at the top of the image
            bot = contour_pixels[0][1]

        # Get topmost pixel of a number by only selecting top contours which 
        # are part of a bigger vertical pixel segment (i.e. a number)
        # Done by checking if a vertical strip of 10% img_height is set
        for contour in reversed(contour_pixels):
            if img[contour[1]:contour[1]-STRIP,contour[0]].all():
                top = contour[1]+1
                break
        else:
            # Top is the last pixel, which is located at the bottom of the image
            top = contour_pixels[-1][1]

        # Get the rightmost pixel for the width
        contour_pixels = sorted(conts_combined, key=lambda f:f[0],reverse=True)
        for contour in contour_pixels:
            if img[contour[1],contour[0]-STRIP:contour[0]].all():
                right = contour[0]+1
                break
        else:
            right = contour_pixels[0][0]

        # Cut out individual numbers by a sliding horizontal window
        digit_images_to_return = []
        met_empty_space = False
        current_right_edge = right
        bar_w = int(STRIP/2)
        sliding_bar_x = right-bar_w
        while sliding_bar_x-bar_w >= 0:
            if not self.utils.is_a_percentage_of_pixels_set(img[bot:top, sliding_bar_x-bar_w:sliding_bar_x+bar_w], 0.05):
                met_empty_space = True

            elif met_empty_space:
                single_digit_image = img[bot:top, sliding_bar_x + bar_w:current_right_edge]
                if debug:
                    self.utils.show_image(single_digit_image)
                digit_images_to_return.append(single_digit_image)

                current_right_edge = sliding_bar_x+bar_w
                met_empty_space = False

            if debug:
                img_temp = cv2.cvtColor(img.copy(), cv2.COLOR_GRAY2BGR)
                cv2.rectangle(img_temp, (sliding_bar_x-bar_w, top), (sliding_bar_x+bar_w, bot), (0, 0, 255))
                self.utils.show_image(img_temp)

            sliding_bar_x -= int(math.ceil(width/200))

        digit_images_to_return.append(img[bot:top, 0:current_right_edge])

        return digit_images_to_return

    def find_number_table_in_image(self, image, debug=False):
        """ Find the number table by matchTemplate, crop, scale and rotate it """
        if not self.position_of_number_table_in_image or (self.iteration % 60):
            try:
                #Find template
                result = cv2.matchTemplate(image, self.template_whole, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                template_height, template_width = self.template_whole.shape
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

    def recognize_single_seven_segment_digit(self, img, debug=False):

        height, width = img.shape
        if not img.any() or not height or not width:
            return -1, 0
        _, contours, hierarchy = cv2.findContours(img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        conts_combined = []
        [[conts_combined.extend(j) for j in i] for i in contours]
        contour_pixels = sorted(conts_combined, key=lambda f:f[0])
        if not contour_pixels:
            return -1, 0
        # Find left border of the digit
        if np.sum(img[:,0]) > 255*height/20:    # contours cannot find points on the outside border
            left = 0
        else:
            for contour in contour_pixels:
                if img[contour[1],contour[0]:contour[0]+int(width/10)].all():
                    left = contour[0]
                    break
            else:
                left = contour_pixels[-1][0]

        # Find right border of the digit
        if np.sum(img[:,-1]) > 255*height/20:    # contours cannot find points on the outside border
            right = width
        else:
            for contour in reversed(contour_pixels):
                if img[contour[1],contour[0]-int(width/10):contour[0]].all():
                    right = contour[0]
                    break
            else:
                right = contour_pixels[0][0]

        img_num = img[:,left:right]
        height, width = img_num.shape
        # It's a 1, if the ratio is way off the normal width/height
        if 1.0*width/height < 0.4:
            return 1, 100

        # --- Set up the boxes searched for the segments ---
        segment_size_vert, segment_size_horiz = img_num.shape[0]/10.0, img_num.shape[1]/10.0

        top_l, top_r =          0,                                    0 + int(segment_size_horiz*2)
        top_mid_l, top_mid_r = int(height/4  -segment_size_vert),    int(height/4 + segment_size_vert)
        mid_l, mid_r = int(height/2  -segment_size_horiz),   int(height/2 + segment_size_horiz)
        bot_mid_l, bot_mid_r = int(3*height/4-segment_size_vert),    int(3*height/4 + segment_size_vert)
        bot_l, bot_r = height - int(segment_size_horiz*2),    height
        left_l, left_r      = 0,                                    int(math.floor(0 + segment_size_horiz*2.0))
        center_l, center_r = int(width/2-segment_size_vert), int(width/2+segment_size_vert)
        right_l, right_r    = int(math.ceil(width  -segment_size_horiz*2.0)), width

        top_segment       = np.mean(img_num[top_l:top_r,         center_l:center_r])
        top_left_segment  = np.mean(img_num[top_mid_l:top_mid_r, left_l:left_r ])
        top_right_segment = np.mean(img_num[top_mid_l:top_mid_r, right_l:right_r])
        middle_segment    = np.mean(img_num[mid_l:mid_r,         center_l:center_r])
        bot_left_segment  = np.mean(img_num[bot_mid_l:bot_mid_r, left_l:left_r])
        bot_right_segment = np.mean(img_num[bot_mid_l:bot_mid_r, right_l:right_r ])
        bot_segment       = np.mean(img_num[bot_l:bot_r,         center_l:center_r])

        # --- Get number from segments set ---
        # If segments don't match, repeat with lower threshold (and lower certanty)
        certanty = 100
        thresholds = [255.0/6, 255.0/7, 255.0/8, 255.0/10, 255.0/16, 255.0/24]
        for thres in thresholds:
            top      = top_segment      > thres
            top_left = top_left_segment > thres
            top_right= top_right_segment> thres
            middle   = middle_segment   > thres
            bot_left = bot_left_segment > thres
            bot_right= bot_right_segment> thres
            bot      = bot_segment      > thres

            if debug:
                def _color(correct):
                    return (0, 255, 0) if correct else (0, 0, 255)
                img_temp = cv2.cvtColor(img_num, cv2.COLOR_GRAY2BGR)
                cv2.rectangle(img_temp, (center_l,top_l), (center_r,top_r), _color(top))
                cv2.rectangle(img_temp, (left_l,top_mid_l), (left_r,top_mid_r), _color(top_left))
                cv2.rectangle(img_temp, (right_l,top_mid_l), (right_r,top_mid_r), _color(top_right))
                cv2.rectangle(img_temp, (center_l,mid_l), (center_r,mid_r), _color(middle))
                cv2.rectangle(img_temp, (left_l,bot_mid_l), (left_r,bot_mid_r), _color(bot_left))
                cv2.rectangle(img_temp, (right_l,bot_mid_l), (right_r,bot_mid_r), _color(bot_right))
                cv2.rectangle(img_temp, (center_l,bot_l), (center_r,bot_r), _color(bot))
                self.utils.show_image(img_temp)

            if top and top_left and top_right and middle and bot_left and bot_right and bot:
                num=8
            elif top and top_left and top_right and bot_left and bot_right and bot and not middle:
                num=0
            elif top and top_left and top_right and middle and bot_right and bot and not bot_left:
                num=9
            elif top and top_left and middle and bot_left and bot_right and bot and not top_right:
                num=6
            elif top and top_left and middle and bot_right and bot and not top_right and not bot_left:
                num=5
            elif top and top_right and middle and bot_right and bot and not top_left and not bot_left:
                num=3
            elif top and top_right and middle and bot_left and bot and not top_left and not bot_right:
                num=2
            elif top_left and top_right and middle and bot_right and not top and not bot_left and not bot:
                num=4
            elif top and top_right and bot_right and not top_left and not middle and not bot_left and not bot:
                num=7
            elif top_right and bot_right and not top and not top_left and not middle and not bot_left and not bot:
                num=1   # But should be recognised before
            else:
                certanty -= 100/len(thresholds)
                continue
            return num, certanty

        return -1, 0


if __name__ == '__main__':
    import sys
    template=cv2.imread(sys.argv[1], cv2.IMREAD_GRAYSCALE)
    img=cv2.imread(sys.argv[2])

    logging.basicConfig(format='%(levelname)s:%(funcName)s:%(message)s',
                                                     level=logging.INFO)

    from waitingnumberrecognition.waitingnumberrecognition import Configuration
    c = {"valid_ranges":[[0, 999],[0, 999],[0, 999]], "previous_numbers":[448,719,71]}
    _config = Configuration(c)
    _config.template = template

    i = ImageRecognitor2015(_config)
    print([str(num) for num in i.recognize(img)])
