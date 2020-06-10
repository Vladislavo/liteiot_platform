from flask import Flask
from flask_mail import Mail
import app.helpers.log

# app initialization
app = Flask(__name__)

# config loading
if app.config['ENV'] == 'production':
    app.config.from_object('config.ProductionConfig')
else:
    app.config.from_object('config.DevelopmentConfig')

# mailer initialization
mail = Mail(app)

# load views and notification manager
from app import views
from app import views_admin
# No need anymore in maintainer since 
#  1) Notifications are fired in soft real time
#  2) data folder is cleaned after every csv download
# from app.helpers import maintainer
from app.helpers import notification_manager
