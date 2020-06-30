from flask import render_template

import app.dao.application.application as ad

import telegram


def send(msg, chat_id, token):
    bot = telegram.Bot(token=token)
    bot.sendMessage(chat_id, text=msg, parse_mode=telegram.ParseMode.HTML)

def send_message(app, alert, fired):
    with app.app_context():
        ap = ad.get(fired['appkey'])
        context = {'alert':alert, 'username':ap[1][2], 'appname':ap[1][0], 'message':fired['message']}
        msg = render_template('mailing/telegram_alert.html', **context)
        send(msg, alert[6], app.config['TELEGRAM_BOT_TOKEN'])
