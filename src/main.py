import sys
import os
import numpy as np

# import matplotlib.pyplot as plt

# from utils.crack_detect import crack_detect_method_1
# from utils.camera import main_video_stream

from utils.gui import run_gui
from utils.database import nmlDB


def main():
    run_gui()


# def main_camera():
#     print("Running main camera stream")
#     main_video_stream()
#     print("Done")


# def main_image_proc():
#     save_img = "save-img" in sys.argv
#     img_paths = [
#         os.path.abspath(f"test-images/concrete/original/positive0{i}.jpg")
#         for i in range(1, 4)
#     ]
#     img_paths.append(os.path.abspath("test-images/concrete/original/negative01.jpg"))
#     img_paths.append(os.path.abspath("test-images/concrete/original/negative02.jpg"))

#     fig, axes = plt.subplots(5, 2)
#     fig.suptitle("Original Vs Crack Detection")

#     for count, img in enumerate(img_paths):
#         src, result = crack_detect_method_1(img_src=img, save_img=save_img)

#         axes[count, 0].imshow(src)
#         axes[count, 0].set_xticks([]), axes[count, 0].set_yticks([])
#         axes[count, 1].imshow(result, cmap="gray")
#         axes[count, 1].set_xticks([]), axes[count, 1].set_yticks([])

#     plt.show()


if __name__ == "__main__":
    # main()

    db = nmlDB("nml.db")

    all_classifier_list = []
    all_data_list = []

    all_crack = db.get_all_ml_data("CRACK")
    for entry in all_crack:
        after_img = np.frombuffer(entry.img, dtype=np.uint8)
        all_classifier_list.append(entry.classifier)
        all_data_list.append(after_img)

    no_crack = db.get_all_ml_data("NO_CRACK")
    for entry in no_crack:
        after_img = np.frombuffer(entry.img, dtype=np.uint8)
        all_classifier_list.append(entry.classifier)
        all_data_list.append(after_img)

    np.save("test_data.npy", all_data_list)
    np.save("test_classifiers.npy", all_classifier_list)

    data = np.load("test_data.npy")
    classifiers = np.load("test_classifiers.npy")
    print(f"data shape = {data.shape}")
    print(f"data example = {data}")

    print(f"classifiers shape = {classifiers.shape}")
    print(f"classifiers example = {classifiers}")
