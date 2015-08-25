import os


class Config(object):
    DEBUG = False


class DevelopmentConfig(object):
    DEBUG = True
    CASEWORK_DB_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://localhost:5014"
