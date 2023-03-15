import os
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from typing import Optional

from utils.exceptions import VideoNotOpened
from utils.database import nmlDB
from utils.crack_detect import NMLModel


class VideoThread(QThread):
    change_image_signal = pyqtSignal(np.ndarray)
    error_image_signal = pyqtSignal(str)
    camera_available_signal = pyqtSignal(bool)
    capture_complete_signal = pyqtSignal(bool)

    def __init__(self, user_uuid: str, database: nmlDB):
        super().__init__()

        # TODO If bugs need to wrap as mutex or atomics
        self._run_flag = True
        self._record_flag = False
        self._capture_flag = False

        self._DATABASE = database
        self.USER_UUID = user_uuid
        self.img_session_id = 0

        self.frame_width = 1920
        self.frame_hight = 1080

        self.internal_ml_img_counter = 0

    def set_user(self, user_uuid) -> None:
        self.USER_UUID = user_uuid

    # def record_toggle(self) -> None:
    #     # TODO Dont think this is the right way to do it, maybe need to set up signal and slot
    #     if self._record_flag:
    #         # originally True, set to False
    #         self._record_flag = False
    #     else:
    #         # originally False, set to True
    #         self._DATABASE.check_set_filepath(self.USER_UUID)
    #         self.img_session_id = self._DATABASE.insert_new_image_session(
    #             self.USER_UUID
    #         )
    #         self._set_video_writer(self.img_session_id)
    #         self._record_flag = True

    # def _set_video_writer(self, image_session: int) -> None:
    #     # Create the video writer to save video
    #     # (path, codec, fps, size)
    #     self.video_writer = cv2.VideoWriter(
    #         os.path.join(
    #             self._DATABASE.get_base_filepath(self.USER_UUID),
    #             "raw",
    #             f"{image_session}.avi",
    #         ),
    #         cv2.VideoWriter_fourcc("M", "J", "P", "G"),
    #         30,
    #         (self.frame_width, self.frame_hight),
    #     )

    def init_capture_image(self, image_name) -> int:
        self._DATABASE.check_set_filepath(self.USER_UUID)
        self.image_session_id = self._DATABASE.insert_new_image_session(
            self.USER_UUID, image_name
        )
        self._capture_flag = True
        return self.image_session_id

    def _save_image(self, video_frame):
        img_path = os.path.join(
            self._DATABASE.get_base_filepath(self.USER_UUID),
            "raw",
            f"{self.image_session_id}.jpg",
        )
        cv2.imwrite(img_path, video_frame)

    def _video_close(self) -> None:
        self.video.release()
        # TODO error on ubuntu with this
        cv2.destroyAllWindows()

    def run(self):
        self.video = cv2.VideoCapture(1)
        print(f"Video = {self.video}")

        if not self.video.isOpened():
            self._video_close()
            self.error_image_signal.emit("Unable to open Video Capture")
            raise VideoNotOpened("Unable to open Video Capture")

        # Emit to allow for recording
        self.camera_available_signal.emit(True)

        # # To set the resolution
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_hight)

        # Ensure the paths are set to save images
        self._DATABASE.check_set_filepath(self.USER_UUID)

        # # Create the video writer to save video
        # # (path, codec, fps, size)
        # self._set_video_writer(0)

        while self._run_flag:
            success, frame = self.video.read()
            # if frame is read correctly success is True
            if not success:
                print("Can't receive frame. Exiting ...")
                self.error_image_signal.emit("Unable to read from video")
                break

            # Our operations on the frame come here
            # Increase contrast
            frame, alpha, beta = self.automatic_brightness_and_contrast(
                frame, clip_hist_percent=5
            )

            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Save the frame to the video
            # if self._record_flag:
            #     self.video_writer.write(frame)

            # Capture the current image to file
            if self._capture_flag:
                # TODO UNCOMMENT FOR NORMAL FUNCTIONALITY
                # self._capture_flag = False
                # self._save_image(frame)

                # TODO FOR ML DATA CAPTURE REMOVE AFTER
                if self.internal_ml_img_counter >= 10:
                    self._capture_flag = False
                    self.internal_ml_img_counter = 0
                else:
                    self.internal_ml_img_counter += 1
                    print(frame.shape)
                    print(f"alpha = {alpha}, beta = {beta}")
                    NMLModel.get_data_for_ml_v2(frame, self._DATABASE)

                self.capture_complete_signal.emit(True)

            # Emit the resulting frame
            self.change_image_signal.emit(frame)

        print("Cleaning Up!")
        self._video_close()

    # Automatic brightness and contrast optimization with optional histogram clipping
    def automatic_brightness_and_contrast(self, image, clip_hist_percent=1):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate grayscale histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist_size = len(hist)

        # Calculate cumulative distribution from the histogram
        accumulator = []
        accumulator.append(float(hist[0]))
        for index in range(1, hist_size):
            accumulator.append(accumulator[index - 1] + float(hist[index]))

        # Locate points to clip
        maximum = accumulator[-1]
        clip_hist_percent *= maximum / 100.0
        clip_hist_percent /= 2.0

        # Locate left cut
        minimum_gray = 0
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1

        # Locate right cut
        maximum_gray = hist_size - 1
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1

        # Calculate alpha and beta values
        alpha = 255 / (maximum_gray - minimum_gray)
        beta = -minimum_gray * alpha

        auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return (auto_result, alpha, beta)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self._record_flag = False
        self._capture_flag = False

        self.wait()
