import schedule
import time
import os
from datetime import datetime, timedelta

def delete_old_logs():
    archive_dir = 'logs/archive'
    retention_period_days = 30
    cutoff_date = datetime.now() - timedelta(days=retention_period_days)

    for filename in os.listdir(archive_dir):
        file_path = os.path.join(archive_dir, filename)
        if os.path.isfile(file_path):
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mod_time < cutoff_date:
                os.remove(file_path)
                print(f'Deleted old log file: {file_path}')

# Schedule the cleanup task
schedule.every().day.at("00:00").do(delete_old_logs)

while True:
    schedule.run_pending()
    time.sleep(60)