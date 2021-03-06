import pgpubsub
from app import app
from uwsgidecorators import thread
import json
import app.dao.notification.notification as nf
import app.dao.pend.pend as pend
import app.helpers.mailer as mailer
import app.helpers.misc as misc
import app.dao.device.device as dd
import app.helpers.device_data_model as ddm

import app.helpers.telegram_sender as ts

from binascii import unhexlify

@thread
def listening():
    ps = pgpubsub.connect(
        database = app.config['DB_NAME'], 
        user = app.config['DB_USERNAME'],
        password = app.config['DB_PASSWORD'],
        host = app.config['DB_HOST'],
        port = app.config['DB_PORT']
    )
    ps.listen('nf_channel')
    while True:
        for e in ps.events():
            try:
                d = json.loads(e.payload)
                dev = dd.get(d['appkey'], d['devid'])[1]
                d['message']['data'] = ddm.read_data(unhexlify(d['message']['data'][2:]), dev[3])
                if d['lvalue'] in d['message']['data'] and (d['op'][0] == 'O' or eval(str(d['message']['data'][d['lvalue']]) + d['op'] + d['rvalue'])):
                    if d['action_type'] == 'alert_email':
                        # send mail
                        n = nf.get(d['appkey'], d['devid'], d['nfid'])[1]
                        mailer.send_mail(app, n, d)
                        app.logger.info('Alert {} was fired.')
                    elif d['action_type'] == 'alert_telegram':
                        # send telegram message
                        n = nf.get(d['appkey'], d['devid'], d['nfid'])[1]
                        ts.send_message(app, n, d)
                        app.logger.info('Alert {} was fired.')
                    elif d['action_type'] == 'automation':
                        # enqueue confid
                        # action format: '<devid>#<confid>#<arg>'
                        action = d['action'].split('#')
                        base64_args = misc.pend_base64_encode(action[2], action[1])
                        pend.create(d['appkey'], action[0], base64_args)
                        app.logger.info('Automation for application {} with format {} was fired.'.format(d['appkey'], d['action']))
            except Exception as e:
                app.logger.error('Notification manager thread error: {}'.format(e))
                pass
            

listening()
