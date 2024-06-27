# config.py
import os
from git import Repo

class Config:
    SECRET_KEY = 'supersecretkey'
    BASE_UPLOAD_FOLDER = 'uploads'
    ORIGINAL_LIBRARY_PATH = '../transport_model_9th_edition_public'
    USER_DATA_FILE = 'user_data.txt'
    SESSION_TIMEOUT = 3600  # Session timeout in seconds

    # Flask-Mail configuration
    MAIL_SERVER = 'smtp.example.com'  # Replace with your SMTP server
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'your-email@example.com'  # Replace with your email
    MAIL_PASSWORD = 'your-email-password'  # Replace with your email password

    # APScheduler configuration
    JOBS = [
        {
            'id': 'session_cleanup',
            'func': 'app:delete_inactive_sessions',
            'trigger': 'interval',
            'seconds': 3600  # Run every hour
        }
    ]
    SCHEDULER_API_ENABLED = True

def create_folders():
    os.makedirs(Config.BASE_UPLOAD_FOLDER, exist_ok=True)
    
    if not os.path.exists(Config.ORIGINAL_LIBRARY_PATH):
        Repo.clone_from('https://github.com/asia-pacific-energy-research-centre/transport_model_9th_edition.git', Config.ORIGINAL_LIBRARY_PATH, branch='public_master')