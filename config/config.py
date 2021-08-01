import os

basedir = os.path.join(os.curdir)

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'slvnuhgriuha556RE69#&554mnbv'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False