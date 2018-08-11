import os

basedir = os.path.abspath(os.path.dirname(__file__))

VERSION_NAME = '2.0.0-alpha.1'


class Config:
    WORKING_DIR = os.getenv('GENERATOR_WORKING_DIR', os.path.abspath(os.path.dirname(__file__) + '/../temp/'))
    UPLOAD_DIR = os.path.abspath(WORKING_DIR + '/uploads/')
    VERSION = VERSION_NAME
    DEBUG = False
    BASE_DIR = basedir
    MINIFY_PAGE = True
    STATICFILES_DIR = os.path.join(BASE_DIR, 'app/static')
    STATICFILES_DIRS = (STATICFILES_DIR,)
    SERVER_NAME = os.getenv('SERVER_NAME', None)
    ANDROID_HOME = os.getenv('ANDROID_HOME')
    FORCE_SSL = os.getenv('FORCE_SSL', 'no') == 'yes'
    STATIC_URL = '/static/'
    APP_SOURCE_DIR = os.path.abspath(basedir + '/../../android/')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    SECRET_KEY = os.environ.get('SECRET_KEY', 'JQgeEYk9b4VjxhJP')
    EMAIL_SERVICE = os.environ.get('EMAIL_SERVICE', 'none')
    SMTP_ENCRYPTION = os.environ.get('SMTP_ENCRYPTION', 'none')
    SMTP_HOST = os.environ.get('SMTP_HOST', 'none')
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'none')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'none')
    SMTP_PORT = os.environ.get('SMTP_PORT', 'none')
    SENDGRID_KEY = os.environ.get('SENDGRID_KEY', 'none')
    FROM_EMAIL = os.environ.get('FROM_EMAIL', 'none')
    def __init__(self):
        pass


class ProductionConfig(Config):
    DEBUG = False
    MINIFY_PAGE = True
    PRODUCTION = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    MINIFY_PAGE = False


class TestingConfig(Config):
    TESTING = True
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    BROKER_BACKEND = 'memory'
