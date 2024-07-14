import logging
from flask import Flask
from config import Config
########################
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    return app
class SafeConfig(dict):#for allowing config.attributes rather than have to use it liek config['attribute']
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            return None  # Or set a default value here
########################
# Dictionary to track the progress of each user's model run
progress_tracker = {}

# Dictionary to keep track of model threads for each user
model_threads = {}

model_FILE_DATE_IDs = {}

def setup_global_logger():
    # Set up a global logger for the 
    global_logger = logging.getLogger('global_logger')
    global_logger.setLevel(logging.DEBUG)

    # Create a file handler for logging
    fh = logging.FileHandler('app.log')
    
    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Add the handler to the logger
    global_logger.addHandler(fh)
    global_logger.info('Global logger setup complete')
    
    return global_logger

def setup_error_logger():
    #this should be used for the most importnat errors to spot them easilyq
    # Set up a global logger for the 
    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.DEBUG)

    # Create a file handler for logging
    fh = logging.FileHandler('errors.log')
    
    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Add the handler to the logger
    error_logger.addHandler(fh)
    error_logger.info('Error logger setup complete')
    
    return error_logger

def setup_logger(name, log_filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create a file handler for logging
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.DEBUG)

    # Create a formatter and set it for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Clear previous handlers if they exist
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add the handler to the logger
    logger.addHandler(fh)
    logger.info(f'Logger {name} setup complete')

    return logger

# Initialize the global logger
global_logger = setup_global_logger()
error_logger = setup_error_logger()
