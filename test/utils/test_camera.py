import pytest
from unittest.mock import patch, Mock, ANY

from src.utils.camera import main_video_stream, save_image, video_close

mocked_video_writer = Mock()
mocked_video_writer.write

mocked_video_not_opened = Mock()
mocked_video_not_opened.isOpened.return_value = False
mocked_video_not_opened.read.return_value = (False, None)


@patch("src.utils.camera.video_close")
@patch("cv2.waitKey", return_value=ord("q"))
@patch("cv2.imshow", return_value=())
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoWriter", return_value=mocked_video_writer)
@patch("cv2.VideoCapture", return_value=mocked_video_not_opened)
def test_main_video_stream_not_opened(
    VideoCapture_mock,
    VideoWriter_mock,
    cvtColor_mock,
    imshow_mock,
    waitKey_mock,
    video_close_mock,
):
    with pytest.raises(Exception) as e_info:
        main_video_stream()

    VideoCapture_mock.assert_called_once_with(0)
    VideoWriter_mock.assert_not_called()
    video_close_mock.assert_called_once_with(video=mocked_video_not_opened)
    assert "Unable to open Video Capture" in str(e_info.value)
    mocked_video_not_opened.isOpened.assert_called_once()
    mocked_video_not_opened.read.assert_not_called()

    cvtColor_mock.assert_not_called()
    imshow_mock.assert_not_called()
    waitKey_mock.assert_not_called()


mocked_video_no_read = Mock()
mocked_video_no_read.isOpened.return_value = True
mocked_video_no_read.read.return_value = (False, None)


@patch("src.utils.camera.video_close")
@patch("cv2.waitKey", return_value=ord("q"))
@patch("cv2.imshow", return_value=())
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoWriter", return_value=mocked_video_writer)
@patch("cv2.VideoCapture", return_value=mocked_video_no_read)
def test_main_video_stream_no_read(
    VideoCapture_mock,
    VideoWriter_mock,
    cvtColor_mock,
    imshow_mock,
    waitKey_mock,
    video_close_mock,
):
    main_video_stream()

    VideoCapture_mock.assert_called_once_with(0)
    VideoWriter_mock.assert_called_once_with(ANY, ANY, 10, (ANY, ANY))
    video_close_mock.assert_called_once_with(video=mocked_video_no_read)

    mocked_video_writer.assert_not_called()
    mocked_video_no_read.isOpened.assert_called_once()
    mocked_video_no_read.read.assert_called_once()

    cvtColor_mock.assert_not_called()
    imshow_mock.assert_not_called()
    waitKey_mock.assert_not_called()


mocked_video_valid = Mock()
mocked_video_valid.isOpened.return_value = True
mocked_video_valid.read.return_value = (True, "Frame")


@patch("src.utils.camera.video_close")
@patch("cv2.waitKey", return_value=ord("q"))
@patch("cv2.imshow", return_value=())
@patch("cv2.cvtColor", return_value="Frame")
@patch("cv2.VideoWriter", return_value=mocked_video_writer)
@patch("cv2.VideoCapture", return_value=mocked_video_valid)
def test_main_video_stream_valid(
    VideoCapture_mock,
    VideoWriter_mock,
    cvtColor_mock,
    imshow_mock,
    waitKey_mock,
    video_close_mock,
):
    main_video_stream()

    mocked_video_valid.isOpened.assert_called_once()
    mocked_video_valid.read.assert_called_once()

    VideoCapture_mock.assert_called_once_with(0)
    VideoWriter_mock.assert_called_once_with(ANY, ANY, 10, (ANY, ANY))

    mocked_video_writer.write.assert_called_once_with("Frame")

    video_close_mock.assert_called_once_with(video=mocked_video_valid)
    cvtColor_mock.assert_called_once_with("Frame", ANY)
    imshow_mock.assert_called_once_with("NML", "Frame")
    waitKey_mock.assert_called_once_with(1)


@patch("os.path.abspath", return_value="test/path/img.jpg")
@patch("cv2.imwrite")
def test_save_image(imwrite_mock, os_path_mock):
    frame_mock = Mock()
    save_image(frame_mock)

    os_path_mock.assert_called_once_with("tmp_img/test.jpg")
    imwrite_mock.assert_called_once_with("test/path/img.jpg", frame_mock)


@patch("cv2.destroyAllWindows")
def test_video_close(destroy_all_windows_patch):
    video_mock = Mock()
    video_mock.release

    video_close(video_mock)

    video_mock.release.assert_called_once_with()
    destroy_all_windows_patch.assert_called_once_with()