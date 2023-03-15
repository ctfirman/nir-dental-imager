import sys
import os
import numpy as np

from utils.gui import run_gui
from utils.database import nmlDB


def main():
    run_gui()


def pull_ml_data():
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


def update_ml_data():
    db = nmlDB("nml.db")
    db.change_ml_data_class_label(5, 15, 20)


if __name__ == "__main__":
    main()
    # update_ml_data()
