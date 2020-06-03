from flask import Flask
from flask_mail import Mail

app = Flask(__name__)

if app.config['ENV'] == 'production':
    app.config.from_object('config.ProductionConfig')
else:
    app.config.from_object('config.DevelopmentConfig')

mail = Mail(app)

from app import views
from app import views_admin
from app.helpers import maintainer
from app.helpers import notification_manager
