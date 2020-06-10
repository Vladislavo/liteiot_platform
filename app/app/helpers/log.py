from logging.config import dictConfig

dictConfig({
    'version' : 1,
    'formatters' : { 'default' : {
        'format' : '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers' : { 'wsgi' : {
        'class' : 'logging.handlers.RotatingFileHandler',
        'filename' : 'app.log',
        'maxBytes' : 1048576, # 1Mb 
        'backupCount': 1,
        'formatter' : 'default',
        'level': 'INFO'
    }},
    'loggers' : { 'file' : {
        'level' : 'INFO',
        'handlers' : ['wsgi']
    }},
    'root' : {
        'level' : 'INFO',
        'handlers' : ['wsgi']
    }
})
