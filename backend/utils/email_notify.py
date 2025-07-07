# ==========================================
# 💡 Support Assistant Project .gitignore
# For FastAPI + PostgreSQL + React + Docker
# Author: Shivam Srivastav
# ==========================================

import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
import os

# Load from environment variables or config.py
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "your_email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your_app_password")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)
ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "admin@example.com").split(",")

def setup_email_notifications():
    """
    Called on FastAPI startup — logs or validates the email setup.
    """
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            print("✅ Email server connection successful.")
    except Exception as e:
        print(f"❌ Failed to connect to email server: {e}")

def send_email_notification(subject: str, message: str, to_emails: list = ADMIN_EMAILS):
    """
    Sends an email notification to the given recipients.
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = FROM_EMAIL
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_emails, msg.as_string())

        print(f"✅ Email sent to: {to_emails}")

    except Exception as e:
        print(f"❌ Error sending email: {e}")


def send_upload_notification(to_email: str, subject: str, body: str):
    """
    Send an email notification (e.g., when a file is uploaded or processing completes).

    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            print(f"[✓] Email sent to {to_email}")
    except Exception as e:
        print(f"[✗] Failed to send email: {e}")


def notify_training_complete(to_email: str, model_name: str, details: str = ""):
    """
    Sends an email notification when model training is complete.

    Args:
        to_email (str): Recipient email address
        model_name (str): Name of the trained model
        details (str): Optional additional training info
    """
    subject = f"✅ Training Completed for Model: {model_name}"
    body = f"""
Hello,

The training for your model '{model_name}' has been successfully completed.

Details:
{details or 'No additional details provided.'}

Regards,  
AI Support Assistant
    """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            print(f"[✓] Training notification sent to {to_email}")
    except Exception as e:
        print(f"[✗] Failed to send training notification: {e}")
