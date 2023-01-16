import sys
import os

import matplotlib.pyplot as plt

from src.nml.img_processing.crack_detect import crack_detect_method_1
from src.nml.camera_utils.camera import main_video_stream


def main():
    return "Hello World!"


def main_camera():
    print("Running main camera stream")
    main_video_stream()
    print("Done")


def main_image_proc():
    save_img = "save-img" in sys.argv
    img_paths = [
        os.path.abspath(f"test-images/concrete/original/positive0{i}.jpg")
        for i in range(1, 4)
    ]
    img_paths.append(os.path.abspath("test-images/concrete/original/negative01.jpg"))
    img_paths.append(os.path.abspath("test-images/concrete/original/negative02.jpg"))

    fig, axes = plt.subplots(5, 2)
    fig.suptitle("Original Vs Crack Detection")

    for count, img in enumerate(img_paths):
        src, result = crack_detect_method_1(img_src=img, save_img=save_img)

        axes[count, 0].imshow(src)
        axes[count, 0].set_xticks([]), axes[count, 0].set_yticks([])
        axes[count, 1].imshow(result, cmap="gray")
        axes[count, 1].set_xticks([]), axes[count, 1].set_yticks([])

    plt.show()


if __name__ == "__main__":
    print(main())

    main_camera()
