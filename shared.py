import logging

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
