from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_migrate import Migrate, migrate
from flask_login import LoginManager

app = Flask(__name__)

app.config.from_object(config.Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)

login.login_view = 'index'

from app import routes, models