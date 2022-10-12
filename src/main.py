import sys
import os

from crack_detect.crack_detect import crack_detect_method_1


def main():
    return "Hello World!"


if __name__ == "__main__":
    print(main())

    img_path = sys.argv
    if len(img_path) > 1:
        img_path = os.path.abspath(f"test-images/concrete/{img_path[1]}")
    else:
        img_path = os.path.abspath(f"test-images/concrete/00019.jpg")

    crack_detect_method_1(img_src=img_path)
