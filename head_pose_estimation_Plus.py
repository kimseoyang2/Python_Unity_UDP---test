# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 03:00:36 2020

@author: hp
"""


from os import stat
from google.protobuf.text_format import PrintField
import UdpComms as U
import cv2
import numpy as np
import math
from face_detector import get_face_detector, find_faces
from face_landmarks import get_landmark_model, detect_marks
import csv

# 라이다
import serial
from serial import Serial


#라이다 센서 변수
line = 50  # 멀고 가깝고 기준
maxDist = 130  # 센서 벗어나는 거리
testCounter = 1
closeCounter = 1
farCounter = 1
total = 0
state = 0  # 유니티 인풋 default=False
ser = serial.Serial("COM7", 115200)
dis = 0
i = 0
peopleNum = 0

isSent=False
isStart=False



# 유디피 통신 선언
sock = U.UdpComms(
    udpIP="127.0.0.1", portTX=8000, portRX=8001, enableRX=True, suppressWarnings=True
)

# 라이다 csv에 입력
def addDis(val):
    global total
    total += val
    #print(total)

def get_2d_points(img, rotation_vector, translation_vector, camera_matrix, val):
    """Return the 3D points present as 2D for making annotation box"""
    point_3d = []
    dist_coeffs = np.zeros((4, 1))
    rear_size = val[0]
    rear_depth = val[1]
    point_3d.append((-rear_size, -rear_size, rear_depth))
    point_3d.append((-rear_size, rear_size, rear_depth))
    point_3d.append((rear_size, rear_size, rear_depth))
    point_3d.append((rear_size, -rear_size, rear_depth))
    point_3d.append((-rear_size, -rear_size, rear_depth))

    front_size = val[2]
    front_depth = val[3]
    point_3d.append((-front_size, -front_size, front_depth))
    point_3d.append((-front_size, front_size, front_depth))
    point_3d.append((front_size, front_size, front_depth))
    point_3d.append((front_size, -front_size, front_depth))
    point_3d.append((-front_size, -front_size, front_depth))
    point_3d = np.array(point_3d, dtype=np.float).reshape(-1, 3)

    # Map to 2d img points
    (point_2d, _) = cv2.projectPoints(point_3d,
                                      rotation_vector,
                                      translation_vector,
                                      camera_matrix,
                                      dist_coeffs)
    point_2d = np.int32(point_2d.reshape(-1, 2))
    return point_2d


def draw_annotation_box(img, rotation_vector, translation_vector, camera_matrix,
                        rear_size=300, rear_depth=0, front_size=500, front_depth=400,
                        color=(255, 255, 0), line_width=2):
    """
    Draw a 3D anotation box on the face for head pose estimation

    Parameters
    ----------
    img : np.unit8
        Original Image.
    rotation_vector : Array of float64
        Rotation Vector obtained from cv2.solvePnP
    translation_vector : Array of float64
        Translation Vector obtained from cv2.solvePnP
    camera_matrix : Array of float64
        The camera matrix
    rear_size : int, optional
        Size of rear box. The default is 300.
    rear_depth : int, optional
        The default is 0.
    front_size : int, optional
        Size of front box. The default is 500.
    front_depth : int, optional
        Front depth. The default is 400.
    color : tuple, optional
        The color with which to draw annotation box. The default is (255, 255, 0).
    line_width : int, optional
        line width of lines drawn. The default is 2.

    Returns
    -------
    None.

    """

    rear_size = 1
    rear_depth = 0
    front_size = img.shape[1]
    front_depth = front_size*2
    val = [rear_size, rear_depth, front_size, front_depth]
    point_2d = get_2d_points(img, rotation_vector,
                             translation_vector, camera_matrix, val)
    # # Draw all the lines
    cv2.polylines(img, [point_2d], True, color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[1]), tuple(
        point_2d[6]), color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[2]), tuple(
        point_2d[7]), color, line_width, cv2.LINE_AA)
    cv2.line(img, tuple(point_2d[3]), tuple(
        point_2d[8]), color, line_width, cv2.LINE_AA)


def head_pose_points(img, rotation_vector, translation_vector, camera_matrix):
    """
    Get the points to estimate head pose sideways

    Parameters
    ----------
    img : np.unit8
        Original Image.
    rotation_vector : Array of float64
        Rotation Vector obtained from cv2.solvePnP
    translation_vector : Array of float64
        Translation Vector obtained from cv2.solvePnP
    camera_matrix : Array of float64
        The camera matrix

    Returns
    -------
    (x, y) : tuple
        Coordinates of line to estimate head pose

    """
    rear_size = 1
    rear_depth = 0
    front_size = img.shape[1]
    front_depth = front_size*2
    val = [rear_size, rear_depth, front_size, front_depth]
    point_2d = get_2d_points(img, rotation_vector,
                             translation_vector, camera_matrix, val)
    y = (point_2d[5] + point_2d[8])//2
    x = point_2d[2]

    return (x, y)

########################################################################################################
# 내가 만든 함수


def timer(f):
    global timeCounter
    timeCounter += 1
    if (timeCounter > f):
        timeCounter = 0
        return True
    else:
        return False


def add():
    global count
    global counter
    global resetTimer
    global addTimer

    addTimer += 1
    if(count and addTimer > 5):
        counter += 1
        count = False
        print("Counter:",counter)
    timer = 0


def decide():
    global result
    if(counter > limit):
        result= "Over"
    else:
        result = "Under"
    


def getTFminiData():

    while True:
        # time.sleep(0.1)
        count = ser.in_waiting
        if count > 8:
            recv = ser.read(9)
            ser.reset_input_buffer()

            if recv[0] == 0x59 and recv[1] == 0x59:  # python3
                distance = recv[2] + recv[3] * 256
                strength = recv[4] + recv[5] * 256
                print(distance)

                if distance < maxDist:
                    if distance < line:
                        global closeCounter
                        closeCounter += 1
                        addDis(distance)

                    else:
                        global farCounter
                        farCounter += 1
                        addDis(distance)





                global testCounter
                testCounter += 1
                if(testCounter > 500):

                    break


                 # checkUnity()
                # print(testCounter)


                # print('(', distance, ',', strength, ')')
                ser.reset_input_buffer()


def saveCSV():

    global peopleNum
    f = 0
    f = open(
        "C:\\Users\jsn07\Documents\HeadPose.csv",
        "a",
        encoding="utf-8",
        newline="",
    )
    wr = csv.writer(f)
    if peopleNum == 0:
        wr.writerow(["Num", "Val"])
        wr.writerow([peopleNum, counter])

    else:
        wr.writerow([peopleNum, counter])
    f.close()
    peopleNum += 1

########################################################################################################
# 본문


face_model = get_face_detector()
landmark_model = get_landmark_model()
cap = cv2.VideoCapture(0)
ret, img = cap.read()
size = img.shape
font = cv2.FONT_HERSHEY_SIMPLEX

state =0
counter = 0
count = True
resetTimer = 0
addTimer = 0
limit = 2  # 기준 파라미터
result01 = "Over"  # 유니티 보낼 값
peopleNum = 0
timeCounter = 0


# 3D model points.
model_points = np.array([
    (0.0, 0.0, 0.0),             # Nose tip
    (0.0, -330.0, -65.0),        # Chin
    (-225.0, 170.0, -135.0),     # Left eye left corner
    # Right eye right corne
    (225.0, 170.0, -135.0),
    (-150.0, -150.0, -125.0),    # Left Mouth corner
    (150.0, -150.0, -125.0)      # Right mouth corner
])

# Camera internals
focal_length = size[1]
center = (size[1]/2, size[0]/2)
camera_matrix = np.array(
    [[focal_length, 0, center[0]],
     [0, focal_length, center[1]],
     [0, 0, 1]], dtype="double"
)




while True:

       


                   
    
    data = sock.ReadReceivedData()
    if data != None:

      # if NEW data has been received since last ReadReceivedData function call
        print("from Unity",data)  # print new received data
        state = int(data)

    ret, img = cap.read()
    if ret == True:
        faces = find_faces(img, face_model)
        for face in faces:
            marks = detect_marks(img, landmark_model, face)
            # mark_detector.draw_marks(img, marks, color=(0, 255, 0))
            image_points = np.array([
                                    marks[30],     # Nose tip
                                    marks[8],     # Chin
                                    marks[36],     # Left eye left corner
                                    marks[45],     # Right eye right corne
                                    marks[48],     # Left Mouth corner
                                    marks[54]      # Right mouth corner
                                    ], dtype="double")
            dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion
            (success, rotation_vector, translation_vector) = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_UPNP)

            # Project a 3D point (0, 0, 1000.0) onto the image plane.
            # We use this to draw a line sticking out of the nose

            (nose_end_point2D, jacobian) = cv2.projectPoints(np.array(
                [(0.0, 0.0, 1000.0)]), rotation_vector, translation_vector, camera_matrix, dist_coeffs)

            for p in image_points:
                cv2.circle(img, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)

            p1 = (int(image_points[0][0]), int(image_points[0][1]))
            p2 = (int(nose_end_point2D[0][0][0]),
                  int(nose_end_point2D[0][0][1]))
            x1, x2 = head_pose_points(
                img, rotation_vector, translation_vector, camera_matrix)

            cv2.line(img, p1, p2, (0, 255, 255), 2)
            cv2.line(img, tuple(x1), tuple(x2), (255, 255, 0), 2)
            # for (x, y) in marks:
            #     cv2.circle(img, (x, y), 4, (255, 255, 0), -1)
            # cv2.putText(img, str(p1), p1, font, 1, (0, 255, 255), 1)
            try:
                m = (p2[1] - p1[1])/(p2[0] - p1[0])
                ang1 = int(math.degrees(math.atan(m)))
            except:
                ang1 = 90

            try:
                m = (x2[1] - x1[1])/(x2[0] - x1[0])
                ang2 = int(math.degrees(math.atan(-1/m)))
            except:
                ang2 = 90

            # 임시방편 코드
            #if(timer(30)):
                #if(state < 3):
                    #state += 1
                    #print("state=", state)

    

           



            if(state == 0):
                # headpose 초기화
                counter = 0
                isStart=False

                result = "null"
                result01 = "null"
                #print("from Unity",data)



               



            elif(state == 1):

                if ang1 >= 40:

                    cv2.putText(img, 'Head down', (30, 30),
                                font, 2, (255, 255, 128), 3)
                    add()
                elif ang1 <= -40:

                    cv2.putText(img, 'Head up', (30, 30),
                                font, 2, (255, 255, 128), 3)
                    add()

                if ang2 >= 40:

                    cv2.putText(img, 'Head right', (90, 30),
                                font, 2, (255, 255, 128), 3)
                    add()

                elif ang2 <= -40:

                    cv2.putText(img, 'Head left', (90, 30),
                                font, 2, (255, 255, 128), 3)
                    add()

                if (ang2 > -40 and ang2 < 40):
                    resetTimer += 1
                    if(resetTimer > 30):
                        count = True
                        resetTimer = 0
                        addTimer = 0

                cv2.putText(img, str(ang1), tuple(p1),
                            font, 2, (128, 255, 255), 3)
                cv2.putText(img, str(ang2), tuple(x1),
                            font, 2, (255, 255, 128), 3)
                # print('div by zero error')
                
                # 라이다
                getTFminiData()





            elif(state == 2 ):



                if ang1 >= 40:

                    cv2.putText(img, 'Head down', (30, 30),
                                font, 2, (255, 255, 128), 3)
                    add()
                elif ang1 <= -40:

                    cv2.putText(img, 'Head up', (30, 30),
                                font, 2, (255, 255, 128), 3)
                    add()

                if ang2 >= 40:

                    cv2.putText(img, 'Head right', (90, 30),
                                font, 2, (255, 255, 128), 3)
                    add()

                elif ang2 <= -40:

                    cv2.putText(img, 'Head left', (90, 30),
                                font, 2, (255, 255, 128), 3)
                    add()

                if (ang2 > -40 and ang2 < 40):
                    resetTimer += 1
                    if(resetTimer > 30):
                        count = True
                        resetTimer = 0
                        addTimer = 0

                cv2.putText(img, str(ang1), tuple(p1),
                            font, 2, (128, 255, 255), 3)
                cv2.putText(img, str(ang2), tuple(x1),
                            font, 2, (255, 255, 128), 3)

                if(closeCounter < farCounter):
                    result01 = "FAR"
                else:
                    result01 = "CLOSE"

                if(isSent==False):
                #sock.SendData('Sent from Python: ' + result)
                    sock.SendData(result01)
                    text=result01


                    print(result01)
                    isSent=True

                

                #else:
                

                    #print(result)


           


                

            elif(state == 3):
                
                
                
                
                decide()
                if(isSent):
                    sock.SendData(result)
                    print(result)
                    isSent=False


               
                #isSent=False
                closeCounter = 1
                farCounter = 1
                #isSent=False
                #saveToFile(dis)
                


                # sendtoUnity

            elif(state == 4):
                
                #sock.SendData(result)
                saveCSV()
                state=0
                #isON=False
                
                
                #sock = U.UdpComms(
                #udpIP="127.0.0.1", portTX=8002, portRX=8001, enableRX=True, suppressWarnings=True
                #)
                

        cv2.imshow('img', img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        break
cv2.destroyAllWindows()
cap.release()

