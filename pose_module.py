import mediapipe as mp
import cv2
import math

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
        self.state = States[0]
        self.repetitions= 0
        self.barPath = []
        self.barPathColor = (255, 0 ,255 ) #purple
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(static_image_mode = self.mode,
                                     smooth_landmarks=self.smooth, min_detection_confidence=self.detectionCon,
                                     min_tracking_confidence=self.trackCon)

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
            print(self.rightTorso, self.leftTorso)

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
        wrist = self.lmList[15]

        #Start
        if self.state == States[0]:
            self.barPathColor = (255, 0, 255)  # purple
            self.barPath.append([wrist[1:],self.barPathColor ])
            if armAngle < 160:
                self.state = States[1]
        #Eccentric
        elif self.state == States[1]:
            self.barPath.append([wrist[1:],self.barPathColor ])
            if armAngle < 40: #75
                self.state = States[2]
        #Bottom
        elif self.state == States[2]:
            self.barPath.append([wrist[1:],self.barPathColor ])
            if armAngle > 45: #85
                self.state = States[3]
        #Concentric
        elif self.state == States[3]:
            self.barPathColor = (0, 255, 0)  # green
            self.barPath.append([wrist[1:],self.barPathColor ])
            if armAngle > 165:
                self.repetitions += 1
                self.state = States[0]
        return (self.state, self.repetitions, self.barPathColor)




