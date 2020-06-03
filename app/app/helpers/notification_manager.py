import pgpubsub
from app import app
from uwsgidecorators import thread


@thread
def listening():
    ps = pgpubsub.connect(
        database = app.config['DB_NAME'], 
        user = app.config['DB_USERNAME'],
        password = app.config['DB_PASSWORD'],
        host = app.config['DB_HOST'],
        port = app.config['DB_PORT']
    )
    ps.listen('test')
    while True:
        for e in ps.events():
            print(e.payload)

listening()
