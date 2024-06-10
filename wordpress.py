from flask import Blueprint, redirect, url_for, request, flash, jsonify
from flask_login import current_user, login_required
from urllib.parse import urlencode
import requests
import base64
from database import session, UserDB

wordpress_bp = Blueprint('wordpress', __name__)

@wordpress_bp.route('/edit_template_wp_auth/<int:template_id>', methods=['GET', 'POST'])
def edit_template_wp_auth(template_id):
    base_url = request.form.get('base_url')

    if not base_url.startswith(('http://', 'https://')):
        base_url = 'http://' + base_url

    site_url = request.args.get('site_url')
    user_login = request.args.get('user_login')
    password = request.args.get('password')

    if site_url and user_login and password:
        flash('Successfully authorized.', 'success')
    elif site_url:
        flash('Authorization rejected.', 'danger')

    app_name = "Programmatic SEO App - BGD"
    success_url = f"https://programmatic-seo-app.bogdananghelin1.repl.co/edit_template/{template_id}"
    reject_url = f"https://programmatic-seo-app.bogdananghelin1.repl.co/reject?template_id={template_id}"

    params = {
        "app_name": app_name,
        "success_url": success_url,
        "reject_url": reject_url
    }

    auth_url = f"{base_url}/wp-admin/authorize-application.php?{urlencode(params)}"
    return redirect(auth_url)

@wordpress_bp.route('/success')
def success():
    site_url = request.args.get('site_url')
    user_login = request.args.get('user_login')
    password = request.args.get('password')
    template_id = request.args.get('template_id')

    flash('Successfully authorized.', 'success')
    return redirect(url_for('template.edit_template', template_id=template_id))

@wordpress_bp.route('/reject')
def reject():
    flash('Authorization rejected.', 'danger')
    template_id = request.args.get('template_id')
    return redirect(url_for('template.edit_template', template_id=template_id))

@wordpress_bp.route('/verify_wp_connection', methods=['GET'])
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