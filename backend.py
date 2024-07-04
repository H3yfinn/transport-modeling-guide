import logging
import os
import json
import shutil
import sys
import time
import importlib.util
import threading
from datetime import datetime, timedelta

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
    
    if Config.LOGGING:
        global_logger.info(f'Running model thread for economy: {economy_to_run}')
        
    logger = StreamToLogger(log_filename)
    sys.stdout = logger
    sys.stderr = logger
    try:
        if Config.DEBUG:
            pass
        else:
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
                FILE_DATE_ID = main_module.main(economy_to_run, progress_callback)
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
