from flask import Flask, render_template
from flask_login import LoginManager
from auth import auth_bp
from login_manager import login_manager

from template_routes import template_bp
from wordpress import wordpress_bp
from helpers import initialize_app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key_here')
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
