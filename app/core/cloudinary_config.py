import os
import cloudinary
from dotenv import load_dotenv

load_dotenv()  # Looks for a .env file in the current working directory

cloudinary.config(
    cloud_name=("dwldu16e9"),
    api_key=("567475229725234"),
    api_secret=("7hg65Yisnqd0mUHeWdf6WMcKY-M"),
    secure=True
)

# os.getenv