try:
    from flask import Flask, render_template, Response, request, send_file, jsonify
    import cv2 as cv
    import numpy as np
    import face_recognition
    import os
    from datetime import datetime,date
    from werkzeug.utils import secure_filename
    import json
    import pandas as pd
    from flask_mail import Mail, Message

except Exception as e:
    print("Some packeges are missing")

# global virables
global CtString,CdString,jdata

app = Flask(__name__)
mail = Mail(app)

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'fenilshah158@gmail.com'
app.config['MAIL_PASSWORD'] = 'ouxdemcgsihyrgen'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

camera = cv.VideoCapture(0) 

student_info = {}
UPLOAD_FOLDER = 'C:/Users/fenil/Programming/computer_vision/project/temp3_project/img'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

path = 'img'
images = []
className = []

myList = os.listdir(path)

for cl in myList:
    curImg = cv.imread(f'{path}/{cl}')
    images.append(curImg)
    className.append(os.path.splitext(cl)[0])

def findEncoding(images):
    encodeList = []

    for img in images:
        img = cv.cvtColor(img,cv.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

def markAttendance(no):
    with open('Attendance.csv','r+') as f:
        myDataList = f.readlines()
        EnrollmentList = []

        for line in myDataList:
            entry = line.split(',')
            EnrollmentList.append(entry[0])
        

        if no not in EnrollmentList:
            Ctnow = datetime.now()
            CtString = Ctnow.strftime('%H:%M:%S')

            Cdnow = date.today()
            CdString = Cdnow.strftime("%d/%m/%Y")

            jdata = json.load(open("sample.json",'r'))

            for data in jdata:
                if no == data:
                    name = jdata[data]['Name']

            f.writelines(f'\n{no},{name},{CdString},{date.today().strftime("%A")},{CtString}')

    with open('detailed_attendace.csv','r+') as f:
        myDataList = f.readlines()
        EnrollmentList = []

        for line in myDataList:
            entry = line.split(',')
            EnrollmentList.append(entry[0])
        
        for data in jdata:
            if no == data:
                name = jdata[data]['Name']

        f.writelines(f'\n{no},{name},{CdString},{date.today().strftime("%A")},{CtString}')


encodeListKnown = findEncoding(images)    

def gen_frames():  # generate frame by frame from camera
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            frame = cv.flip(frame,1)

            imgs = cv.resize(frame,(0,0),None,0.25,0.25)

            imgs = cv.cvtColor(imgs,cv.COLOR_BGR2RGB)

            facesCurFrame = face_recognition.face_locations(imgs)
            encodesCurFrame = face_recognition.face_encodings(imgs,facesCurFrame)

            for encodeFace,faceLoc in zip(encodesCurFrame,facesCurFrame):
                mathces = face_recognition.compare_faces(encodeListKnown,encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown,encodeFace)

                matchIndex = np.argmin(faceDis)

                if mathces[matchIndex]:
                    no = className[matchIndex]
                    y1,x2,y2,x1 = faceLoc
                    y1,x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
                    cv.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
                    cv.putText(frame,no,(x2+6,y1-6),cv.FONT_HERSHEY_COMPLEX,1,(255,255,255),2)
                    markAttendance(no)

            ret, buffer = cv.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
@app.route('/home')
def index():
    """Video streaming home page."""
    return render_template('temp.html')

@app.route('/registration')
def regiPage():
    with open('sample.json','r') as f:
        data = f.read()
    return render_template("registraion.html",jsonfile = json.dumps(data))

@app.route('/registration',methods=["POST","GET"])
def registration():
        user = request.form["nm"]
        en = request.form["en"]
        email = request.form["email"]
        image = request.files["image"]       
        
        extenstion = image.filename.split('.')[1]

        # checking the length of enrollment num
        if len(en) != 12:
            return "Please enter correct information"

        # face detection
        # imgTemp = cv.cvtColor(image,cv.COLOR_BGR2RGB)
        # imageo = face_recognition.load_image_file(imgTemp)
        # face_locations = face_recognition.face_locations(imageo)

        # if face_locations == []:
        #     return "Sorry, can't detect the face, please upload proper picture"        

        # saveing the image in folder
        image.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(en+"."+extenstion)))

        student_info[en] = {
            "Name" : user.upper(),
            "Email" : email,
            "file_path" : UPLOAD_FOLDER+"/"+image.filename
        }    
        
        # saving the user data into jason file 
        with open("sample.json","w") as f:
            json.dump(student_info,f)

        return  "Succsessfully recive data"

def gimmeAttandace():
    data = pd.read_csv('detailed_attendace.csv')

    mainTime = []
    last_seen = []

    for en in data['Enrollment No'].unique():
        x = data[data['Enrollment No'] == en]
        end = x.iloc[len(x)-1]['Time']
        start = x.iloc[0]['Time']
        endTime = end.split(':')
        startTime = start.split(':')

        last_seen.append(end)

        tempTime = []

        for i in range(len(endTime)):
            tempTime.append(str(abs((int(endTime[i]))-(int(startTime[i])))))
        mainTime.append(":".join(tempTime))

    with open('main_attandance.csv','r+') as f:
        i = 0
        f.writelines(f'{"Enrollment No"},{"Name"},{"Date"},{"Day"},{"Arrival Time"},{"Last Seen"},{"Total Time Spend"}')
        for en in data['Enrollment No'].unique():
            x = data[data['Enrollment No'] == en].iloc[0]
            name = x['Name']

            Ctnow = datetime.now()
            CtString = Ctnow.strftime('%H:%M:%S')

            Cdnow = date.today()
            CdString = Cdnow.strftime("%d/%m/%Y")

            f.writelines(f'\n{en},{name},{CdString},{date.today().strftime("%A")},{CtString},{last_seen[i]},{mainTime[i]}')
            i = i + 1

@app.route('/download')
def download():
        gimmeAttandace()

        # who was not attendated class
        with open('sample.json') as f:
            data = json.load(f)

        main_Data = []

        for k in data:
            main_Data.append(k)

        df = pd.read_csv('Attendance.csv')
        temp = np.array((df['Enrollment No']))

        newtemp = []

        for data in temp:
            newtemp.append(str(data))

        dumb = []
        Email = []

        for acutal in main_Data:
            if acutal not in newtemp:
                dumb.append(acutal)

        if not dumb:
            pass
        else:
            with open('sample.json') as f:
                data = json.load(f)
                for no in dumb:
                    Email.append(data[no]['Email'])


            # mail sending 
            msg = Message(
                    'Attendance',
                    sender ='fenilshah158@gmail.com',
                    recipients = Email
                )
            msg.body = 'Your child was not attended Todays class'
            mail.send(msg)

        return send_file("main_attandance.csv",as_attachment=True)


@app.route('/attandance')
def displayAttandance():
    data = pd.read_csv('Attendance.csv')
    return render_template("attandance.html",tables=[data.to_html()],titles=[''])

if __name__ == '__main__':
    app.run(debug=True)