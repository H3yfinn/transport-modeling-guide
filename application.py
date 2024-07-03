#todo check that singvble user having multiple open sessions does not cause issues
from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session, jsonify, stream_with_context, Response
import os
import shutil
import sys
from datetime import timedelta, datetime
import markdown
import time
from dotenv import load_dotenv
import importlib.util
import threading
import schedule
from encryption import load_keys_from_file
import jwt
import uuid
from shared import progress_tracker, global_logger, model_threads,model_FILE_DATE_IDs

# Load environment variables from .env file and keys from secret.key file
load_dotenv()
# load_keys_from_file()

from config import Config, create_folders
from user_management import UserManagement
from encryption import encrypt_password, decrypt_password
import backend
from backend import global_logger

# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)
# create_folders()

# Initialize user management and mail
user_manager = UserManagement(app)
mail = user_manager.mail

# Global dictionary to track model progress

# Pass the global model_progress_tracker to backend
# backend.set_model_progress_tracker(model_progress_tracker)
############################################################################

def get_required_input_files_and_their_locations(CHECK_FOLDER_STRUCTURE, INPUT_DATA_FOLDER_PATH, SAVED_FOLDER_STRUCTURE_PATH, OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH):
    """Will search through transport_model_9th_edition/input_data and record the names of all input files and their locations. Then when a file is passed to this app, if it is in the list of required files, it will be moved to the correct location. If it is not, an error message will be returned to the user. This will also take in a list of allowed files to be uploaded, as well as having the option to be passed the structure of the input_data folder, so it doesn't have to be run all the time, only when the structure of the input_data folder changes and the user sets CHECK_FOLDER_STRUCTURE to true.
    
    CHECK_FOLDER_STRUCTURE = True or False
    INPUT_DATA_FOLDER_PATH = the path to the input_data folder
    SAVED_FOLDER_STRUCTURE_PATH = the path to the file that will store the structure of the input_data folder
    OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH = True or False
    """
    excluded_files = ['.gitkeep', 'lifecycle_emissions.xlsx']
    allowed_folders = ['user_input_spreadsheets']#['__pycache__', 'previous_run_archive', 'alternate_sales_shares', '9th_model_inputs', 'archive'
    if CHECK_FOLDER_STRUCTURE:
        # Get all the files in the input_data folder
        input_data_files = os.listdir(INPUT_DATA_FOLDER_PATH)
        # Set up a dict which maps the file name to the file path
        file_dict = {}
        for file in input_data_files:
            if not os.path.isfile(os.path.join(INPUT_DATA_FOLDER_PATH, file)):
                if file in allowed_folders:
                    folder = file
                    for file in os.listdir(os.path.join(INPUT_DATA_FOLDER_PATH, file)):
                        filename = os.path.basename(file)
                        if filename in excluded_files:
                            continue
                        file_dict[filename] = os.path.join(INPUT_DATA_FOLDER_PATH, folder, file)
                continue
            filename = os.path.basename(file)
            if filename in excluded_files:
                continue
            file_dict[filename] = os.path.join(INPUT_DATA_FOLDER_PATH, file)
        
        if OVERWRITE_SAVED_FOLDER_STRUCTURE_PATH:
            with open(SAVED_FOLDER_STRUCTURE_PATH, 'w') as f:
                f.write(str(file_dict))
    else:
        with open(SAVED_FOLDER_STRUCTURE_PATH, 'r') as f:
            file_dict = eval(f.read())
    
    #ALSO ADD parameters.yml FROM CONFIG FOLDER
    file_dict['parameters.yml'] = os.path.join(app.config['ORIGINAL_MODEL_LIBRARY_NAME'], 'config', 'parameters.yml')
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
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    keys = [
        '01_AUS', '02_BD', '03_CDA', '04_CHL', '05_PRC', '06_HKC',
        '07_INA', '08_JPN', '09_ROK', '10_MAS', '11_MEX', '12_NZ',
        '13_PNG', '14_PE', '15_PHL', '16_RUS', '17_SGP', '18_CT',
        '19_THA', '20_USA', '21_VN'
    ]
    return render_template('index.html', keys=keys)

@app.route('/staging', methods=['GET', 'POST'])
def staging():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    #double check that theuser isnt mid model run or has results available
    if user_manager.check_model_is_running():
        return redirect(url_for('model_progress'))
    elif user_manager.check_if_results_available():
        return redirect(url_for('results'))
    
    #now we need to set the session data
    user_manager.setup_user_session()
    
    if request.method == 'POST':
        economy_to_run = request.form.get('economy')
        session['economy_to_run'] = economy_to_run
    
    elif request.method == 'GET':
        economy_to_run = session.get('economy_to_run')
        if not economy_to_run:
            flash('No economy selected. Please select an economy to run the model.')
            return redirect(url_for('index'))

    input_files = file_dict.keys() 

    return render_template('staging.html', input_files=input_files, economy=economy_to_run)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('FLASH: No file part')
        return redirect(url_for('staging'))
    
    file = request.files['file']
    if file.filename == '':
        flash('FLASH: No selected file')
        return redirect(url_for('staging'))
    
    if file:
        filename = file.filename
        if filename not in file_dict:
            flash(f'FLASH: {filename} is not a required input file. Maybe you need to name it correctly.')
            return redirect(url_for('staging'))
        
        new_filepath = os.path.join(session['session_library_path'], 'input_data', filename)
        file.save(new_filepath)
        flash(f'FLASH: File {filename} uploaded successfully')
    
    return redirect(url_for('staging'))
    
@app.route('/download_input_file/<path:filename>')
def download_input_file(filename):
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    file_path = os.path.join(session['session_library_path'], 'input_data', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('FLASH: File not found.')
        return redirect(url_for('staging'))
    
@app.route('/reset_user_session', methods=['GET', 'POST'])
def reset_user_session():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    user_manager.reset_user_session()
    return redirect(url_for('index'))

@app.route('/results')
def results():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))

    if not user_manager.check_if_results_available():
        if user_manager.check_model_is_running():
            return redirect(url_for('model_progress'))
        else:
            return redirect(url_for('index'))
        
    economy_to_run = session.get('economy_to_run')
    if not economy_to_run:
        global_logger.info('No economy selected. Please run the model first.')
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
    
    key_csv_files = results_files
    #     f'plotting_output/key_results_{economy_to_run}.csv',
    #     input_data/key_input_{economy_to_run}.csv'
    # ]
    if session['user_id'] in model_FILE_DATE_IDs:
        model_FILE_DATE_ID = model_FILE_DATE_IDs[session['user_id']]
        
        key_csv_files += [f'output_data/for_other_modellers/{economy_to_run}/{model_FILE_DATE_ID}_{economy_to_run}_transport_stocks.csv',
        f'output_data/for_other_modellers/{economy_to_run}/{model_FILE_DATE_ID}_{economy_to_run}_transport_stock_shares.csv',
        f'output_data/for_other_modellers/{economy_to_run}/{model_FILE_DATE_ID}_{economy_to_run}_transport_activity.csv',
        f'output_data/for_other_modellers/{economy_to_run}/{economy_to_run}_{model_FILE_DATE_ID}_transport_energy_use.csv']

    key_csv_paths = [os.path.join(session['session_library_path'], file) for file in key_csv_files]
    
    logs = backend.get_logs_from_file(session['session_log_filename'])
    
    global_logger.info('Displaying the following results:')
    global_logger.info(results_paths)
    return render_template('results.html', results_paths=results_paths, key_csv_paths=key_csv_paths, logs=logs)

@app.route('/serve_file/<path:filename>')
def serve_file(filename):
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    file_path = filename  # Use the full path directly from the template
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        flash('FLASH: File not found.')
        return redirect(url_for('results'))

@app.route('/download/<path:filename>')
def download_file(filename):
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))

    file_path = filename  # Use the full path directly from the template
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('FLASH: File not found.')
        return redirect(url_for('results'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if user_manager.is_session_valid():
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_manager.find_user_in_user_data_by_key_value('email', email)
        if user and decrypt_password(user['password']) == password:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            user_manager.restart_user_session()
            flash('FLASH: Login successful.')
            return redirect(url_for('index'))
        elif not user:
            flash('FLASH: User does not exist. Please register first.')
            return redirect(url_for('register'))
        elif decrypt_password(user['password']) != password:
            flash('FLASH: Invalid password.')
            return redirect(url_for('login'))
        else:
            flash('FLASH: An unknown error occurred.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        if user_manager.register_user(email):
            user = user_manager.find_user_in_user_data_by_key_value('email', email)
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash('FLASH: Registration successful. Please check your email for your password.')
            return redirect(url_for('login'))
        else:
            flash('FLASH: Email already registered.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))

    # Save session data into the user object
    user_manager.save_session_data()

    session.clear()  # Clear the session without using delete_session
    flash('FLASH: You have been logged out.')
    return redirect(url_for('login'))

####################################################
@app.route('/running_model', methods=['POST'])
def running_model():
    """
    #kind of irrelevant page but it acts as a middle man between the index page and the model progress page or the results page.
    The way this will work is:
    if the user accidentally reaches this apge and they dont have a valid session, they will be redirected to the login page.
    else:
    If they have a session active, they will be shown the progress of the model run. But if the model run is complete, they will be redirected to the results page.
    else:
    If they do not have a session active and they selected and economy to run the model will be run in a separate thread and they will be shown the progress of the model run on the model progress page.
    
    When the model run is completed, the user will be redirected to the results page.
    
    If an error occurs during any stage, the user will be redirected to the error page.
    """
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    economy_to_run = request.form.get('economy')
    if economy_to_run and economy_to_run != session.get('economy_to_run'):
        #need to reset the user session before running a new model
        user_manager.reset_user_session()
    elif not economy_to_run:
        economy_to_run = session.get('economy_to_run')#try using the previous economy to run if the user has somehow not selected a new one
        if not economy_to_run:
            #send user back to the index page to select an economy to run the model
            return redirect(url_for('index'))
        
    session['economy_to_run'] = economy_to_run
    
    #check if a user session has already been set up. if so the user must restart it before running a new model
    if user_manager.check_if_results_available():
        global_logger.info('User results are available. User must restart the session before running a new model.')
        return redirect(url_for('results'))
    if user_manager.check_model_is_running():
        global_logger.info('User model is running. User must restart the session before running a new model.')
        return redirect(url_for('model_progress'))
    
    try:
        # Start the model run in a separate thread
        thread = threading.Thread(target=backend.run_model_thread, args=(session['session_log_filename'], session['session_library_path'], economy_to_run, session['user_id']))
        thread.start()
        global_logger.info('Model run started successfully.')
        app.logger.info('Model run started successfully.')
        session['model_thread_running'] = True
        session['results_available'] = False
        global_logger.info('Saving session data after starting model run.')
        user_manager.save_session_data()
        model_threads[session['user_id']] = thread
        return redirect(url_for('model_progress'))
        
    except Exception as e:
        app.logger.error(f'Error running model: {str(e)}')
        flash(f'FLASH: Error running model: {str(e)}')
        print(f'PRINT: Error running model: {str(e)}')

        return redirect(url_for('error_page', error_message=str(e)))
    
@app.route('/error')
def error_page():
    error_message = request.args.get('error_message', 'An unknown error occurred.')
    return render_template('error.html', error_message=error_message)

@app.route('/model_progress', methods=['GET', 'POST'])
def model_progress():
    if request.method == 'POST':
        if not user_manager.is_session_valid():
            user_manager.clear_invalid_session()
            return redirect(url_for('login'))
        
        if not user_manager.check_model_is_running():
            if user_manager.check_if_results_available():
                global_logger.info('model_progress() POST: Model is not running and results are available. Redirecting to results page.')
                return jsonify({'redirect': url_for('results')})
            else:
                global_logger.info('model_progress() POST: Model is not running and results not available. Redirecting to index page.')
                return jsonify({'redirect': url_for('index')})
        
        estimated_time = backend.calculate_average_time()
        if estimated_time is None:
            estimated_time = "No previous execution times available to estimate."
        
        logs = backend.get_logs_from_file(session['session_log_filename'])
        
        return jsonify({'progress': progress_tracker.get(session['user_id'], 0), 'logs': logs, 'estimated_time': estimated_time})
        
    elif request.method == 'GET':
        if not user_manager.is_session_valid():
            user_manager.clear_invalid_session()
            return redirect(url_for('login'))

        if not user_manager.check_model_is_running():
            if user_manager.check_if_results_available():
                global_logger.info('model_progress() GET: Model is not running and results are available. Redirecting to results page.')
                return redirect(url_for('results'))
            else:
                global_logger.info('model_progress() GET: Model is not running and results not available. Redirecting to index page.')
                return redirect(url_for('index'))
        
        # Check if the model is still running
        user_id = session['user_id']
        if user_id in model_threads:
            thread = model_threads[user_id]
            session['model_thread_running'] = thread.is_alive()
            if not session['model_thread_running']:
                global_logger.info('model_progress() GET: Model completed running. Redirecting to results page.')
                del model_threads[user_id]
                session['results_available'] = True
                user_manager.save_session_data()
                return redirect(url_for('results'))
            
            else:   
                estimated_time = backend.calculate_average_time()
                if estimated_time is None:
                    estimated_time = "No previous execution times available to estimate."
                logs = backend.get_logs_from_file(session['session_log_filename'])
                return render_template('model_progress.html', progress=progress_tracker[session['user_id']], logs=logs, estimated_time=estimated_time)
        
        else:
            global_logger.error('Model thread not found yet model_running is True. This should not happen.')
            app.logger.error('Model thread not found yet model_running is True. This should not happen.')
            return redirect(url_for('reset_user_session'))
    
####################################################
# METHODOLOGY RELATED
@app.route('/content/<page_name>')
def content_page(page_name):
    content_folder = os.path.join('content', page_name)
    explanation_file = os.path.join(content_folder, 'explanation.md')

    if not os.path.exists(explanation_file):
        flash('FLASH: Content not found.')
        return redirect(url_for('index'))

    with open(explanation_file, 'r') as f:
        explanation = f.read()

    # Replace custom placeholders with actual HTML content
    explanation = replace_placeholders(explanation, content_folder)

    # Convert markdown to HTML
    explanation_html = markdown.markdown(explanation)

    return render_template('content_page.html', title=page_name, explanation=explanation_html)

def replace_placeholders(explanation, content_folder):
    import re
    pattern = re.compile(r'#insert (table|graph) here<(.+?)>')

    def replacement(match):
        file_type = match.group(1)
        file_name = match.group(2)
        file_path = os.path.join(content_folder, file_name)

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            except UnicodeDecodeError:
                return f'<div style="color:red;">Error reading {file_type} file: {file_name} (encoding issue)</div>'
        else:
            return f'<div style="color:red;">{file_type.capitalize()} file not found: {file_name}</div>'

    return pattern.sub(replacement, explanation)

def content_page(page_name):
    content_folder = os.path.join('content', page_name)
    #check for html and md files in the folder and render them
    graph_files = [f for f in os.listdir(content_folder) if f.endswith('.html')]
    explanation_files = [f for f in os.listdir(content_folder) if f.endswith('.md')]
    if not graph_files and not explanation_files:
        return render_template('error.html', error_message='Content not found.')

    graph_files_list = []
    for graph_file in graph_files:
        graph_file = os.path.join(content_folder, graph_file)
        graph_files_list += [graph_file]
    # with open(explanation_file, 'r') as f:
    #     explanation = markdown.markdown(f.read())
    explanation = ''
    for explanation_file in explanation_files:
        explanation_file = os.path.join(content_folder, explanation_file)
        with open(explanation_file, 'r') as f:
            explanation += markdown.markdown(f.read())

    return render_template('content_page.html', title=page_name, graph=graph_files_list, explanation=explanation)

####################################################
# @app.route('/stream')
# def stream():
#     if not user_manager.is_session_valid():
#         return user_manager.clear_invalid_session()
#     if not user_manager.is_session_active():
#         return redirect(url_for('index'))
    
#     user_id = session.get('user_id')
#     log_filename = f'logs/model_output_{user_id}.log'

#     def generate():
#         with open(log_filename, 'r') as log_file:
#             while True:
#                 line = log_file.readline()
#                 if not line:
#                     break
#                 yield line
#                 time.sleep(1)

#     return app.response_class(generate(), mimetype='text/plain')
####################################################
# Schedule the cleanup task
schedule.every().day.at("00:00").do(user_manager.delete_inactive_users_sessions)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == '__main__':
    app.run()#debug=False)
####################################################
