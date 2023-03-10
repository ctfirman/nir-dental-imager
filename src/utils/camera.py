import os
import cv2
from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
from typing import Optional

from utils.exceptions import VideoNotOpened
from utils.database import nmlDB


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

        self.frame_width = 640
        self.frame_hight = 480

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
        self.video = cv2.VideoCapture(0)
        print(f"Video = {self.video}")

        if not self.video.isOpened():
            self._video_close()
            self.error_image_signal.emit("Unable to open Video Capture")
            raise VideoNotOpened("Unable to open Video Capture")

        # Emit to allow for recording
        self.camera_available_signal.emit(True)

        # # To set the resolution
        # video.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        # video.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_hight)

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
            frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Save the frame to the video
            # if self._record_flag:
            #     self.video_writer.write(frame)

            # Capture the current image to file
            if self._capture_flag:
                self._capture_flag = False
                self._save_image(frame)
                self.capture_complete_signal.emit(True)

            # Emit the resulting frame
            self.change_image_signal.emit(frame)

        print("Cleaning Up!")
        self._video_close()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self._record_flag = False
        self._capture_flag = False

        self.wait()
