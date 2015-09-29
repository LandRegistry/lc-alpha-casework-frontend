from flask import Flask
from log.logger import setup_logging
import os


app = Flask(__name__)
app.config.from_object(os.environ.get('SETTINGS'))
app.secret_key = '123456passwordmonkeyletmein'

setup_logging(app.config['DEBUG'])
