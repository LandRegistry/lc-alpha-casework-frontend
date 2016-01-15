import os


class Config(object):
    DEBUG = False


class DevelopmentConfig(object):
    DEBUG = True
    CASEWORK_API_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://localhost:5014"
    DEMONSTRATION_VIEW = False


class PreviewConfig(Config):
    CASEWORK_API_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://localhost:5014"
    DEMONSTRATION_VIEW = False


class DemoConfig(Config):
    CASEWORK_API_URL = "http://localhost:5006"
    BANKRUPTCY_DATABASE_URL = "http://localhost:5004"
    DOCUMENT_URL = "http://lrq00103187:5014"
    DEMONSTRATION_VIEW = False
