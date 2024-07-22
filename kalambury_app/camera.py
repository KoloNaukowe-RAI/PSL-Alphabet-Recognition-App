import cv2
import threading

class VideoCamera:
    def __init__(self):
        print(cv2.VideoCapture(0).isOpened())
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            print("Camera is already in use.")
            self.video = None
            return

        self.grabbed, self.frame = self.video.read()
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        _, jpeg = cv2.imencode('.jpg', self.frame)
        return jpeg.tobytes()

    def update(self):
        while True:
            self.grabbed, self.frame = self.video.read()


