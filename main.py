import pose_module as pd
import cv2
import time
import streamlit as st
###############################
imgW, imgH = 1280, 720
videosPath = "assets/videos/test_1.mp4"
###############################


def analyze(videoPath, imgWidth, imgHeight, streamlit_mode=False, delay = 0.0, side = 'left', progress_bar=None):
    # camera / video
    cap = cv2.VideoCapture(str(videoPath))

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    current_frame = 0

    detector = pd.PoseDetector(detectionCon=0.8, trackCon=0.8)
    pTime = 0

    if streamlit_mode:
        stframe = st.empty()
        st_text = st.empty()

    while cap.isOpened():
        success, img = cap.read()

        if not success:
            break

        current_frame += 1

        if progress_bar is not None and total_frames > 0:
            progress = min(int((current_frame / total_frames) * 100), 99)
            progress_bar.progress(progress, text=f"Analyzing frame {current_frame}/{total_frames}...")

        img = cv2.resize(img, (imgWidth, imgHeight))
        img = detector.findPose(img, draw=False)
        lmList = detector.findPosition(img, draw=False)

        if len(lmList) != 0:

            state, reps, drawColor = detector.checkState(img, side)
            if state:
                cv2.putText(img, f'Phase: {state}', (20, 90), cv2.FONT_HERSHEY_PLAIN, 3, drawColor, 3)
                cv2.putText(img, f'Reps: {reps}', (20, 140), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
            detector.drawBarPath(img, detector.barPath)
            detector.calculateVelocity(img, detector.barPath)
            detector.detectAsymmetry(img, True)
            detector.displayMessages(img)


        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, f'FPS: {str(int(fps))}', (1150, 30), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

        if delay > 0:
            time.sleep(delay)

        if streamlit_mode:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            stframe.image(img_rgb, channels="RGB", width=imgWidth)
        else:
            cv2.imshow("Bench press tracker", img)

            if cv2.waitKey(100) & 0xFF == ord('q'):
                break

    cap.release()
    if not streamlit_mode:
        cv2.destroyAllWindows()
    metrics = detector.saveToCsv()
    return metrics

def main():

    analyze(videosPath , imgW , imgH)

if __name__ == '__main__':
    main()