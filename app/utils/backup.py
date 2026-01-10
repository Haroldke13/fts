import os
import shutil
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

def backup_files(app):
    scheduler = BackgroundScheduler()
    @scheduler.scheduled_job('interval', hours=24)
    def perform_backup():
        backup_dir = os.path.join(app.root_path, 'backups', datetime.now().strftime('%Y%m%d'))
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copytree('uploads', os.path.join(backup_dir, 'uploads'))
    scheduler.start()

def start_backup_scheduler(app):
    backup_files(app)
