from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session, jsonify, stream_with_context, Response
# from flask_apscheduler import APScheduler
from config import Config, create_folders
from user_management import UserManagement
import os
import shutil
import sys
from datetime import timedelta
from encryption import encrypt_password, decrypt_password
import markdown
import time
from dotenv import load_dotenv
import importlib.util
import backend
import threading
# Load environment variables from .env file
load_dotenv()

# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)
create_folders()

# Initialize user management and mail
user_management = UserManagement(app)
mail = user_management.mail

############################################################################

def get_required_input_files_and_their_locations(CHECK_FOLDER_STRUCTURE, INPUT_DATA_FOLDER_PATH, SAVED_FOLDER_STRUCTURE_PATH, OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH):
    """Will search through transport_model_9th_edition/input_data and record the names of all input files and their locations. Then when a file is passed to this app, if it is in the list of required files, it will be moved to the correct location. If it is not, an error message will be returned to the user. This will also take in a list of allowed files to be uploaded, as well as having the option to be passed the structure of the input_data folder, so it doesn't have to be run all the time, only when the structure of the input_data folder changes and the user sets CHECK_FOLDER_STRUCTURE to true.
    
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
    INPUT_DATA_FOLDER_PATH=os.path.join(app.config['ORIGINAL_MODEL_LIBRARY_NAME'], 'input_data'), 
    SAVED_FOLDER_STRUCTURE_PATH=app.config['SAVED_FOLDER_STRUCTURE_PATH'], 
    OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH=True
)

############################################################################
#MODEL RELATED
# Set session lifetime to one week
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(weeks=1)

@app.before_request
def update_session_timeout():
    session.permanent = True
    session.modified = True  # Ensures the session cookie is sent to the client
    session['last_active'] = time.time()
    
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))#get user to create or login, if they are not logged in
    
    keys = [
        '01_AUS', '02_BD', '03_CDA', '04_CHL', '05_PRC', '06_HKC',
        '07_INA', '08_JPN', '09_ROK', '10_MAS', '11_MEX', '12_NZ',
        '13_PNG', '14_PE', '15_PHL', '16_RUS', '17_SGP', '18_CT',
        '19_THA', '20_USA', '21_VN'
    ]
    return render_template('index.html', keys=keys)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))#get user to create or login, if they are not logged in
    
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
            flash(f'{filename} is not a required input file. Maybe you need to name it correctly.')
            return redirect(request.url)
        
        original_filepath = file_dict[filename]#get the path to the file wihtin the input_data folder of the original model library
        new_filepath = os.path.join(session['session_library_path'], original_filepath)
        file.save(new_filepath)
        
        flash(f'File {filename} uploaded successfully')
        return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset_session():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_management.reset_sessions_model()
    flash('Session reset successfully')
    return redirect(url_for('index'))

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))

    economy_to_run = session.get('economy_to_run')
    if not economy_to_run:
        flash('No economy selected. Please run the model first.')
        return redirect(url_for('index'))
    
    results_files = [
        f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_results.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions_extra.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_results.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions.html',
        f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions_extra.html'
    ]
    
    results_paths = [os.path.join(session['session_library_path'], 'plotting_output', file) for file in results_files]
    
    key_csv_files = [
        f'plotting_output/key_results_{economy_to_run}.csv',
        f'input_data/key_input_{economy_to_run}.csv'
    ]
    key_csv_paths = [os.path.join(session['session_library_path'], file) for file in key_csv_files]
    
    return render_template('results.html', results_paths=results_paths, key_csv_paths=key_csv_paths)

@app.route('/download/<path:filename>')
def download_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))

    file_path = os.path.join(session['session_folder'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found.')
        return redirect(url_for('results'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        if not email:
            flash('Email is required!')
            return redirect(url_for('login'))

        user_data = user_management.read_user_data()
        if email in user_data:
            entered_password = request.form['password']
            if decrypt_password(user_data[email]) == entered_password:
                session_data = user_management.load_session_data(email)
                if session_data:
                    session.update(session_data)
                else:
                    user_management.create_session(email)
                flash('Login successful!')
                return redirect(url_for('index'))
            else:
                flash('Invalid password!')
        else:
            password = user_management.generate_password()
            encrypted_password = encrypt_password(password)
            user_data[email] = encrypted_password#.decode()#TO DO SHOULDNT THIS BE ENCODED?
            user_management.write_user_data(user_data)
            user_management.send_password_email(email, password)
            flash('Password sent to your email!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    email = session.get('username')
    user_management.save_session_data(email)
    session.clear()  # Clear the session without using delete_session
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/running_model')
def running_model():
    estimated_time = backend.calculate_average_time()
    if estimated_time is None:
        estimated_time = "No previous execution times available to estimate."
    return render_template('running_model.html', estimated_time=estimated_time)

@app.route('/model_progress')
def model_progress():
    progress = session.get('model_progress', 0)
    return jsonify(progress=progress)

####################################################
#METHODOLOGY RELATED
@app.route('/content/<page_name>')
def content_page(page_name):
    if 'username' not in session:
        return redirect(url_for('login'))

    content_folder = os.path.join('content', page_name)
    graph_file = os.path.join(content_folder, 'graph.html')
    explanation_file = os.path.join(content_folder, 'explanation.md')

    if not os.path.exists(graph_file) or not os.path.exists(explanation_file):
        flash('Content not found.')
        return redirect(url_for('index'))

    with open(explanation_file, 'r') as f:
        explanation = markdown.markdown(f.read())

    return render_template('content_page.html', title=page_name, graph=graph_file, explanation=explanation)

####################################################

@app.route('/run', methods=['POST'])
def run_model_endpoint():
    if 'username' not in session:
        return redirect(url_for('login'))

    economy_to_run = request.form.get('economy')
    if not economy_to_run:
        flash('No economy selected. Please select an economy to run.')
        return redirect(url_for('index'))

    session['economy_to_run'] = economy_to_run

    # Start the model run in a separate thread
    thread = threading.Thread(target=run_model, args=(economy_to_run,))
    thread.start()

    return redirect(url_for('running_model'))

def run_model(economy_to_run):
    session_id = session.get('session_id')
    log_filename = f'logs/model_output_{session_id}.log'

    # Redirect stdout and stderr to the log file
    logger = backend.StreamToLogger(log_filename)
    sys.stdout = logger
    sys.stderr = logger

    model_code_path = os.path.abspath(os.path.join(session['session_library_path'], 'model_code'))
    sys.path.insert(0, model_code_path)

    try:
        main_module_spec = importlib.util.spec_from_file_location("main", os.path.join(model_code_path, "main.py"))
        main_module_spec = importlib.util.find_spec("main")
        if main_module_spec is None:
            raise ImportError("Could not find the main module in the session-specific path")
        main_module = importlib.util.module_from_spec(main_module_spec)
        main_module_spec.loader.exec_module(main_module)

        start_time = time.time()
        session['model_progress'] = 0

        # Assuming main_module.main supports progress reporting via callback
        def progress_callback(progress):
            session['model_progress'] = progress
            session.modified = True

        main_module.main(economy_to_run, progress_callback)

        execution_time = time.time() - start_time
        backend.save_execution_time(execution_time)
    finally:
        if sys.path[0] == model_code_path:
            sys.path.pop(0)
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

@app.route('/stream')
def stream():
    session_id = session.get('session_id')
    log_filename = f'logs/model_output_{session_id}.log'

    # Ensure the log file exists
    if not os.path.isfile(log_filename):
        open(log_filename, 'w').close()

    def generate():
        with open(log_filename, 'r') as log_file:
            while True:
                line = log_file.readline()
                if not line:
                    break
                yield f"data: {line}\n\n"
                time.sleep(1)

    return Response(stream_with_context(generate()), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)