from flask import Flask, render_template
from flask_login import LoginManager
from auth import auth_bp
from template_routes import template_bp
from wordpress import wordpress_bp
from helpers import initialize_app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key_here')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

initialize_app(app)
app.register_blueprint(auth_bp)
app.register_blueprint(template_bp)
app.register_blueprint(wordpress_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)