import os

import cv2
import numpy as np
import matplotlib.pyplot as plt


def crack_detect_method_1(img_src: str) -> None:
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
    print(img_src)

    src = cv2.imread(img_src)
    # cv2.imshow("input", src)

    gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("gray", gray)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # cv2.imshow("blur", blur)

    # Apply logarithmic transform
    img_log = (np.log(blur + 1) / (np.log(1 + np.max(blur)))) * 255

    # Specify the data type
    img_log = np.array(img_log, dtype=np.uint8)
    # cv2.imshow("img_log", img_log)

    # Image smoothing: bilateral filter
    bilateral = cv2.bilateralFilter(img_log, 5, 10, 10)
    # cv2.imshow("bilateral", bilateral)

    # ret, binary = cv2.threshold(
    #     bilateral, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    # )
    # cv2.imshow("binary", binary)

    # Canny Edge Detection
    # max value will be half of max - min from bilateral

    # TODO: Figure out why bilateral image won't work
    # edges = cv2.Canny(blur, 100, 150)
    edges = cv2.Canny(bilateral, 25, 50)
    # cv2.imshow("edges", edges)

    # Morphological Closing Operator
    kernel = np.ones((5, 5), np.uint8)
    closing = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    # cv2.imshow("closing", closing)

    # Create feature detecting method
    # sift = cv2.xfeatures2d.SIFT_create()
    # surf = cv2.xfeatures2d.SURF_create()
    orb = cv2.ORB_create(nfeatures=1500)

    # Make featured Image
    keypoints, descriptors = orb.detectAndCompute(closing, None)
    result = cv2.drawKeypoints(closing, keypoints, None)
    # cv2.imshow("result", result)

    img_file_name = os.path.basename(img_src)
    final_img_path = os.path.abspath(f"test-images/concrete/completed/{img_file_name}")
    # cv2.imwrite(final_img_path, result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return src, result
