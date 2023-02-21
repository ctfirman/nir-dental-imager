import os
import pytest
from unittest.mock import patch, Mock, ANY, call

from src.utils.camera import (
    VideoNotOpened,
    VideoThread,
)


test_VideoThread = VideoThread(None, None)
test_VideoThread.error_image_signal = Mock()
test_VideoThread.error_image_signal.emit

test_VideoThread.change_image_signal = Mock()
test_VideoThread.change_image_signal.emit

test_VideoThread.video_writer = Mock()
test_VideoThread.video_writer.write

mocked_video_not_opened = Mock()
mocked_video_not_opened.isOpened.return_value = False
mocked_video_not_opened.read.return_value = (False, None)


@patch("src.utils.camera.VideoThread._video_close")
@patch("src.utils.camera.VideoThread._check_set_filepath")
@patch("src.utils.camera.VideoThread._set_video_writer")
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_not_opened)
def test_VideoThread_run_not_opened(
    VideoCapture_mock,
    cvtColor_mock,
    _check_set_filepath_mock,
    _set_video_writer_mock,
    video_close_mock,
):
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

    _check_set_filepath_mock.assert_not_called()
    _set_video_writer_mock.assert_not_called()

    cvtColor_mock.assert_not_called()
    test_VideoThread.change_image_signal.emit.assert_not_called()


mocked_video_no_run_flag = Mock()
mocked_video_no_run_flag.isOpened.return_value = True
mocked_video_no_run_flag.read.return_value = (False, None)


@patch("src.utils.camera.VideoThread._video_close")
@patch("src.utils.camera.VideoThread._check_set_filepath")
@patch("src.utils.camera.VideoThread._set_video_writer")
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_no_run_flag)
def test_VideoThread_run_no_run_flag(
    VideoCapture_mock,
    cvtColor_mock,
    _set_video_writer_mock,
    _check_set_filepath_mock,
    video_close_mock,
):
    test_VideoThread._run_flag = False
    test_VideoThread.run()
    test_VideoThread._run_flag = True

    VideoCapture_mock.assert_called_once_with(ANY)
    video_close_mock.assert_called_once_with()

    _check_set_filepath_mock.assert_called_once_with()
    _set_video_writer_mock.assert_called_once_with(0)

    mocked_video_no_run_flag.isOpened.assert_called_once()
    mocked_video_no_run_flag.read.assert_not_called()
    test_VideoThread.video_writer.write.assert_not_called()
    cvtColor_mock.assert_not_called()
    test_VideoThread.change_image_signal.emit.assert_not_called()


mocked_video_no_read = Mock()
mocked_video_no_read.isOpened.return_value = True
mocked_video_no_read.read.return_value = (False, None)


@patch("src.utils.camera.VideoThread._video_close")
@patch("src.utils.camera.VideoThread._check_set_filepath")
@patch("src.utils.camera.VideoThread._set_video_writer")
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_no_read)
def test_VideoThread_run_no_read(
    VideoCapture_mock,
    cvtColor_mock,
    _set_video_writer_mock,
    _check_set_filepath_mock,
    video_close_mock,
):
    test_VideoThread.run()

    VideoCapture_mock.assert_called_once_with(ANY)
    video_close_mock.assert_called_once_with()

    mocked_video_no_read.isOpened.assert_called_once()
    _check_set_filepath_mock.assert_called_once_with()
    _set_video_writer_mock.assert_called_once_with(0)

    mocked_video_no_read.read.assert_called_once()
    test_VideoThread.video_writer.write.assert_not_called()
    cvtColor_mock.assert_not_called()
    test_VideoThread.change_image_signal.emit.assert_not_called()


mocked_video_valid_no_record = Mock()
mocked_video_valid_no_record.isOpened.return_value = True
mocked_video_valid_no_record.read.side_effect = [(True, "Frame1"), (False, "Frame2")]


@patch("src.utils.camera.VideoThread._video_close")
@patch("src.utils.camera.VideoThread._check_set_filepath")
@patch("src.utils.camera.VideoThread._set_video_writer")
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_valid_no_record)
def test_VideoThread_run_valid_no_record(
    VideoCapture_mock,
    cvtColor_mock,
    _set_video_writer_mock,
    _check_set_filepath_mock,
    video_close_mock,
):
    test_VideoThread.run()

    mocked_video_valid_no_record.isOpened.assert_called_once()
    mocked_video_valid_no_record.read.assert_has_calls([call(), call()])

    VideoCapture_mock.assert_called_once_with(ANY)

    _check_set_filepath_mock.assert_called_once_with()
    _set_video_writer_mock.assert_called_once_with(0)

    test_VideoThread.video_writer.write.assert_not_called()
    video_close_mock.assert_called_once_with()
    cvtColor_mock.assert_called_once_with("Frame1", ANY)
    test_VideoThread.change_image_signal.emit.assert_has_calls([call("Frame1")])


mocked_video_valid_with_record = Mock()
mocked_video_valid_with_record.isOpened.return_value = True
mocked_video_valid_with_record.read.side_effect = [(True, "Frame3"), (False, "Frame4")]


@patch("src.utils.camera.VideoThread._video_close")
@patch("src.utils.camera.VideoThread._check_set_filepath")
@patch("src.utils.camera.VideoThread._set_video_writer")
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoCapture", return_value=mocked_video_valid_with_record)
def test_VideoThread_run_valid_with_record(
    VideoCapture_mock,
    cvtColor_mock,
    _set_video_writer_mock,
    _check_set_filepath_mock,
    video_close_mock,
):
    test_VideoThread._record_flag = True
    test_VideoThread.run()
    test_VideoThread._record_flag = False

    mocked_video_valid_with_record.isOpened.assert_called_once()
    mocked_video_valid_with_record.read.assert_has_calls([call(), call()])

    VideoCapture_mock.assert_called_once_with(ANY)

    _check_set_filepath_mock.assert_called_once_with()
    _set_video_writer_mock.assert_called_once_with(0)

    test_VideoThread.video_writer.write.assert_called_once_with("Frame3")
    cvtColor_mock.assert_called_once_with("Frame3", ANY)
    test_VideoThread.change_image_signal.emit.assert_has_calls([call("Frame3")])
    video_close_mock.assert_called_once_with()


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
    wait_mock.assert_called_once_with()


@patch("os.path.abspath", side_effect=[None, "path1", "path2"])
@patch("os.makedirs")
@patch("os.path.isdir", return_value=True)
def test__check_set_filepath_exists(isdir_mock, makedirs_mock, abspath_mock):
    test_VideoThread.USER_UUID = "test-uuid-filepath-exist"
    test_VideoThread._check_set_filepath()

    isdir_mock.assert_called_once()
    abspath_mock.assert_called_once_with("tmp_vid/test-uuid-filepath-exist/raw")
    makedirs_mock.assert_not_called()


@patch("os.path.abspath", side_effect=[None, "path1", "path2"])
@patch("os.makedirs")
@patch("os.path.isdir", return_value=False)
def test__check_set_filepath_doesnt_exist(isdir_mock, makedirs_mock, abspath_mock):
    test_VideoThread.USER_UUID = "test-uuid-filepath-not-exist"
    test_VideoThread._check_set_filepath()

    isdir_mock.assert_called_once()
    abspath_mock.assert_has_calls(
        [
            call("tmp_vid/test-uuid-filepath-not-exist/raw"),
            call("tmp_vid/test-uuid-filepath-not-exist/raw"),
            call("tmp_vid/test-uuid-filepath-not-exist/complete"),
        ]
    )
    makedirs_mock.assert_has_calls([call("path1"), call("path2")])


@patch("cv2.VideoWriter")
def test__set_video_writer(VideoWriter_mock):
    # Create the video writer to save video
    # (path, codec, fps, size)
    test_VideoThread.USER_UUID = "test-uuid-video-writer"
    test_VideoThread._set_video_writer(0)

    VideoWriter_mock.assert_called_once_with(
        os.path.abspath("tmp_vid/test-uuid-video-writer/raw/0.avi"),
        ANY,
        30,
        (ANY, ANY),
    )


def test_set_user():
    test_VideoThread.set_user("test-uuid-set-user")
    assert test_VideoThread.USER_UUID == "test-uuid-set-user"


@patch("src.utils.camera.VideoThread._set_video_writer")
def test_record_toggle_original_false(_set_video_writer_mock):
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.insert_new_image_session.return_value = 0

    test_VideoThread._record_flag = False
    test_VideoThread.USER_UUID = "test-uuid-record-toggle-false"
    test_VideoThread.record_toggle()

    assert test_VideoThread._record_flag == True
    test_VideoThread._DATABASE.insert_new_image_session.assert_called_with(
        "test-uuid-record-toggle-false"
    )
    _set_video_writer_mock.assert_called_once_with(0)


@patch("src.utils.camera.VideoThread._set_video_writer")
def test_record_toggle_original_true(_set_video_writer_mock):
    test_VideoThread._DATABASE = Mock()
    test_VideoThread._DATABASE.insert_new_image_session.return_value = 0

    test_VideoThread._record_flag = True
    test_VideoThread.USER_UUID = "test-uuid-record-toggle-true"
    test_VideoThread.record_toggle()

    assert test_VideoThread._record_flag == False
    test_VideoThread._DATABASE.insert_new_image_session.assert_not_called()
    _set_video_writer_mock.assert_not_called()
