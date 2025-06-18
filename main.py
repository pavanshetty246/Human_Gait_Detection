import numpy as np
import math
import time
from flask import Flask, render_template, redirect, url_for, flash, request, session, Response, send_from_directory
import mysql.connector
from mysql.connector import Error
from werkzeug.utils import secure_filename
import os
import bcrypt
import cv2
import mediapipe as mp
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'zmdb'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join('static', 'processed_video')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}




# MySQL Database Connection
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        database='gait',
        user='root',
        password=''
    )
    return connection

# Allowed file check for video uploads
def allowed_file(filename):
    print(f"Received filename: {filename}")  # Debugging line
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/')
def index():
    return render_template('index.html')




@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))





@app.route('/dashboard')
def dashboard():
    physiotherapist_id = session.get('physiotherapist_id')  # Assuming you have a session variable for the logged-in physiotherapist

    total_patients = 0
    total_reports = 0
    total_physiotherapists = 0

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch total patients for the logged-in physiotherapist
        cursor.execute("SELECT COUNT(*) as count FROM patients WHERE physiotherapist_id=%s", (physiotherapist_id,))
        total_patients = cursor.fetchone()['count']

        # Fetch total reports
        cursor.execute("SELECT COUNT(*) as count FROM logs where physiotherapist_id=%s",(physiotherapist_id,))  # Modify as per your reports table
        total_reports = cursor.fetchone()['count']

        # Fetch total physiotherapists
        cursor.execute("SELECT COUNT(*) as count FROM physiotherapists")  # Modify as per your physiotherapists table
        total_physiotherapists = cursor.fetchone()['count']

    except Error as e:
        print(e)
        flash('Error occurred while fetching dashboard data.', 'danger')

    finally:
        cursor.close()
        connection.close()

    return render_template('dashboard.html',
                           total_patients=total_patients,
                           total_reports=total_reports,
                           total_physiotherapists=total_physiotherapists)

# Register a physiotherapist
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check if email exists
            cursor.execute("SELECT * FROM physiotherapists WHERE email=%s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email already exists!', 'danger')
                return redirect(url_for('register'))

            # Insert the new user
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO physiotherapists (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, hashed_password))
            connection.commit()

            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))

        except Error as e:
            print(e)
            flash('Error occurred during registration.', 'danger')

        finally:
            cursor.close()
            connection.close()

    return render_template('register.html')

# Login physiotherapist
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # Fetch user by email
            cursor.execute("SELECT * FROM physiotherapists WHERE email=%s", (email,))
            physiotherapist = cursor.fetchone()

            if physiotherapist and bcrypt.checkpw(password.encode('utf-8'), physiotherapist['password'].encode('utf-8')):
                session['physiotherapist_id'] = physiotherapist['id']
                session['name'] = physiotherapist['name']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')

        except Error as e:
            print(e)
            flash('Error occurred during login.', 'danger')

        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

# Dashboard to manage patients
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():

    physiotherapist_id = session.get('physiotherapist_id')

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch patients for the logged-in physiotherapist
        cursor.execute("SELECT * FROM patients WHERE physiotherapist_id=%s", (physiotherapist_id,))
        patients = cursor.fetchall()

        if request.method == 'POST':
            name = request.form['name']
            age = request.form['age']
            diagnosis = request.form['diagnosis']

            # Insert patient data
            cursor.execute("INSERT INTO patients (name, age, diagnosis, physiotherapist_id) VALUES (%s, %s, %s, %s)",
                           (name, age, diagnosis, physiotherapist_id))
            connection.commit()
            flash('Patient added successfully!', 'success')
            return redirect(url_for('add_patient'))

    except Error as e:
        print(e)
        flash('Error occurred while fetching or adding patients.', 'danger')

    finally:
        cursor.close()
        connection.close()

    return render_template('add_patient.html',patients=patients)



@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Fetch the patient's current details
        cursor.execute("SELECT * FROM patients WHERE id=%s", (id,))
        patient = cursor.fetchone()

        # If patient is not found, redirect with an error message
        if not patient:
            flash('Patient not found.', 'danger')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            name = request.form['name']
            age = request.form['age']
            diagnosis = request.form['diagnosis']

            # Update patient details
            cursor.execute("UPDATE patients SET name=%s, age=%s, diagnosis=%s WHERE id=%s",
                           (name, age, diagnosis, id))
            connection.commit()
            flash('Patient details updated!', 'success')
            return redirect(url_for('add_patient'))

    except Error as e:
        print(e)
        flash('Error occurred while editing patient.', 'danger')
        
    finally:
        cursor.close()
        connection.close()

    # Render the edit_patient.html template with patient details
    return render_template('add_patient.html', patient=patient)


# Delete patient
@app.route('/patient/<int:id>/delete', methods=['POST'])
def delete_patient(id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Delete patient record
        cursor.execute("DELETE FROM patients WHERE id=%s", (id,))
        connection.commit()

        flash('Patient deleted successfully!', 'success')
        return redirect(url_for('add_patient'))

    except Error as e:
        print(e)
        flash('Error occurred while deleting patient.', 'danger')

    finally:
        cursor.close()
        connection.close()



@app.route('/upload_video', methods=['POST','GET'])
def upload_video():
    physiotherapist_id = session.get('physiotherapist_id')

    if request.method == 'GET':
        print("fghj")
        connection = get_db_connection()  # Ensure you have this function defined elsewhere
        cursor = connection.cursor(dictionary=True)

        # Fetch patients for the logged-in physiotherapist
        cursor.execute("SELECT * FROM patients WHERE physiotherapist_id=%s", (physiotherapist_id,))
        patients = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template('upload_video.html', patients=patients)
    
    if request.method=='POST':
    
        patient_id = request.form['patient_id']
    

        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return redirect(request.url)
        
        # Save the uploaded file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        print(filepath,"dfghj")

        # Process the video
        result = process_video(filepath)
        result_serialized = json.dumps(result) 
        print(physiotherapist_id,result_serialized,patient_id)

        # Return results (you can modify this to return a more user-friendly response)

        connection = get_db_connection()  # Re-establish connection for logging
        cursor = connection.cursor()

        try:
            # Log the video upload and result
            cursor.execute(
                "INSERT INTO logs (physiotherapist_id, patient_id, filepath, result) VALUES (%s, %s, %s, %s)",
                (physiotherapist_id, patient_id, filepath, result_serialized)
            )
            connection.commit()

            flash('Video uploaded and gait analyzed!', 'success')
        except Error as e:
            print(f"Database error: {e}")
            flash('Error occurred during video upload. Please try again.', 'danger')
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('upload_video'))

@app.route('/report', methods=['GET', 'POST'])
def physiotherapist_report():
    physiotherapist_id = session.get('physiotherapist_id')
    connection = get_db_connection()  # Ensure you have this function defined elsewhere
    cursor = connection.cursor(dictionary=True)

    # Initialize filters
    patient_name = request.form.get('patient_name', '').strip()
    report_date = request.form.get('report_date', '')

    # Construct the base query
    query = """
        SELECT p.name AS patient_name, p.age, p.diagnosis, l.result, l.date AS date, l.filepath
        FROM patients p
        INNER JOIN logs l ON p.id = l.patient_id
        WHERE p.physiotherapist_id = %s
    """

    filters = [physiotherapist_id]

    # Add filters based on user input
    if patient_name:
        query += " AND p.name LIKE %s"
        filters.append(f"%{patient_name}%")
    
    if report_date:
        query += " AND DATE(l.date) = %s"
        filters.append(report_date)

    # Execute the query with filters
    query += " ORDER BY l.date DESC"
    cursor.execute(query, filters)
    reports = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('report.html', reports=reports)






def process_video(video_path):
    # Your existing video processing code goes here
    # Replace the video path in your code with `video_path`
    # For example, replace `cap = cv2.VideoCapture(r"C:\Users\User\Downloads\Parkinsonian Gait (1).mp4")`
    # with `cap = cv2.VideoCapture(video_path)`

    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    mp_draw = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(video_path)

        # Initialize variables for analysis
    rl1, rl2, rl3 = 24, 26, 28
    ll1, ll2, ll3 = 23, 25, 27
    left_ear, left_shoulder, left_hip = 8, 12, 24
    ra1, ra2, ra3 = 11, 13, 15
    la1, la2, la3 = 12, 14, 16
    rs1, rs2, rs3 = 23, 11, 15
    ls1, ls2, ls3 = 24, 12, 16


    right_toe_y = []
    right_toe_x = []
    left_toe_y = []
    left_toe_x = []
    left_heel_x = []
    left_heel_y = []
    right_heel_x = []
    right_heel_y = []
    right_arm_x = []
    right_arm_y = []
    left_arm_x = []
    left_arm_y = []

    check_lead_foot = 0 #boolean
    no_total_frame = 0
    no_neck_frame = 0
    no_rightleg_frame = 0
    no_leftleg_frame = 0
    no_limping_right = 0
    no_limping_left = 0
    no_swing_right = 0
    no_swing_left = 0
    lead_foot_right = 0
    lead_foot_left = 0


    while True:
        try:
            # read videos
            ret, img = cap.read()
            cv2.imshow('Frame', img)
            cv2.waitKey(1)
            results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            mp_draw.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            h, w, c = img.shape
            opImg = np.zeros([h, w, c])
            opImg.fill(128)
            mp_draw.draw_landmarks(opImg, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_draw.DrawingSpec((255, 0, 0), 2, 2),
                                mp_draw.DrawingSpec((255, 0, 255), 2, 2))

            ########################################################################### Start analyze ################################################################################
            # Read data by mediapipe
            result=[]
            new_lmList = []
            if results.pose_landmarks:
                for id, lm in enumerate(results.pose_landmarks.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    new_lmList.append([id, cx, cy])
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)

            if len(new_lmList) != 0:
                no_total_frame += 1
                cv2.putText(img, str(no_total_frame), (50, 50),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 256, 0), 2)

                # Right leg
                rx1, ry1 = new_lmList[rl1][1:]
                rx2, ry2 = new_lmList[rl2][1:]
                rx3, ry3 = new_lmList[rl3][1:]
                # Calculate the angle right leg
                right_angle = math.degrees(math.atan2(ry3 - ry2, rx3 - rx2) - math.atan2(ry1 - ry2, rx1 - rx2))
                if right_angle < 0:
                    right_angle += 360
                
                # Left leg
                lx1, ly1 = new_lmList[ll1][1:]
                lx2, ly2 = new_lmList[ll2][1:]
                lx3, ly3 = new_lmList[ll3][1:]
                # Calculate the angle left leg
                left_angle = math.degrees(math.atan2(ly3 - ly2, lx3 - lx2) - math.atan2(ly1 - ly2, lx1 - lx2))
                if left_angle < 0:
                    left_angle += 360

                # Right arm
                rax1, ray1 = new_lmList[ra1][1:]
                rax2, ray2 = new_lmList[ra2][1:]
                rax3, ray3 = new_lmList[ra3][1:]
                # Calculate the angle right arm
                right_arm_angle = math.degrees(math.atan2(ray3 - ray2, rax3 - rax2) - math.atan2(ray1 - ray2, rax1 - rax2))
                if right_arm_angle < 0:
                    right_arm_angle += 360
                
                # Left arm
                lax1, lay1 = new_lmList[la1][1:]
                lax2, lay2 = new_lmList[la2][1:]
                lax3, lay3 = new_lmList[la3][1:]
                # Calculate the angle left arm
                left_arm_angle = math.degrees(math.atan2(lay3 - lay2, lax3 - lax2) - math.atan2(lay1 - lay2, lax1 - lax2))
                if left_arm_angle < 0:
                    left_arm_angle += 360

                # Right shoulder
                rsx1, rsy1 = new_lmList[rs1][1:]
                rsx2, rsy2 = new_lmList[rs2][1:]
                rsx3, rsy3 = new_lmList[rs3][1:]
                # Calculate the angle right arm
                right_shoulder_angle = math.degrees(math.atan2(rsy3 - rsy2, rsx3 - rsx2) - math.atan2(rsy1 - rsy2, rsx1 - rsx2))
                # if right_shoulder_angle < 0:
                #     right_shoulder_angle += 360
                
                # Left shoulder
                lsx1, lsy1 = new_lmList[ls1][1:]
                lsx2, lsy2 = new_lmList[ls2][1:]
                lsx3, lsy3 = new_lmList[ls3][1:]
                # Calculate the angle left arm
                left_shoulder_angle = math.degrees(math.atan2(lsy3 - lsy2, lsx3 - lsx2) - math.atan2(lsy1 - lsy2, lsx1 - lsx2))
                # if left_shoulder_angle < 0:
                #     left_shoulder_angle += 360

                # Showing line and angle two legs
                cv2.line(img, (rx1, ry1), (rx2, ry2), (255, 255, 255), 3)
                cv2.line(img, (rx3, ry3), (rx2, ry2), (255, 255, 255), 3)
                cv2.circle(img, (rx1, ry1), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rx1, ry1), 15, (0, 0, 255), 2)
                cv2.circle(img, (rx2, ry2), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rx2, ry2), 15, (0, 0, 255), 2)
                cv2.circle(img, (rx3, ry3), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rx3, ry3), 15, (0, 0, 255), 2)
                cv2.putText(img, str(int(right_angle)), (rx2 - 50, ry2 + 50),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                cv2.line(img, (lx1, ly1), (lx2, ly2), (255, 255, 255), 3)
                cv2.line(img, (lx3, ly3), (lx2, ly2), (255, 255, 255), 3)
                cv2.circle(img, (lx1, ly1), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lx1, ly1), 15, (0, 255, 0), 2)
                cv2.circle(img, (lx2, ly2), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lx2, ly2), 15, (0, 255, 0), 2)                 
                cv2.circle(img, (lx3, ly3), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lx3, ly3), 15, (0, 255, 0), 2)
                cv2.putText(img, str(int(left_angle)), (lx2 - 50, ly2 + 50),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                
                # Showing line and angle two arms
                cv2.line(img, (rax1, ray1), (rax2, ray2), (255, 255, 255), 3)
                cv2.line(img, (rax3, ray3), (rax2, ray2), (255, 255, 255), 3)
                cv2.circle(img, (rax1, ray1), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rax1, ray1), 15, (0, 0, 255), 2)
                cv2.circle(img, (rax2, ray2), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rax2, ray2), 15, (0, 0, 255), 2)
                cv2.circle(img, (rax3, ray3), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rax3, ray3), 15, (0, 0, 255), 2)
                # cv2.putText(img, str(int(right_arm_angle)), (rax2 - 50, ray2 + 50),
                #             cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                cv2.line(img, (lax1, lay1), (lax2, lay2), (255, 255, 255), 3)
                cv2.line(img, (lax3, lay3), (lax2, lay2), (255, 255, 255), 3)
                cv2.circle(img, (lax1, lay1), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lax1, lay1), 15, (0, 255, 0), 2)
                cv2.circle(img, (lax2, lay2), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lax2, lay2), 15, (0, 255, 0), 2)                 
                cv2.circle(img, (lax3, lay3), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lax3, lay3), 15, (0, 255, 0), 2)
                # cv2.putText(img, str(int(left_arm_angle)), (lax2 - 50, lay2 + 50),
                #             cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                
                # Showing angle sholder
                cv2.line(img, (rsx1, rsy1), (rax2, ray2), (255, 255, 255), 3)
                cv2.line(img, (rsx3, rsy3), (rax2, ray2), (255, 255, 255), 3)
                cv2.circle(img, (rsx1, rsy1), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rsx1, rsy1), 15, (0, 0, 255), 2)
                cv2.circle(img, (rsx2, rsy2), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rsx2, rsy2), 15, (0, 0, 255), 2)
                cv2.circle(img, (rsx3, rsy3), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (rsx3, rsy3), 15, (0, 0, 255), 2)
                cv2.putText(img, str(int(right_shoulder_angle)), (rax2 - 50, ray2 + 50),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                cv2.line(img, (lsx1, lsy1), (lsx2, lsy2), (255, 255, 255), 3)
                cv2.line(img, (lsx3, lsy3), (lsx2, lsy2), (255, 255, 255), 3)
                cv2.circle(img, (lsx1, lsy1), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lsx1, lsy1), 15, (0, 255, 0), 2)
                cv2.circle(img, (lsx2, lsy2), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lsx2, lsy2), 15, (0, 255, 0), 2)                 
                cv2.circle(img, (lsx3, lsy3), 10, (0, 255, 0), cv2.FILLED)
                cv2.circle(img, (lsx3, lsy3), 15, (0, 255, 0), 2)
                cv2.putText(img, str(int(left_shoulder_angle)), (lsx2 - 50, lsy2 + 50),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
            
                #Showing angle of shoulder
                # cv2.putText(img, "angle right shoulder : " + str(int(right_shoulder_angle)), (50, 125),
                #                 cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 5)
                # cv2.putText(img, "angle right shoulder : " + str(int(right_shoulder_angle)), (50, 125),
                #                 cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                # cv2.putText(img, "angle left shoulder : " + str(int(left_shoulder_angle)), (50, 150),
                #                 cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 5)
                # cv2.putText(img, "angle left shoulder : " + str(int(left_shoulder_angle)), (50, 150),
                #                 cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)

                ############################################################################### Circumduction ################################################################################## 
                #data for check Circumduction (some leg always swing phase)
                if 200 > right_angle > 160 :
                    no_rightleg_frame += 1
                if 200 > left_angle > 160 :
                    no_leftleg_frame += 1
                # Circumduction 99% of one leg always swing phase
                if no_rightleg_frame / no_total_frame > 0.99 or no_leftleg_frame / no_total_frame > 0.99:
                    cv2.putText(img, "Gait abnormal - risk : Circumduction", (50, 100),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 5)
                    cv2.putText(img, "Gait abnormal - risk : Circumduction", (50, 100),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
                
                ############################################################################# Slouch posture ###################################################################################
                # display angle of neck / bent
                left_ear_x, left_ear_y = new_lmList[left_ear][1:]
                left_shoulder_x, left_shoulder_y = new_lmList[left_shoulder][1:]
                left_hip_x, left_hip_y = new_lmList[left_hip][1:]
                left_ear_angle = math.degrees(math.atan2(left_hip_y - left_shoulder_y, left_hip_x - left_shoulder_x) - math.atan2(left_ear_y - left_shoulder_y, left_ear_x - left_shoulder_x))

                if left_ear_angle < 0:
                    left_ear_angle += 360

                cv2.line(img, (left_ear_x, left_ear_y), (left_shoulder_x, left_shoulder_y), (255, 255, 255), 3)
                cv2.line(img, (left_hip_x, left_hip_y), (left_shoulder_x, left_shoulder_y), (255, 255, 255), 3)
                cv2.circle(img, (left_ear_x, left_ear_y), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (left_ear_x, left_ear_y), 15, (0, 0, 255), 2)
                cv2.circle(img, (left_shoulder_x, left_shoulder_y), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (left_shoulder_x, left_shoulder_y), 15, (0, 0, 255), 2)
                cv2.circle(img, (left_hip_x, left_hip_y), 10, (0, 0, 255), cv2.FILLED)
                cv2.circle(img, (left_hip_x, left_hip_y), 15, (0, 0, 255), 2)
                cv2.putText(img, str(int(left_ear_angle)-180), (left_shoulder_x - 50, left_shoulder_y + 50),
                            cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

                if left_ear_angle - 180 > 30 or left_ear_angle - 180 < -30 :
                    no_neck_frame += 1

                if no_neck_frame / no_total_frame > 0.6 :
                    cv2.putText(img, "Gait abnormal - risk : Slouch posture", (50, 125),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 5)
                    cv2.putText(img, "Gait abnormal - risk : Slouch posture", (50, 125),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
                
                ############################################################################# Gait limping ################################################################################
                # Gait limping read toe and heel point
                right_toe_index_x, right_toe_index_y = new_lmList[32][1:]
                right_heel_index_x, right_heel_index_y = new_lmList[30][1:]
                left_toe_index_x, left_toe_index_y = new_lmList[31][1:]
                left_heel_index_x, left_heel_index_y = new_lmList[29][1:]
                right_toe_y.append(right_toe_index_y)
                right_toe_x.append(right_toe_index_x)
                right_heel_x.append(right_heel_index_x)
                right_heel_y.append(right_heel_index_y)
                left_toe_y.append(left_toe_index_y)
                left_toe_x.append(left_toe_index_x)
                left_heel_x.append(left_heel_index_x)
                left_heel_y.append(left_heel_index_y)
                # print("X : ", right_toe_index_x, "     Y : ", right_toe_index_y)

                if left_toe_index_x > left_heel_index_x: #Check gait side (right side)
                    if left_toe_index_x > right_heel_index_x:
                        check_lead_foot = 1 #Left foot is lead
                        no_limping_left += 1
                    else:
                        check_lead_foot = 0 #Right foot is lead
                        no_limping_right += 1
                elif left_toe_index_x < left_heel_index_x:
                    if left_toe_index_x < right_heel_index_x:
                        check_lead_foot = 1 #Left foot is lead
                        no_limping_left += 1
                    else:
                        check_lead_foot = 0 #Right foot is lead
                        no_limping_right += 1

                if no_limping_right / no_total_frame > 0.75 or no_limping_left / no_total_frame > 0.75:
                    cv2.putText(img, "Gait abnormal - risk : Limping", (50, 150),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 5)
                    cv2.putText(img, "Gait abnormal - risk : Limping", (50, 150),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
                #Showing Lead of feet
                if check_lead_foot:
                    cv2.putText(img, "Lead foot : left", (50, 350),
                                cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                else:
                    cv2.putText(img, "Lead foot : right", (50, 350),
                                cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                
                ############################################################################# No arm swing ################################################################################
                if left_shoulder_angle <= 15 and left_shoulder_angle >= -15: 
                    no_swing_left += 1
                if right_shoulder_angle <= 15 and right_shoulder_angle >= -15:
                    no_swing_right += 1
                
                if no_swing_right / no_total_frame > 0.90:
                    cv2.putText(img, "Gait abnormal - risk : Left arm no swing", (50, 175),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 5)
                    cv2.putText(img, "Gait abnormal - risk : Left arm no swing", (50, 175),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
                if no_swing_left / no_total_frame > 0.90:
                    cv2.putText(img, "Gait abnormal - risk : Right arm no swing", (50, 200),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 5)
                    cv2.putText(img, "Gait abnormal - risk : Right arm no swing", (50, 200),
                                cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), 2)
                    
                print("="*20)
                # Check Neck, Circumduction(R L legs), Limping(R L feet), No arm swing(R L shoulder)
                print("Slouch posture : %.3f "%float(no_neck_frame / no_total_frame), "\nStraight \t Right leg : %.3f "%float(no_rightleg_frame / no_total_frame), "\tLeft leg : %.3f "%float(no_leftleg_frame / no_total_frame), "\nLimping \t right leg : %.3f "%float(no_limping_right / no_total_frame), "\t left leg : %.3f "%float(no_limping_left / no_total_frame), "\nNo swing \t Right arm : %.3f "%float(no_swing_right / no_total_frame), "\t Left arm : %.3f"%float(no_swing_left / no_total_frame))
                print("="*20)

            cv2.imshow("Extracted Pose", opImg)
            cv2.imshow("Pose Estimation", img)

            # Break the loop if the user presses 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except:
            no_gait = 0
            
            print("="*30," Conclude ", "="*30, "\n Gait abnormal - risk : ", sep='', end='')
            if no_limping_right / no_total_frame > 0.75 or no_limping_left / no_total_frame > 0.75:
                no_gait += 1
                result=result+["Limping"]
                print("\n\t- Limping", end='')
            if no_neck_frame / no_total_frame > 0.60 :
                no_gait += 1
                result=result+["Slouch posture"]
                print("\n\t- Slouch posture", end='')
            if no_rightleg_frame / no_total_frame > 0.99 or no_leftleg_frame / no_total_frame > 0.99:
                no_gait += 1
                result=result+["Circumduction"]
                print("\n\t- Circumduction", end='')
            if no_swing_right / no_total_frame > 0.90:
                no_gait += 1
                result=result+["Right arm no swing"]
                print("\n\t- Right arm no swing", end='')
            if no_swing_left / no_total_frame > 0.90:
                no_gait += 1
                result=result+["Left arm no swing"]
                print("\n\t- Left arm no swing", end='')
            if no_gait == 0:
                result=result+["No risk"]
                print("No risk", end='')
            print()
            print("="*70)
            break


    # At the end, return a summary of the results
    cap.release()
    cv2.destroyAllWindows()

    return result

if __name__ == '__main__':
    app.run(debug=True)