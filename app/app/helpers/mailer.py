from app import mail
from flask import render_template, session
from flask_mail import Message

import app.dao.application.application as ad

def send_mail(app, alert, alert_evt):
    with app.app_context():
        ap = ad.get(alert[1])
        msg = Message('Alert '+alert[3], recipients=[alert[6]])
        context = {'alert':alert, 'username':ap[1][2], 'appname':ap[1][0], 'timestamp':alert_evt[3]}
        msg.html = render_template('mailing/alert.html', **context)
        mail.send(msg)
