from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session
from flask_mail import Mail, Message
import os
import pandas as pd
import plotly.express as px
import plotly.io as pio
import shutil
import uuid
import sys
import random
import string
from encryption import encrypt_password, decrypt_password, load_key

# Adjust the Python path to include the workflow directory inside LIBRARY_NAME
LIBRARY_NAME = 'transport_model_9th_edition_public'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), LIBRARY_NAME, 'workflow')))

# Import the main function from your model
from main import main

# also run and pull FILE_DATE_ID and transport_data_system_FILE_DATE_ID from the model inside {LIBRARY_NAME}/config/config.py
from config.config import FILE_DATE_ID, transport_data_system_FILE_DATE_ID

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages

BASE_UPLOAD_FOLDER = 'uploads'
ORIGINAL_LIBRARY_PATH = f'../{LIBRARY_NAME}'
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

SAVED_FOLDER_STRUCTURE_PATH = 'folder_structure.txt'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@example.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Replace with your email password
mail = Mail(app)

# Store user data in a text file
USER_DATA_FILE = 'user_data.txt'

def get_required_input_files_and_their_locations(CHECK_FOLDER_STRUCTURE, INPUT_DATA_FOLDER_PATH, SAVED_FOLDER_STRUCTURE_PATH, OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH):
    """Will search through transport_model_9th_edition_public/input_data and record the names of all input files and their locations. Then when a file is passed to this app, if it is in the list of required files, it will be moved to the correct location. If it is not, an error message will be returned to the user. This will also take in a list of allowed files to be uploaded, as well as having the option to be passed the structure of the input_data folder, so it doesn't have to be run all the time, only when the structure of the input_data folder changes and the user sets CHECK_FOLDER_STRUCTURE to true.
    
    CHECK_FOLDER_STRUCTURE = True or False
    INPUT_DATA_FOLDER_PATH = the path to the input_data folder
    SAVED_FOLDER_STRUCTURE_PATH = the path to the file that will store the structure of the input_data folder
    OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH = True or False
    """
    
    if CHECK_FOLDER_STRUCTURE:
        # Get all the files in the input_data folder
        input_data_files = os.listdir(INPUT_DATA_FOLDER_PATH)
        # Set up a dict which maps the file name to the file path
        file_dict = {}
        for file in input_data_files:
            filename = os.path.basename(file)
            file_dict[filename] = os.path.join(INPUT_DATA_FOLDER_PATH, file)
        
        if OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH:
            with open(SAVED_FOLDER_STRUCTURE_PATH, 'w') as f:
                f.write(str(file_dict))
    else:
        with open(SAVED_FOLDER_STRUCTURE_PATH, 'r') as f:
            file_dict = eval(f.read())
    
    return file_dict

# Load or check the folder structure at startup
file_dict = get_required_input_files_and_their_locations(
    CHECK_FOLDER_STRUCTURE=True, 
    INPUT_DATA_FOLDER_PATH=os.path.join(ORIGINAL_LIBRARY_PATH, 'input_data'), 
    SAVED_FOLDER_STRUCTURE_PATH=SAVED_FOLDER_STRUCTURE_PATH, 
    OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH=True
)

def read_user_data():
    """Read user data from the text file and return it as a dictionary."""
    if not os.path.exists(USER_DATA_FILE):
        return {}
    
    with open(USER_DATA_FILE, 'r') as file:
        lines = file.readlines()
    
    user_data = {}
    for line in lines:
        email, encrypted_password = line.strip().split(':')
        user_data[email] = encrypted_password
    return user_data

def write_user_data(user_data):
    """Write user data to the text file."""
    with open(USER_DATA_FILE, 'w') as file:
        for email, encrypted_password in user_data.items():
            file.write(f'{email}:{encrypted_password}\n')

def generate_password(length=12):
    """Generate a random password."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def send_password_email(email, password):
    """Send an email with the generated password."""
    msg = Message('Your Login Password', sender='your-email@example.com', recipients=[email])
    msg.body = f'Your password is: {password}'
    mail.send(msg)

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    keys = [
        '01_AUS',
        '02_BD',
        '03_CDA',
        '04_CHL',
        '05_PRC',
        '06_HKC',
        '07_INA',
        '08_JPN',
        '09_ROK',
        '10_MAS',
        '11_MEX',
        '12_NZ',
        '13_PNG',
        '14_PE',
        '15_PHL',
        '16_RUS',
        '17_SGP',
        '18_CT',
        '19_THA',
        '20_USA',
        '21_VN'
    ]
    return render_template('index.html', keys=keys)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        if not email:
            flash('Email is required!')
            return redirect(url_for('login'))

        user_data = read_user_data()
        if email in user_data:
            entered_password = request.form['password']
            if decrypt_password(user_data[email]) == entered_password:
                session['username'] = email
                session['session_id'] = str(uuid.uuid4())
                flash('Login successful!')
                return redirect(url_for('index'))
            else:
                flash('Invalid password!')
        else:
            # Generate and send a new password
            password = generate_password()
            encrypted_password = encrypt_password(password)
            user_data[email] = encrypted_password.decode()
            write_user_data(user_data)
            send_password_email(email, password)
            flash('Password sent to your email!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('session_id', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))

    session_id = session.get('session_id')
    session_folder = os.path.join(BASE_UPLOAD_FOLDER, session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    session_library_path = os.path.join(session_folder, LIBRARY_NAME)
    if not os.path.exists(session_library_path):
        shutil.copytree(ORIGINAL_LIBRARY_PATH, session_library_path)
    
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = file.filename
        if filename not in file_dict:
            flash(f'{filename} is not a required input file.')
            return redirect(request.url)
        
        filepath = os.path.join(session_folder, filename)
        file.save(filepath)
        
        model_input_path = os.path.join(session_library_path, 'input_data', filename)
        shutil.move(filepath, model_input_path)
        
        flash(f'File {filename} uploaded successfully')
        return redirect(url_for('index'))

@app.route('/run', methods=['POST'])
def run_model_endpoint():
    if 'username' not in session:
        return redirect(url_for('login'))

    session_id = session.get('session_id')
    economy_to_run = request.form.get('economy')
    if not economy_to_run:
        flash('No economy selected. Please select an economy to run.')
        return redirect(url_for('index'))
    
    session['economy_to_run'] = economy_to_run
    
    try:
        run_model(economy_to_run)
        return redirect(url_for('results'))
    except Exception as e:
        flash(str(e))
        return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_session():
    if 'username' not in session:
        return redirect(url_for('login'))

    session_id = session.pop('session_id', None)
    if session_id:
        session_folder = os.path.join(BASE_UPLOAD_FOLDER, session_id)
        shutil.rmtree(session_folder)
    flash('Session reset successfully')
    return redirect(url_for('index'))

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))

    session_id = session.get('session_id')
    economy_to_run = session.get('economy_to_run')
    if not economy_to_run:
        flash('No economy selected. Please run the model first.')
        return redirect(url_for('index'))
    
    session_folder = os.path.join(BASE_UPLOAD_FOLDER, session_id)
    session_library_path = os.path.join(session_folder, LIBRARY_NAME)
    
    results_files = [
        f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_results.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions_extra.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_results.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions_extra.html'
    ]
    
    results_paths = [os.path.join(session_library_path, 'plotting_output', file) for file in results_files]
    
    key_csv_files = [
        f'plotting_output/key_results_{economy_to_run}.csv',
        f'input_data/key_input_{economy_to_run}.csv'
    ]
    key_csv_paths = [os.path.join(session_library_path, file) for file in key_csv_files]
    
    return render_template('results.html', results_paths=results_paths, key_csv_paths=key_csv_paths)

@app.route('/download/<path:filename>')
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    session_id = session.get('session_id')
    session_folder = os.path.join(BASE_UPLOAD_FOLDER, session_id)
    file_path = os.path.join(session_folder, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found.')
        return redirect(url_for('results'))

def run_model(economy_to_run):
    main(economy_to_run)

if __name__ == '__main__':
    app.run(debug=True)
