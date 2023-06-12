# Import modules
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_wtf.csrf import CSRFProtect
# .env for hidden variables for github purposes
from dotenv import load_dotenv
import os

# Injecting hidden variables
load_dotenv('.env')
secret_key = os.getenv("SECRET_KEY")
database_uri = os.getenv("SQLALCHEMY_DATABASE_URI")

# Creating a Flask instance
app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key

app.config['CKEDITOR_PKG_TYPE'] = 'basic'
ckeditor = CKEditor(app)

# Enable CSRF protection globally
csrf = CSRFProtect()
csrf.init_app(app)

# Connect the app to the database
app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLACHEMY_TRACK_MODIFICATIONS"] = False

# Establish database:
db = SQLAlchemy(app)

# Add password salt and hashing
bcrypt = Bcrypt(app)

# Adding a LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user_login'
login_manager.needs_refresh_message_category = "danger"
login_manager.login_message = u"Please login first"
