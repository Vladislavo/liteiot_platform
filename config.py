class Config(object):
    DEBUG = False
    TESTING = False

    SECRET_KEY = b'ksj^*(s90*Dklds;osdj'

    DB_NAME = 'gateway'
    DB_USERNAME = 'pi'
    DB_PASSWORD = 'dev'
    DB_HOST = 'localhost'
    DB_PORT = 5432

    SESSION_COOKIE_SECURE = True

    APPKEY_LENGTH = 8
    DATA_DOWNLOAD_DIR = 'data'

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    SESSION_COOKIE_SECURE = False
    

class TestingConfig(Config):
    TESTING = True
    
    SESSION_COOKIE_SECURE = False
