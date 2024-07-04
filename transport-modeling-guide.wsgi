import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(stream=sys.stderr)

# Add the project directory to the sys.path
sys.path.insert(0, "/var/www/transport-modeling-guide")

# Load environment variables from .env file
load_dotenv()

# Import the Flask application
from app import app as application
