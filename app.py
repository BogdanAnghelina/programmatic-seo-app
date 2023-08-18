from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config[
  'SECRET_KEY'] = 'your_secret_key_here'  # change this to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///templates.db'
db = SQLAlchemy(app)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    # For now, we aren't using a database, so we'll mock a user object
    user = User()
    user.id = user_id
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # hardcoded username and password for demonstration
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            user = User()
            user.id = 'admin'
            login_user(user)
            return redirect(url_for('new_template'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/new_template', methods=['GET', 'POST'])
@login_required
def new_template():
    if request.method == 'POST':
        template_name = request.form['template_name']
        template_content = request.form['template_content']

        new_template = Template(name=template_name, content=template_content)
        db.session.add(new_template)
        db.session.commit()

        flash('Template saved successfully!')
        return redirect(url_for('new_template'))
    return render_template('new_template.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)