import os
import cloudinary
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=r"C:\Users\ghara\OneDrive\Desktop\parth\FastAPI\app\.env")

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
