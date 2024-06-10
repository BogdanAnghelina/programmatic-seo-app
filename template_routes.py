from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from database import Template, session
from helpers import format_variable

template_bp = Blueprint('template_bp', __name__)

@template_bp.route('/new_template', methods=['GET', 'POST'])
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
            draft.template_variables = draft.template_variables
            draft.user_id = current_user.id
            session.commit()

            flash('Template saved successfully!', 'success')
            return redirect(url_for('template.edit_template', template_id=draft.id))

        elif 'add_variable' in request.form:
            variable_name = request.form['variable_name'].strip()
            if not variable_name:
                flash('Variable cannot be empty!')
                return redirect(url_for('template.new_template'))

            formatted_variable = format_variable(variable_name)
            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('template.new_template'))

            if not draft:
                draft = Template(template_name="Draft", template_content='', draft=True, user_id=current_user.id)
                session.add(draft)
                session.commit()

            current_variables = draft.template_variables.split(",") if draft.template_variables else []
            if formatted_variable in current_variables:
                flash(f'Variable {formatted_variable} already exists.')
                return redirect(url_for('template.new_template'))

            current_variables.append(formatted_variable)
            draft.template_variables = ",".join(current_variables)
            session.commit()
            flash(f'Variable {formatted_variable} added successfully!')
            return redirect(url_for('template.new_template'))

        elif 'delete_variable' in request.form:
            variable_to_delete = request.form['delete_variable']
            if draft:
                current_variables = draft.template_variables.split(",") if draft.template_variables else []
                if variable_to_delete in current_variables:
                    current_variables.remove(variable_to_delete)
                    draft.template_variables = ",".join(current_variables)
                    session.commit()
                    flash(f'Variable {variable_to_delete} deleted successfully!')
            return redirect(url_for('template.new_template'))

    template_name = ""
    template_content = ""
    variables = []

    if draft:
        template_name = draft.template_name
        template_content = draft.template_content
        variables = draft.template_variables.split(",") if draft.template_variables else []

    return render_template('new_template.html', template_name=template_name, template_content=template_content, variables=variables)

@template_bp.route('/reset_draft', methods=['GET'])
@login_required
def reset_draft():
    draft = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()
    if draft:
        draft.template_name = "Draft"
        draft.template_content = ""
        draft.template_variables = ""
        session.commit()
    return redirect(url_for('template.new_template'))

@template_bp.route('/saved_templates', methods=['GET'])
@login_required
def saved_templates():
    templates = session.query(Template).filter_by(draft=False, user_id=current_user.id).all()
    return render_template('saved_templates.html', templates=templates)

@template_bp.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    user_db = session.query(UserDB).filter_by(username=current_user.id).first()
    template_data = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first()

    if template_data is None:
        flash("Template not found.")
        return redirect(url_for('template.saved_templates'))

    site_url = request.args.get('site_url')
    user_login = request.args.get('user_login')
    password = request.args.get('password')

    if site_url and user_login and password:
        api_url = f"{site_url}/wp-json/wp/v2/users/me"
        credentials = f"{user_login}:{password}"
        headers = {'Authorization': f'Basic {base64.b64encode(credentials.encode()).decode()}'}
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                flash('Successfully connected to WordPress!', 'success')
                if user_db:
                    user_db.wp_url = site_url
                    user_db.wp_user = user_login
                    user_db.wp_app_password = password
                    user_db.connection_status = "connected"
                    session.commit()
                return redirect(url_for('template.edit_template', template_id=template_id))
            else:
                flash(f'Failed to connect to WordPress: {response.json()}')
                if user_db:
                    user_db.connection_status = "not_connected"
                session.commit()
                return redirect(url_for('template.edit_template', template_id=template_id))
        except Exception as e:
            flash('Connection failed. Please make sure your details are correct.', 'error')
            if user_db:
                user_db.connection_status = "not_connected"
            session.commit()
            return redirect(url_for('template.edit_template', template_id=template_id))

    if request.method == 'POST':
        if 'add_variable' in request.form:
            variable_name = request.form['variable_name'].strip()
            if not variable_name:
                flash('Variable cannot be empty!')
                return redirect(url_for('template.edit_template', template_id=template_id))
            formatted_variable = format_variable(variable_name)
            if not formatted_variable:
                flash('Variable can only contain letters, numbers, and underscores.')
                return redirect(url_for('template.edit_template', template_id=template_id))
            current_variables = template_data.template_variables.split(",") if template_data.template_variables else []
            if formatted_variable in current_variables:
                flash(f'Variable {formatted_variable} already exists.')
            else:
                current_variables.append(formatted_variable)
                template_data.template_variables = ",".join(current_variables)
                session.commit()
                flash(f'Variable {formatted_variable} added successfully!')
        elif 'connect_wp' in request.form:
            if user_db:
                user_db.wp_url = None
                user_db.wp_user = None
                user_db.wp_app_password = None
                user_db.connection_status = None
                session.commit()

            wp_url = request.form['wp_url']
            wp_user = request.form['wp_user']
            wp_app_password = request.form['wp_app_password']
            api_url = f"{wp_url}/wp-json/wp/v2/users/me"
            credentials = f"{wp_user}:{wp_app_password}"
            headers = {'Authorization': f'Basic {base64.b64encode(credentials.encode()).decode()}'}

            try:
                response = requests.get(api_url, headers=headers)
                user_db = session.query(UserDB).filter_by(username=current_user.id).first()
                if response.status_code == 200:
                    flash('Successfully connected to WordPress!', 'success')
                    if user_db:
                        user_db.wp_url = wp_url
                        user_db.wp_user = wp_user
                        user_db.wp_app_password = wp_app_password
                        user_db.connection_status = "connected"
                    session.commit()
                else:
                    if user_db:
                        user_db.wp_url = None
                        user_db.wp_user = None
                        user_db.wp_app_password = None
                        user_db.connection_status = None
                    session.commit()
                    flash(f'Failed to connect to WordPress: {response.json()}')

            except Exception as e:
                flash('The URL, user, or password for this connection is wrong. Please make sure you use the app password instead of your user password in WordPress.', 'error')
                user_db = session.query(UserDB).filter_by(username=current_user.id).first()
                if user_db:
                    user_db.connection_status = "not_connected"
                session.commit()
        elif 'publish_wp' in request.form:
            publish_type = request.form['publish_type']
            wp_status = request.form['wp_status']

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
                    "status": wp_status
                }

                try:
                    response = requests.post(api_url, headers=headers, json=data)
                    if response.status_code == 201:
                        flash(f'Successfully published as {publish_type[:-1].title()} in WordPress!', 'success')
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

@template_bp.route('/delete_template', methods=['POST'])
@login_required
def delete_template():
    template_id = request.form.get('template_id')
    if not template_id:
        return jsonify({'status': 'failure'})

    try:
        template = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first()
        if template:
            session.delete(template)
            session.commit()
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'failure'})
    except Exception as e:
        session.rollback()
        return jsonify({'status': 'failure'})

@template_bp.route('/update_template', methods=['POST'])
def update_template():
    template_id = request.form.get('template_id')
    new_template_name = request.form.get('template_name')
    new_template_content = request.form.get('hidden_template_content')

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

    return redirect(url_for('template.edit_template', template_id=template_id))

@template_bp.route('/check_variable_in_draft', methods=['POST'])
def check_variable_in_draft():
    variable_name = request.form.get('variable_name')
    user_id = current_user.id

    existing_draft = session.query(Template).filter_by(user_id=user_id, draft=1).first()

    if existing_draft:
        existing_variables = existing_draft.template_variables.split(",") if existing_draft.template_variables else []
        if variable_name in existing_variables:
            return jsonify({'status': 'duplicate'})

    return jsonify({'status': 'ok'})

@template_bp.route('/get_template_data', methods=['GET'])
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

@template_bp.route('/get_variables', methods=['GET'])
@login_required
def get_variables():
    template = session.query(Template).filter_by(draft=True, user_id=current_user.id).first()

    if not template:
        return jsonify({
            'status': 'error',
            'message': 'No draft template found for current user.'
        }), 404

    variables = template.template_variables.split(",") if template.template_variables else []

    return jsonify({
        'status': 'success',
        'variables': variables
    })

@template_bp.route('/add_variable', methods=['POST'])
def add_variable():
    variable_name, template_id = request.form.get('variable_name'), request.form.get('template_id')
    formatted_variable = format_variable(variable_name.strip())
    response = {}

    if not formatted_variable:
        return jsonify(status='error', message='Invalid variable name.'), 400

    template = session.query(Template).filter_by(id=template_id, user_id=current_user.id).first() or \
               session.query(Template).filter_by(draft=True, user_id=current_user.id).first()

    if not template:
        return jsonify(status='error', message='Template not found.'), 400

    current_variables = template.template_variables.split(",") if template.template_variables else []
    if formatted_variable in current_variables:
        return jsonify(status='duplicate', message=f'Variable {formatted_variable} already exists.'), 400

    current_variables.append(formatted_variable)
    template.template_variables = ",".join(current_variables)
    session.commit()
    return jsonify(status='success', message=f'Variable {formatted_variable} added successfully!'), 200

@template_bp.route('/delete_variable', methods=['POST'])
@login_required
def delete_variable():
    variable_to_delete = request.form.get('variable_name')
    template_id = request.form.get('template_id')

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

@template_bp.route('/extract_variables', methods=['GET', 'POST'])
def extract_variables():
    if request.method == 'POST':
        template_id = request.form['template_id']
        template = session.query(Template).filter_by(id=template_id).first()

        if template:
            variables = template.template_variables.split(",") if template.template_variables else []
            return render_template('extract_variables.html', variables=variables)

    return render_template('extract_variables.html')
