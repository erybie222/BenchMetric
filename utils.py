import cv2
def drawBarPath(img,path):
    if len(path) == 0: return
    for i in range(len(path) - 1):
        p1 = path[i][0]
        p2 = path[i+1][0]
        drawColor = path[i][1]
        cv2.line(img, p1, p2,drawColor, 2, 2)