import os
import cv2


def main_video_stream() -> None:
    frame_width = 640
    frame_hight = 480

    video = cv2.VideoCapture(0)
    print(f"Video = {video}")

    if not video.isOpened():
        video_close(video=video)
        # TODO CHANGE Exception
        raise Exception("Unable to open Video Capture")

    # # To set the resolution
    # video.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    # video.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_hight)

    # Create the video writer to save video
    # (path, codec, fps, size)
    video_writer = cv2.VideoWriter(
        os.path.abspath("tmp_vid/test.avi"),
        cv2.VideoWriter_fourcc("M", "J", "P", "G"),
        30,
        (frame_width, frame_hight),
    )

    while True:
        success, frame = video.read()
        # if frame is read correctly success is True
        if not success:
            print("Can't receive frame. Exiting ...")
            break

        # Save the frame to the video
        video_writer.write(frame)

        # Our operations on the frame come here
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Display the resulting frame
        cv2.imshow("NML", gray)

        key_press = cv2.waitKey(1) & 0xFF
        # "q" will break out of the video
        # "c" will capture a image from the video
        if key_press == ord("q"):
            break
        elif key_press == ord("c"):
            save_image(frame)

    print("Cleaning Up!")
    video_close(video=video)


def save_image(video_frame: cv2.Mat) -> None:
    print("Capturing Image")
    img_path = os.path.abspath("tmp_img/test.jpg")
    cv2.imwrite(img_path, video_frame)


def video_close(video: cv2.VideoCapture) -> None:
    video.release()
    cv2.destroyAllWindows()
