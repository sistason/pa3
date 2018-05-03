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
        kmeaned = res.reshape(img.shape)
        brightness_numbers = np.max(kmeaned)
        brightness_k = sorted(center)[brightness][0]
        _, res2 = cv2.threshold(img, brightness_k, 255, 0)

        ImageRecognitionUtilities.show_image([image, kmeaned, res2])
        import time; time.sleep(3)

        return res2

    @staticmethod
    def morph_open_image(image, iterations=1):
        if not iterations:
            return image
        kernel = np.array([[0, 1, 0],
                           [1, 1, 1],
                           [0, 1, 0]], dtype=np.uint8)
        image_eroded = cv2.erode(image, kernel, iterations=iterations)
        image_opened = cv2.dilate(image_eroded, kernel, iterations=iterations)
        return image_opened

    @staticmethod
    def get_set_pixels(image):
        height, width = image.shape

        conts_combined = []
        for h in range(height):
            for w in range(width):
                if image.item(h, w) == 255:
                    conts_combined.append((h, w))

        return conts_combined

    def get_contour_values(self, image, strip_size=0):
        bot, top, left, right = 0, 0, 0, 0
        if len(image.shape) != 2:
            logging.warning('image was not thresholded before finding contours!')
            return bot, top, left, right

        height, width = image.shape
        if not strip_size:
            strip_size = int(height / 15)-1

        conts_combined = self.get_set_pixels(image)

        # Get topmost pixel of the relevant part of the image by checking which pixel
        # is part of a bigger vertical pixel segment (i.e. a number)
        # Done by checking if a vertical strip of strip_size image_height is set
        pixels = sorted(conts_combined, key=lambda f: f[0])
        for pixel in pixels:
            if image[pixel[0]:pixel[0]+strip_size, pixel[1]].all():
                top = pixel[0]
                break
            if pixel[0] >= height/2:
                top = pixel[0]
                break
        else:
            top = 0

        for pixel in reversed(pixels):
            if image[pixel[0] - strip_size:pixel[0], pixel[1]].all():
                bot = pixel[0]
                break
            if pixel[0] <= height/2:
                bot = pixel[0]
                break
        else:
            bot = height

        # Get the rightmost pixel for the width via the same algorithm, but horizontally
        pixels = sorted(conts_combined, key=lambda f: f[1], reverse=True)
        for pixel in pixels:
            if image[pixel[0], pixel[1] - strip_size:pixel[1]].all():
                right = pixel[1]
                break
            if pixel[1] <= width/2:
                right = pixel[1]
                break
        else:
            right = width

        for pixel in reversed(pixels):
            if image[pixel[0], pixel[1]:pixel[1] + strip_size].all():
                left = pixel[1]
                break
            if pixel[1] >= width/2:
                left = pixel[1]
                break
        else:
            left = 0

        logging.debug('Found Contours [{}:{}, {}:{}]'.format(bot, top, left, right))
        return bot, top, left, right

    @staticmethod
    def show_image(images):
        if type(images) != list:
            images = [images]

        whitespace = 3
        height = max(image.shape[0] for image in images)
        width = sum(image.shape[1] for image in images)
        images = [cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) != 3 else image for image in images]
        stack = np.zeros((height, width+len(images)*whitespace, 3))

        y = 0
        for image in images:
            h, w = image.shape[:2]

            stack[0:h, y:y + w] = image
            stack[0:h, y+w:y+w+whitespace] = np.ones((h, whitespace, 3))
            y += w+whitespace

        cv2.imwrite('/srv/pa3/current_images/debug_image.png', stack)
        return
        cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('image', 300, 500)
        cv2.imshow('image', stack)
        cv2.waitKey()

