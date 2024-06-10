from flask import render_template
from login_manager import login_manager
from app_init import app
from template_routes import template_bp
from wordpress import wordpress_bp
from helpers import initialize_app

from auth import auth_bp

login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
