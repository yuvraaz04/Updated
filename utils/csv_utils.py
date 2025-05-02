import os
import csv
from datetime import datetime

def export_attendance_to_csv(section_name, group_name, subject_name, present_students, absent_students):
    """
    Export attendance data to a CSV file
    
    Args:
        section_name: Name of the section
        group_name: Name of the group
        subject_name: Name of the subject
        present_students: List of present student objects
        absent_students: List of absent student objects
        
    Returns:
        The path to the generated CSV file
    """
    # Create directory for CSV files if it doesn't exist
    csv_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'csv')
    os.makedirs(csv_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"attendance_{section_name}_{group_name}_{subject_name}_{timestamp}.csv"
    filepath = os.path.join(csv_dir, filename)
    
    # Create CSV file
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Date', 'Section', 'Group', 'Subject', 'Student Name', 'Status', 'Phone Number', 'Notification Sent'])
        
        # Write present students
        for student in present_students:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                section_name,
                group_name,
                subject_name,
                student.name,
                'Present',
                student.phone_number or 'N/A',
                'N/A'  # No notifications for present students
            ])
            
        # Write absent students
        for student in absent_students:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                section_name,
                group_name,
                subject_name,
                student.name,
                'Absent',
                student.phone_number or 'N/A',
                'Yes' if student.phone_number else 'No'  # Notifications only sent if phone number exists
            ])
    
    return filename
