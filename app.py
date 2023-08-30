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

            if not draft:
                draft = Template(template_name="Draft", template_content='', draft=True, user_id=current_user.id)
                session.add(draft)
                session.commit()

            draft.template_name = template_name or "Unnamed Template"
            draft.template_content = template_content or ''
            draft.draft = False
            draft.template_variables = draft.template_variables  # Retain the existing variables
            draft.user_id = current_user.id
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


@app.route('/saved_templates', methods=['GET'])
@login_required
def saved_templates():
    templates = session.query(Template).filter_by(draft=False, user_id=current_user.id).all()
    return render_template('saved_templates.html', templates=templates)


@app.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    template = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first()

    if not template:
        flash('Template not found.')
        return redirect(url_for('saved_templates'))

    print("Template Variables:", template.template_variables)  # Debugging print statement

    # Extract variables using regular expression
    if template.template_variables:
        variables = re.findall(r'\[([^\]]+)\]', template.template_variables)
    else:
        variables = []

    print("Extracted Variables:", variables)  # Add this line for debugging

    if request.method == 'POST':
        if 'update_template' in request.form:
            template.template_name = request.form['template_name']
            template.template_content = request.form['template_content']
            session.commit()
            flash('Template updated successfully!')
            return redirect(url_for('edit_template', template_id=template_id))

        elif 'add_variable' in request.form:
            variable_name = request.form['variable_name']
            formatted_variable = format_variable(variable_name)

            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('edit_template', template_id=template_id))

            current_variables = template.template_variables.split(",") if template.template_variables else []
            current_variables.append(formatted_variable)
            template.template_variables = ",".join(current_variables)
            session.commit()
            flash(f'Variable {formatted_variable} added successfully!')
            return redirect(url_for('edit_template', template_id=template_id))

        elif 'delete_variable' in request.form:
            variable_to_delete = request.form['delete_variable']
            current_variables = template.template_variables.split(",") if template.template_variables else []
            if variable_to_delete in current_variables:
                current_variables.remove(variable_to_delete)
                template.template_variables = ",".join(current_variables)
                session.commit()
                flash(f'Variable {variable_to_delete} deleted successfully!')
            return redirect(url_for('edit_template', template_id=template_id))

    variables = template.template_variables.split(",") if template.template_variables else []

    return render_template('edit_template.html', template_name=template.template_name, template_id=template_id, variables=variables, template_content=template.template_content)


@app.route('/get_template_data', methods=['GET'])
def get_template_data():
    template_id = request.args.get('template_id')
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


@app.route('/get_variables', methods=['GET'])
@login_required
def get_variables():
    # Assuming the logged-in user's draft template has the variables
    template = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()
    
    # If there is no such template, return an error
    if not template:
        return jsonify({
            'status': 'error',
            'message': 'No draft template found for current user.'
        }), 404

    # Otherwise, split the stored variables string into separate variables
    variables = template.template_variables.split(",") if template.template_variables else []

    # And then return them as JSON to the client
    return jsonify({
        'status': 'success',
        'variables': variables
    })



@app.route('/add_variable', methods=['POST'])
def add_variable():
    variable_name = request.form.get('variable_name')
    formatted_variable = format_variable(variable_name)

    if not formatted_variable:
        response = {
            'status': 'error',
            'message': 'Variable can only contain letters, numbers, and underscores.'
        }
    else:
        response = {
            'status': 'success',
            'variable': formatted_variable
        }

        draft = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()
        if not draft:
            draft = Template(template_name="Draft", template_content='', draft=True, user_id=current_user.id)
            session.add(draft)
            session.commit()

        current_variables = draft.template_variables.split(",") if draft.template_variables else []
        current_variables.append(formatted_variable)
        draft.template_variables = ",".join(current_variables)
        session.commit()

    return jsonify(response)


@app.route('/update_template', methods=['POST'])
def update_template():
    template_id = request.form.get('template_id')
    new_template_name = request.form.get('template_name')
    new_template_content = request.form.get('template_content')

    template = session.query(Template).filter_by(id=template_id).first()

    if not template:
        response = {
            'status': 'error',
            'message': 'Template not found.'
        }
    else:
        template.template_name = new_template_name
        template.template_content = new_template_content
        session.commit()

        response = {
            'status': 'success',
            'message': 'Template updated successfully.'
        }

    return jsonify(response)


@app.route('/delete_variable', methods=['POST'])
def delete_variable():
    variable_to_delete = request.form.get('variable_name')

    if not variable_to_delete:
        return jsonify(status='error', message='Variable name is required.')

    try:  # Start of try block
        draft = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()
        if not draft:
            return jsonify(status='error', message='No draft template found.')

        current_variables = draft.template_variables.split(",") if draft.template_variables else []
        if variable_to_delete in current_variables:
            current_variables.remove(variable_to_delete)
            draft.template_variables = ",".join(current_variables)
            session.commit()
            return jsonify(status='success', message=f'Variable {variable_to_delete} deleted successfully!')
        else:
            return jsonify(status='error', message=f'Variable {variable_to_delete} not found.')

    except Exception as e:  # Handle any exception here
        # Log the error for debugging purposes
        print(f"Database error: {e}")
        return jsonify(status='error', message='An internal error occurred. Please try again later.')


@app.route('/extract_variables', methods=['GET', 'POST'])
def extract_variables():
    if request.method == 'POST':
        template_id = request.form['template_id']
        template = session.query(Template).filter_by(id=template_id).first()

        if template:
            variables = template.template_variables.split(",") if template.template_variables else []
            return render_template('extract_variables.html', variables=variables)

    return render_template('extract_variables.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)