import os


class Config(object):
    DEBUG = os.getenv('DEBUG', False)
    APPLICATION_NAME = 'lc-casework-frontend'
    CASEWORK_FRONTEND_URL = os.getenv('CASEWORK_FRONTEND_URL', "http://localhost:5010")
    CASEWORK_API_URL = os.getenv('CASEWORK_API_URL', "http://localhost:5006")
    AMQP_URI = os.getenv("AMQP_URI", "amqp://mquser:mqpassword@localhost:5672")