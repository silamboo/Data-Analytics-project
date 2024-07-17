import cv2
import pickle
import cvzone
import numpy as np
from flask import Flask, render_template, request, session
import re
import ibm_db



app = Flask(__name__)

conn = ibm_db.connect("DATABASE=bludb; HOSTNAME=2f3279a5-73d1-4859-88f0-a6c3e6b4b907.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=30756;PROTOCOL=TCPIP;UID=dpp16990;
                PWD=VMckXGtgoJf0Hlnc;", "", "")
print("connected")


@app.route('/')
def project():
    return render_template('index.html')

@app.route('/hero')
def home():
    return render_template('index.html')

@app.route('/model')
def model():
    return render_template('model.html')

@app.route('/login')
def login():
    return render_template('login.html')

def signup():
    msg = ''
    if request.method == 'POST':
        name = request.form["Full Name"]
        emailAddress = request.form["Email Address"]
        username = request.form["Username"]
        Password = request.form["Password"]
        confirmPassword = request.form["Confirm Password"]
        sql = "SELECT * FROM REGISTER WHERE name=?"
        stmt = ibm_db.program(conn, sql)
        ibm_db.bind_param(stmt,1,name)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            return render_template('login.html', error=True)
        elif not re.match(r'[^@]+@[^@]+\.[^@]+',emailAddress):
            msg = "Invalid Email Address!"
        else:
            insert_sql = "INSERT INTO REGISTER VALUES (?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, emailAddress )
            ibm_db.bind_param(prep_stmt, 3, username)
            ibm_db.bind_param(prep_stmt, 4, Password)
            ibm_db.bind_param(prep_stmt, 5, confirmPassword)
            ibm_db.execute(prep_stmt)
            msg = "You have successfully registered !"
    return render_template('login.html', msg=msg)


@app.route("/log", methods=['POST', 'GET'])
def login1():
    if request.method == "POST":
        Username  = request.form["Username"]
        Password = request.form["Password"]
        sql = "SELECT * FROM REGISTER WHERE USERNAME=? AND PASSWORD=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, Username)
        ibm_db.bind_param(stmt, 2, Password)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            session['Loggedin'] = True
            session['id'] = account['Email']
            session['email'] = account['Email']
            return render_template('model.html')
        else:
            msg = "Incorrect Email/password"
            return render_template('login.html', msg=msg)
    else:
        return render_template('login.html')





cap = cv2.VideoCapture('carParkingInput.mp4')

with open('CarParkPos', 'rb') as f:
    posList = pickle.load(f)


width, height = 107, 48

def checkParkingSpace(imgPro):
    spaceCounter = 0
    for pos in posList:
        x,y = pos

        imgCrop = imgPro[y:y+height, x:x+width]
        #cv2.imshow(str(x*y),imgCrop)
        count = cv2.countNonZero(imgCrop)
        cvzone.putTextRect(img, str(count),(x,y+height-3), scale=0.75,
                           thickness=2, offset=0, colorR = (0, 0, 255))



        if count < 800:
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1

        else:
            color = (0, 0, 255)
            thickness = 2
        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)

    cvzone.putTextRect(img, f'FREE:{spaceCounter}/{len(posList)}', (100, 50), scale=3,
                       thickness=5, offset=20, colorR=(0, 0, 0))


while True:

    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES,0)
    success, img = cap.read()
    imgGray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
    imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                         cv2.THRESH_BINARY_INV, 25, 16)
    imgMedian = cv2.medianBlur(imgThreshold, 5)
    kernel = np.ones((3,3), np.int8)
    imgDilate = cv2.dilate(imgMedian, kernel, iterations = 1 )



    checkParkingSpace(imgDilate)
    #for pos in posList:
     #   cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), (255, 0, 255), 2)

    cv2.imshow("Image",img)
    #cv2.imshow("ImageBlur", imgBlur)
    #cv2.imshow("ImageThresh", imgMedian)
    cv2.waitKey(10)


if __name__ == "__main__":
    app.run(debug=True)
