import os
from typing import Tuple, Any

import cv2
import numpy as np


# input is image from the raw capture
# output is a processed image in the complete folder

def crack_detect_method_1(session_id: str, save_img: bool = False) -> Tuple[Any, Any]:
    """
    Algo from https://github.com/shomnathsomu/crack-detection-opencv
    1. read image
    2. Gray scale and average
    3. log transform
    4. Image smoothing: bilateral filter
    5. Image segmentation Techniques
        - Canny edge detection
        - Morphological closing operator
        - Feature extraction
    """
    # Get absolute path of session_id, which is the image
    img_src = os.path.abspath(session_id)
    print(img_src)

    src = cv2.imread(img_src)
    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply logarithmic transform
    img_log = (np.log(blur + 1) / (np.log(1 + np.max(blur)))) * 255

    # Specify the data type
    img_log = np.array(img_log, dtype=np.uint8)

    # Image smoothing: bilateral filter
    bilateral = cv2.bilateralFilter(img_log, 15, 30, 30)   # 45, 22, 22

    # Run Canny Edge Detector
    edges = cv2.Canny(bilateral, 20, 20)   # 20, 20

    # Morphological Closing Operator
    kernel = np.ones((5, 5), np.uint8)
    closing = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Create feature detecting method
    # sift = cv2.xfeatures2d.SIFT_create()
    # surf = cv2.xfeatures2d.SURF_create()
    orb = cv2.ORB_create(nfeatures=2)

    # Make featured Image
    keypoints, descriptors = orb.detectAndCompute(closing, None)
    result = cv2.drawKeypoints(closing, keypoints, None)

    if save_img:
        img_file_name = os.path.basename(img_src)
        # final_img_path = os.path.abspath(
        #     f"test-images\concrete\completed\{img_file_name}"
        # )
        #final_img_path = os.chdir("/complete/" + img_file_name)
        final_img_path = os.path.abspath(os.path.join(os.path.dirname(img_src), "..", "complete/" + img_file_name))

        #print(final_img_path)
        cv2.imwrite(final_img_path, result)

    cv2.destroyAllWindows()

    return src, result

def crop(img_src: str):
    img = cv2.imread(img_src)
    y=245 # Starting at top
    x=187 # Starting at left
    h=158 # Height
    w=158 # Width
    crop = img[y:y+h, x:x+w]
    cv2.imshow('image', crop)
    cv2.waitKey(0)
    #cv2.imwrite(img_src, crop)

if __name__ == "__main__":
    crop(r"C:\Users\TirthPatel\Desktop\Tirth\NMLai\src\nml_img\eae2d22d-eb2c-46e5-8d03-5f29c10d9a2b\raw\1677959162446.jpg")
    #crack_detect_method_1(r"C:\Users\TirthPatel\Desktop\Tirth\NMLai\src\nml_img\eae2d22d-eb2c-46e5-8d03-5f29c10d9a2b\raw\1677958109315.jpg", True)



