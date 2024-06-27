# user_management.py
import os
import uuid
import time
from flask import session, flash
from flask_mail import Mail, Message
from encryption import encrypt_password, decrypt_password
import sys
import shutil
import string
import random


class UserManagement:
    """Note that a session is a flask concept that is unique to each user. It will have a folder set up for a unique model as well as a its own username/password combination for login and recognition of the user (really just so two users sessions dont corrupt each other).
    
    
    """
    def __init__(self, app):
        self.app = app
        self.mail = Mail(app)

    def read_user_data(self):
        """Read user data from the text file and return it as a dictionary."""
        if not os.path.exists(self.app.config['USER_DATA_FILE']):
            return {}

        with open(self.app.config['USER_DATA_FILE'], 'r') as file:
            lines = file.readlines()

        user_data = {}
        for line in lines:
            email, encrypted_password = line.strip().split(':')
            user_data[email] = encrypted_password
        return user_data

    def write_user_data(self, user_data):
        """Write user data to the text file."""
        with open(self.app.config['USER_DATA_FILE'], 'w') as file:
            for email, encrypted_password in user_data.items():
                file.write(f'{email}:{encrypted_password}\n')

    def generate_password(self, length=12):
        """Generate a random password."""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))

    def send_password_email(self, email, password):
        """Send an email with the generated password."""
        msg = Message('Your Login Password', sender=self.app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = f'Your password is: {password}'
        self.mail.send(msg)

    def create_session(self, email):
        """Note that a session is a flask concept that is unique to each user. It will have a folder set up for a unique model as well as a its own username/password combination for login and recognition of the user (really just so two users sessions dont corrupt each other).
        """
        session_id = str(uuid.uuid4())
        session['username'] = email
        session['session_id'] = session_id
        session['last_active'] = time.time()
        
        session_folder = os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], session_id)
        session_library_path = os.path.join(session_folder, self.app.config['ORIGINAL_LIBRARY_PATH'])
        if not os.path.exists(session_library_path):
            shutil.copytree(self.app.config['ORIGINAL_LIBRARY_PATH'], session_library_path)
            
        # Import the main function from your model
        from main import main
        # also run and pull FILE_DATE_ID and transport_data_system_FILE_DATE_ID from the model inside {LIBRARY_NAME}/config/config.py
        from config.config import FILE_DATE_ID, transport_data_system_FILE_DATE_ID
            

    # def check_session_expiry(self):
    #     if 'last_active' in session:
    #         now = time.time()
    #         if now - session['last_active'] > self.app.config['SESSION_TIMEOUT']:
    #             self.delete_session()

    # def delete_session(self):
    #     session.pop('username', None)
    #     session.pop('session_id', None)
    #     session.pop('last_active', None)
    #     flash('Your session has expired.')

    def delete_inactive_sessions(self):
        """Want it to check for sessions where the session has expired and delete their folders."""
        now = time.time()
        for filename in os.listdir(self.app.config['BASE_UPLOAD_FOLDER']):
            folder_path = os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], filename)
            if os.path.isdir(folder_path):
                last_active = os.path.getmtime(folder_path)
                if now - last_active > self.app.config['SESSION_TIMEOUT']:
                    shutil.rmtree(folder_path)

    def session_specific_setup():
        """
        If there has been a session set up for this user, then set up the session specific variables for the model, given that the session has not expired.
        """
        if 'session_id' in session:
            session_id = session.get('session_id')
            session_folder = os.path.join(app.config['BASE_UPLOAD_FOLDER'], session_id)
            session_library_path = os.path.join(session_folder, app.config['ORIGINAL_LIBRARY_PATH'])
            
            # Adjust the Python path to include the workflow directory inside LIBRARY_NAME
            LIBRARY_NAME = 'transport_model_9th_edition_public'
            sys.path.append(os.path.abspath(os.path.join(session_library_path, 'workflow')))
            # Import the main function from your model
            from main import main
            # also run and pull FILE_DATE_ID and transport_data_system_FILE_DATE_ID from the model inside {LIBRARY_NAME}/config/config.py
            from config.config import FILE_DATE_ID, transport_data_system_FILE_DATE_ID
            
        
    def reset_sessions_model(self):
        if 'session_id' in session:
            session_id = session.get('session_id')
            session_folder = os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], session_id)
            if os.path.exists(session_folder):
                shutil.rmtree(session_folder)
            os.makedirs(session_folder, exist_ok=True)

            #create a new model for the session to use.
            session_library_path = os.path.join(session_folder, self.app.config['ORIGINAL_LIBRARY_PATH'])
            if not os.path.exists(session_library_path):
                shutil.copytree(self.app.config['ORIGINAL_LIBRARY_PATH'], session_library_path)

            # Adjust the Python path to include the workflow directory inside LIBRARY_NAME
            LIBRARY_NAME = 'transport_model_9th_edition_public'
            sys.path.append(os.path.abspath(os.path.join(session_library_path, 'workflow')))
            # Import the main function from your model
            from main import main
            # also run and pull FILE_DATE_ID and transport_data_system_FILE_DATE_ID from the model inside {LIBRARY_NAME}/config/config.py
            from config.config import FILE_DATE_ID, transport_data_system_FILE_DATE_ID