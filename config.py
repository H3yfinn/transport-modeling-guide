# config.py
import os
from git import Repo
from dotenv import load_dotenv
    
class Config:
    
    SECRET_KEY = os.getenv('SECRET_KEY', None)
    DEBUG = False#os.getenv('DEBUG', 'True').lower() in ['true', '1', 't']
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', None)

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in the environment.")
    if not ENCRYPTION_KEY or len(ENCRYPTION_KEY) != 44:
        raise ValueError("ENCRYPTION_KEY must be a 32-byte, URL-safe base64-encoded string.")
        
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
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
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

def create_folders():
    os.makedirs(Config.BASE_UPLOAD_FOLDER, exist_ok=True)
    
    if not os.path.exists(Config.ORIGINAL_MODEL_LIBRARY_NAME):
        Repo.clone_from('https://github.com/H3yfinn/transport_model_9th_edition', Config.ORIGINAL_MODEL_LIBRARY_NAME, branch='public_master')
    
    # if not os.path.exists(root_dir + '/' + './PyLMDI'):#this is needed by the transport model
    #     Repo.clone_from('https://github.com/asia-pacific-energy-research-centre/PyLMDI.git', Config.ORIGINAL_LIBRARY_PATH, branch='main')