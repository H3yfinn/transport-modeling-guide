from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session
# from flask_apscheduler import APScheduler
from config import Config, create_folders
from user_management import UserManagement
import os
import shutil
import sys
from datetime import timedelta
from encryption import encrypt_password, decrypt_password
import markdown
# Initialize the app
app = Flask(__name__)
app.config.from_object(Config)
create_folders()

# Initialize user management and mail
user_management = UserManagement(app)
mail = user_management.mail

# # Initialize APScheduler
# scheduler = APScheduler()
# scheduler.init_app(app)
# scheduler.start()

# Adjust the Python path to include the workflow directory inside LIBRARY_NAME
LIBRARY_NAME = '../transport_model_9th_edition'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), LIBRARY_NAME, 'workflow')))
# # Import the main function from your model
# from main import main
# # also run and pull FILE_DATE_ID and transport_data_system_FILE_DATE_ID from the model inside {LIBRARY_NAME}/config/config.py
# from config.config import FILE_DATE_ID, transport_data_system_FILE_DATE_ID

############################################################################
SAVED_FOLDER_STRUCTURE_PATH = 'folder_structure.txt' 
ORIGINAL_LIBRARY_PATH = '../transport_model_9th_edition'
BASE_UPLOAD_FOLDER = 'uploads'

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
    INPUT_DATA_FOLDER_PATH=os.path.join(ORIGINAL_LIBRARY_PATH, 'input_data'), 
    SAVED_FOLDER_STRUCTURE_PATH=SAVED_FOLDER_STRUCTURE_PATH, 
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
    session['last_active'] = timedelta(weeks=1)
    
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))#get user to create or login, if they are not logged in
    
    user_management.session_specific_setup()
    
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

    user_management.session_specific_setup()

    session_id = session.get('session_id')
    session_folder = os.path.join(app.config['BASE_UPLOAD_FOLDER'], session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    session_library_path = os.path.join(session_folder, app.config['ORIGINAL_LIBRARY_PATH'])

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
        
        # filepath = os.path.join(session_folder, filename)
        # file.save(filepath)
        
        filepath = file_dict[filename]#get the path to the file wihtin the input_data folder
        filepath = os.path.join(session_library_path, filepath)
        file.save(filepath)
        
        # model_input_path = os.path.join(session_library_path, 'input_data', filename)
        # shutil.move(filepath, model_input_path)
        
        flash(f'File {filename} uploaded successfully')
        return redirect(url_for('index'))

@app.route('/run', methods=['POST'])
def run_model_endpoint():
    if 'username' not in session:#get user to create or login, if they are not logged in
        return redirect(url_for('login'))

    user_management.session_specific_setup()

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

    user_management.reset_sessions_model()
    flash('Session reset successfully')
    return redirect(url_for('index'))

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_management.session_specific_setup()

    session_id = session.get('session_id')
    economy_to_run = session.get('economy_to_run')
    if not economy_to_run:
        flash('No economy selected. Please run the model first.')
        return redirect(url_for('index'))
    
    session_folder = os.path.join(app.config['BASE_UPLOAD_FOLDER'], session_id)
    session_library_path = os.path.join(session_folder, app.config['ORIGINAL_LIBRARY_PATH'])
    
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

    user_management.session_specific_setup()

    session_id = session.get('session_id')
    session_folder = os.path.join(app.config['BASE_UPLOAD_FOLDER'], session_id)
    file_path = os.path.join(session_folder, filename)
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
            user_data[email] = encrypted_password.decode()#TO DO SHOULDNT THIS BE ENCODED?
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

####################################################
#METHODOLOGY RELATED
@app.route('/content/<page_name>')
def content_page(page_name):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user_management.session_specific_setup()

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
def run_model(economy_to_run):
    main(economy_to_run)

if __name__ == '__main__':
    app.run(debug=True)