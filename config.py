# config.py
import os
from dotenv import load_dotenv
import boto3

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
    PERSONAL_EMAIL = os.getenv('PERSONAL_EMAIL')
    MASTER_USER_EMAIL = os.getenv('MASTER_USER_EMAIL')
    MASTER_USER_PASSWORD = os.getenv('MASTER_USER_PASSWORD')
    KMS_KEY_ID = os.getenv('KMS_KEY_ID')
    SECRET_KEY = os.getenv('SECRET_KEY')
    NON_KMS_ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    AWS_CONNECTION_AVAILABLE = os.getenv('AWS_CONNECTION_AVAILABLE')
    
    # Initialize the SES client using the IAM role credentials. it doesnt matter if we dont have access, it  wont cause an error, it just will be set to None
    ses_client = boto3.client('ses', region_name='ap-northeast-1')
    AWS_ACCESS_KEY_ID = ses_client._request_signer._credentials.access_key
    AWS_SECRET_ACCESS_KEY = ses_client._request_signer._credentials.secret_key
    AWS_REGION = ses_client.meta.region_name
    kms_client = boto3.client('kms', region_name='ap-northeast-1')
    if ses_client == None and AWS_CONNECTION_AVAILABLE:
        print("AWS connection for ses_client not available. Check your IAM role permissions.")
        raise Exception("AWS connection for ses_client not available. Check your IAM role permissions.")
    if kms_client == None and AWS_CONNECTION_AVAILABLE:
        print("AWS connection for kms_client not available. Check your IAM role permissions.")
        raise Exception("AWS connection for kms_client not available. Check your IAM role")
    if not AWS_CONNECTION_AVAILABLE:
        kms_client = None
        ses_client = None
        
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
    
