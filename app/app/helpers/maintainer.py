from apscheduler.schedulers.background import BackgroundScheduler 
from app import app, views
import os

def clean_data_folder():
    try:
        filelist = [f for f in os.listdir(app.config['DATA_DOWNLOAD_DIR_OS'])]
        for f in filelist:
            os.remove(app.config['DATA_DOWNLOAD_DIR_OS']+'/'+f)
    except OSError:
        pass

def maintainer():
    views.pend_delete_all_ack()
    clean_data_folder()

scheduler = BackgroundScheduler()
job = scheduler.add_job(maintainer, 'interval', minutes=app.config['MAINTAINER_INTERVAL'])
scheduler.start()
