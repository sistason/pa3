#!/usr/bin/env python

import logging
import requests
import json
import os
import re
import time
import numpy as np
import cv2
import sys

# Image processing functions sorted out for better readability
import utils_imgRec as utils

logging.getLogger("requests").setLevel(logging.WARNING)


class ImageRecognitor:
    ACTIVE = True       # Do upload?
    CROP = None         # Manual image crop? None=gets read from settings
    FLIP = 0            # rotate?
    last_numbers = []     # Used to detect duplicates
    last_crop = 0       # Don't crop every image, which doesn't get detected
    flag_upload_picture = False

    def __init__(self, user, client_password='', server_url=''):
        self.USER = user
        self.URL = server_url
        self.PASS = client_password
        if not self._load_settings():
            del self

    def work_image(self, image):
        processing_begin = time.time()
        numbers, image = self.image_processing(image)
        if self.ACTIVE and numbers:
            self.upload(image, numbers, processing_begin)

    def _load_settings(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), 'config_file.json')) as f:
                cfg = json.load(f)
            settings_dict = cfg[self.USER]
            self.NUMBERS = settings_dict['numbers']
            self.RANGES = settings_dict['ranges']
            if 'rotate' in settings_dict.keys():
                self.FLIP = int(settings_dict['rotate'])
            if 'crop' in settings_dict.keys():
                self.CROP = settings_dict['crop']
        except Exception as e:
            logging.exception('Settings malformed! {0}'.format(e))
            return

        # get history from server or generate an empty one
        ret = None
        fails=0
        while fails<3:
            try:
                ret = requests.get('https://{}/api/{}'.format(self.URL, self.USER.split('_')[-1]), verify=False)
                break
            except requests.exceptions.SSLError:
                logging.exception("Certificate Failed")
                return
            except Exception as e:
                # Recursive wait until internet has returned
                logging.exception(e)
                time.sleep(3)
            fails+=1

        if ret:
            print(ret)
            entries = (ret.json())['entries']
            entry = entries[0] if entries else {}
            numbers = entry.get('numbers', [])
            if len(numbers) == self.NUMBERS:
                numbers.sort(key=lambda f:int(re.findall(r'\d+', f['src'])[-1]))
                self.history = [[int(num['number']) for j in range(10)] for num in numbers]
            else:
                self.history = [list(range(10))]
            logging.info('Initial Numbers: {0}'.format(str([num['num'] for num in numbers])))
        else:
            logging.exception('Loading initial numbers failed, initiallizing with zeros')
            self.history = [[0 for j in range(10)] for i in range(self.NUMBERS)]

        current_dir = os.path.dirname(os.path.abspath(__file__))
        try:
            self.TEMPLATE_WHOLE = cv2.imread(os.path.join(current_dir, 'templates', 'template_whole_{}.png'.format(self.USER)), 0)
        except Exception as e:
            logging.exception('Could not load whole template! Error: {0}'.format(e))
            return

        # generate self.ONE_RATIO from template
        try:
            im = cv2.imread(os.path.join(current_dir, 'templates', 'template_digit_{}.png'.format(self.USER)), 0)
            temp_height, temp_width = im.shape
            self.ONE_RATIO = 1.0*temp_width/temp_height
        except Exception as e:
            logging.exception('Could not load digit template! Error: {0}'.format(e))
            self.ONE_RATIO = 0.7

        return True
            
    def _is_number_valid(self, digits, i):
        if not digits or (-1,0) in digits or len(digits) not in [3,4]:
            self.history[i].pop(0)
            self.history[i].append(-1)
            return False

        number_ = int(''.join([str(j[0]) for j in digits]))

        if number_ < self.RANGES[i][0] or number_ > self.RANGES[i][1]:
            logging.debug('{0} not in range {1}-{2}' .format(number_, self.RANGES[i][0], self.RANGES[i][1]))
            self.history[i].pop(0)
            self.history[i].append(-1)
            return False

        # which number occurs the most in the history?
        most=(-1,-1)
        for num in self.history[i]:
            if num > -1:
                occurrence = self.history[i].count(num)
                if occurrence > most[1]:
                    most = (num,occurrence)
        
        # if number is postdecessor of previous and doesn't jump or number has made jumps
        number_seems_okay = ((number_ >= most[0] and number_ <= most[0]+4) or 
                 (most[0] >= self.RANGES[i][1]-4 and number_ <= self.RANGES[i][0]+4))

        self.history[i].pop(0)
        self.history[i].append(number_)

        if number_seems_okay:
            # New, different Numbers need high confidence to be accepted
            if number_ != self.history[i][-1]:
                if len([1 for j in digits if j[1]>50]) != len(digits):
                    return False
            return number_
            
    def image_processing(self, picture):
        """ Number Recognition on the whole picture
        
        Steps:
            1. Find Numbers in the whole picture
            2. Rotate if necessary
            3. Split image / self.NUMBERS to get 3 digits
                4.0 Threshold image to binary
                4.1 Get outer edges (bot:top, right) of image
                4.2 Compute left side and crop fitting
                4.3 Split image / 3 to get 1 digit
                    4.3.1 Get outer edges (left,right)
                    4.3.2 Compute position of the segments
                    4.3.3 Check which segments are set (pixels/area)
                    4.3.x Return digit or lower pixels/area and confidence
        """
        temp_numbers = [[] for i in range(self.NUMBERS)]
        current_numbers = []

        picture = self.preprocess_image(picture)
        if picture is None:
            return '', picture

        img = picture.copy()    # Save picture for uploading later
        height, width = img.shape

        for number in range(self.NUMBERS):
            # Image is cropped, so height/NUMBERS gives the single numbers
            img_ = img.copy()[number*(height/self.NUMBERS):(1+number)*(height/self.NUMBERS),:]

            img_ = self.threshold_image(img_)

            all_current_digits = self.process_image(img_, number)

            current_digits = [i_ for i_ in all_current_digits if i_[0] >= 0]
            valid = self._is_number_valid(current_digits, number)
            if not current_digits:
                avg_confidence = 0
            else:
                avg_confidence = sum([i_[1] for i_ in current_digits])/len(current_digits)
            if valid is not False and valid >= -1:
                logging.info('\tValid!')
                current_numbers.append((valid, avg_confidence))
            else:
                logging.info('Nope: {}'.format(str(all_current_digits)))
                current_numbers.append((-1, avg_confidence))
            
        numbers = ' | '.join(["{0}:{1:.0%}".format(i[0],i[1]/100.0) for i in current_numbers])
        logging.info('Numbers: ### {0} ###'.format(numbers))
        current_numbers_int = [i[0] for i in current_numbers]

        if -1 in current_numbers_int:
            return current_numbers_int, picture
        elif current_numbers_int == self.last_numbers:
            logging.info('same number')
            return current_numbers_int, None
        else:
            self.last_numbers = current_numbers_int
            logging.info("new number")
            return current_numbers_int, picture

    @staticmethod
    def threshold_image(img):
        img = cv2.normalize(img, alpha=0, beta=255, norm_type=cv2.cv.CV_MINMAX, dtype=cv2.cv.CV_8UC1)
        Z = img.reshape((-1,1))
        Z = np.float32(Z)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 1.0)
        ret, label, center = cv2.kmeans(Z, 3, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        center = np.uint8(center)
        res = center[label.flatten()]
        res2 = res.reshape(img.shape)
        brightness_numbers = np.max(res2)
        _, res2 = cv2.threshold(res2, brightness_numbers-1,255, 0)
        logging.debug('thresholding image to {0}'.format(brightness_numbers))
        return res2

    def process_image(self, img_, number):
        """Threshold, find and crop edges, then recognise digits one by one
        """
#        img_ = cv2.threshold(img_, np.max(img_)*(threshold/100.0), 255, 0)[1]

        bot, top, left, right, width_one_number = utils.find_outer_edges(img_, one_ratio=self.ONE_RATIO)
        if not bot and not top and not left and not right:
            return []
        img_ = img_[bot:top,left:right]

        height, width = img_.shape
        if height < 2 or width < 2 or width_one_number < 1:
            # Empty Img or find_outer_edges returned 0 (img[0:0,0:0] == shape = 1)
            logging.debug('find_outer_edges returned 0: TBR: {0} {1} {2}, img: {3}, width_whole: {4}'.format(top, bot, right, img_.shape, right-left))
            return []

        # ------------ Split into digits by splitting the image on the spacing
        w = width
        current_digits = []
        i=0
        while w > 0 and w >= width/40:         #iterate reversed through the width
            if i > 500:
                logging.warning('Strange image, i>500: i={0}, w={1}, width/40:{2}, img:{3}'.format(i, w, width/40, img_.shape))
            i += 1
            for h_ in range(height):
                #If a horizontal strip is found anywhere in the height
                if img_[h_,w-width/40:w].all():
                    digit_width = int(width_one_number)
                    if digit_width > w:
                        digit_width = w
                    #default width: Computed number_width + until empty space (n pixels set per width)
                    #FIXME: IndexError? warum auch immer... how? siehe :262
                    while digit_width < w and np.sum(img_[:,w-digit_width]) > 255*height/20:
                        digit_width += 1
                    current_digits.insert(0, utils.digit_recog(img_[:,w-digit_width:w], one_ratio=self.ONE_RATIO))
                    w -= digit_width
                    break
            else:
                w -= 1
        # On PA H23, a 1 is glued in front to get numbers above 1000
        if self.USER == "pa_23" and number == 2:
            current_digits.insert(0, (1, 100))
        logging.debug('  Digits: {0}'.format(current_digits))
        return current_digits

    def preprocess_image(self, picture_):
        """Flip, findTemplate and crop, scale and rotate
        """
        # Flip image if set in the config

        if self.FLIP:
            (h, w) = picture_.shape[:2]
            (cX, cY) = (w // 2, h // 2)
         
            # grab the rotation matrix (applying the negative of the
            # angle to rotate clockwise), then grab the sine and cosine
            # (i.e., the rotation components of the matrix)
            M = cv2.getRotationMatrix2D((cX, cY), -(self.FLIP), 1.0)
            cos = np.abs(M[0, 0])
            sin = np.abs(M[0, 1])
         
            # compute the new bounding dimensions of the image
            nW = int((h * sin) + (w * cos))
            nH = int((h * cos) + (w * sin))
         
            # adjust the rotation matrix to take into account translation
            M[0, 2] += (nW / 2) - cX
            M[1, 2] += (nH / 2) - cY
         
            # perform the actual rotation and return the image
            picture_ = cv2.warpAffine(picture_, M, (nW, nH))

        if len(picture_.shape) > 2:
            picture_ = cv2.cvtColor(picture_, cv2.cv.CV_BGR2GRAY)

        # Crop image accordingly if history shows many fails
        # Many is defined as 10 numbers in all histories are not recognised
        if not self.CROP or (sum([len([1 for i in h if i == -1]) 
                            for h in self.history]) > (self.NUMBERS*5) and 
                            time.time()-self.last_crop > 10):
            crop = utils.find_nums_in_whole(picture_, self.TEMPLATE_WHOLE)
            if not crop[0]:
                logging.warning('crop was false? camera moved?: {0}'.format(crop[1]))
                return None
            self.CROP = crop
            self.last_crop = time.time()
            logging.info('Cropping image to: {0}'.format(str(crop)))
        picture_ = picture_[self.CROP[1]:self.CROP[3],
                            self.CROP[0]:self.CROP[2]]

        height, width = picture_.shape
        if not (height or width):
            return None

        # Scale down for faster processing
        if width > 200:
            f = 200.0/width
            picture_ = cv2.resize(picture_,None,fx=f, fy=f)

        # Rotate if necessary (many fails in history)
        if sum([len([i for i in h if i == -1]) for h in self.history]) > self.NUMBERS*5:
            return utils.straighten_image(picture_)

        return picture_

    def upload(self, picture, numbers, processing_begin):
        data = {'user': self.USER, 'password': self.PASS, 'ts': int(time.time()),
                'numbers': numbers, 'begin': int(processing_begin)}
        files = {}

        if picture is not None and picture.any():
            _, img_encoded = cv2.imencode('.jpg', picture)
            files = {'raw_image': ('{}.jpeg'.format(self.USER), img_encoded.tostring(), 'image/jpeg', {'Expires': '0'})}

        try:
            requests.post("https://{}/write".format(self.URL), data=data, files=files, verify=False)
        except Exception as e:
            logging.exception("Failed to submit request: {0}".format(e))


if __name__ == '__main__':
    from cv2 import imread
    from sys import argv, exit
    if len(argv) < 3:
        print("missing argument PICTURE or PA! exiting")
        exit(1)
    pic = argv[1]
    pa = argv[2]
    img_rec = ImageRecognitor(pa)
    img_rec.work_image(imread(pic))
