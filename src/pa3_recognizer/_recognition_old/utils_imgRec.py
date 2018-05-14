import os
import cv2
import numpy as np
import math
import logging


def find_nums_in_whole(img, template):
    """Find template"""
    try:
        temp_height, temp_width = template.shape

        res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        found_point = list(max_loc)
        found_point.append(max_loc[0]+temp_width)
        found_point.append(max_loc[1]+temp_height)
        return found_point
    except Exception as e:
        return None, e

def find_outer_edges(img, one_ratio=0.7):
    # ------ Find Area of Interest (the numbers only) ------------
    # FIXME: findContours not really neccessary, just manually iterate
    #        from the borders of the image to the center, checking the
    #        requirements. Saves a findContours and a sort for few pixel
    #        checks.

    height, width = img.shape
    img_tmp = img.copy()   #findContours modifies source image!
    _, contours, hierarchy = cv2.findContours(img_tmp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    conts_combined = []
    [[conts_combined.extend(j) for j in i] for i in contours]
    contour_pixels = sorted(conts_combined, key=lambda f:f[1])
    if not contour_pixels:
            logging.debug('No contour found! h:{0}, w:{1}'.format(height, width))
            return None, None, None, None, None
    # Get botmost pixel of a number by only selecting bot contours which 
    # are part of a bigger vertical pixel segment (i.e. a number)
    # Done by checking if a vertical strip of 10% img_height is set
    # Bot is the first pixel, which is located at the top of the image
    for contour in contour_pixels:
        if img[contour[1]+height/10:contour[1],contour[0]].all():
            bot = contour[1]
            break
    else:
        bot = contour_pixels[0][1]

    # Get topmost pixel of a number by only selecting top contours which 
    # are part of a bigger vertical pixel segment (i.e. a number)
    # Done by checking if a vertical strip of 10% img_height is set
    # Top is the last pixel, which is located at the bottom of the image
    for contour in reversed(contour_pixels):
        if img[contour[1]:contour[1]-height/10,contour[0]].all():
            top = contour[1]
            break
    else:
        top = contour_pixels[-1][1]

    # Get the rightmost pixel for the width
    contour_pixels = sorted(conts_combined, key=lambda f:f[0],reverse=True)
    for contour in contour_pixels:
        if img[contour[1],contour[0]-width/40:contour[0]].all():
            right = contour[0]
            break
    else:
        right = contour_pixels[0][0]

    # After having the image height, we get the width of the numbers because
    # the height/width ratio of the numbers are known (and the spacing).
    # Wouldn't be possible without that, since a 1 as first digit would lead
    # to wrong width
    # After computation, widen until there is spacing on the left
    width_height_number_ratio = one_ratio
    width_height_spacing_ratio = one_ratio/2.5
    width_one_number = width_height_number_ratio * (top-bot)
    width_spacing = width_height_spacing_ratio * (top-bot)
    width_whole = int(3*width_one_number + 2*width_spacing)
    width_whole = right if width_whole > right else width_whole
    while width_whole != right and np.sum(img[:,right-width_whole:right]) > 255*height/20:
        width_whole += 1
    left = right-width_whole

    # Cropping crops at these pixels, but we want these pixels included
    return bot, top+1, left, right+1, width_one_number

def straighten_image(img):
    # -- Straighten Image by line detection of the horizontal background structure --
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


def digit_recog(img, one_ratio=0.7):
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
    if np.sum(img[:,0]) > 255*height/20:    #contours cannot find points on the outside border
        left = 0
    else:
        for contour in contour_pixels:
            if img[contour[1],contour[0]:contour[0]+width/10].all():
                left = contour[0]
                break
        else:
            left = contour_pixels[-1][0]

    # Find right border of the digit
    if np.sum(img[:,-1]) > 255*height/20:    #contours cannot find points on the outside border
        right = width
    else:
        for contour in reversed(contour_pixels):
            if img[contour[1],contour[0]-width/10:contour[0]].all():
                right = contour[0]
                break
        else:
            right = contour_pixels[0][0]

    img_num = img[:,left:right]
    height, width = img_num.shape
    # It's a 1, if the ratio is way off the normal width/height
    if 1.0*width/height < one_ratio/2:
        return 1, 100
    # --- Set up the boxes searched for the segments ---
    segment_size_vert, segment_size_horiz = img_num.shape[0]/10.0, img_num.shape[1]/10.0

    top_l, top_r        = 0                              ,    0         +int(segment_size_horiz*2)
    top_mid_l, top_mid_r= int(height/4  -segment_size_vert),  int(height/4  +segment_size_vert)
    mid_l, mid_r        = int(height/2  -segment_size_horiz), int(height/2  +segment_size_horiz)
    bot_mid_l, bot_mid_r= int(3*height/4-segment_size_vert),  int(3*height/4+segment_size_vert)
    bot_l, bot_r        = height - int(segment_size_horiz*2),    height
    left_l, left_r      = 0                             , int(math.floor(0      +segment_size_horiz*2.0))
    center_l, center_r  = int(width/2-segment_size_vert)     , int(width/2+segment_size_vert)
    right_l, right_r    = int(math.ceil(width  -segment_size_horiz*2.0)), width 

#   FIXME: Image mask to scale
    # Digits are not straight, so adapt the segments a bit
    top_segment       = np.mean(img_num[top_l:top_r,         center_l:center_r])
    top_left_segment  = np.mean(img_num[top_mid_l:top_mid_r, left_l+1:left_r+1 ])
    top_right_segment = np.mean(img_num[top_mid_l:top_mid_r, right_l:right_r])
    middle_segment    = np.mean(img_num[mid_l:mid_r,         center_l:center_r])
    bot_left_segment  = np.mean(img_num[bot_mid_l:bot_mid_r, left_l:left_r])
    bot_right_segment = np.mean(img_num[bot_mid_l:bot_mid_r, right_l-1:right_r-1 ])
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
            num=1   # But could/should be recognised before
        else:
            certanty -= 100/len(thresholds)
            continue
        return num, certanty

    return -1, 0

