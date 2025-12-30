import pose_module
import pose_module as pd
import cv2
import time

###############################
imgWidth, imgHeight = 1280, 720
videosPath = "videos"
###############################

def main():
    # camera / video
    cap = cv2.VideoCapture(f'{videosPath}/test_1.mp4')

    detector = pd.PoseDetector(detectionCon=0.8, trackCon=0.8)
    pTime = 0

    while True:
        success, img = cap.read()
        img = cv2.resize(img, (imgWidth, imgHeight))
        img = detector.findPose(img)
        lmList = detector.findPosition(img)

        if len(lmList) != 0:
            #rightArmAngle = detector.findAngle(img, 12 ,14, 16)
            leftArmAngle = detector.findAngle(img, 11 ,13, 15)
            state, reps = detector.checkState(img, "left")
            if state:
                cv2.putText(img, f'Phase: {state}', (20, 40), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)
                cv2.putText(img, f'Reps: {reps}', (20, 90), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)


            #leftElbowangle = detector.findAngle(img, 13, 11, 33)


        cTime = time.time()
        fps = 1/(cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {str(int(fps))}' ,(1150, 30), cv2.FONT_HERSHEY_PLAIN , 2, (255,0, 255), 2)

        cv2.imshow("Bench press tracker", img)


        if cv2.waitKey(50) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()