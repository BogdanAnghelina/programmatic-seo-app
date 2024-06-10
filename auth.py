from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, login_required, logout_user
from database import session, UserDB
from login_manager import login_manager
from flask_login import UserMixin

auth_bp = Blueprint('auth', __name__)

class FlaskUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return FlaskUser(user_id=user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        if username == 'admin' and password == 'password':
            user_db = session.query(UserDB).filter_by(username='admin').first()
            if not user_db:
                session.add(UserDB(username='admin', password='password'))
                session.commit()
            login_user(FlaskUser(user_id='admin'))
            return redirect(url_for('template_bp.new_template'))
        flash('Invalid credentials.')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
