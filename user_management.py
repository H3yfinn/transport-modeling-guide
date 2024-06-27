# user_management.py
import os
import uuid
import time
import shutil
import json
from flask import session, flash
from flask_mail import Mail, Message
import sys
import shutil
import string
import random

class UserManagement:
    def __init__(self, app):
        self.app = app
        self.mail = Mail(app)
        self.session_data_file = 'session_data.json'

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
        session['username'] = email
        session['session_id'] = str(uuid.uuid4())
        session['last_active'] = time.time()
        self.save_session_data(email)

        session_id = session['session_id']
        session_folder = os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], session_id)
        os.makedirs(session_folder, exist_ok=True)

        session_library_path = os.path.join(session_folder, self.app.config['ORIGINAL_LIBRARY_PATH'])
        if not os.path.exists(session_library_path):
            shutil.copytree(self.app.config['ORIGINAL_LIBRARY_PATH'], session_library_path)

    def save_session_data(self, email):
        session_data = {
            'username': session['username'],
            'session_id': session['session_id'],
            'last_active': session['last_active']
        }
        if not os.path.exists(self.session_data_file):
            data = {}
        else:
            with open(self.session_data_file, 'r') as file:
                data = json.load(file)
        data[email] = session_data
        with open(self.session_data_file, 'w') as file:
            json.dump(data, file)

    def load_session_data(self, email):
        if not os.path.exists(self.session_data_file):
            return None
        with open(self.session_data_file, 'r') as file:
            data = json.load(file)
        return data.get(email, None)

    def reset_session_folder(self):
        if 'session_id' in session:
            session_id = session.get('session_id')
            session_folder = os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], session_id)
            if os.path.exists(session_folder):
                shutil.rmtree(session_folder)
            os.makedirs(session_folder, exist_ok=True)

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

    def delete_inactive_sessions(self):
        now = time.time()
        if not os.path.exists(self.session_data_file):
            return

        with open(self.session_data_file, 'r') as file:
            data = json.load(file)

        # Get a list of session IDs from the JSON data
        active_session_ids = {session_data['session_id'] for session_data in data.values()}

        # Iterate over session folders and delete those that are not active
        for session_folder in os.listdir(self.app.config['BASE_UPLOAD_FOLDER']):
            folder_path = os.path.join(self.app.config['BASE_UPLOAD_FOLDER'], session_folder)
            if os.path.isdir(folder_path) and session_folder not in active_session_ids:
                shutil.rmtree(folder_path)
        
    
    def session_specific_setup():
        """
        If there has been a session set up for this user already, then grab some model variables from the users session specific model rather than the default model.
        """
        if 'session_id' in session:
            session_id = session.get('session_id')
            session_folder = os.path.join(app.config['BASE_UPLOAD_FOLDER'], session_id)
            session_library_path = os.path.join(session_folder, app.config['ORIGINAL_LIBRARY_PATH'])
            
            # Adjust the Python path to include the workflow directory inside LIBRARY_NAME
            LIBRARY_NAME = 'transport_model_9th_edition_public'
            sys.path.append(os.path.abspath(os.path.join(session_library_path, 'workflow')))
            # Import the main function from the session specific model
            from main import main
            # also run and pull FILE_DATE_ID and transport_data_system_FILE_DATE_ID from the model inside {LIBRARY_NAME}/config/config.py
            from config.config import FILE_DATE_ID, transport_data_system_FILE_DATE_ID
            