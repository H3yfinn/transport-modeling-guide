#todo check that singvble user having multiple open sessions does not cause issues
from flask import request, render_template, send_file, flash, redirect, url_for, session, jsonify
import os
from datetime import timedelta
import markdown
import time
import threading

import re
import pandas as pd
from shared import progress_tracker, global_logger, model_threads,model_FILE_DATE_IDs
from itsdangerous import URLSafeTimedSerializer
import backend
from shared import global_logger, error_logger, create_app, SafeConfig
import validators
from bs4 import BeautifulSoup
# Initialize the app
app = create_app()
app.config = SafeConfig(app.config)

from user_management import UserManagement
from encryption import decrypt_data

# Initialize user management and mail
user_manager = UserManagement(app)
mail = user_manager.mail

s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

estimated_time = None #this will be updated and made global in the running_model() function

app.config['INITIALIZED'] = False
############################################################################
#maybe this is needed:from flask import Flask, current_app
# from flask import Flask, current_app
# app = Flask(__name__)

# @app.context_processor
# def inject_config():
#     return dict(config=current_app.config)
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
    if not app.config['INITIALIZED']:
        user_manager.startup_tasks()
        app.config['INITIALIZED'] = True
    session.permanent = True
    session.modified = True  # Ensures the session cookie is sent to the client
    session['last_active'] = time.time()
    
@app.route('/')
def index():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    return render_template('index.html', keys=app.config.ECONOMY_NAMES.keys())

# @app.route('/no_login_and_model')
# def no_login_and_model():
#     #if we think noones going to use website we can activate app.config.NO_LOGIN_AND_MODEL and use this page to redirect user
#     return render_template('no_login_and_model.html')

@app.route('/staging', methods=['GET', 'POST'])
def staging():
    if app.config.NO_MODEL:
        return render_template('no_login_or_model.html')
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        economy_to_run = app.config.ECONOMY_NAMES.get(request.form.get('economy'), None)
        if session['economy_to_run'] == economy_to_run:
            #double check that theuser isnt mid model run or has results available
            if user_manager.check_model_is_running():
                return redirect(url_for('model_progress'))
            elif user_manager.check_if_results_available():
                return redirect(url_for('results'))
            #now we need to set the session data
            user_manager.setup_user_session()
        else:
            #now we need to set the session data
            user_manager.setup_user_session()
            session['economy_to_run'] = economy_to_run
            
    if request.method == 'GET':
        
        if user_manager.check_model_is_running():
            return redirect(url_for('model_progress'))
        elif user_manager.check_if_results_available():
            return redirect(url_for('results'))
        
        user_manager.setup_user_session()
        economy_to_run = session.get('economy_to_run')
        if not economy_to_run:
            flash('No economy selected. Please select an economy to run the model.')
            return redirect(url_for('index'))

    input_files = file_dict.keys() 

    return render_template('staging.html', input_files=input_files, economy=economy_to_run)

@app.route('/upload', methods=['POST'])
def upload_file():
    if app.config.NO_MODEL:
        return render_template('no_login_or_model.html')

    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('staging'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('staging'))
    
    if file:
        filename = file.filename
        if filename not in file_dict:
            flash(f'{filename} is not a required input file. Maybe you need to name it correctly.')
            return redirect(url_for('staging'))
        
        new_filepath = os.path.join(session['session_library_path'], 'input_data', filename)
        file.save(new_filepath)
        flash(f'File {filename} uploaded successfully')
    
    return redirect(url_for('staging'))
    
@app.route('/download_input_file/<path:filename>')
def download_input_file(filename):
    if app.config.NO_MODEL:
        return render_template('no_login_or_model.html')

    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    file_path = os.path.join(session['session_library_path'], 'input_data', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        flash('File not found.')
        return redirect(url_for('staging'))
    
@app.route('/reset_user_session', methods=['GET', 'POST'])
def reset_user_session():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
        
    #double check user is not still running the model. if so they must wait for it to finish
    if user_manager.check_model_is_running():
        flash('Model is still running. Please wait for it to finish.')
        
    user_manager.reset_user_session()
    return redirect(url_for('index'))

@app.route('/hard_reset_user_session', methods=['GET', 'POST'])
def hard_reset_user_session():        
    #this is a hard reset and will not check if the user is still running the model
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
        
    user_manager.reset_user_session()
    return redirect(url_for('index'))

@app.route('/results', methods=['GET', 'POST'])
def results():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))

    if not user_manager.check_if_results_available():
        if user_manager.check_model_is_running():
            return redirect(url_for('model_progress'))
        else:
            return redirect(url_for('index'))
    
    if request.method == 'POST':
        session['economy_to_run'] = app.config.ECONOMY_NAMES.get(request.form.get('economy'), None)
    economy_to_run = session.get('economy_to_run')
    
    results_files = [
        # f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_results.html',
        # f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions.html',
        #f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions_extra.html',
        # f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_results.html',
        # f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions.html'#,
        # #f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions_extra.html'
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Low_Carbon_dashboard_results.html',
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Low_Carbon_dashboard_secondary_results.html',
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Business_as_Usual_dashboard_results.html',
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Business_as_Usual_dashboard_secondary_results.html'
    ]
    
    results_paths = [os.path.join(session['session_library_path'], 'plotting_output', file) for file in results_files]
    #check that they exist, otherwise remove them from the list
    results_paths = [file for file in results_paths if os.path.exists(file)]
    
    key_csv_files = results_files
    #     f'plotting_output/key_results_{economy_to_run}.csv',
    #     input_data/key_input_{economy_to_run}.csv'
    # ]
    if session['user_id'] in model_FILE_DATE_IDs.keys():
        model_FILE_DATE_ID = model_FILE_DATE_IDs[session['user_id']]
        
        key_csv_files += [f'output_data/for_other_modellers/output_for_outlook_data_system/{model_FILE_DATE_ID}_{economy_to_run}_transport_stocks.csv',
        f'output_data/for_other_modellers/output_for_outlook_data_system/{model_FILE_DATE_ID}_{economy_to_run}_transport_stock_shares.csv',
        f'output_data/for_other_modellers/output_for_outlook_data_system/{model_FILE_DATE_ID}_{economy_to_run}_transport_activity.csv',
        f'output_data/for_other_modellers/output_for_outlook_data_system/{economy_to_run}_{model_FILE_DATE_ID}_transport_energy_use.csv']

    key_csv_paths = [os.path.join(session['session_library_path'], file) for file in key_csv_files]
    #check that they exist, otherwise remove them from the list
    key_csv_paths = [file for file in key_csv_paths if os.path.exists(file)]
    
    logs = backend.get_logs_from_file(session['session_log_filename'])
    
    if app.config.DEBUG_LOGGING:
        global_logger.info('Displaying results.')
    # global_logger.info(results_paths)
    return render_template('results.html', results_paths=results_paths, key_csv_paths=key_csv_paths, logs=logs)

####################################################
@app.route('/default_results', methods=['GET', 'POST'])
def default_results():
    #this is a copy of the results() function but with the paths changed to the original model library and no logs shown
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        session['economy_to_run'] = app.config.ECONOMY_NAMES.get(request.form.get('economy'), None)
    economy_to_run = session.get('economy_to_run')
    
    results_files = [
        # f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_results.html',
        # f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions.html',
        #f'dashboards/{economy_to_run}/{economy_to_run}_Target_dashboard_assumptions_extra.html',
        # f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_results.html',
        # f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions.html'#,
        #f'dashboards/{economy_to_run}/{economy_to_run}_Reference_dashboard_assumptions_extra.html'
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Low_Carbon_dashboard_results.html',
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Low_Carbon_dashboard_secondary_results.html',
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Business_as_Usual_dashboard_results.html',
        f'dashboards/dashboards_for_web/{economy_to_run}//WEB_{economy_to_run}_Business_as_Usual_dashboard_secondary_results.html'
    ]
    
    results_paths = [os.path.join(app.config.ORIGINAL_MODEL_LIBRARY_NAME, 'plotting_output', file) for file in results_files]
    #check that they exist, otherwise remove them from the list
    results_paths = [file for file in results_paths if os.path.exists(file)]
    
    key_csv_files = results_files
    #     f'plotting_output/key_results_{economy_to_run}.csv',
    #     input_data/key_input_{economy_to_run}.csv'
    # ]
    if session['user_id'] in model_FILE_DATE_IDs.keys():
        model_FILE_DATE_ID = model_FILE_DATE_IDs[session['user_id']]
        
        key_csv_files += [f'output_data/for_other_modellers/{economy_to_run}/{model_FILE_DATE_ID}_{economy_to_run}_transport_stocks.csv',
        f'output_data/for_other_modellers/{economy_to_run}/{model_FILE_DATE_ID}_{economy_to_run}_transport_stock_shares.csv',
        f'output_data/for_other_modellers/{economy_to_run}/{model_FILE_DATE_ID}_{economy_to_run}_transport_activity.csv',
        f'output_data/for_other_modellers/{economy_to_run}/{economy_to_run}_{model_FILE_DATE_ID}_transport_energy_use.csv']

    key_csv_paths = [os.path.join(app.config.ORIGINAL_MODEL_LIBRARY_NAME, file) for file in key_csv_files]
    #check that they exist, otherwise remove them from the list
    key_csv_paths = [file for file in key_csv_paths if os.path.exists(file)]
    
    if app.config.DEBUG_LOGGING:
        global_logger.info('Displaying results.')
    # global_logger.info(results_paths)
    return render_template('default_results.html', results_paths=results_paths, key_csv_paths=key_csv_paths)

######################################################
@app.route('/serve_file/<path:filename>')
def serve_file(filename):
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    file_path = filename  # Use the full path directly from the template
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        flash('File not found.')
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
        flash('File not found.')
        return redirect(url_for('results'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if app.config.NO_LOGIN:
        return render_template('no_login_or_model.html')
    if user_manager.is_session_valid():
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_manager.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
        if user and decrypt_data(user['password']) == password:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            user_manager.restart_user_session()
            flash('Login successful.')
            
            ################SPACE MANAGEMENT################
            #since this is a point where we need to know how much space is available, we will check the disk space here and run some cleanup tasks. Note that this could be done with a cron/scheduled job, but this is a more simple way to do it.
            backend.check_disk_space()
            user_manager.delete_inactive_users_sessions()
            ################################################
            
            return redirect(url_for('index'))
        elif not user:
            flash('User does not exist. Please register first.')
            return redirect(url_for('register'))
        elif decrypt_data(user['password']) != password:
            flash('Invalid password.')
            return redirect(url_for('login'))
        else:
            flash('An unknown error occurred.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if app.config.NO_LOGIN:
        return render_template('no_login_or_model.html')
    if user_manager.is_session_valid():
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        if user_manager.register_user(email): 
            user = user_manager.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            user_manager.restart_user_session()
            
            ################SPACE MANAGEMENT################
            #since this is a point where we need to know how much space is available, we will check the disk space here and run some cleanup tasks. Note that this could be done with a cron/scheduled job, but this is a more simple way to do it.
            backend.check_disk_space()
            user_manager.delete_inactive_users_sessions()
            ################################################
            
            return redirect(url_for('index'))
        else:
            flash('Email already registered.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if app.config.NO_LOGIN:
        return render_template('no_login_or_model.html')
    
    if user_manager.is_session_valid():
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        user = user_manager.find_user_in_user_data_by_key_value('email', email, ENCRYPTED=True)
        
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            if app.config.LOGGING:
                global_logger.info(f'Password reset token: {token}')
            reset_link = url_for('reset_password', token=token, _external=True)
            if app.config.LOGGING:
                global_logger.info(f'Password reset link: {reset_link}')
            try:
                user_manager.send_reset_password_email(email, reset_link)
                flash('A password reset link has been sent to your email.', 'info')
            except Exception as e:
                flash('Failed to send password reset email. Please try again later.', 'danger')
        else:
            flash('Email address not found.', 'danger')
        return redirect(url_for('forgot_password'))
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if app.config.NO_LOGIN:
        return render_template('no_login_or_model.html')
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        if user_manager.update_user_password(email, new_password):
            flash('Your password has been updated!', 'success')
            return redirect(url_for('login'))
        else:
            flash('An error occurred while updating your password.', 'danger')
            return redirect(url_for('reset_password', token=token))

    return render_template('reset_password.html', token=token)

@app.route('/logout')
def logout():
    if app.config.NO_LOGIN:
        return render_template('no_login_or_model.html')
    
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
 
    # Save session data into the user object
    user_manager.save_session_data()

    session.clear()  # Clear the session without using delete_session
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/feedback_form')
def feedback_form():
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    return render_template('feedback_form.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form['name']
    message = request.form['message']
    try:
        backend.process_feedback(name, message)
    except Exception as e:
        global_logger.error(f'Error processing feedback: {str(e)}')
        error_logger.error(f'Error processing feedback: {str(e)}')
    return redirect(url_for('index'))

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
    if app.config.NO_MODEL:
        return render_template('no_login_or_model.html')
    
    if not user_manager.is_session_valid():
        user_manager.clear_invalid_session()
        return redirect(url_for('login'))
    
    economy_to_run = app.config.ECONOMY_NAMES.get(request.form.get('economy'), None)
    session.get('economy_to_run')
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
        if app.config.LOGGING:
            global_logger.info('User results are available. User must restart the session before running a new model.')
        return redirect(url_for('results'))
    if user_manager.check_model_is_running():
        if app.config.LOGGING:
            global_logger.info('User model is running. User must restart the session before running a new model.')
        return redirect(url_for('model_progress'))
    
    if len(model_threads.keys()) > 0:
        #we already have a model thread running, we should avoid running another till thats done, because of memory issues.
        if app.config.LOGGING:
            global_logger.info('Another model thread is already running. User must wait for it to finish before running a new model.')
        flash('Another model is already running. Please wait for it to finish before running a new model.')
        return 
        
    #update estimated_time 
    global estimated_time
    estimated_time = backend.calculate_average_time()
    
    try:
        # Start the model run in a separate thread. also initiate alll variables now, since we are about to start a new thread and things could get messy if we dont
        session['model_thread_running'] = True
        session['results_available'] = False
        progress_tracker[session['user_id']] = 0
        
        model_threads[session['user_id']] = [True, None]
        
        if app.config.DEBUG:
            session['model_thread_running'] = False
            session['results_available'] = True
            progress_tracker[session['user_id']] = 0
            del model_threads[session['user_id']]
            user_manager.save_session_data()
            return redirect(url_for('model_progress'))
            
        thread = threading.Thread(target=backend.run_model_thread, args=(app, session['session_log_filename'], session['session_library_path'], economy_to_run, session['user_id']))
        thread.start()
        model_threads[session['user_id']][1] = thread
        
        if app.config.LOGGING:
            global_logger.info('Model run started successfully, thread is: {}'.format(thread))
        user_manager.save_session_data()
        return redirect(url_for('model_progress'))
        
    except Exception as e:
        if app.config.LOGGING:
            global_logger.error(f'Error running model: {str(e)}')
            global_logger.error(f'Error running model: {str(e)}')

        return redirect(url_for('error_page', error_message=str(e)))
    
@app.route('/error_page')
def error_page():
    error_message = request.args.get('error_message', 'An unknown error occurred.')
    return render_template('error.html', error_message=error_message)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/model_progress', methods=['GET', 'POST'])
def model_progress():
    if app.config.NO_MODEL:
        return render_template('no_login_or_model.html')
    if request.method == 'POST':
        if app.config.DEBUG_LOGGING:
            global_logger.info('model_progress() Running POST request')
        if not user_manager.is_session_valid():
            user_manager.clear_invalid_session()
            return redirect(url_for('login'))
        
        if not user_manager.check_model_is_running():
            if user_manager.check_if_results_available():
                if app.config.DEBUG_LOGGING:
                    global_logger.info('model_progress() POST: Model is not running and results are available. Redirecting to results page.')
                return jsonify({'redirect': url_for('results')})
            else:
                if app.config.DEBUG_LOGGING:
                    global_logger.info('model_progress() POST: Model is not running and results not available. Redirecting to index page.')
                return jsonify({'redirect': url_for('index')})
        
        logs = backend.get_logs_from_file(session['session_log_filename'])
        
        if app.config.DEBUG_LOGGING:
            global_logger.info('model_progress() setting up model progress page')
        return jsonify({'progress': progress_tracker.get(session['user_id'], 0), 'logs': logs})#, 'estimated_time': estimated_time})
        
    elif request.method == 'GET':
        #following are in case of accidental visit to the model progress page
        if not user_manager.is_session_valid():
            user_manager.clear_invalid_session()
            return redirect(url_for('login'))
        if not user_manager.check_model_is_running():
            if user_manager.check_if_results_available():
                if app.config.LOGGING:
                    global_logger.info('model_progress() GET: Model is not running and results are available. Redirecting to results page.')
                return redirect(url_for('results'))
            else:
                if app.config.LOGGING:
                    global_logger.info('model_progress() GET: Model is not running and results not available. Redirecting to index page.')
                return redirect(url_for('index'))
        
        # While on the page, check if the model is still running
        user_id = session['user_id']
        if session['model_thread_running']:#user_id in model_threads.keys():
            # thread = model_threads[user_id][1]
            # session['model_thread_running'] = thread.is_alive()
            # if not session['model_thread_running']:
            #     global_logger.error('Model thread found yet model_thread_running is True. This should not happen. Model threads are: {}'.format(model_threads))
            # if app.config.LOGGING:
            #     global_logger.info('model_progress() GET: Model completed running. Redirecting to results page.')
            # del model_threads[user_id]
            # session['results_available'] = True
            # user_manager.save_session_data()
            # return redirect(url_for('results'))
            
            # else:   
            logs = backend.get_logs_from_file(session['session_log_filename'])
            return render_template('model_progress.html', progress=progress_tracker[session['user_id']], logs=logs)#, estimated_time=estimated_time)
        
        else:
            # if session['model_thread_running']:
            if app.config.LOGGING:
                global_logger.info('model_progress() GET: Model completed running. Redirecting to results page.')
            # session['model_thread_running'] = False
            # session['results_available'] = True
            if user_id in model_threads.keys():
                if app.config.LOGGING:
                    global_logger.info('Model thread still in model thread after model_thread_running set to False.')
            else:
                if app.config.LOGGING:
                    global_logger.info('Model thread not in model thread after model_thread_running set to False.')
            user_manager.save_session_data()
            return redirect(url_for('results'))
        # else:
        #     global_logger.error('User id not in keys yet model_thread_running is True. This should not happen. Model threads are: {}'.format(model_threads))
            
            
            
            
            # if app.config.LOGGING:
            #     global_logger.error('Model thread not found yet model_running is True. This should not happen. Model threads are: {}'.format(model_threads))
            # return redirect(url_for('index'))
    
####################################################

# Define the function to replace placeholders
def replace_placeholders(explanation, content_folder):
    file_pattern = re.compile(r'\{\{(table|graph):(.+?)\}\}')        
    link_pattern = re.compile(r'\{\{(link):(.+?):(text):(.+?)\}\}')#{{link:https://transport-energy-modelling.com/content/activity_growth:text:here}}
    image_pattern = re.compile(r'\{\{(image):(.+?)\}\}') 

    def replace_with_link(match):
        link = match.group(2)
        text = match.group(4)
        #if https is not in the link, add it
        if not link.startswith('http://') and not link.startswith('https://'):
            link = 'https://' + link
        # Check if link is correct using validators.url
        if not validators.url(link):
            # put an error in the error.log file for me to check, but otehrwsie jsut let the 404 page handle it
            error_logger.error(f'replace_placeholders: Invalid link: {link}')
        return f'<a href="{link}" target="_blank">{text}</a>'
        
    def replace_with_file(match):
        file_type = match.group(1)
        file_name = match.group(2)
        file_path = os.path.join(content_folder, file_name)

        if file_type == 'table' and os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                return df.to_html(classes='table table-striped', index=False)
            except Exception as e:
                error_logger.error(f'Error reading table file: {file_name} ({str(e)})')
                return ''#f'<div style="color:red;">Error reading table file: {file_name} ({str(e)})</div>'
            
        elif os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        return file.read()
                except UnicodeDecodeError:
                    error_logger.error(f'Error reading {file_type} file: {file_name} (encoding issue)')
                    return f'<div style="color:red;">Error reading {file_type} file: {file_name} (encoding issue)</div>'
        else:
            return f'<div style="color:red;">{file_type.capitalize()} file not found: {file_name}</div>'

    def replace_with_image(match):
        image_name = match.group(2)
        image_path = os.path.join(content_folder, image_name)
        if os.path.exists(image_path):
            return f'<img src="{image_path}" alt="{image_name}" class="img-fluid">'
        else:
            error_logger.error(f'Image file not found: {image_name}')
            return f'<div style="color:red;">Image file not found: {image_name}</div>'
        
    # Process line by line
    lines = explanation.split('\n')
    replaced_lines = []
    for line in lines:
        if file_pattern.search(line):
            line = file_pattern.sub(replace_with_file, line)
        if link_pattern.search(line):
            line = link_pattern.sub(replace_with_link, line)
        if image_pattern.search(line):  # Process image placeholders
            line = image_pattern.sub(replace_with_image, line)
        replaced_lines.append(line)
    
    return '\n'.join(replaced_lines)

# Additional helper to ensure well-formed HTML for debugging
def validate_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.prettify()

# Define the route to serve the content
@app.route('/content/<page_name>')
def content_page(page_name):
    content_folder = os.path.join('content', page_name)
    
    # Get all HTML and markdown files in the content folder
    explanation_files = [f for f in os.listdir(content_folder) if f.endswith('.md')]
    if not explanation_files:
        return render_template('error.html', error_message='Content not found.')
    
    if app.config.get('LOGGING', False):
        global_logger.info(f'Generating content for page {page_name}')
    
    explanation = ''
    for explanation_file in explanation_files:
        explanation_file_path = os.path.join(content_folder, explanation_file)
        with open(explanation_file_path, 'r', encoding='utf-8') as f:
            explanation_content = f.read()
            explanation_markdown = markdown.markdown(explanation_content)
            explanation += replace_placeholders(explanation_markdown, content_folder)
    
    
    # Validate and prettify HTML for debugging
    explanation_html = validate_html(explanation)
    
    return render_template('content_page.html', explanation=explanation_html)

####################################################
#tehse need to be here because not all global variables are defined yet, i think?
# def run_tasks():
#     global_logger.info('Running tasks: delete_inactive_users_sessions, check_disk_space')
#     # Run the tasks in a separate thread
            
# # Schedule the cleanup task
# # schedule.every().day.at("00:00").do(run_tasks)
# schedule.every().minute.do(run_tasks)
# def run_scheduler():
#     while True:
#         schedule.run_pending()
#         time.sleep(30)

# # Start the scheduler in a separate thread
# scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
# scheduler_thread.start()
####################################################
if __name__ == '__main__':
    app.run()#debug=False)
####################################################
