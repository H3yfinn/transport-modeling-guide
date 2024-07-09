# config.py
import os
from dotenv import load_dotenv
    
class Config:
        
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))    #is thjer any need for this?
    BASE_UPLOAD_FOLDER = 'uploads'
    BASE_LOGS_FOLDER = 'logs'
    USER_DATA_FILE = 'user_data.json'
    SESSION_TIMEOUT = 3600  # Session timeout in seconds
    SAVED_FOLDER_STRUCTURE_PATH = 'folder_structure.txt' 
    ORIGINAL_MODEL_LIBRARY_NAME = 'transport_model_9th_edition'

    
    EXECUTION_TIMES_FILE = 'execution_times.json'
    # Flask-Mail configuration
    #now in .env file
    # Load environment variables from .env file
    load_dotenv()
    LOGGING = os.getenv('LOGGING', 'True').lower() in ['true', '1', 't']
    DEBUG = os.getenv('DEBUG', 'True').lower() in ['true', '1', 't']
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    SECRET_KEY = os.getenv('SECRET_KEY')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    # app.config['MAIL_DEFAULT_SENDER'] = ('Your Name', os.getenv('MAIL_USERNAME'))
    
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
