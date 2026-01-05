import mediapipe as mp
import cv2
import math
import numpy as np
import time
import csv
import pandas as pd
States = {
    0: "START",
    1: "ECCENTRIC",
    2: "BOTTOM",
    3: "CONCENTRIC",
    4: "FINISH"
}

class PoseDetector():
    def __init__(self, mode = False, smooth = True,
                 detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(static_image_mode = self.mode,
                                     smooth_landmarks=self.smooth, min_detection_confidence=self.detectionCon,
                                     min_tracking_confidence=self.trackCon)
        self.state = States[0]
        self.repetitions = 0
        self.bottomStartTime = 0
        self.barPath = []
        self.currentPhasePath = []
        self.barPathColor = (255, 0, 255)  # purple
        self.lastBottomTime = 0
        self.messageTimer = 0
        self.rightTorso, self.leftTorso = [], []
        self.metrics = []
        self.bottomPause = False
        self.wasAsymmetric = False


    def findPose(self, img, draw=True):

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)
        return img

    def findPosition(self, img, draw=True):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
            self.findTorsoPoints(img, draw=draw)
            self.lmList.append(self.leftTorso)
            self.lmList.append(self.rightTorso)
        return self.lmList

    def findAngle(self, img, p1, p2, p3,draw=True ):

        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        x3, y3 = self.lmList[p3][1:]

        angle = math.degrees(math.atan2(y3- y2, x3-x2) - math.atan2(y1-y2, x1-x2))

        if angle < 0:
            angle += 360

        if angle > 180:
            angle = 360 - angle

        #print(angle)

        if draw:
            cv2.line(img, (x1,y1), (x2,y2), (0, 0, 255), 3)
            cv2.line(img, (x2,y2), (x3,y3), (0, 0, 255), 3)

            cv2.circle(img, (x1, y1), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x1, y1), 15, (0, 0, 255), 2)

            cv2.circle(img, (x2, y2), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 15, (0, 0, 255), 2)

            cv2.circle(img, (x3, y3), 10, (0, 0, 255), cv2.FILLED)
            cv2.circle(img, (x3, y3), 15, (0, 0, 255), 2)
            cv2.putText(img, str(int(angle)), (x2-50, y2+50), cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 2)

        return angle

    def findTorsoPoints(self, img , draw = True):
        if len(self.lmList) != 0:
            rightTorsoX = int((self.lmList[12][1] + self.lmList[24][1])/2)
            rightTorsoY = int((self.lmList[12][2] + self.lmList[24][2])/2)

            leftTorsoX = int((self.lmList[11][1] + self.lmList[23][1]) / 2)
            leftTorsoY = int((self.lmList[11][2] + self.lmList[23][2]) / 2)

            self.rightTorso = [34, rightTorsoX, rightTorsoY]
            self.leftTorso = [33, leftTorsoX, leftTorsoY]

            if draw:
                cv2.circle(img, (leftTorsoX, leftTorsoY), 5, (255, 0, 0), cv2.FILLED)
                cv2.circle(img, (rightTorsoX, rightTorsoY), 5, (255, 0, 0), cv2.FILLED)

    def checkState(self, img, side):
        if side == "left":
            p1, p2 , p3 = 11, 13, 15
        elif side == "right":
            p1, p2, p3 = 12, 14, 16
        else:
            return

        armAngle = self.findAngle(img,p1, p2, p3)
        wrist = self.lmList[p3]
        #Start
        if self.state == States[0]:
            self.barPath.append([wrist[1:],self.barPathColor, self.state, time.time()])
            self.currentPhasePath.append([wrist[1:], time.time()])
            if armAngle < 165:
                self.saveData()
                self.currentPhasePath= []

                self.wasAsymmetric = False
                self.state = States[1]
        #Eccentric
        elif self.state == States[1]:
            self.barPathColor = (255, 0, 255)  # purple
            self.barPath.append([wrist[1:],self.barPathColor, self.state, time.time()])
            self.currentPhasePath.append([wrist[1:], time.time()])
            if armAngle < 35: #75
                self.bottomStartTime = time.time()
                self.saveData()
                self.currentPhasePath= []
                self.wasAsymmetric = False
                self.state = States[2]
        #Bottom
        elif self.state == States[2]:
            self.barPath.append([wrist[1:],self.barPathColor, self.state, time.time()])
            self.currentPhasePath.append([wrist[1:], time.time()])
            if armAngle > 40: #85
                bottomTime = time.time() - self.bottomStartTime
                self.lastBottomTime = bottomTime
                self.messageTimer = time.time()
                if bottomTime > 1.0:
                    self.bottomPause = True
                else:
                    self.bottomPause = False
                self.saveData()
                self.currentPhasePath= []
                self.wasAsymmetric = False
                self.bottomPause = False
                self.state = States[3]
        #Concentric
        elif self.state == States[3]:
            self.barPathColor = (0, 255, 0)  # green
            self.barPath.append([wrist[1:],self.barPathColor, self.state, time.time()])
            self.currentPhasePath.append([wrist[1:], time.time()])
            if armAngle > 170:
                self.saveData()
                self.currentPhasePath= []
                self.repetitions += 1
                self.wasAsymmetric = False
                self.state = States[0]
        return (self.state, self.repetitions, self.barPathColor)

    def drawBarPath(self, img, path):
        if len(path) < 2: return
        for i in range(len(path) - 1):
            p1 = path[i][0]
            p2 = path[i + 1][0]
            drawColor = path[i][1]
            cv2.line(img, p1, p2, drawColor, 2, 2)

    def calculateVelocity(self, img,path,draw=True):
        if len(path) < 2:
            return {}
        self.phase_velocities = {}
        current_state = path[0][2]
        phase_start_time = path[0][3]
        phase_distance = 0.0


        for i in range(len(path) - 1):
            p1 = np.array(path[i][0])
            p2 = np.array(path[i + 1][0])
            next_state = path[i+1][2]
            current_time = path[i+1][3]

            phase_distance += np.linalg.norm(p2 - p1)

            if current_state != next_state :

                passed_time = current_time - phase_start_time

                if passed_time > 0:
                    velocity = phase_distance / passed_time
                else:
                    velocity = 0.0

                self.phase_velocities[current_state] = velocity

                current_state = next_state
                phase_start_time = current_time
                phase_distance = 0.0


        if draw:
            color = path[-1][1]
            y_offset = 50
            cv2.putText(img, f'Velocity [px/s]', (20, 190), cv2.FONT_HERSHEY_PLAIN, 3, (0,0,255), 3)
            for phase, velocity in self.phase_velocities.items():
                cv2.putText(img, f'{phase}: {velocity:.2f}', (20, 190 + y_offset), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0 ,0 ), 2)
                y_offset += 50

        return self.phase_velocities

    def detectAsymmetry(self, img, draw=True):
        leftWrist, rightWrist = self.lmList[15:17]
        if abs(leftWrist[2] - rightWrist[2]) > 100:
            self.wasAsymmetric = True
            if draw:
                cv2.circle(img, leftWrist[1:], 10,(0,255, 255),3)
                cv2.circle(img, rightWrist[1:], 10,(0,255, 255),3)
                cv2.line(img, leftWrist[1:], rightWrist[1:],(0,255, 255), 3)
                cv2.putText(img,'WRIST ASYMETRY DETECTED', (300,700),cv2.FONT_HERSHEY_PLAIN,3, (0,0,255), 3)
        return self.wasAsymmetric

    def displayMessages(self, img):
        if self.lastBottomTime > 1 and time.time() - self.messageTimer < 1.5:
            cv2.putText(img,f'BOTTOM PAUSE DETECTED: {self.lastBottomTime:.2f}s', (250,650),cv2.FONT_HERSHEY_PLAIN,3, (255, 0 ,0), 3)

    def saveData(self):
        if len(self.currentPhasePath) < 2:
            return

        start_time = self.currentPhasePath[0][1]
        end_time = self.currentPhasePath[-1][1]
        duration = end_time - start_time

        distance = 0.0
        for i in range(len(self.currentPhasePath) - 1):
            p1 = np.array(self.currentPhasePath[i][0])
            p2 = np.array(self.currentPhasePath[i + 1][0])
            distance += np.linalg.norm(p1 - p2)

        avg_velocity = distance / duration if duration > 0 else 0.0

        self.metrics.append({
            "Repetition": int(self.repetitions),
            "Phase": self.state,
            "Duration_s": round(duration, 2),
            "Velocity_avg": round(avg_velocity, 2),
            "Distance_px": int(distance),
            "Bottom_pause": 1 if self.bottomPause else 0,
            "Asymmetry": 1 if self.wasAsymmetric else 0
        })

    def saveToCsv(self, output_file = 'results.csv'):
        if not self.metrics:
            print("Lack of data to save!")
            return
        df = pd.DataFrame(self.metrics)
        try:
            df.to_csv(output_file,index=False)
            print(f'Metrics saved in {output_file}.')
        except Exception as e:
            print(f'Saving error {e}')

        return df








