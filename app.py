import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import pandas as pd
import base64
import numpy as np
from datetime import datetime
import json
from models import db, User, Section, Group, Subject, Student, Attendance
from utils.face_recognition_utils import process_face_recognition, load_known_faces
from utils.csv_utils import export_attendance_to_csv
from utils.sms_utils import send_absence_notification

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_for_testing")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Function to create tables and initial data
def create_tables_and_data():
    # Create all tables
    db.create_all()
    
    # Check if we need to populate initial data
    if not User.query.filter_by(username="Lachoo").first():
        # Create admin user
        admin = User(username="Lachoo", password_hash=generate_password_hash("Lachoo"))
        db.session.add(admin)
        
        # Create sections
        sections = ["J", "K", "L"]
        for section_name in sections:
            section = Section(name=section_name)
            db.session.add(section)
        
        db.session.commit()
        
        # Create groups
        section_j = Section.query.filter_by(name="J").first()
        section_k = Section.query.filter_by(name="K").first()
        section_l = Section.query.filter_by(name="L").first()
        
        for i in range(1, 4):
            db.session.add(Group(name=f"J{i}", section_id=section_j.id))
            db.session.add(Group(name=f"K{i}", section_id=section_k.id))
            db.session.add(Group(name=f"L{i}", section_id=section_l.id))
        
        db.session.commit()
        
        # Create subjects
        subjects = ["Python", "Java", "Software Engineering"]
        for subject_name in subjects:
            subject = Subject(name=subject_name)
            db.session.add(subject)
        
        db.session.commit()
        
        # Create students with sample phone numbers for demonstration
        student_data = [
            {"name": "Tanish", "phone": "+919876543201"},
            {"name": "Yuvraj", "phone": "+919876543202"},
            {"name": "Vishal", "phone": "+919876543203"},
            {"name": "Suraj", "phone": "+919876543204"},
            {"name": "Sanyam", "phone": "+919876543205"}
        ]
        
        for student_info in student_data:
            student = Student(
                name=student_info["name"],
                phone_number=student_info["phone"]
            )
            db.session.add(student)
        
        db.session.commit()

# Initialize the database
db.init_app(app)

# Create the application context
app_ctx = app.app_context()
app_ctx.push()

# Drop all tables and recreate them
db.drop_all()
db.create_all()
create_tables_and_data()

# Ensure the student faces directory exists
FACES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'faces')
RECOGNIZED_FACES_DIR = os.path.join(os.path.dirname(__file__), 'static', 'recognized_faces')
os.makedirs(FACES_DIR, exist_ok=True)
os.makedirs(RECOGNIZED_FACES_DIR, exist_ok=True)

# Create student face folders
for student in ['Tanish', 'Yuvraj', 'Vishal', 'Suraj', 'Sanyam']:
    student_dir = os.path.join(RECOGNIZED_FACES_DIR, student)
    os.makedirs(student_dir, exist_ok=True)
    # Create all tables
    db.create_all()
    
    # Check if we need to populate initial data
    if not User.query.filter_by(username="Lachoo").first():
        # Create admin user
        admin = User(username="Lachoo", password_hash=generate_password_hash("Lachoo"))
        db.session.add(admin)
        
        # Create sections
        sections = ["J", "K", "L"]
        for section_name in sections:
            section = Section(name=section_name)
            db.session.add(section)
        
        db.session.commit()
        
        # Create groups
        section_j = Section.query.filter_by(name="J").first()
        section_k = Section.query.filter_by(name="K").first()
        section_l = Section.query.filter_by(name="L").first()
        
        for i in range(1, 4):
            db.session.add(Group(name=f"J{i}", section_id=section_j.id))
            db.session.add(Group(name=f"K{i}", section_id=section_k.id))
            db.session.add(Group(name=f"L{i}", section_id=section_l.id))
        
        db.session.commit()
        
        # Create subjects
        subjects = ["Python", "Java", "Software Engineering"]
        for subject_name in subjects:
            subject = Subject(name=subject_name)
            db.session.add(subject)
        
        db.session.commit()
        
        # Create students with sample phone numbers for demonstration
        student_data = [
            {"name": "Tanish", "phone": "+919928687408"},
            {"name": "Yuvraj", "phone": "+916376405987"},
            {"name": "Vishal", "phone": "+919509595111"},
            {"name": "Suraj", "phone": "+919876543204"},
            {"name": "Sanyam", "phone": "+919876543205"}
        ]
        
        for student_info in student_data:
            student = Student(
                name=student_info["name"],
                phone_number=student_info["phone"]
            )
            db.session.add(student)
        
        db.session.commit()

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('selection'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/selection', methods=['GET', 'POST'])
def selection():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        section_id = request.form.get('section')
        group_id = request.form.get('group')
        subject_id = request.form.get('subject')
        
        if not all([section_id, group_id, subject_id]):
            flash('Please select all required fields', 'danger')
            return redirect(url_for('selection'))
        
        # Store selections in session
        session['section_id'] = section_id
        session['group_id'] = group_id
        session['subject_id'] = subject_id
        
        return redirect(url_for('attendance'))
    
    # Fetch data for the form
    sections = Section.query.all()
    subjects = Subject.query.all()
    
    return render_template('selection.html', sections=sections, subjects=subjects)

@app.route('/get_groups/<section_id>')
def get_groups(section_id):
    groups = Group.query.filter_by(section_id=section_id).all()
    return jsonify([{"id": group.id, "name": group.name} for group in groups])

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user_id' not in session or not all(k in session for k in ['section_id', 'group_id', 'subject_id']):
        return redirect(url_for('selection'))
    
    section = Section.query.get(session['section_id'])
    group = Group.query.get(session['group_id'])
    subject = Subject.query.get(session['subject_id'])
    students = Student.query.all()
    
    # Load known faces for recognition
    known_face_encodings, known_face_names = load_known_faces(FACES_DIR)
    
    return render_template('attendance.html', 
                          section=section, 
                          group=group, 
                          subject=subject, 
                          students=students,
                          known_faces={'encodings': json.dumps([e.tolist() for e in known_face_encodings]), 
                                      'names': json.dumps(known_face_names)})

@app.route('/process_attendance', methods=['POST'])
def process_attendance():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    data = request.json
    student_id = data.get('student_id')
    status = data.get('status')
    image_data = data.get('image_data')
    
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    
    # Get section, group, and subject information
    section = Section.query.get(session['section_id'])
    group = Group.query.get(session['group_id'])
    subject = Subject.query.get(session['subject_id'])
    
    # Process the attendance
    if status == 'present':
        if not image_data:
            return jsonify({"success": False, "message": "No image data provided for present student"}), 400
        
        # Process face recognition
        recognition_result = process_face_recognition(image_data, student.name, RECOGNIZED_FACES_DIR)
        
        if not recognition_result['success']:
            return jsonify({"success": False, "message": recognition_result['message']}), 400
    elif status == 'absent':
        # Send SMS notification for absent student if phone number is available
        if student.phone_number:
            notification_result = send_absence_notification(
                student_name=student.name,
                phone_number=student.phone_number,
                subject_name=subject.name,
                section_name=section.name,
                group_name=group.name,
                date=datetime.now().strftime('%Y-%m-%d')
            )
            
            if notification_result['success']:
                logging.info(f"SMS notification sent to {student.name}")
            else:
                logging.warning(f"Failed to send SMS to {student.name}: {notification_result['message']}")
        else:
            logging.warning(f"No phone number available for {student.name}. SMS notification not sent.")
    
    # Record the attendance
    attendance = Attendance(
        student_id=student_id,
        section_id=session['section_id'],
        group_id=session['group_id'],
        subject_id=session['subject_id'],
        status=status,
        date=datetime.now().date(),
        # Mark if notification was sent for absent students
        notification_sent=(status == 'absent' and student.phone_number is not None)
    )
    db.session.add(attendance)
    
    try:
        db.session.commit()
        
        # Prepare response message
        response_message = f"Attendance marked as {status} for {student.name}"
        if status == 'absent' and student.phone_number:
            response_message += ". SMS notification sent."
        elif status == 'absent' and not student.phone_number:
            response_message += ". No phone number available for SMS notification."
            
        return jsonify({
            "success": True, 
            "message": response_message
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/summary')
def summary():
    if 'user_id' not in session or not all(k in session for k in ['section_id', 'group_id', 'subject_id']):
        return redirect(url_for('selection'))
    
    section = Section.query.get(session['section_id'])
    group = Group.query.get(session['group_id'])
    subject = Subject.query.get(session['subject_id'])
    
    # Get attendance for the current selections
    attendance_records = Attendance.query.filter_by(
        section_id=session['section_id'],
        group_id=session['group_id'],
        subject_id=session['subject_id'],
        date=datetime.now().date()
    ).all()
    
    # Organize attendance records
    present_students = []
    absent_students = []
    
    for record in attendance_records:
        student = Student.query.get(record.student_id)
        if record.status == 'present':
            present_students.append(student)
        else:
            absent_students.append(student)
    
    # Export to CSV
    csv_filename = export_attendance_to_csv(
        section.name, 
        group.name, 
        subject.name, 
        present_students, 
        absent_students
    )
    
    return render_template('summary.html', 
                          section=section,
                          group=group,
                          subject=subject,
                          present_students=present_students,
                          absent_students=absent_students,
                          csv_filename=csv_filename,
                          current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/export_csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    section = Section.query.get(session['section_id'])
    group = Group.query.get(session['group_id'])
    subject = Subject.query.get(session['subject_id'])
    
    # Get all students and their attendance status
    attendance_records = Attendance.query.filter_by(
        section_id=session['section_id'],
        group_id=session['group_id'],
        subject_id=session['subject_id'],
        date=datetime.now().date()
    ).all()
    
    # Prepare data for CSV
    present_students = []
    absent_students = []
    
    for record in attendance_records:
        student = Student.query.get(record.student_id)
        if record.status == 'present':
            present_students.append(student)
        else:
            absent_students.append(student)
    
    # Generate CSV file
    csv_filename = export_attendance_to_csv(
        section.name, 
        group.name, 
        subject.name, 
        present_students, 
        absent_students
    )
    
    return jsonify({"success": True, "filename": csv_filename})

# Initialize the app with database
with app.app_context():
    create_tables_and_data()
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
