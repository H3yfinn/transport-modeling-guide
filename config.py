# config.py
import os
from dotenv import load_dotenv
import boto3

# Initialize the SES client using the IAM role credentials
ses_client = boto3.client('ses', region_name='ap-northeast-1')

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
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    AWS_ACCESS_KEY_ID = ses_client._request_signer._credentials.access_key
    AWS_SECRET_ACCESS_KEY = ses_client._request_signer._credentials.secret_key
    AWS_REGION = ses_client.meta.region_name
    PERSONAL_EMAIL = os.getenv('PERSONAL_EMAIL')
    MASTER_USER_EMAIL = os.getenv('MASTER_USER_EMAIL')
    MASTER_USER_PASSWORD = os.getenv('MASTER_USER_PASSWORD')
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
