import os
import uuid
import time
import shutil
import json
from flask import session, current_app
from flask_mail import Mail, Message
import string
import random
import jwt
import backend
from encryption import encrypt_data, decrypt_data
from datetime import datetime
SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
from shared import progress_tracker, global_logger, model_threads, error_logger
# from app import progress_tracker

class UserManagement:
    def __init__(self, app):
        self.app = app
        self.mail = Mail(app)
        self.user_data_file = 'user_data.json'

    def read_user_data(self):
        # if current_app.config.LOGGING:
        #     global_logger.info('Reading user data')
        if not os.path.exists(self.user_data_file):
            return {}
        try:
            with open(self.user_data_file, 'r') as file:
                data = json.load(file)
                # if current_app.config.LOGGING:
                #     global_logger.info('User data read successfully')
                return data
        except (json.JSONDecodeError, IOError) as e:
            if current_app.config.LOGGING:
                global_logger.error(f'Error reading user data: {e}')
            return {}

    def write_user_data(self, data):
        if current_app.config.LOGGING:
            global_logger.info('Writing user data')
        with open(self.user_data_file, 'w') as file:
            json.dump(data, file)
            if current_app.config.LOGGING:
                global_logger.info('User data written successfully')
                
    def generate_password(self, length=4):
        """Generate a random password."""
        if current_app.config.LOGGING:
            global_logger.info(f'Generating password of length {length}')
        characters = string.ascii_letters + string.digits
        password = ''.join(random.choice(characters) for _ in range(length))
        if current_app.config.LOGGING:
            global_logger.info(f'Password generated')
        return password
    
    def update_user_password(self, email, new_password):
        if current_app.config.LOGGING:
            global_logger.info(f'Updating password for user: {encrypt_data(email)}')
        user_data = self.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
        if user_data:
            user_data['password'] = encrypt_data(new_password)
            self.save_user_data(user_data)
            if current_app.config.LOGGING:
                global_logger.info('Password updated successfully')
            return True
        else:
            if current_app.config.LOGGING:
                global_logger.error('User not found')
            return False

    def send_password_email(self, email, password):
        """Send an email with the generated password."""
        if current_app.config.LOGGING:
            global_logger.info(f'Sending password email to {(email)}')#encrypt_data
            
        new_values_dict={}
        new_values_dict['password'] = password
        
        from_email = 'new-password' + self.app.config['MAIL_USERNAME']
        backend.setup_and_send_email(email, from_email,
        new_values_dict, email_template='templates/new_password_email_template.html', subject_title='Your Login Password')
        
        if current_app.config.LOGGING:
            global_logger.info('Password email sent')

    def send_reset_password_email(self, email, reset_link):
        new_values_dict = {'reset_link': reset_link}
        
        from_email = self.app.config["MAIL_USERNAME"]
        
        if current_app.config.LOGGING:
            global_logger.info(f'Sending password reset email with reset link: {reset_link} to email {encrypt_data(email)}')
             
        try:
            backend.setup_and_send_email(
                email=email,
                from_email=from_email,
                new_values_dict=new_values_dict,
                email_template='templates/reset_password_email_template.html',
                subject_title='Password Reset Request'
            )
            if current_app.config.LOGGING:
                global_logger.info('Password reset email sent')
        except Exception as e:
            if current_app.config.LOGGING:
                global_logger.error(f'Failed to send password reset email: {e}')
            raise e
        
    def find_user_in_user_data_by_key_value(self, key, value, ENCRYPTED=False):
        #note that because the Fernet encryption scheme, uses a unique initialization vector (IV) for each encryption operation, resulting in different ciphertexts for the same plaintext each time it's encrypted. We need to decrypt the data before comparing it to the value as the encrypted data will be different each time it is encrypted.
        user_data = self.read_user_data()
        for user in user_data.values():
            if ENCRYPTED:
                try:
                    if decrypt_data(user.get(key)) == value:
                        if current_app.config.DEBUG_LOGGING:
                            global_logger.info(f'User found: {user} for {key}: {value}')
                        return user
                except Exception as e:
                    if current_app.config.LOGGING:
                        global_logger.error(f'Error decrypting data: {e} for user {user} for {key}: {value}')
                    continue
            else:
                if user.get(key) == value:
                    # if current_app.config.LOGGING:
                    #     global_logger.info(f'User found: {user}')
                    return user
        if current_app.config.LOGGING:
            global_logger.info(f'User not found for {key}: {value}')
        return None 

    def register_user(self, email):
        if current_app.config.LOGGING:
            global_logger.info(f'Registering user with email: {(email)}')#encrypt_data
        user_data = self.read_user_data()
        user = self.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
        if user:
            if current_app.config.LOGGING:
                global_logger.info('User already exists')
            return False
        user = self.create_user(encrypt_data(email))
        user_id = user['user_id']
        password = self.generate_password()
        user_data[user_id] = user
        user_data[user_id]['password'] = encrypt_data(password)
        self.write_user_data(user_data)
        self.send_password_email(email, password)
        if current_app.config.LOGGING:
            global_logger.info('User registered successfully')
        return True

    def create_user(self, email):
        if current_app.config.LOGGING:
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
        if current_app.config.LOGGING:
            global_logger.info(f'User created: {user}')
        return user

    def save_user_data(self, user):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f'Saving user data for user_id: {user["user_id"]}')
        user_data = self.read_user_data()
        user_data[user['user_id']] = user
        self.write_user_data(user_data)
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('User data saved successfully')

    def update_user_data(self, user):
        user_id = user['user_id']
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f'Updating session data for user_id: {user_id}')
        user_data = self.read_user_data()
        if user_id in user_data:
            user_data[user_id] = user
            self.write_user_data(user_data)
            if current_app.config.DEBUG_LOGGING:
                global_logger.info('Session data updated successfully')

    def get_user_by_session(self):
        if 'user_id' in session:
            user_data = self.read_user_data()
            user = user_data.get(session['user_id'])
            return user
        return None

    def save_session_data(self):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Saving session data')
        user = self.get_user_by_session()
        if user:
            user['economy_to_run'] = session.get('economy_to_run', '01_AUS')
            user['progress'] = session.get('progress', 0)
            user['model_thread_running'] = session.get('model_thread_running', False)
            user['results_available'] = session.get('results_available', False)
            self.update_user_data(user)

    def setup_user_session(self):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Activating user session')
        session['last_active'] = time.time()
        user = self.get_user_by_session()
        
        os.makedirs(user['session_folder'], exist_ok=True)
        # if not os.path.exists(user['session_library_path']):#had to remove this because someitmes beause of permission issues, the folder is not fully deleted and the code thinks it exists
        if current_app.config.LOGGING:
            global_logger.info('Creating session library path {}'.format(user['session_library_path']))
        # shutil.copytree(self.app.config['ORIGINAL_MODEL_LIBRARY_NAME'], user['session_library_path'], dirs_exist_ok=True)
        
        session['session_folder'] = user['session_folder']
        session['session_library_path'] = user['session_library_path']
        session['session_log_filename'] = user['session_log_filename']
        
        # session['user_session_active'] = True
        session['model_thread_running'] = False
        session['results_available'] = False
        
        self.save_session_data()
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f'User session activated successfully. User session is {session}')

    def restart_user_session(self):
        if current_app.config.DEBUG_LOGGING:
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
        if current_app.config.LOGGING:
            global_logger.info(f'User session restarted successfully. User session is {session}')

    def is_session_valid(self):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Checking if session is valid')
        user = self.get_user_by_session()
        is_valid = user is not None
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f'Session valid: {is_valid}')
        return is_valid
        
    def check_if_results_available(self):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Checking if results are available')
        user = self.get_user_by_session()
        if not user:
            if current_app.config.DEBUG_LOGGING:
                global_logger.error('User not found in session')
            error_logger.error('User not found in session')
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f"Results available: {user['results_available']}")
        return user['results_available']
    
    def check_model_is_running(self):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Checking if model is running')
        user = self.get_user_by_session()
        if not user:
            if current_app.config.DEBUG_LOGGING:
                global_logger.error('User not found in session')
            raise Exception('User not found in session')#not sure if raising error is the best way to handle this
        model_running = user['model_thread_running']
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f'Model running: {model_running}')
        return model_running
    
    def clear_invalid_session(self):
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Clearing invalid session')
        session.clear()
        if current_app.config.DEBUG_LOGGING:
            global_logger.info('Session cleared')
        return True

    def reset_user_session(self):
        if current_app.config.LOGGING:
            global_logger.info('Resetting user session')
        user = self.get_user_by_session()
        if user:
            if os.path.exists(user['session_folder']):
                if current_app.config.DEBUG:
                    pass
                else:
                    shutil.rmtree(user['session_folder'], ignore_errors=True)
                if current_app.config.LOGGING:
                    global_logger.info(f'Deleting session folder: {user["session_folder"]}')
            
            if os.path.exists(user['session_library_path']):
                if current_app.config.DEBUG:
                    pass
                else:
                    shutil.rmtree(user['session_library_path'], ignore_errors=True)
                if current_app.config.LOGGING:
                    global_logger.info(f'Deleting session library path: {user["session_library_path"]}')
            
            if os.path.exists(user['session_log_filename']):
                if current_app.config.DEBUG:
                    pass
                if current_app.config.LOGGING:
                    global_logger.info(f'Archiving log file: {user["session_log_filename"]}')
                backend.archive_log(user['session_log_filename'])
            
            user['economy_to_run'] = '01_AUS'
            user['progress'] = 0
            user['model_thread_running'] = False
            user['results_available'] = False
            self.save_user_data(user)
            if current_app.config.LOGGING:
                global_logger.info('User session reset successfully')
                
    def delete_inactive_users_sessions(self):
        global_logger.info('Deleting inactive user sessions')
        user_data = self.read_user_data()
        
        retention_period = 60*60*24*7 # 7 days
        for user in user_data.values():
            if user['last_active'] < time.time() - retention_period:
                if current_app.config.LOGGING:
                    global_logger.info(f'Deleting session data for inactive user: {user["user_id"]}')
                if os.path.exists(user['session_folder']):
                    if current_app.config.DEBUG:
                        pass
                    else:
                        shutil.rmtree(user['session_folder'], ignore_errors=True)
                
                if os.path.exists(user['session_library_path']):
                    if current_app.config.DEBUG:
                        pass
                    else:
                        shutil.rmtree(user['session_library_path'], ignore_errors=True)
                
                backend.archive_log(user['session_log_filename'])
                
                user['model_thread_running'] = False
                user['economy_to_run'] = '01_AUS'
                user['progress'] = 0
                user['results_available'] = False
                self.save_user_data(user)
        if current_app.config.LOGGING:
            global_logger.info('Inactive user sessions deleted successfully')
    
    def create_master_user(self):
        user_data = self.read_user_data()
        if user_data is None:
            user_data = {}
        # Check that the master user does not already exist
        if self.find_user_in_user_data_by_key_value('email', current_app.config.MASTER_USER_EMAIL, ENCRYPTED=True):
            if current_app.config.LOGGING:
                global_logger.error('Master user already exists')
            return
        
        if current_app.config.LOGGING:
            global_logger.info('Creating master user')
        
        encrypted_email = encrypt_data(current_app.config.MASTER_USER_EMAIL)
        encrypted_password = encrypt_data(current_app.config.MASTER_USER_PASSWORD)
        
        if current_app.config.LOGGING:
            global_logger.debug(f"Encrypted master user email: {encrypted_email}")
            global_logger.debug(f"Encrypted master user password: {encrypted_password}")
        
        user = self.create_user(encrypted_email)
        user_id = user['user_id']
        user_data[user_id] = user
        user_data[user_id]['password'] = encrypted_password
        self.write_user_data(user_data)
        self.send_password_email(current_app.config.MASTER_USER_EMAIL, current_app.config.MASTER_USER_PASSWORD)
        
        if current_app.config.LOGGING:
            global_logger.info('Master user created successfully')
            
    def startup_tasks(self, DELETE_LOGS_INSTEAD_OF_ARCHIVING=True):
        user_data = self.read_user_data()
        if user_data is None:
            user_data = {}
        #also go thorugh the /uploads folder and remove any folders that are not in the user_data
        for folder in os.listdir(self.app.config['BASE_UPLOAD_FOLDER']):
            user_id = folder
            if user_id not in user_data.keys():
                global_logger.info(f"Deleting upload folder {folder} as it is not in user_data")
                shutil.rmtree(os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], folder), ignore_errors=True)
                #and see if theres a log file in logs, we can remove it
                log_file = os.path.join(self.app.config['BASE_LOGS_FOLDER'], f"model_output_{user_id}.log")
                
                if os.path.exists(log_file):
                    global_logger.info(f"Deleting/archiving log file {log_file} as it is not in user_data")
                    archived_log_filename = os.path.join('logs', 'archive', f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{os.path.basename(log_file)}')
                    if DELETE_LOGS_INSTEAD_OF_ARCHIVING:
                        os.remove(log_file)
                    else:
                        shutil.move(log_file, archived_log_filename)
        
        #and create the master user
        self.create_master_user()
                