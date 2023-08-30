from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy.orm.exc import NoResultFound
from database import Template, session
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

def format_variable(variable):
    if not re.match(r'^[a-zA-Z0-9_]*$', variable):
        return ''
    return f"[{variable.lower()}]"

def strip_tags(input_string):
    if not input_string or not isinstance(input_string, str):
        return ''
    return re.sub(r'<[^>]*>', '', input_string)

app.jinja_env.filters['strip_tags'] = strip_tags

@login_manager.user_loader
def load_user(user_id):
    return User(user_id=user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            user = User(user_id='admin')
            login_user(user)
            return redirect(url_for('new_template'))
        else:
            flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new_template', methods=['GET', 'POST'])
@login_required
def new_template():
    draft = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()

    if request.method == 'POST':
        if 'save_template' in request.form:
            template_name = request.form['template_name']
            template_content = request.form['template_content']

            # If they're saving, save the new template and remove the draft
            new_template = Template(template_name=template_name or "Unnamed Template", 
                                    template_content=template_content or '', 
                                    draft=False, 
                                    user_id=current_user.id)
            session.add(new_template)

            if draft:
                session.delete(draft)
                
            session.commit()
            flash('Template saved successfully!')
            return redirect(url_for('new_template'))

        elif 'add_variable' in request.form:
            variable_name = request.form['variable_name']
            formatted_variable = format_variable(variable_name)

            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('new_template'))

            if not draft:
                draft = Template(template_name="Draft", template_content='', draft=True, user_id=current_user.id)
                session.add(draft)
                session.commit()

            current_variables = draft.template_variables.split(",") if draft.template_variables else []
            current_variables.append(formatted_variable)
            draft.template_variables = ",".join(current_variables)
            session.commit()
            flash(f'Variable {formatted_variable} added successfully!')
            return redirect(url_for('new_template'))

        elif 'delete_variable' in request.form:
            variable_to_delete = request.form['delete_variable']

            if draft:
                current_variables = draft.template_variables.split(",") if draft.template_variables else []
                if variable_to_delete in current_variables:
                    current_variables.remove(variable_to_delete)
                    draft.template_variables = ",".join(current_variables)
                    session.commit()
                    flash(f'Variable {variable_to_delete} deleted successfully!')

            return redirect(url_for('new_template'))

    template_name = ""
    template_content = ""
    variables = []

    if draft:
        template_name = draft.template_name
        template_content = draft.template_content
        variables = draft.template_variables.split(",") if draft.template_variables else []

    return render_template('new_template.html', template_name=template_name, template_content=template_content, variables=variables)

@app.route('/edit_template', methods=['GET', 'POST'])
@login_required
def edit_template():
    templates = session.query(Template).filter_by(draft=False, user_id=current_user.id).all()
    template_id = request.args.get('template_id', None)

    # Check if the provided template_id is valid
    if not template_id or not session.query(Template).filter_by(id=template_id).first():
        flash('Template not found.')
        return redirect(url_for('edit_template'))

    current_template = None
    if template_id:
        try:
            current_template = session.query(Template).filter_by(id=template_id, user_id=current_user.id).one()
            variables = current_template.template_variables.split(",") if current_template and current_template.template_variables else []
        except NoResultFound:
            flash('Template not found.')
          
            return redirect(url_for('edit_template'))

    if request.method == 'POST':

        if 'update_template' in request.form and current_template:
            current_template.template_name = request.form['template_name']
            current_template.template_content = request.form['template_content']
            session.commit()
            flash('Template updated successfully!')
            return redirect(url_for('edit_template', template_id=template_id))

        elif 'add_variable' in request.form and current_template:
            variable_name = request.form['variable_name']
            formatted_variable = format_variable(variable_name)

            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('edit_template'))

            current_variables = current_template.template_variables.split(",") if current_template.template_variables else []
            current_variables.append(formatted_variable)
            current_template.template_variables = ",".join(current_variables)
            session.commit()
            flash(f'Variable {formatted_variable} added successfully!')
            return redirect(url_for('edit_template', template_id=template_id))

        elif 'delete_variable' in request.form and current_template:
            variable_to_delete = request.form['delete_variable']
            current_variables = current_template.template_variables.split(",") if current_template.template_variables else []
            if variable_to_delete in current_variables:
                current_variables.remove(variable_to_delete)
                current_template.template_variables = ",".join(current_variables)
                session.commit()
                flash(f'Variable {variable_to_delete} deleted successfully!')
                return redirect(url_for('edit_template', template_id=template_id))

    variables = current_template.template_variables.split(",") if current_template and current_template.template_variables else []

    # These debug lines should be outside of any if or exception blocks, right before the final return.
    print("DEBUG TEMPLATE ID:", template_id)
    print("DEBUG CURRENT TEMPLATE:", current_template)
    print("DEBUG VARIABLES LIST:", variables)
  
    return render_template('edit_template.html', templates=templates, template_id=template_id, variables=variables)

@app.route('/get_template_data', methods=['GET'])
def get_template_data():
    template_id = request.args.get('template_id')
    print("DEBUG: Fetching data for template ID:", template_id) 
    
    template = session.query(Template).filter_by(id=template_id).first()
    
    if not template:
        return jsonify(success=False, message="Template not found"), 404

    return jsonify(
        template_name=template.template_name,
        template_content=template.template_content,
        template_variables=template.template_variables.split(",") if template.template_variables else []
    )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:
        session.rollback()
    else:
        session.commit()
    session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)