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

    def __init__(self, user_uuid: Optional[str], database: nmlDB):
        super().__init__()
        self._run_flag = True
        self._record_flag = False
        self._DATABASE = database
        self.USER_UUID = user_uuid
        self.img_session_id = 0

        self.frame_width = 640
        self.frame_hight = 480

    def set_user(self, user_uuid) -> None:
        self.USER_UUID = user_uuid

    def record_toggle(self) -> None:
        # TODO Dont think this is the right way to do it, maybe need to set up signal and slot
        if self._record_flag:
            # originally True, set to False
            self._record_flag = False
        else:
            # originally False, set to True
            self.img_session_id = self._DATABASE.insert_new_image_session(
                self.USER_UUID
            )
            self._set_video_writer(self.img_session_id)
            self._record_flag = True

        # update record flag

    def _set_video_writer(self, image_session: int) -> None:
        # Create the video writer to save video
        # (path, codec, fps, size)
        self.video_writer = cv2.VideoWriter(
            os.path.abspath(f"tmp_vid/{self.USER_UUID}/raw/{image_session}.avi"),
            cv2.VideoWriter_fourcc("M", "J", "P", "G"),
            30,
            (self.frame_width, self.frame_hight),
        )

    def _check_set_filepath(self) -> None:
        if not os.path.isdir(os.path.abspath(f"tmp_vid/{self.USER_UUID}/raw")):
            os.makedirs(os.path.abspath(f"tmp_vid/{self.USER_UUID}/raw"))
            os.makedirs(os.path.abspath(f"tmp_vid/{self.USER_UUID}/complete"))

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

        # # To set the resolution
        # video.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        # video.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_hight)

        # Ensure the paths are set to save images
        self._check_set_filepath()

        # Create the video writer to save video
        # (path, codec, fps, size)
        self._set_video_writer(0)

        while self._run_flag:
            success, frame = self.video.read()
            # if frame is read correctly success is True
            if not success:
                print("Can't receive frame. Exiting ...")
                break

            # Save the frame to the video
            if self._record_flag:
                self.video_writer.write(frame)

            # Our operations on the frame come here
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Emit the resulting frame
            self.change_image_signal.emit(frame)

        print("Cleaning Up!")
        self._video_close()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self._record_flag = False
        self.wait()


# def main_video_stream() -> None:
#     frame_width = 640
#     frame_hight = 480

#     video = cv2.VideoCapture(4)
#     print(f"Video = {video}")

#     if not video.isOpened():
#         video_close(video=video)
#         # TODO CHANGE Exception
#         raise VideoNotOpened("Unable to open Video Capture")

#     # # To set the resolution
#     # video.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
#     # video.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_hight)

#     # Create the video writer to save video
#     # (path, codec, fps, size)
#     video_writer = cv2.VideoWriter(
#         os.path.abspath("tmp_vid/test.avi"),
#         cv2.VideoWriter_fourcc("M", "J", "P", "G"),
#         30,
#         (frame_width, frame_hight),
#     )

#     while True:
#         success, frame = video.read()
#         # if frame is read correctly success is True
#         if not success:
#             print("Can't receive frame. Exiting ...")
#             break

#         # Save the frame to the video
#         video_writer.write(frame)

#         # Our operations on the frame come here
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         # Display the resulting frame
#         cv2.imshow("NML", frame)

#         key_press = cv2.waitKey(1) & 0xFF
#         # "q" will break out of the video
#         # "c" will capture a image from the video
#         if key_press == ord("q"):
#             break
#         elif key_press == ord("c"):
#             save_image(frame)

#     print("Cleaning Up!")
#     video_close(video=video)


# def save_image(video_frame) -> None:
#     print("Capturing Image")
#     img_path = os.path.abspath("tmp_img/test.jpg")
#     cv2.imwrite(img_path, video_frame)


# def video_close(video: cv2.VideoCapture) -> None:
#     video.release()
#     cv2.destroyAllWindows()
