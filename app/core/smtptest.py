import smtplib
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

# Read credentials
sender_email = os.getenv("EMAIL_USER")
sender_password = os.getenv("EMAIL_PASSWORD")

print(f"Email: {sender_email}")
print(f"Password loaded: {bool(sender_password)}")

try:
    # Connect to Titan SMTP with STARTTLS (recommended)
    server = smtplib.SMTP("smtp.titan.email", 587)
    server.ehlo()               # Identify to the server
    server.starttls()           # Upgrade to secure TLS connection
    server.ehlo()               # Re-identify after STARTTLS

    # Attempt login
    server.login(sender_email, sender_password)
    print("✅ Login successful!")

except smtplib.SMTPAuthenticationError as e:
    print("❌ Authentication failed:", e)

except Exception as e:
    print("⚠️ An error occurred:", e)

finally:
    server.quit()
    print("Connection closed.")
