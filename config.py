import os


class Config(object):
    DEBUG = False


class DevelopmentConfig(object):
    DEBUG = False
    CASEWORK_DB_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://localhost:5014"


class PreviewConfig(Config):
    CASEWORK_DB_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://localhost:5014"


class DemoConfig(Config):
    CASEWORK_DB_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://lrq00103187:5014"
