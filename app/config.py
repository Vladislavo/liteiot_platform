class Config(object):
    DEBUG = False
    TESTING = False

    SECRET_KEY = b'ksj^*(s90*Dklds;osdj'

    DB_NAME = 'iotserver'
    DB_USERNAME = 'pi'
    DB_PASSWORD = 'dev'
    DB_HOST = 'localhost'
    DB_PORT = 5432

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    APPKEY_LENGTH = 8
    NID_LENGTH = 5
    DATA_DOWNLOAD_DIR = 'data'
    DATA_DOWNLOAD_DIR_OS = 'app/data'

    # in minutes - 24 hours by default
    MAINTAINER_INTERVAL = 1440

    # manual user signup by default
    USERS_SIGNUP = False

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True

    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    

class TestingConfig(Config):
    TESTING = True
    
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
