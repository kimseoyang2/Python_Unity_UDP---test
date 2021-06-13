# Created by Youssef Elashry to allow two-way communication between Python3 and Unity to send and receive strings

# Feel free to use this in your individual or commercial projects BUT make sure to reference me as: Two-way communication between Python 3 and Unity (C#) - Y. T. Elashry
# It would be appreciated if you send me how you have used this in your projects (e.g. Machine Learning) at youssef.elashry@gmail.com

# Use at your own risk
# Use under the Apache License 2.0

# Example of a Python UDP server

import UdpComms as U
import serial
from serial import Serial

import csv


# Create UDP socket to use for sending (and receiving)
sock = U.UdpComms(
    udpIP="127.0.0.1", portTX=8001, portRX=8002, enableRX=True, suppressWarnings=True
)

# 라이다 센서 변수
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

isSent = False
isSame = False


def addDis(val):
    global total
    total += val
    #print(total)


def saveToFile(val):
    global peopleNum
    #text = str(val)
    f = open(
        "C:/Users/jsn07/Desktop/Python_Unity_UDP/lidar.csv",
        "a",
        encoding="utf-8",
        newline="",
    )
    wr = csv.writer(f)
    if peopleNum == 0:
        wr.writerow(["Num", "Val"])
        wr.writerow([peopleNum, text])

    else:
        wr.writerow([peopleNum, text])
    f.close()

    peopleNum += 1


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


while True:


    #sock.SendData('Sent from Python: ' + str(i)) # Send this string to other application
    # i += 1


    data = sock.ReadReceivedData()

     # read data
    if data != None:

      # if NEW data has been received since last ReadReceivedData function call
        print("from Unity",data)  # print new received data
        state = int(data)

    if(state == 0):


        result = "null"
        print("from Unity",data)

    elif state == 1:

        getTFminiData()

    elif(state == 2 ):

        if(closeCounter < farCounter):
            result = "FAR"
        else:
            result = "CLOSE"

        #if(isSent==False):
            #sock.SendData('Sent from Python: ' + result)
        sock.SendData(result)
        text=result


        print(result)
        #isSent=True

        #else:
        state=3

            #print(result)

    elif state == 3:
        #isSent=False
        closeCounter = 1
        farCounter = 1
        #isSent=False
        saveToFile(dis)
        state=0



while __name__ == "__main__":
    try:
        if ser.is_open == False:
            ser.open()

    except KeyboardInterrupt:  # Ctrl+C
        if ser != None:
            ser.close()
