from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy.exc import OperationalError, InvalidRequestError, PendingRollbackError, InterfaceError
from sqlalchemy.orm.exc import NoResultFound
from database import Template, Session, session, UserDB
import requests
import base64
import re


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class FlaskUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

def format_variable(variable):
    variable = variable.replace(" ", "_")
    if not re.match(r'^[a-zA-Z0-9_]*$', variable):
        return ''
    return f"[{variable.lower()}]"

def strip_tags(input_string):
    if not input_string or not isinstance(input_string, str):
        return ''
    return re.sub(r'<[^>]*>', '', input_string)

app.jinja_env.filters['strip_tags'] = strip_tags



@app.route('/check_connection', methods=['GET'])
@login_required
def check_connection():
    user_db = session.query(UserDB).filter_by(username=current_user.id).first()
    if user_db and user_db.connection_status == "connected":
        return jsonify(status='connected')
    else:
        return jsonify(status='not_connected')


@login_manager.user_loader
def load_user(user_id):
    return FlaskUser(user_id=user_id)
  

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'password':
            user_db = session.query(UserDB).filter_by(username='admin').first()
            if not user_db:
                new_user = UserDB(username='admin', password='password')
                session.add(new_user)
                session.commit()
            user = FlaskUser(user_id='admin')  # Initialize the user object from flask_login
            login_user(user)  # Log the user in
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
            return redirect(url_for('edit_template', template_id=draft.id))

        elif 'add_variable' in request.form:
            variable_name = request.form['variable_name'].strip()  # Trim white spaces
            
            # Check for empty variable_name
            if not variable_name:
                flash('Variable cannot be empty!')
                return redirect(url_for('new_template'))

            formatted_variable = format_variable(variable_name)

            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('new_template'))
    
            if not draft:
                draft = Template(template_name="Draft", template_content='', draft=True, user_id=current_user.id)
                session.add(draft)
                session.commit()
    
            current_variables = draft.template_variables.split(",") if draft.template_variables else []
            if formatted_variable in current_variables:
                flash(f'Variable {formatted_variable} already exists.')
                return redirect(url_for('new_template'))
    
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
    user_db = session.query(UserDB).filter_by(username=current_user.id).first()
    template_data = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first()

    if template_data is None:
        flash("Template not found.")
        return redirect(url_for('saved_templates'))

    if request.method == 'POST':
        if 'add_variable' in request.form:
            variable_name = request.form['variable_name'].strip()
            if not variable_name:
                flash('Variable cannot be empty!')
                return redirect(url_for('edit_template', template_id=template_id))
            formatted_variable = format_variable(variable_name)
            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('edit_template', template_id=template_id))
            current_variables = template_data.template_variables.split(",") if template_data.template_variables else []
            if formatted_variable in current_variables:
                flash(f'Variable {formatted_variable} already exists.')
            else:
                current_variables.append(formatted_variable)
                template_data.template_variables = ",".join(current_variables)
                session.commit()
                flash(f'Variable {formatted_variable} added successfully!')
        elif 'connect_wp' in request.form:
            # Clear old data first
            if user_db:
                user_db.wp_url = None
                user_db.wp_user = None
                user_db.wp_app_password = None
                user_db.connection_status = None
                session.commit()  # Commit immediately
        
            # Get new data from form
            wp_url = request.form['wp_url']
            wp_user = request.form['wp_user']
            wp_app_password = request.form['wp_app_password']
            
            api_url = f"{wp_url}/wp-json/wp/v2/users/me"
            credentials = f"{wp_user}:{wp_app_password}"
            headers = {'Authorization': f'Basic {base64.b64encode(credentials.encode()).decode()}'}
        
            try:
                response = requests.get(api_url, headers=headers)
                user_db = session.query(UserDB).filter_by(username=current_user.id).first()  # Re-query user_db
                if response.status_code == 200:
                    flash('Successfully connected to WordPress!', 'success')
                    if user_db:  # Check if user_db is not None
                        user_db.wp_url = wp_url
                        user_db.wp_user = wp_user
                        user_db.wp_app_password = wp_app_password
                        user_db.connection_status = "connected"
                    session.commit()
                else:
                    if user_db:  # Clear old data
                        user_db.wp_url = None
                        user_db.wp_user = None
                        user_db.wp_app_password = None
                        user_db.connection_status = None
                    session.commit()
                    flash(f'Failed to connect to WordPress: {response.json()}')
        
            except Exception as e:
                flash('The URL, user, or password for this connection is wrong. Please make sure you use the app password instead of your user password in WordPress.', 'error')
                user_db = session.query(UserDB).filter_by(username=current_user.id).first()  # Re-query user_db
                if user_db:
                    user_db.connection_status = "not_connected"
                session.commit()
        elif 'publish_wp' in request.form:
            publish_type = request.form['publish_type']
            if user_db and user_db.connection_status == "connected":
                wp_url = user_db.wp_url
                wp_user = user_db.wp_user
                wp_app_password = user_db.wp_app_password
                credentials = f"{wp_user}:{wp_app_password}"
                headers = {'Authorization': f'Basic {base64.b64encode(credentials.encode()).decode()}'}
                api_url = f"{wp_url}/wp-json/wp/v2/{publish_type}"
                data = {
                    "title": template_data.template_name,
                    "content": template_data.template_content,
                    "status": "draft"
                }
                try:
                    response = requests.post(api_url, headers=headers, json=data)
                    if response.status_code == 201:
                        flash(f'Successfully published as {publish_type[:-1].title()} in WordPress', 'success')
                    else:
                        flash(f'Failed to publish to WordPress: {response.json()}', 'error')
                except Exception as e:
                    flash(f'An error occurred while publishing to WordPress: {str(e)}', 'error')
            else:
                flash('You are not connected to WordPress. Connect first to publish.', 'warning')

    variables = template_data.template_variables.split(",") if template_data.template_variables else []
    return render_template('edit_template.html', template=template_data, variables=variables,
                           template_name=template_data.template_name, template_id=template_id,
                           template_content=template_data.template_content, user_db=user_db)








  


@app.route('/get_template_data', methods=['GET'])
def get_template_data():
    template_id = request.args.get('template_id')
    template = session.query(Template).filter_by(id=template_id).first()

    print("Debug:", template)  # For debugging

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
    template_id = request.form.get('template_id')
    
    print(f"Debug: Received variable_name: {variable_name}, template_id: {template_id}")

    if variable_name is None or template_id is None:
        return jsonify(status='error', message='Variable name and template ID are required.'), 400

    # Replace spaces with underscores
    variable_name = variable_name.replace(' ', '_')

    formatted_variable = format_variable(variable_name)
    response = {}

    if not formatted_variable:
        response['status'] = 'error'
        response['message'] = 'Variable can only contain letters, numbers, and underscores.'
        return jsonify(response), 400
    else:
        try:
            template = None
            if template_id:
                # This is for edit_template
                template = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first()
            else:
                # This is for new_template (draft)
                template = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()
            
            if not template:
                response['status'] = 'error'
                response['message'] = 'Template not found.'
                return jsonify(response), 400

            current_variables = template.template_variables.split(",") if template.template_variables else []
            if formatted_variable not in current_variables:
                current_variables.append(formatted_variable)
                template.template_variables = ",".join(current_variables)
                session.commit()

                response['status'] = 'success'
                response['message'] = f'Variable {formatted_variable} added successfully!'
                return jsonify(response), 200
            else:
                response['status'] = 'error'
                response['message'] = f'Variable {formatted_variable} already exists.'
                return jsonify(response), 400

        except Exception as e:
            response['status'] = 'error'
            response['message'] = f'An unexpected error occurred: {str(e)}'
            return jsonify(response), 500
          


@app.route('/delete_variable', methods=['POST'])
@login_required
def delete_variable():
    variable_to_delete = request.form.get('variable_name')
    template_id = request.form.get('template_id')
    print(f"Debug: Received template_id: {template_id}")  # Debug line

    if not variable_to_delete:
        return jsonify(status='error', message='Variable name is required.')

    template = None
    if template_id:
        template = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first()
    else:
        template = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()
    
    if not template:
        return jsonify(status='error', message='No appropriate template found.')

    current_variables = template.template_variables.split(",") if template.template_variables else []
    if variable_to_delete in current_variables:
        current_variables.remove(variable_to_delete)
        template.template_variables = ",".join(current_variables)
        session.commit()
        return jsonify(status='success', message=f'Variable {variable_to_delete} deleted successfully!')
    else:
        return jsonify(status='error', message=f'Variable {variable_to_delete} not found.')








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

    return redirect(url_for('edit_template', template_id=template_id))






@app.route('/extract_variables', methods=['GET', 'POST'])
def extract_variables():
    if request.method == 'POST':
        template_id = request.form['template_id']
        template = session.query(Template).filter_by(id=template_id).first()

        if template:
            variables = template.template_variables.split(",") if template.template_variables else []
            return render_template('extract_variables.html', variables=variables)

    return render_template('extract_variables.html')








@app.route('/verify_wp_connection', methods=['GET'])
@login_required
def verify_wp_connection():
    user_db = None
    try:
        user_db = session.query(UserDB).filter_by(username=current_user.id).first()
        if user_db is None:
            return jsonify(status='no_credentials')
    except Exception as e:
        return jsonify(status='database_error')
    
    try:
        wp_url = user_db.wp_url
        wp_user = user_db.wp_user
        wp_app_password = user_db.wp_app_password
        api_url = f"{wp_url}/wp-json/wp/v2/users/me"
        credentials = f"{wp_user}:{wp_app_password}"
        headers = {'Authorization': f'Basic {base64.b64encode(credentials.encode()).decode()}'}
        
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            user_db.connection_status = "connected"
        else:
            user_db.connection_status = "not_connected"
    except Exception as e:
        if user_db is not None:
            user_db.connection_status = "not_connected"
    
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        return jsonify(status='database_error')
    
    return jsonify(status=user_db.connection_status if user_db else 'error')



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)