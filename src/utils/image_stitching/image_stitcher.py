import cv2
import os
import glob

def save_all_frames_from_video(video_path, dir_path, basename, ext='jpg'):

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return

    os.makedirs(dir_path, exist_ok=True)
    base_path = os.path.join(dir_path, basename)

    digit = len(str(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))))
    n = 0

    while True:
        ret, frame = cap.read()
        if ret:
            cv2.imwrite('{}_{}.{}'.format(base_path, str(n).zfill(digit), ext), frame)
            n += 1
        else:
            return

def image_stitch(sensitivity_factor, images_folder, ext='jpg'):
    image_path = glob.glob(images_folder + '/*.' + ext)
    image_path = image_path[0::sensitivity_factor]
    images = []

    for image in image_path:
        img = cv2.imread(image)
        images.append(img)
        #cv2.imshow("Image", img)
        #cv2.waitKey(0)

    imageStitcher = cv2.Stitcher_create()

    error, stitched_img = imageStitcher.stitch(images)

    if not error:
        cv2.imwrite("stitchedOutput.png", stitched_img)
        cv2.imshow("Stitched Image", stitched_img)
        #cv2.waitKey(0)