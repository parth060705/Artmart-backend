import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

def send_otp_email(to_email: str, otp: str):
    sender_email = os.getenv("EMAIL_USER")       # e.g., your Gmail address
    sender_password = os.getenv("EMAIL_PASSWORD") # App password (see below)

    subject = "Your OTP for Password Reset"
    body = f"Your OTP is: {otp}\nValid for 10 minutes."

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # ✅ Gmail SMTP settings
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(sender_email, sender_password)
    server.send_message(msg)
    server.quit()
