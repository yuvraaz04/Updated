import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

def send_absence_notification(student_name, phone_number, subject_name, section_name, group_name, date):
    """
    Send an SMS notification to a student who was marked absent
    
    Args:
        student_name: Name of the student
        phone_number: Student's phone number to send the SMS to
        subject_name: Name of the subject
        section_name: Name of the section
        group_name: Name of the group
        date: Date of the absence
        
    Returns:
        dict: Result of the notification attempt
    """
    # Check if phone number is provided
    if not phone_number:
        logging.warning(f"No phone number available for {student_name}. SMS notification not sent.")
        return {
            "success": False,
            "message": f"No phone number available for {student_name}"
        }
    
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Validate Twilio credentials
    if not all([account_sid, auth_token, twilio_phone]):
        logging.error("Twilio credentials not found in environment variables")
        return {
            "success": False,
            "message": "Twilio credentials not configured"
        }
    
    try:
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Compose message
        message_body = (
            f"Dear {student_name}, this is an automated message from Lachoo College.\n\n"
            f"You were marked absent for {subject_name} in section {section_name}, "
            f"group {group_name} on {date}.\n\n"
            f"Please contact the faculty for more information."
        )
        
        # Send the SMS
        message = client.messages.create(
            body=message_body,
            from_=twilio_phone,
            to=phone_number
        )
        
        logging.info(f"SMS notification sent to {student_name} at {phone_number}: {message.sid}")
        return {
            "success": True,
            "message": f"SMS notification sent to {student_name}",
            "sid": message.sid
        }
        
    except TwilioRestException as e:
        logging.error(f"Twilio error while sending SMS to {student_name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error sending SMS: {str(e)}"
        }
    except Exception as e:
        logging.error(f"Error sending SMS notification to {student_name}: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }