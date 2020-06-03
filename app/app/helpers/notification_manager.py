import pgpubsub
from app import app
from uwsgidecorators import thread
import json
import app.dao.notification.notification as nf
import app.dao.pend.pend as pend
import app.helpers.mailer as mailer
import app.helpers.misc as misc

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
            d = json.loads(e.payload)
            if d['action_type'] == 'alert':
                # send mail
                n = nf.get(d['appkey'], d['devid'], d['nfid'])[1]
                print(n)
                mailer.send_mail(app, n, d)
            elif d['action_type'] == 'automation':
                # enqueue confid
                # action format: '<devid>#<confid>#<arg>'
                action = d['action'].split('#')
                base64_args = misc.pend_base64_encode(action[2], action[1])
                pend.create(d['appkey'], action[0], base64_args)
            

listening()
