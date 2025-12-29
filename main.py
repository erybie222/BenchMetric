import pose_module
import pose_module as pd
import cv2
def main():
    # camera / video
    cap = cv2.VideoCapture(0)

    detector = pd.PoseDetector()

    while True:
        success, img = cap.read()
        img = detector.findPose(img)
        cv2.imshow("Bench press tracker", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    main()