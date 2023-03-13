import os
from typing import Tuple, Any, Union, Literal

import cv2
import keras
import numpy as np
from time import time

from PyQt5.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot, QThread

from utils.database import nmlDB


class NMLModel:
    def __init__(self, model_name: str, data_base: nmlDB) -> None:
        self._database = data_base

        self.crack_detect_model = keras.models.load_model(model_name)
        if not self.crack_detect_model:
            raise Exception("Model not found")
        # print(self.crack_detect_model.summary())

    def predict(self, img_path: str) -> Union[Literal[0], Literal[1]]:
        cropped_img = self.ml_img_crop(img_path)

        # flatten and reduce img to pass into model
        reduced_img = []
        for row in cropped_img:
            reduced = []
            for col in row:
                reduced.append(col[0])
            reduced_img.append(reduced)
        reduced_img = np.array(reduced_img).flatten()
        reduced_img = np.array([reduced_img])

        # prediction = self.crack_detect_model.predict(reduced_img)[0]  # type: ignore
        prediction = self.crack_detect_model(reduced_img)[0]  # type: ignore

        print(prediction)
        if np.argmax(prediction):
            return 1
        else:
            return 0

    @classmethod
    def ml_img_crop(cls, img_path: str) -> np.ndarray:
        img = cv2.imread(img_path)
        y = 245  # Starting at top
        x = 187  # Starting at left
        h = 158  # Height
        w = 158  # Width
        crop = img[y : y + h, x : x + w]
        return crop

    @classmethod
    def get_data_for_ml(cls, user_uuid, session_id, db: nmlDB):
        img_filepath = os.path.join(
            nmlDB.get_base_filepath(user_uuid), "raw", f"{session_id}.jpg"
        )
        print(img_filepath)

        croped_img_arr = cls.ml_img_crop(img_filepath)
        reduced_img = []
        for row in croped_img_arr:
            reduced = []
            for col in row:
                reduced.append(col[0])
            reduced_img.append(reduced)

        reduced_img = np.array(reduced_img)
        reduced_img = reduced_img.tobytes()

        # db.insert_ml_data(reduced_img, 1)
        # db.get_ml_data_len()

        # first_entry = np.frombuffer(db.get_first_ml_data().img, dtype=np.uint8)
        # print(first_entry.shape)


class CrackDetectHighlightSignals(QObject):
    finished = pyqtSignal(str)


class CrackDetectHighlight(QRunnable):
    def __init__(self, database: nmlDB, img_session_id: int, user_uuid: str):
        super().__init__()
        # Need to do this as db session will fail if called multiple times
        self._database = nmlDB("nml.db")
        self.image_session_id = img_session_id
        self.user_uuid = user_uuid
        self.signals = CrackDetectHighlightSignals()
        self.continueThread = True

    @classmethod
    def crop(cls, img):

        y = 257  # Starting at top
        x = 197  # Starting at left
        h = 130  # Height
        w = 146  # Width

        crop = img[y : y + h, x : x + w]
        # cv2.imshow('image', crop)
        # cv2.waitKey(0)

        return crop

    def crack_detect_method_1(self):
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

        print("Running crack detection...")

        raw_img_path = os.path.join(
            self._database.get_base_filepath(self.user_uuid),
            "raw",
            f"{self.image_session_id}.jpg",
        )
        completed_img_path = os.path.join(
            self._database.get_base_filepath(self.user_uuid),
            "complete",
            f"{self.image_session_id}.jpg",
        )

        # Get absolute path of session_id, which is the image
        src = cv2.imread(raw_img_path)

        # Crop the image to hone in on the tooth
        cropped_img = self.crop(src)

        blur = cv2.GaussianBlur(cropped_img, (5, 5), 0)

        # Apply logarithmic transform
        img_log = (np.log(blur + 1) / (np.log(1 + np.max(blur)))) * 255

        # Specify the data type
        img_log = np.array(img_log, dtype=np.uint8)

        # Image smoothing: bilateral filter
        bilateral = cv2.bilateralFilter(img_log, 10, 22, 22)  # original: 45, 22, 22

        # Run Canny Edge Detector
        edges = cv2.Canny(bilateral, 20, 20)  # original:  20, 20

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
        # test keypoints

        # Makes the highlighted cracks red
        result[np.where((result == [255, 255, 255]).all(axis=2))] = [0, 0, 255]

        # Overlay detected cracks onto original image
        final_image = cv2.addWeighted(cropped_img, 0.6, result, 1, 0)
        cv2.imwrite(completed_img_path, final_image)

        print("Finished crack detection!")

    def cropped_image_save(self):

        raw_img_path = os.path.join(
            self._database.get_base_filepath(self.user_uuid),
            "raw",
            f"{self.image_session_id}.jpg",
        )
        completed_img_path = os.path.join(
            self._database.get_base_filepath(self.user_uuid),
            "complete",
            f"{self.image_session_id}-cropped.jpg",
        )

        # Get absolute path of session_id, which is the image
        src = cv2.imread(raw_img_path)

        # Crop the image to hone in on the tooth
        cropped_img = self.crop(src)
        cv2.imwrite(completed_img_path, cropped_img)

    @pyqtSlot()
    def run(self):

        # TODO: determine if we can pass and share the model between worker threads or each thread loads their own
        raw_img_path = os.path.join(
            self._database.get_base_filepath(self.user_uuid),
            "raw",
            f"{self.image_session_id}.jpg",
        )
        completed_img_path = os.path.join(
            self._database.get_base_filepath(self.user_uuid),
            "complete",
            f"{self.image_session_id}.jpg",
        )

        # load model
        self.model = NMLModel("nmlModelV2", self._database)
        # predict the crack
        ml_result = self.model.predict(raw_img_path)
        # Update the database
        self._database.update_img_session_crack_detection(
            self.image_session_id, ml_result
        )

        if ml_result:
            print("Crack Detected")

        else:
            print("No Crack")

        self.crack_detect_method_1()
        self.cropped_image_save()

        # emit the finished signal to update image selector list
        self.signals.finished.emit(str(self.image_session_id))

        while self.continueThread:
            QThread.sleep(1)

    def stop_thread(self):
        self.continueThread = False


# if __name__ == "__main__":
# crack_detect_method_1(1677963412788, "7e246217-c7b8-4b93-84ca-5c8319214db1", True)
