import os

class Config(object):
    """docstring for Config."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or "There will be a 128-bit random string here at some point"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///catalog.db'
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
