from supabase import create_client, Client
import os

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class Template:
    def __init__(self, id, template_name, template_content, template_variables, draft, user_id, active_tab):
        self.id = id
        self.template_name = template_name
        self.template_content = template_content
        self.template_variables = template_variables
        self.draft = draft
        self.user_id = user_id
        self.active_tab = active_tab

class UserDB:
    def __init__(self, id, username, password, wp_url, wp_user, wp_app_password, connection_status):
        self.id = id
        self.username = username
        self.password = password
        self.wp_url = wp_url
        self.wp_user = wp_user
        self.wp_app_password = wp_app_password
        self.connection_status = connection_status

def get_templates():
    response = supabase.table('templates').select('*').execute()
    return [Template(**template) for template in response.data]

def get_users():
    response = supabase.table('users').select('*').execute()
    return [UserDB(**user) for user in response.data]

def add_template(template):
    response = supabase.table('templates').insert(template.__dict__).execute()
    return response

def add_user(user):
    response = supabase.table('users').insert(user.__dict__).execute()
    return response

def update_template(template_id, updates):
    response = supabase.table('templates').update(updates).eq('id', template_id).execute()
    return response

def update_user(user_id, updates):
    response = supabase.table('users').update(updates).eq('id', user_id).execute()
    return response

def delete_template(template_id):
    response = supabase.table('templates').delete().eq('id', template_id).execute()
    return response

def delete_user(user_id):
    response = supabase.table('users').delete().eq('id', user_id).execute()
    return response
