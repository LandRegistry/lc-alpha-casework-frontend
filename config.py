import os


class Config(object):
    DEBUG = False


class DevelopmentConfig(object):
    DEBUG = True
    CASEWORK_DB_URL = "http://localhost:5006"
