import logging
import os
import json
import shutil
import sys
import time
import importlib.util
from datetime import datetime
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from flask import current_app
import psutil
# from flask import session#trying to avoid using flask session within this module
from shared import progress_tracker, global_logger, error_logger, setup_logger, model_FILE_DATE_IDs

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
    if current_app.config.LOGGING:
        global_logger.info('Getting logs from file')
    if not os.path.exists(log_filename):
        return ''
    logs = open(log_filename, 'r').read()
    if not logs or logs.isspace():
        return 'No logs available yet'
    else:
        return logs

def archive_log(log_filename, DELETE_LOGS_INSTEAD_OF_ARCHIVING=True):
    if current_app.config.LOGGING:
        global_logger.info(f'Archiving log file: {log_filename}')
    if os.path.exists(log_filename):
        try:
            with open(log_filename, 'a') as log_file:
                log_file.flush()
                os.fsync(log_file.fileno())
            
            archived_log_filename = os.path.join('logs', 'archive', f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{os.path.basename(log_filename)}')
            if DELETE_LOGS_INSTEAD_OF_ARCHIVING:
                os.remove(log_filename)
            else:
                shutil.move(log_filename, archived_log_filename)
            if current_app.config.LOGGING:
                global_logger.info(f'Log file archived: {archived_log_filename}')
        except PermissionError as e:
            global_logger.error(f"Permission error moving log file: {e}")  # Normally occurs if user is still running the model
        except Exception as e:
            global_logger.error(f"Error moving log file: {e}")

def run_model_thread(app, log_filename, session_library_path, economy_to_run, user_id):
    """Run the model in a separate thread with the Flask application context."""
    with app.app_context():
        if current_app.config.LOGGING:
            global_logger.info(f'Running model thread for economy: {economy_to_run}')
        FILE_DATE_ID = None
        logger = StreamToLogger(log_filename)
        # sys.stdout = logger
        # sys.stderr = logger
        try:
            if current_app.config['DEBUG']:
                pass
            else:            
                # Check if the operating system is Windows
                if os.name == 'nt':
                    # For Windows, prepend with '\\?\' to handle long paths if necessary
                    root_dir_param = "\\\\?\\" + os.path.join(os.getcwd(), session_library_path)
                    # Replace '/' with '\\' for Windows paths
                    root_dir_param = root_dir_param.replace("/", "\\")
                else:
                    # For Linux and other OS, use the os.path.join directly
                    root_dir_param = os.path.join(os.getcwd(), session_library_path)
                sys.path.append(root_dir_param)
                if current_app.config.LOGGING:
                    global_logger.info(f"Running model for sys.path[-1]: {sys.path[-1]}")
                # This is a hack to allow long paths in Windows
                main_module_spec = importlib.util.spec_from_file_location("main", os.path.join(session_library_path, "main.py"))
                global_logger.info(f"main_module_spec: {main_module_spec}")
                if main_module_spec is None:
                    if current_app.config.LOGGING:
                        global_logger.error("Could not find the main module in the session-specific path")
                        global_logger.info("Main module found in the session-specific path")
                    raise ImportError("Could not find the main module in the session-specific path")
                else:
                    if current_app.config.LOGGING:
                        global_logger.info("Main module found in the session-specific path")
                try:        
                    #loading main module: 
                    if current_app.config.DEBUG_LOGGING:
                        global_logger.info("Loading main module")
                    main_module = importlib.util.module_from_spec(main_module_spec)
                    if current_app.config.DEBUG_LOGGING:
                        global_logger.info(f"Setting up exec_module for main module {main_module}")
                    main_module_spec.loader.exec_module(main_module)
                except Exception as e:
                    if current_app.config.LOGGING:
                        global_logger.info(f"Error loading main module: {e}")
                        error_logger.error(f"Error loading main module: {e}")
                    raise e

            progress_tracker[user_id] = 0

            def progress_callback(progress_value):
                # if not 0 <= progress_value <= 100:
                #     logger.error(f"Invalid progress value: {progress_value}")
                if 0 <= progress_value <= 100:
                    progress_tracker[user_id] = progress_value  # Update progress
                # logger.info(f"Progress: {progress_value}")

            if current_app.config['DEBUG']:
                test_dummy_run_model(economy_to_run, progress_callback, logger)
            else:
                try:
                    start_time = time.time()
                    # Set sys.path to include the session library path. Note that if we have multiple users running models at the same time, this will mean multiple paths for duplicates of the same module are added to the path. In that case, sys.path will just use the first one it finds.
                    if current_app.config.LOGGING:
                        global_logger.info('Running model with arguments: economy_to_run={}, progress_callback={}, root_dir_param={}, script_dir_param={}'.format( economy_to_run, progress_callback, root_dir_param, root_dir_param))
                    FILE_DATE_ID, COMPLETED, error_message = main_module.main(economy_to_run=economy_to_run, progress_callback=progress_callback, root_dir_param=root_dir_param, script_dir_param=root_dir_param)
                    if not COMPLETED:  # Sometimes don't get error from model so catch it via this variable
                        error_logger.error(f"Model execution did not complete successfully with economy: {economy_to_run}, with error message: {error_message}")
                        logging.getLogger('model_logger').info(f"Model execution did not complete successfully, with error message: {error_message}")
                        raise Exception(f"Model execution did not complete successfully, with error message: {error_message}")
                    logging.getLogger('model_logger').info("Model execution completed successfully.")
                    if current_app.config.LOGGING:
                        global_logger.info(f"Model execution completed successfully for economy: {economy_to_run}")
                    logging.getLogger('model_logger').info(f"Progress: {progress_tracker[user_id]}")
                            
                    execution_time = time.time() - start_time
                    if not current_app.config['DEBUG']:
                        save_execution_time(execution_time)
                except Exception as e:
                    # print(f"PRINT: An error occurred during model execution: {e}")
                    logging.getLogger('model_logger').info(f"An error occurred during model execution: {e}")
                    if current_app.config.LOGGING:
                        global_logger.error(f"An error occurred during model execution: {e}")
                        error_logger.error(f"An error occurred during model execution: {e}")
                    logging.getLogger('model_logger').info(f"Progress: {progress_tracker[user_id]}")

        finally:         
            # Check if the operating system is Windows
            if os.name == 'nt':
                # For Windows, prepend with '\\?\' to handle long paths if necessary
                root_dir_param = "\\\\?\\" + os.path.join(os.getcwd(), session_library_path)
                # Replace '/' with '\\' for Windows paths
                root_dir_param = root_dir_param.replace("/", "\\")
            else:
                # For Linux and other OS, use the os.path.join directly
                root_dir_param = os.path.join(os.getcwd(), session_library_path)
            # If the session library path is in the sys.path, remove it
            if root_dir_param in sys.path:
                sys.path.remove(root_dir_param)
            if FILE_DATE_ID:
                model_FILE_DATE_IDs[user_id] = FILE_DATE_ID
            # sys.stdout = sys.__stdout__
            # sys.stderr = sys.__stderr__
            logger.close()  # We don't seem to be getting here?
            if current_app.config.LOGGING:
                global_logger.info('Model thread finished execution')
            progress_tracker[user_id] = 100
            
def calculate_average_time():
    if current_app.config.DEBUG_LOGGING:
        global_logger.info('Calculating average execution time')
    if not os.path.exists(current_app.config.EXECUTION_TIMES_FILE):
        return "No previous execution times available to estimate."

    with open(current_app.config.EXECUTION_TIMES_FILE, 'r') as f:
        try:
            execution_times = json.load(f)
        except json.JSONDecodeError:
            return "No previous execution times available to estimate."

    if not execution_times:
        return "No previous execution times available to estimate."

    average_time = sum(execution_times) / len(execution_times)
    return round(average_time, 2)

def save_execution_time(execution_time):
    if current_app.config.DEBUG_LOGGING:
        global_logger.info(f'Saving execution time: {execution_time}')
    if not os.path.exists(current_app.config.EXECUTION_TIMES_FILE):
        execution_times = []
    else:
        with open(current_app.config.EXECUTION_TIMES_FILE, 'r') as f:
            try:
                execution_times = json.load(f)
            except json.JSONDecodeError:
                execution_times = []

    execution_times.append(execution_time)
    execution_times = execution_times[-100:]

    with open(current_app.config.EXECUTION_TIMES_FILE, 'w') as f:
        json.dump(execution_times, f)
    if current_app.config.LOGGING:
        global_logger.info('Execution time saved successfully')

def test_dummy_run_model(economy_to_run, progress_callback, logger):
    if current_app.config.LOGGING:
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
    if current_app.config.LOGGING:
        global_logger.info(f'Dummy model run completed for economy: {economy_to_run}')
        
def setup_and_send_email(email, from_email, new_values_dict, email_template, subject_title):
    """Send an email with the generated password. e.g. 
        backend.setup_and_send_email(email, new_values_dict, email_template='reset_password_email_template.html', subject_title='Password Reset Request')"""
    if current_app.config.LOGGING:
        global_logger.info(f'Sending email to {(email)}')#encrypt_data
    
    # Read HTML content from file
    with open(email_template, 'r') as file:
        html_content = file.read()

    # Replace placeholders with actual values
    for key, value in new_values_dict.items():
        html_content = html_content.replace('{{' + key + '}}', value)
        #and cover for any with spaces around them:
        html_content = html_content.replace('{{ ' + key + ' }}', value)
        
    if not current_app.config.AWS_CONNECTION_AVAILABLE:
        error_logger.error("setup_and_send_email: AWS connection not available.")
        return
    try:
        ses_client = boto3.client('ses', region_name='ap-northeast-1')
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
        if current_app.config.LOGGING:
            global_logger.info('Password email sent')
            global_logger.info(f"Email sent! Message ID: {response['MessageId']}")
    except NoCredentialsError:
        global_logger.error("setup_and_send_email: Credentials not available.")
    except PartialCredentialsError:
        global_logger.error("setup_and_send_email: Incomplete credentials provided.")
    except Exception as e:
        global_logger.error(f"setup_and_send_email: Error sending email: {e}")
        error_logger.error(f"setup_and_send_email: Error sending email: {e}")

def process_feedback(name, message):
    global_logger.info(f"Feedback received from {name}: {message}")
    send_feedback_email(name, message)

def send_feedback_email(name, message):
    from_email = current_app.config.MAIL_USERNAME
    feedback_email = current_app.config.PERSONAL_EMAIL
    subject = "New Feedback Received"
    body = f"Name: {name}\nMessage:\n{message}"
    
    if current_app.config.LOGGING:
        global_logger.info(f'Sending feedback email to {(feedback_email)}')#encrypt_data
        
    if not current_app.config.AWS_CONNECTION_AVAILABLE:
        error_logger.error("send_feedback_email: AWS connection not available.")
        return
    try:
        ses_client = boto3.client('ses', region_name='ap-northeast-1')
        response = ses_client.send_email(
            Source=from_email,
            Destination={
                'ToAddresses': [feedback_email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        global_logger.info(f"Feedback email sent successfully: {response}")
    except Exception as e:
        global_logger.error(f"Error sending feedback email: {e}")
        error_logger.error(f"Error sending feedback email: {e}")
        

def check_disk_space():
    # Check the disk space
    if current_app.config.DEBUG_LOGGING:
        global_logger.info('Checking disk space')
        
    disk_usage = psutil.disk_usage('/')
    if current_app.config.LOGGING:
        global_logger.info(f"Disk space used: {disk_usage.percent}%")
        
    if disk_usage.percent > 80:  # Adjust the threshold as needed        
        if current_app.config.AWS_CONNECTION_AVAILABLE:
            ses_client = boto3.client('ses', region_name='ap-northeast-1')
            response = ses_client.send_email(
                Source='low-disk-space' + current_app.config['MAIL_USERNAME'],
                Destination={
                    'ToAddresses': [current_app.config.PERSONAL_EMAIL]
                },
                Message={
                    'Subject': {
                        'Data': f'Disk Space Warning: {disk_usage.percent}%',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': f"Disk space warning: {disk_usage.percent}% used",
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            error_logger.error(f"Disk space warning email sent: {disk_usage.percent}% used, response: {response}")
            global_logger.info(f"Disk space warning email sent: {disk_usage.percent}% used, response: {response}")
    else:
        if current_app.config.DEBUG_LOGGING:
            global_logger.info(f"Disk space is within acceptable limits: {disk_usage.percent}% used")
