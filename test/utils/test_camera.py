import os
import pytest
from unittest.mock import patch, Mock, ANY, call

from src.utils.camera import (
    VideoNotOpened,
    VideoThread,
)
from src.utils.database import nmlDB

test_db = nmlDB(":memory:")
test_VideoThread = VideoThread("test-uuid", test_db)

test_VideoThread._DATABASE = Mock()
test_VideoThread._DATABASE.check_set_filepath
test_VideoThread._DATABASE.get_base_filepath.return_value = "base-path"

test_VideoThread.error_image_signal = Mock()
test_VideoThread.error_image_signal.emit

test_VideoThread.change_image_signal = Mock()
test_VideoThread.change_image_signal.emit

test_VideoThread.camera_available_signal = Mock()
test_VideoThread.camera_available_signal.emit

test_VideoThread.capture_complete_signal = Mock()
test_VideoThread.capture_complete_signal.emit

# test_VideoThread.video_writer = Mock()
# test_VideoThread.video_writer.write

mocked_video_not_opened = Mock()
mocked_video_not_opened.isOpened.return_value = False
mocked_video_not_opened.read.return_value = (False, None)


@patch("src.utils.camera.VideoThread._save_image")
@patch("src.utils.camera.VideoThread._video_close")
@patch("cv2.rotate", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_not_opened)
def test_VideoThread_run_not_opened(
    VideoCapture_mock, cvtRotate_mock, video_close_mock, save_image_mock
):
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.check_set_filepath
    with pytest.raises(VideoNotOpened) as e_info:
        test_VideoThread.run()

    VideoCapture_mock.assert_called_once_with(ANY)
    video_close_mock.assert_called_once_with()
    test_VideoThread.error_image_signal.emit.assert_called_once_with(
        "Unable to open Video Capture"
    )
    assert "Unable to open Video Capture" in str(e_info.value)
    mocked_video_not_opened.isOpened.assert_called_once()
    mocked_video_not_opened.read.assert_not_called()

    test_VideoThread._DATABASE.check_set_filepath.assert_not_called()
    cvtRotate_mock.assert_not_called()
    test_VideoThread.change_image_signal.emit.assert_not_called()
    test_VideoThread.camera_available_signal.emit.assert_not_called()
    test_VideoThread.capture_complete_signal.emit.assert_not_called()
    save_image_mock.assert_not_called()


mocked_video_no_run_flag = Mock()
mocked_video_no_run_flag.isOpened.return_value = True
mocked_video_no_run_flag.read.return_value = (False, None)


@patch("src.utils.camera.VideoThread._save_image")
@patch("src.utils.camera.VideoThread._video_close")
@patch("cv2.rotate", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_no_run_flag)
def test_VideoThread_run_no_run_flag(
    VideoCapture_mock, cvtRotate_mock, video_close_mock, save_image_mock
):
    test_VideoThread.USER_UUID = "test-uuid-no-run-flag"
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.check_set_filepath
    test_VideoThread._run_flag = False
    test_VideoThread.run()
    test_VideoThread._run_flag = True

    VideoCapture_mock.assert_called_once_with(ANY)
    video_close_mock.assert_called_once_with()

    test_VideoThread._DATABASE.check_set_filepath.assert_called_once_with(
        "test-uuid-no-run-flag"
    )

    mocked_video_no_run_flag.isOpened.assert_called_once()
    mocked_video_no_run_flag.read.assert_not_called()
    cvtRotate_mock.assert_not_called()
    test_VideoThread.change_image_signal.emit.assert_not_called()
    test_VideoThread.capture_complete_signal.emit.assert_not_called()
    test_VideoThread.camera_available_signal.emit.assert_has_calls([call(True)])
    save_image_mock.assert_not_called()


mocked_video_no_read = Mock()
mocked_video_no_read.isOpened.return_value = True
mocked_video_no_read.read.return_value = (False, None)


@patch("src.utils.camera.VideoThread._save_image")
@patch("src.utils.camera.VideoThread._video_close")
@patch("cv2.rotate", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_no_read)
def test_VideoThread_run_no_read(
    VideoCapture_mock, cvtRotate_mock, video_close_mock, save_image_mock
):
    test_VideoThread.USER_UUID = "test-uuid-no-read"
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.check_set_filepath
    test_VideoThread.run()

    VideoCapture_mock.assert_called_once_with(ANY)
    video_close_mock.assert_called_once_with()

    mocked_video_no_read.isOpened.assert_called_once()
    test_VideoThread._DATABASE.check_set_filepath.assert_called_once_with(
        "test-uuid-no-read"
    )

    mocked_video_no_read.read.assert_called_once()
    cvtRotate_mock.assert_not_called()
    test_VideoThread.change_image_signal.emit.assert_not_called()
    test_VideoThread.capture_complete_signal.emit.assert_not_called()
    test_VideoThread.camera_available_signal.emit.assert_has_calls([call(True)])
    test_VideoThread.error_image_signal.emit.assert_has_calls(
        [call("Unable to read from video")]
    )
    save_image_mock.assert_not_called()


mocked_video_valid_no_capture = Mock()
mocked_video_valid_no_capture.isOpened.return_value = True
mocked_video_valid_no_capture.read.side_effect = [(True, "Frame1"), (False, "Frame2")]


@patch("src.utils.camera.VideoThread._save_image")
@patch("src.utils.camera.VideoThread._video_close")
@patch("cv2.rotate", return_value="rotated_frame")
@patch("cv2.VideoCapture", return_value=mocked_video_valid_no_capture)
def test_VideoThread_run_valid_no_capture(
    VideoCapture_mock, cvtRotate_mock, video_close_mock, save_image_mock
):
    test_VideoThread.USER_UUID = "test-uuid-no-capture-flag"
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.check_set_filepath
    test_VideoThread.run()

    mocked_video_valid_no_capture.isOpened.assert_called_once()
    mocked_video_valid_no_capture.read.assert_has_calls([call(), call()])

    VideoCapture_mock.assert_called_once_with(ANY)

    test_VideoThread._DATABASE.check_set_filepath.assert_called_once_with(
        "test-uuid-no-capture-flag"
    )

    video_close_mock.assert_called_once_with()
    cvtRotate_mock.assert_called_once_with("Frame1", ANY)
    test_VideoThread.change_image_signal.emit.assert_has_calls([call("rotated_frame")])
    test_VideoThread.camera_available_signal.emit.assert_has_calls([call(True)])
    test_VideoThread.capture_complete_signal.emit.assert_not_called()
    save_image_mock.assert_not_called()


mocked_video_valid_with_capture = Mock()
mocked_video_valid_with_capture.isOpened.return_value = True
mocked_video_valid_with_capture.read.side_effect = [(True, "Frame3"), (False, "Frame4")]


@patch("src.utils.camera.VideoThread._save_image")
@patch("src.utils.camera.VideoThread._video_close")
@patch("cv2.rotate", return_value="rotated_frame")
@patch("cv2.VideoCapture", return_value=mocked_video_valid_with_capture)
def test_VideoThread_run_valid_with_capture(
    VideoCapture_mock, cvtRotate_mock, video_close_mock, save_image_mock
):
    test_VideoThread.USER_UUID = "test-uuid-capture-flag"
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.check_set_filepath
    test_VideoThread._capture_flag = True
    test_VideoThread.run()
    assert test_VideoThread._capture_flag == False

    mocked_video_valid_with_capture.isOpened.assert_called_once()
    mocked_video_valid_with_capture.read.assert_has_calls([call(), call()])

    VideoCapture_mock.assert_called_once_with(ANY)

    test_VideoThread._DATABASE.check_set_filepath.assert_called_once_with(
        "test-uuid-capture-flag"
    )
    cvtRotate_mock.assert_called_once_with("Frame3", ANY)
    test_VideoThread.change_image_signal.emit.assert_has_calls([call("rotated_frame")])
    video_close_mock.assert_called_once_with()
    test_VideoThread.camera_available_signal.emit.assert_has_calls([call(True)])
    test_VideoThread.capture_complete_signal.emit.assert_called_once_with(True)
    save_image_mock.assert_called_once_with("rotated_frame")


@patch("cv2.destroyAllWindows")
def test__video_close(destroy_all_windows_patch):
    video_mock = Mock()
    video_mock.release

    test_VideoThread.video = video_mock
    test_VideoThread._video_close()

    video_mock.release.assert_called_once_with()
    destroy_all_windows_patch.assert_called_once_with()


@patch("src.utils.camera.VideoThread.wait")
def test_stop(wait_mock):
    test_VideoThread.stop()
    assert test_VideoThread._run_flag == False
    assert test_VideoThread._record_flag == False
    assert test_VideoThread._capture_flag == False
    wait_mock.assert_called_once_with()


# @patch("cv2.VideoWriter")
# def test__set_video_writer(VideoWriter_mock):
#     # Create the video writer to save video
#     # (path, codec, fps, size)
#     test_VideoThread.USER_UUID = "test-uuid-video-writer"
#     test_VideoThread._DATABASE = Mock()
#     test_VideoThread._DATABASE.get_base_filepath.return_value = (
#         "base-path-set-video-writer"
#     )
#     test_VideoThread._set_video_writer(0)

#     VideoWriter_mock.assert_called_once_with(
#         os.path.normpath("base-path-set-video-writer/raw/0.avi"),
#         ANY,
#         30,
#         (ANY, ANY),
#     )


def test_set_user():
    test_VideoThread.set_user("test-uuid-set-user")
    assert test_VideoThread.USER_UUID == "test-uuid-set-user"


# @patch("src.utils.camera.VideoThread._set_video_writer")
# def test_record_toggle_original_false(_set_video_writer_mock):
#     test_VideoThread._DATABASE = Mock()
#     test_VideoThread._DATABASE.insert_new_image_session.return_value = 0

#     test_VideoThread._record_flag = False
#     test_VideoThread.USER_UUID = "test-uuid-record-toggle-false"
#     test_VideoThread.record_toggle()

#     assert test_VideoThread._record_flag == True
#     test_VideoThread._DATABASE.insert_new_image_session.assert_called_with(
#         "test-uuid-record-toggle-false"
#     )
#     _set_video_writer_mock.assert_called_once_with(0)
#     test_VideoThread._DATABASE.check_set_filepath.assert_called_once_with(
#         "test-uuid-record-toggle-false"
#     )


# @patch("src.utils.camera.VideoThread._set_video_writer")
# def test_record_toggle_original_true(_set_video_writer_mock):
#     test_VideoThread._DATABASE = Mock()
#     test_VideoThread._DATABASE.insert_new_image_session.return_value = 0

#     test_VideoThread._record_flag = True
#     test_VideoThread.USER_UUID = "test-uuid-record-toggle-true"
#     test_VideoThread.record_toggle()

#     assert test_VideoThread._record_flag == False
#     test_VideoThread._DATABASE.insert_new_image_session.assert_not_called()
#     _set_video_writer_mock.assert_not_called()
#     test_VideoThread._DATABASE.check_set_filepath.assert_not_called()


def test_init_capture_image():
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.check_set_filepath
    test_VideoThread._DATABASE.insert_new_image_session.return_value = 0
    test_VideoThread.USER_UUID = "test-uuid-init-capture-image"

    assert test_VideoThread._capture_flag == False
    ret = test_VideoThread.init_capture_image("test-image-name")
    assert test_VideoThread._capture_flag == True
    test_VideoThread._capture_flag = False

    test_VideoThread._DATABASE.check_set_filepath.assert_called_once_with(
        "test-uuid-init-capture-image"
    )
    test_VideoThread._DATABASE.insert_new_image_session.assert_called_once_with(
        "test-uuid-init-capture-image", "test-image-name"
    )
    assert ret == 0


@patch("cv2.imwrite")
def test__save_image(cv2_imwrite_mock):
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.get_base_filepath.return_value = "base-path-save-image"
    test_VideoThread.image_session_id = 1
    test_VideoThread.USER_UUID = "test-uuid-save-image"
    test_VideoThread._save_image("video_frame")

    test_VideoThread._DATABASE.get_base_filepath.assert_called_once_with(
        "test-uuid-save-image"
    )
    cv2_imwrite_mock.assert_called_once_with(
        os.path.normpath("base-path-save-image/raw/1.jpg"), "video_frame"
    )
