import cv2


def main_video_stream() -> None:
    video = cv2.VideoCapture(0)
    print(f"Video = {video}")

    if not video.isOpened():
        video_close(video=video)
        # TODO CHANGE Exception
        raise Exception("Unable to open Video Capture")

    # # To set the resolution
    # video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = video.read()
        # if frame is read correctly ret is True
        if not ret:
            print("Can't receive frame. Exiting ...")
            break

        # Our operations on the frame come here
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Display the resulting frame
        cv2.imshow("NML", gray)

        # "q" will break out of the video
        if cv2.waitKey(1) == ord("q"):
            break

    print("Cleaning Up!")
    video_close(video=video)


def video_close(video: cv2.VideoCapture) -> None:
    video.release()
    cv2.destroyAllWindows()
