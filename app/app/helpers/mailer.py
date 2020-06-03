from app import mail
from flask import render_template, session
from flask_mail import Message

import app.dao.application.application as ad

def send_mail(app, alert, fired):
    with app.app_context():
        ap = ad.get(fired['appkey'])
        msg = Message('Alert '+alert[3], recipients=[alert[6]])
        context = {'alert':alert, 'username':ap[1][2], 'appname':ap[1][0], 'message':fired['message']}
        msg.html = render_template('mailing/alert.html', **context)
        mail.send(msg)
