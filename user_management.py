import os
import uuid
import time
import shutil
import json
from flask import session, flash, url_for
from flask_mail import Mail, Message
import string
import random
from encryption import encrypt_data_with_kms, decrypt_data_with_kms
import jwt
import backend
from config import Config
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
from shared import progress_tracker, global_logger, model_threads
# from app import progress_tracker

class UserManagement:
    def __init__(self, app):
        self.app = app
        self.mail = Mail(app)
        self.user_data_file = 'user_data.json'
        if Config.LOGGING:
            global_logger.info('UserManagement initialized')

    def read_user_data(self):
        # if Config.LOGGING:
        #     global_logger.info('Reading user data')
        if not os.path.exists(self.user_data_file):
            return {}
        try:
            with open(self.user_data_file, 'r') as file:
                data = json.load(file)
                # if Config.LOGGING:
                #     global_logger.info('User data read successfully')
                return data
        except (json.JSONDecodeError, IOError) as e:
            if Config.LOGGING:
                global_logger.error(f'Error reading user data: {e}')
            return {}

    def write_user_data(self, data):
        if Config.LOGGING:
            global_logger.info('Writing user data')
        with open(self.user_data_file, 'w') as file:
            json.dump(data, file)
            if Config.LOGGING:
                global_logger.info('User data written successfully')

    def generate_password(self, length=1):
        """Generate a random password."""
        if Config.LOGGING:
            global_logger.info(f'Generating password of length {length}')
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(length))
        if Config.LOGGING:
            global_logger.info(f'Password generated: {password}')
        return password
    
    def update_user_password(self, email, new_password):
        if Config.LOGGING:
            global_logger.info(f'Updating password for user: {encrypt_data_with_kms(email)}')
        user_data = self.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
        if user_data:
            user_data['password'] = encrypt_data_with_kms(new_password)
            self.save_user_data(user_data)
            if Config.LOGGING:
                global_logger.info('Password updated successfully')
            return True
        else:
            if Config.LOGGING:
                global_logger.error('User not found')
            return False

    def send_password_email(self, email, password):
        """Send an email with the generated password."""
        if Config.LOGGING:
            global_logger.info(f'Sending password email to {encrypt_data_with_kms(email)}')
            
        new_values_dict={}
        new_values_dict['password'] = password
        
        from_email = 'new-password' + self.app.config['MAIL_USERNAME']
        backend.setup_and_send_email(email, from_email,
        new_values_dict, email_template='templates/new_password_email_template.html', subject_title='Your Login Password')
        
        if Config.LOGGING:
            global_logger.info('Password email sent')

    def send_reset_password_email(self, email, reset_link):
        if Config.LOGGING:
            global_logger.info(f'Sending password reset email to {encrypt_data_with_kms(email)}')
        new_values_dict={}
        new_values_dict['reset_link'] = reset_link
        
        from_email = 'reset-password' + self.app.config['MAIL_USERNAME']
        backend.setup_and_send_email(email, from_email, new_values_dict, email_template='templates/reset_password_email_template.html', subject_title='Password Reset Request')
        
        if Config.LOGGING:
            global_logger.info('Password reset email sent')
        
    def find_user_in_user_data_by_key_value(self, key, value, ENCRYPTED=False):
        #note that because the Fernet encryption scheme, uses a unique initialization vector (IV) for each encryption operation, resulting in different ciphertexts for the same plaintext each time it's encrypted. We need to decrypt the data before comparing it to the value as the encrypted data will be different each time it is encrypted.
        if Config.LOGGING:
            global_logger.info(f'Finding user by {key}: {value}')
        user_data = self.read_user_data()
        for user in user_data.values():
            if ENCRYPTED:
                if decrypt_data_with_kms(user.get(key)) == value:
                    if Config.LOGGING:
                        global_logger.info(f'User found: {user}')
                    return user
            else:
                if user.get(key) == value:
                    if Config.LOGGING:
                        global_logger.info(f'User found: {user}')
                    return user
        if Config.LOGGING:
            global_logger.info('User not found')
        return None 

    def register_user(self, email):
        if Config.LOGGING:
            global_logger.info(f'Registering user with email: {encrypt_data_with_kms(email)}')
        user_data = self.read_user_data()
        user = self.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
        if user:
            if Config.LOGGING:
                global_logger.info('User already exists')
            return False
        user = self.create_user(encrypt_data_with_kms(email))
        user_id = user['user_id']
        password = self.generate_password()
        user_data[user_id] = user
        user_data[user_id]['password'] = encrypt_data_with_kms(password)
        self.write_user_data(user_data)
        self.send_password_email(email, password)
        if Config.LOGGING:
            global_logger.info('User registered successfully')
        return True

    def create_user(self, email):
        if Config.LOGGING:
            global_logger.info(f'Creating user with email: {email}')
        user_id = str(uuid.uuid4())[:5]
        user = {
            'username': email,
            'email': email,
            'user_id': user_id,
            'last_active': time.time(),
            'economy_to_run': session.get('economy_to_run', '01_AUS') if session else '01_AUS',#set to the first value in the dropdown list by default
            'progress': session.get('progress', 0) if session else 0,
            # 'user_session_active': False,
            'model_thread_running': False,
            'results_available': False,
            'session_folder': os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], user_id),
            'session_library_path': os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], user_id, self.app.config['ORIGINAL_MODEL_LIBRARY_NAME']),
            'session_log_filename': os.path.join(self.app.config['BASE_LOGS_FOLDER'], f"model_output_{user_id}.log")
        }
        if Config.LOGGING:
            global_logger.info(f'User created: {user}')
        return user

    def save_user_data(self, user):
        if Config.LOGGING:
            global_logger.info(f'Saving user data for user_id: {user["user_id"]}')
        user_data = self.read_user_data()
        user_data[user['user_id']] = user
        self.write_user_data(user_data)
        if Config.LOGGING:
            global_logger.info('User data saved successfully')

    def update_user_data(self, user):
        user_id = user['user_id']
        if Config.LOGGING:
            global_logger.info(f'Updating session data for user_id: {user_id}')
        user_data = self.read_user_data()
        if user_id in user_data:
            user_data[user_id] = user
            self.write_user_data(user_data)
            if Config.LOGGING:
                global_logger.info('Session data updated successfully')

    def get_user_by_session(self):
        if 'user_id' in session:
            user_data = self.read_user_data()
            user = user_data.get(session['user_id'])
            return user
        return None

    def save_session_data(self):
        if Config.LOGGING:
            global_logger.info('Saving session data')
        user = self.get_user_by_session()
        if user:
            user['economy_to_run'] = session.get('economy_to_run', '01_AUS')
            user['progress'] = session.get('progress', 0)
            user['model_thread_running'] = session.get('model_thread_running', False)
            user['results_available'] = session.get('results_available', False)
            self.update_user_data(user)

    def setup_user_session(self):
        if Config.LOGGING:
            global_logger.info('Activating user session')
        session['last_active'] = time.time()
        user = self.get_user_by_session()
        
        os.makedirs(user['session_folder'], exist_ok=True)
        if not os.path.exists(user['session_library_path']):
            shutil.copytree(self.app.config['ORIGINAL_MODEL_LIBRARY_NAME'], user['session_library_path'])
        
        session['session_folder'] = user['session_folder']
        session['session_library_path'] = user['session_library_path']
        session['session_log_filename'] = user['session_log_filename']
        
        # session['user_session_active'] = True
        session['model_thread_running'] = False
        session['results_available'] = False
        
        self.save_session_data()
        # if Config.LOGGING:
        #     global_logger.info(f'User session activated successfully. User session is {session}')

    def restart_user_session(self):
        if Config.LOGGING:
            global_logger.info('Restarting user session')
        user = self.get_user_by_session()
        if user:
            session['session_folder'] = user['session_folder']
            session['session_library_path'] = user['session_library_path']
            session['session_log_filename'] = user['session_log_filename']
            session['results_available'] = user['results_available']
            session['model_thread_running'] = user['model_thread_running']
            session['last_active'] = time.time()
            session['economy_to_run'] = user['economy_to_run']
            session['progress'] = user['progress']
        if Config.LOGGING:
            global_logger.info(f'User session restarted successfully. User session is {session}')

    def is_session_valid(self):
        # if Config.LOGGING:
        #     global_logger.info('Checking if session is valid')
        user = self.get_user_by_session()
        is_valid = user is not None
        # if Config.LOGGING:
        #     global_logger.info(f'Session valid: {is_valid}')
        return is_valid
        
    def check_if_results_available(self):
        if Config.LOGGING:
            global_logger.info('Checking if results are available')
        user = self.get_user_by_session()
        if not user:
            if Config.LOGGING:
                global_logger.error('User not found in session')
            raise Exception('User not found in session')
        results_available = user['results_available']
        if Config.LOGGING:
            global_logger.info(f'Results available: {results_available}')
        return results_available
    
    def check_model_is_running(self):
        if Config.LOGGING:
            global_logger.info('Checking if model is running')
        user = self.get_user_by_session()
        if not user:
            if Config.LOGGING:
                global_logger.error('User not found in session')
            raise Exception('User not found in session')
        model_running = user['model_thread_running']
        if Config.LOGGING:
            global_logger.info(f'Model running: {model_running}')
        return model_running
    
    def clear_invalid_session(self):
        if Config.LOGGING:
            global_logger.info('Clearing invalid session')
        session.clear()
        if Config.LOGGING:
            global_logger.info('Session cleared')
        return True

    def reset_user_session(self):
        if Config.LOGGING:
            global_logger.info('Resetting user session')
        user = self.get_user_by_session()
        if user:
            if os.path.exists(user['session_folder']):
                if Config.DEBUG:
                    pass
                else:
                    shutil.rmtree(user['session_folder'], ignore_errors=True)
                if Config.LOGGING:
                    global_logger.info(f'Deleting session folder: {user["session_folder"]}')
            
            if os.path.exists(user['session_library_path']):
                if Config.DEBUG:
                    pass
                else:
                    shutil.rmtree(user['session_library_path'], ignore_errors=True)
                if Config.LOGGING:
                    global_logger.info(f'Deleting session library path: {user["session_library_path"]}')
            
            if os.path.exists(user['session_log_filename']):
                if Config.DEBUG:
                    pass
                if Config.LOGGING:
                    global_logger.info(f'Archiving log file: {user["session_log_filename"]}')
                backend.archive_log(user['session_log_filename'])
            
            user['session_data'] = {}
            user['economy_to_run'] = '01_AUS'
            user['progress'] = 0
            user['model_thread_running'] = False
            user['results_available'] = False
            self.save_user_data(user)
            if Config.LOGGING:
                global_logger.info('User session reset successfully')
                
    def delete_inactive_users_sessions(self):
        if Config.LOGGING:
            global_logger.info('Deleting inactive user sessions')
        user_data = self.read_user_data()
        
        retention_period = 60*60*24*7
        for user in user_data.values():
            if user['last_active'] < time.time() - retention_period:
                if Config.LOGGING:
                    global_logger.info(f'Deleting session data for inactive user: {user["user_id"]}')
                if os.path.exists(user['session_folder']):
                    if Config.DEBUG:
                        pass
                    else:
                        shutil.rmtree(user['session_folder'], ignore_errors=True)
                
                if os.path.exists(user['session_library_path']):
                    if Config.DEBUG:
                        pass
                    else:
                        shutil.rmtree(user['session_library_path'], ignore_errors=True)
                
                backend.archive_log(user['session_log_filename'])
                
                user['session_data'] = {}
                user['model_thread_running'] = False
                user['economy_to_run'] = '01_AUS'
                user['progress'] = 0
                user['results_available'] = False
                self.save_user_data(user)
        if Config.LOGGING:
            global_logger.info('Inactive user sessions deleted successfully')

    def create_master_user(self):
        user_data = self.read_user_data()
        if user_data is None:
            user_data = {}
        #check that the master user does not already exist
        if self.find_user_in_user_data_by_key_value('email', Config.MASTER_USER_EMAIL, ENCRYPTED=True):
            if Config.LOGGING:
                global_logger.error('Master user already exists')
            return
        
        if Config.LOGGING:
            global_logger.info('Creating master user')
            
        user = self.create_user(encrypt_data_with_kms(Config.MASTER_USER_EMAIL))
        user_id = user['user_id']
        user_data[user_id] = user
        user_data[user_id]['password'] = encrypt_data_with_kms(Config.MASTER_USER_PASSWORD)
        self.write_user_data(user_data)
        self.send_password_email(Config.MASTER_USER_EMAIL, Config.MASTER_USER_PASSWORD)
        if Config.LOGGING:
            global_logger.info('Master user created successfully')


