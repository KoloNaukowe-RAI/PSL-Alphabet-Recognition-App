import cv2

def test_opencv():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open video device")
    else:
        ret, frame = cap.read()
        if ret:
            print("Frame captured successfully")
        else:
            print("Failed to capture frame")
        cap.release()

test_opencv()

