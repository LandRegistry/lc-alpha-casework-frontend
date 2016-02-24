import os


class Config(object):
    DEBUG = os.getenv('DEBUG', True)
    APPLICATION_NAME = 'lc-casework-frontend'
    CASEWORK_FRONTEND_URL = os.getenv('CASEWORK_FRONTEND_URL', "http://localhost:5010")
    CASEWORK_API_URL = os.getenv('CASEWORK_API_URL', "http://localhost:5006")
    BANKRUPTCY_DATABASE_URL = os.getenv('LAND_CHARGES_URL', "http://localhost:5004") # TODO: go!
