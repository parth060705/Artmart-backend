import smtplib
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASSWORD")


server = smtplib.SMTP_SSL("smtp.titan.email", 465)
try:
    server.login(sender_email, sender_password)
    print("Login successful!")
except smtplib.SMTPAuthenticationError as e:
    print("Authentication failed:", e)
finally:
    server.quit()
