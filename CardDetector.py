import cv2 as cv
import imagehash
import numpy as np
from PIL import Image


def image_resize(image, width=800, height = None, interp = cv.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]


    if width is None and height is None:
        return image

    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)

    else:
        r = width / float(w)
        dim = (width, int(h * r))


    resized = cv.resize(image, dim, interpolation = interp)
    return resized



def histogram_equalization(image):
    clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))

    lab_image = cv.cvtColor(image, cv.COLOR_BGR2LAB)

    l, r, y = cv.split(lab_image)
    l_adjusted = clahe.apply(l)

    adjusted_lab_image = cv.merge((l_adjusted, r, y))
    adjusted_image = cv.cvtColor(adjusted_lab_image, cv.COLOR_LAB2BGR)

    return adjusted_image


def preprocess(image, mode='otsu'):
    resized = image_resize(image)
    equalized = histogram_equalization(resized)
    
    gray = cv.cvtColor(equalized, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (3,3), 0)
    
    if mode == 'binary':
        thresh = cv.threshold(blur, 70, 255, cv.THRESH_BINARY)[1]

    if mode == 'adaptive': 
        thresh = cv.adaptiveThreshold(blur, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 10)
    
    if mode == 'binary_otsu':
        thresh = cv.threshold(blur, 70, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)[1]
    
    if mode == 'otsu':
        thresh = cv.threshold(blur, 70, 255, cv.THRESH_OTSU)[1]

    return thresh



def warp(image, points):
    # TODO: Perspective transform for different card orientations

    temp_rect = np.zeros((4, 2), dtype='float32')
    s = np.sum(points, axis=2)

    top_left = points[np.argmin(s)]
    bottom_right = points[np.argmax(s)]

    difference = np.diff(points, axis = -1)
    top_right = points[np.argmin(difference)]
    bottom_left = points[np.argmax(difference)]

    temp_rect[0] = top_left
    temp_rect[1] = top_right
    temp_rect[2] = bottom_right
    temp_rect[3] = bottom_left

    max_width = 476
    max_height = 664

    dest_array = np.array([[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]], np.float32)
    perspective = cv.getPerspectiveTransform(temp_rect, dest_array)

    warped = cv.warpPerspective(image, perspective, (max_width, max_height))

    return warped



def segmentation(image, original):
    contours, _ = cv.findContours(image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contours_sorted = sorted(contours, key=cv.contourArea, reverse=True)
    card_contour = contours_sorted[1]

    # perimeter and approximate corner points
    perimeter = cv.arcLength(card_contour, True)
    approximate_points = cv.approxPolyDP(card_contour, 0.01 * perimeter, True)
    points = np.float32(approximate_points)

    # x, y, w, h = cv.boundingRect(card_contour)

    warped_image = warp(original, points)
    return warped_image


def detect(image):
    try:
        original_hash = imagehash.phash(Image.fromarray(image), 16)
        processed_hash_otsu = imagehash.phash(Image.fromarray(preprocess(image, mode='otsu')), 16)
        processed_hash_binary_otsu = imagehash.phash(Image.fromarray(preprocess(image, mode='binary_otsu')), 16)
        processed_hash_binary = imagehash.phash(Image.fromarray(preprocess(image, mode='binary')), 16)
        processed_hash_adaptive = imagehash.phash(Image.fromarray(preprocess(image, mode='adaptive')), 16)


        original_hash_int = int(str(original_hash), 16)
        processed_hash_otsu_int = int(str(processed_hash_otsu), 16)
        processed_hash_binary_otsu_int = int(str(processed_hash_binary_otsu), 16)
        processed_hash_binary_int = int(str(processed_hash_binary), 16)
        processed_hash_adaptive_int = int(str(processed_hash_adaptive), 16)


        return original_hash_int, processed_hash_otsu_int, processed_hash_binary_otsu_int, processed_hash_binary_int, processed_hash_adaptive_int
    except:
        return None, None, None, None, None