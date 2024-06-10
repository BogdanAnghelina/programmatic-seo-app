from flask import render_template
from supabase import create_client, Client
from login_manager import login_manager
from app_init import app
from template_routes import template_bp
from wordpress import wordpress_bp
from helpers import initialize_app

from auth import auth_bp

# Supabase connection details
SUPABASE_URL = "https://ogwekmdhhbuiekbpndsv.supabase.co"
SUPABASE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9nd2VrbWRoaGJ1aWVrYnBuZHN2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTE3NDE2MjgsImV4cCI6MjAyNzMxNzYyOH0.LdZE4bQU1s0pLG-tuKP4--uZpjX9sg5AXhDnkmJG_ck"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
login_manager.login_view = 'auth.login'

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(template_bp)
app.register_blueprint(wordpress_bp)

# Initialize helpers
initialize_app(app)

if __name__ == "__main__":
    app.run(debug=True)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
