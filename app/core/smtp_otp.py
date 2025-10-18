# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from dotenv import load_dotenv
# import os

# # Load .env variables
# load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

# def send_otp_email(to_email: str, otp: str):
#     sender_email = os.getenv("EMAIL_USER")       # e.g., your Gmail address
#     sender_password = os.getenv("EMAIL_PASSWORD") # App password (see below)
    

#     subject = "Your OTP for Password Reset"
#     body = f"Your OTP is: {otp}\nValid for 10 minutes."

#     msg = MIMEMultipart()
#     msg["From"] = sender_email
#     msg["To"] = to_email
#     msg["Subject"] = subject
#     msg.attach(MIMEText(body, "plain"))

#     # ✅ Gmail SMTP settings
#     server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
#     server.login(sender_email, sender_password)
#     server.send_message(msg)
#     server.quit()



import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# ✅ Load .env variables (adjust path if needed)
load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

# ✅ Use the correct SendGrid API Key environment variable
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Change to match your .env key name
FROM_EMAIL = "auroraa@auroraa.in"  # Must be a verified sender in SendGrid

def send_otp_email(to_email: str, otp: str):
    """Send OTP email via SendGrid."""
    subject = "Your OTP for Password Reset"
    body = f"Your OTP is: {otp}\n\nThis code is valid for 10 minutes."

    # ✅ Create SendGrid Mail object
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"✅ Email sent to {to_email}! Status: {response.status_code}")
        return {"status": "success", "code": response.status_code}
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return {"status": "error", "message": str(e)}
