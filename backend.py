import logging
import os
import json
import shutil
import sys
import time
import importlib.util
import threading
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from config import Config
# from flask import session#trying to avoid using flask session within this module

import user_management as user_manager
from shared import progress_tracker, global_logger, setup_logger, model_threads,model_FILE_DATE_IDs
class StreamToLogger:
    def __init__(self, log_filename):
        self.logger = setup_logger('model_logger', log_filename)

    def write(self, message):
        with open(self.logger.handlers[0].baseFilename, 'a') as log_file:
            log_file.write(message)
        self.logger.info(message)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

    def close(self):
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()
        
def get_logs_from_file(log_filename):
    if Config.LOGGING:
        global_logger.info('Getting logs from file')
    if not os.path.exists(log_filename):
        return ''
    logs = open(log_filename, 'r').read()
    if not logs or logs.isspace():
        return 'No logs available yet'
    else:
        return logs

def archive_log(log_filename):
    if Config.LOGGING:
        global_logger.info(f'Archiving log file: {log_filename}')
    if os.path.exists(log_filename):
        try:
            with open(log_filename, 'a') as log_file:
                log_file.flush()
                os.fsync(log_file.fileno())
            
            archived_log_filename = os.path.join('logs', 'archive', f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{os.path.basename(log_filename)}')
            shutil.move(log_filename, archived_log_filename)
            if Config.LOGGING:
                global_logger.info(f'Log file archived: {archived_log_filename}')
        except PermissionError as e:
            global_logger.error(f"Permission error moving log file: {e}")#normally occurs if user is still running the model
        except Exception as e:
            global_logger.error(f"Error moving log file: {e}")

def run_model_thread(log_filename, session_library_path, economy_to_run, user_id):
    """Ok one big issue with this and threading and the way ive moidularised the model is that it uses relative imports and these dont work unless we add the models root folder to the path, but if we are threading multiple models from different paths we will end up importing from the firstt model on the path. However, because of the mdoels redevelopments we can sort of overcome this by assuming that all model are the same code an dinstead changing the paths we pass in to the model, especailly the root_dir path, which defines the relative poiint from which ALL files are read and saved from within the scope of that model. So we will add each model to the sys.path and remove it later, but this shouldnt be an issue.

    Args:
        log_filename (_type_): _description_
        session_library_path (_type_): _description_
        economy_to_run (_type_): _description_
        user_id (_type_): _description_

    Raises:
        ImportError: _description_
    """
    if Config.LOGGING:
        global_logger.info(f'Running model thread for economy: {economy_to_run}')
    FILE_DATE_ID = None
    logger = StreamToLogger(log_filename)
    sys.stdout = logger
    sys.stderr = logger
    try:
        if Config.DEBUG:
            pass
        else:
            sys.path.append(os.getcwd() +'\\' +  session_library_path)
            root_dir_param =  "\\\\?\\"+ os.getcwd()+ '\\' + session_library_path
            if Config.LOGGING:
                global_logger.info(f"sys.path: {sys.path}")
            #this is a hack to allow long paths in windows
            main_module_spec = importlib.util.spec_from_file_location("main", os.path.join(session_library_path, "main.py"))
            if main_module_spec is None:
                if Config.LOGGING:
                    global_logger.error("Could not find the main module in the session-specific path")
                raise ImportError("Could not find the main module in the session-specific path")
            else:
                if Config.LOGGING:
                    global_logger.info("Main module found in the session-specific path")
            main_module = importlib.util.module_from_spec(main_module_spec)
            main_module_spec.loader.exec_module(main_module)

        start_time = time.time()
        progress_tracker[user_id] = 0

        def progress_callback(progress_value):
            if not 0 <= progress_value <= 100:
                logger.error(f"Invalid progress value: {progress_value}")
            progress_tracker[user_id] = progress_value  # Update progress

        if Config.DEBUG:
            test_dummy_run_model(economy_to_run, progress_callback, logger)
        else:
            try:
                #set sys.path to include the session library path. Note that if we have multiple users running models at the same time, this will mean multiple paths for duplicates of the same module are added to the path. in that case sys.path will just use the first one it finds
                FILE_DATE_ID, COMPLETED = main_module.main(economy_to_run=economy_to_run, progress_callback=progress_callback, root_dir_param=root_dir_param, script_dir_param=root_dir_param)
                if not COMPLETED:#sometimes dont get error from model so catch it via this variable
                    raise Exception("Model execution did not complete successfully.")
                # print("PRINT: Model execution completed successfully.")
                logging.getLogger('model_logger').info("Model execution completed successfully.")
                if Config.LOGGING:
                    global_logger.info(f"Model execution completed successfully for economy: {economy_to_run}")
                logging.getLogger('model_logger').info(f"Progress: {progress_tracker[user_id]}")
            except Exception as e:
                # print(f"PRINT: An error occurred during model execution: {e}")
                logging.getLogger('model_logger').info(f"An error occurred during model execution: {e}")
                if Config.LOGGING:
                    global_logger.error(f"An error occurred during model execution: {e}")
                logging.getLogger('model_logger').info(f"Progress: {progress_tracker[user_id]}")

        execution_time = time.time() - start_time
        if not Config.DEBUG:
            save_execution_time(execution_time)
    finally:
        #if the session library path is in the sys.path, remove it
        if os.getcwd() +'\\' +  session_library_path in sys.path:
            sys.path.remove(os.getcwd() +'\\' +  session_library_path)
        if FILE_DATE_ID:
            model_FILE_DATE_IDs[user_id] = FILE_DATE_ID
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        logger.close()#we dont seem to be getting here?
        if Config.LOGGING:
            global_logger.info('Model thread finished execution')
        progress_tracker[user_id] = 100

def calculate_average_time():
    if Config.LOGGING:
        global_logger.info('Calculating average execution time')
    if not os.path.exists(Config.EXECUTION_TIMES_FILE):
        return "No previous execution times available to estimate."

    with open(Config.EXECUTION_TIMES_FILE, 'r') as f:
        try:
            execution_times = json.load(f)
        except json.JSONDecodeError:
            return "No previous execution times available to estimate."

    if not execution_times:
        return "No previous execution times available to estimate."

    average_time = sum(execution_times) / len(execution_times)
    return round(average_time, 2)

def save_execution_time(execution_time):
    if Config.LOGGING:
        global_logger.info(f'Saving execution time: {execution_time}')
    if not os.path.exists(Config.EXECUTION_TIMES_FILE):
        execution_times = []
    else:
        with open(Config.EXECUTION_TIMES_FILE, 'r') as f:
            try:
                execution_times = json.load(f)
            except json.JSONDecodeError:
                execution_times = []

    execution_times.append(execution_time)
    execution_times = execution_times[-100:]

    with open(Config.EXECUTION_TIMES_FILE, 'w') as f:
        json.dump(execution_times, f)
    if Config.LOGGING:
        global_logger.info('Execution time saved successfully')

def test_dummy_run_model(economy_to_run, progress_callback, logger):
    if Config.LOGGING:
        global_logger.info(f'Starting dummy run model for economy: {economy_to_run}')
    logger.info(f"Starting dummy model run for {economy_to_run}")
    time.sleep(5)
    progress_callback(10)
    logger.info(f"10% complete for {economy_to_run}")
    time.sleep(5)
    progress_callback(20)
    logger.info(f"20% complete for {economy_to_run}")
    time.sleep(5)
    progress_callback(100)
    logger.info(f"Model run completed for {economy_to_run}")
    if Config.LOGGING:
        global_logger.info(f'Dummy model run completed for economy: {economy_to_run}')

def setup_email(email, from_email, new_values_dict, email_template, subject_title):
    """Send an email with the generated password. e.g. 
        backend.setup_and_send_email(email, new_values_dict, email_template='reset_password_email_template.html', subject_title='Password Reset Request')"""
    if Config.LOGGING:
        global_logger.info(f'Sending password email to {email}')
    
    # Read HTML content from file
    with open(email_template, 'r') as file:
        html_content = file.read()

    # Replace placeholder with actual password
    for key, value in new_values_dict.items():
        html_content = html_content.replace('{{{}}}'.format(key),value)

    # AWS SES client setup
    ses_client = boto3.client('ses', region_name='us-east-1', aws_access_key_id=Config.AWS_ACCESS_KEY_ID, aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)
    
    try:
        # Send email using AWS SES
        response = ses_client.send_email(
            Source=from_email,
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': subject_title,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_content,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        if Config.LOGGING:
            global_logger.info('Password email sent')
            global_logger.info("Email sent! Message ID:", response['MessageId'])
    except NoCredentialsError:
        global_logger.error("Credentials not available.")
    except PartialCredentialsError:
        global_logger.error("Incomplete credentials provided.")
    except Exception as e:
        global_logger.error(f"Error sending email: {e}")

    