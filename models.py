from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import UserMixin
from datetime import datetime

# Create the base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# User model for authentication
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# Section model (J, K, L)
class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    groups = db.relationship('Group', backref='section', lazy=True)
    attendance = db.relationship('Attendance', backref='section', lazy=True)

# Group model (J1, J2, J3, K1, K2, K3, L1, L2, L3)
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    attendance = db.relationship('Attendance', backref='group', lazy=True)

# Subject model (Python, Java, Software Engineering)
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    attendance = db.relationship('Attendance', backref='subject', lazy=True)

# Student model (Tanish, Yuvraj, Vishal, Suraj, Sanyam)
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)  # Added phone number for SMS notifications
    email = db.Column(db.String(100), nullable=True)  # Optional email for future features
    attendance = db.relationship('Attendance', backref='student', lazy=True)
    notification_sent = db.Column(db.Boolean, default=False)  # Track if notification has been sent

# Attendance model
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False)  # 'present' or 'absent'
    date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    notification_sent = db.Column(db.Boolean, default=False)  # Track if absence notification has been sent
