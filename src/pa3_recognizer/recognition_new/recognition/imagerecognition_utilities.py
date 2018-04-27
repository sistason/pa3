import numpy as np
import cv2
import logging


class ImageRecognitionUtilities:

    @staticmethod
    def rotate_image(image, rotation):
        if not rotation:
            return image

        (h, w) = image.shape[:2]
        (cX, cY) = (w // 2, h // 2)

        # grab the rotation matrix (applying the negative of the
        # angle to rotate clockwise), then grab the sine and cosine
        # (i.e., the rotation components of the matrix)
        M = cv2.getRotationMatrix2D((cX, cY), -(rotation), 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])

        # compute the new bounding dimensions of the image
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))

        # adjust the rotation matrix to take into account translation
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY

        # perform the actual rotation and return the image
        return cv2.warpAffine(image, M, (nW, nH))

    @staticmethod
    def is_a_percentage_of_pixels_set(image, percentage):
        percentage = percentage if type(percentage) == float else percentage / 100.0
        return np.sum(image) >= image.size * 255 * percentage

    @staticmethod
    def scale_image(image, factor):
        """ Scale down for faster processing """
        return cv2.resize(image,None,fx=factor, fy=factor)

    @staticmethod
    def straighten_image(img):
        """ Straighten Image by line detection of the horizontal background structure """
        img_temp = cv2.threshold(img.copy(), np.min(img)+15, 255, 0)[1] #thresholing to get only the background
        # Canny Filter for the Hough Line Generatior
        try:
            edges = cv2.Canny(img_temp, 50, 200, 50)
        except TypeError:
            return img
        # Get lines > 60 threshold, resolution 1 deg, for every pixel in the img
        lines = cv2.HoughLines(edges, 1, np.pi/180, 60)
        # Filter out vertical lines
        mean_rotation = 0
        if lines is not None:
            rotations = np.array([l[1] for l in lines[0] if l[1] <= np.pi/1.5 or l[1] >= np.pi/3])
            mean_rotation = np.mean(rotations)-np.pi/2

        # Rotate image (rot - 3/4*pi to convert vertical to horizontal rot)
        if mean_rotation > np.pi/90:
            height, width = img_temp.shape[:2]
            rot_mat = cv2.getRotationMatrix2D((height/2,width/2),mean_rotation,1.0)
            img = cv2.warpAffine(img, rot_mat, (int(width*1.5),int(width*(1.5))))

        return img

    @staticmethod
    def threshold_image(image, k=1, brightness=-1):
        img = image.copy()
        cv2.normalize(image, img, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        Z = img.reshape((-1, 1))
        Z = np.float32(Z)

        label = np.array(img)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        ret, label, center = cv2.kmeans(Z, k, label, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        center = np.uint8(center)
        res = center[label.flatten()]
        res2 = res.reshape(img.shape)
        brightness_numbers = np.max(res2)
        brightness_k = sorted(center)[brightness][0]
        _, res2 = cv2.threshold(img, brightness_k, 255, 0)
        logging.debug('Thresholding image to {0}'.format(brightness_numbers))
        return res2

    @staticmethod
    def morph_open_image(image, iterations=1):
        kernel = np.array([[0, 1, 0],
                           [1, 1, 1],
                           [0, 1, 0]], dtype=np.uint8)
        image_eroded = cv2.erode(image, kernel, iterations=iterations)
        image_opened = cv2.dilate(image_eroded, kernel, iterations=iterations)
        return image_opened

    @staticmethod
    def get_contour_values(image, strip_size=0):
        height, width = image.shape
        if not strip_size:
            strip_size = int(height / 15)

        # TODO: findContours not really neccessary, just manually iterate
        _, contours, hierarchy = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        conts_combined = []
        [[conts_combined.extend(j) for j in i] for i in contours]
        # Sort
        contour_pixels = sorted(conts_combined, key=lambda f: f[1])
        if not contour_pixels:
            logging.debug('No contour found! h:{}, w:{}'.format(*image.shape))
            return 0, 0, 0, 0

        # Get botmost pixel of a number by only selecting bot contours which
        # are part of a bigger vertical pixel segment (i.e. a number)
        # Done by checking if a vertical strip of 10% image_height is set
        for contour in contour_pixels:
            if image[contour[1] + strip_size:contour[1], contour[0]].all():
                bot = contour[1] - 1
                break
        else:
            bot = contour_pixels[0][1]

        # Get topmost pixel of a number by only selecting top contours which
        # are part of a bigger vertical pixel segment (i.e. a number)
        # Done by checking if a vertical strip of 10% image_height is set
        for contour in reversed(contour_pixels):
            if image[contour[1]:contour[1] - strip_size, contour[0]].all():
                top = contour[1] + 1
                break
        else:
            top = contour_pixels[-1][1]

        # Get the rightmost pixel for the width
        contour_pixels = sorted(conts_combined, key=lambda f: f[0], reverse=True)
        if np.sum(image[:, -1]) > 255*strip_size: # contours cannot find points on the outside border, so check manually
            right = width
        else:
            for contour in contour_pixels:
                if image[contour[1], contour[0] - strip_size:contour[0]].all():
                    right = contour[0] + 1
                    break
            else:
                right = contour_pixels[0][0]

        # Find left border of the digit
        contour_pixels = sorted(conts_combined, key=lambda f: f[0])
        if np.sum(image[:, 0]) > 255*strip_size: # contours cannot find points on the outside border, so check manually
            left = 0
        else:
            for contour in contour_pixels:
                if image[contour[1], contour[0]:contour[0]+strip_size].all():
                    left = contour[0]
                    break
            else:
                left = contour_pixels[-1][0]

        return bot, top, left, right

    @staticmethod
    def show_image(images):
        if type(images) != list:
            images = [images]

        height = max(image.shape[0] for image in images)
        width = sum(image.shape[1] for image in images)
        images = [cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) != 3 else image for image in images]
        stack = np.zeros((height, width, 3))

        y = 0
        for image in images:
            h, w = image.shape[:2]
            stack[0:h, y:y + w] = image
            y += w

        cv2.imwrite('/srv/pa3/current_images/debug_image.png', stack)
        return
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('image', 300, 500)
        cv2.imshow('image', stack)
        cv2.waitKey()

