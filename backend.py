import os
import json
import logging
from config import Config

class StreamToLogger:
    def __init__(self, log_filename):
        self.log_filename = log_filename
        self.logger = logging.getLogger('ModelLogger')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_filename)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)

    def write(self, message):
        if message.strip():
            self.logger.info(message)

    def flush(self):
        pass
    
def calculate_average_time():
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
    if not os.path.exists(Config.EXECUTION_TIMES_FILE):
        with open(Config.EXECUTION_TIMES_FILE, 'w') as f:
            json.dump([execution_time], f)
    else:
        with open(Config.EXECUTION_TIMES_FILE, 'r+') as f:
            try:
                execution_times = json.load(f)
            except json.JSONDecodeError:
                execution_times = []

            execution_times.append(execution_time)
            f.seek(0)
            json.dump(execution_times, f)
            f.truncate()
