import re
from flask import Flask
from database import session

def format_variable(variable):
    return f"[{variable.lower().replace(' ', '_')}]" if re.match(r'^[a-zA-Z0-9_ ]*$', variable) else ''

def strip_tags(input_string):
    return re.sub(r'<[^>]*>', '', input_string) if input_string else ''

def initialize_app(app):
    app.jinja_env.filters['strip_tags'] = strip_tags

@app.teardown_appcontext
def shutdown_session(exception=None):
    if exception:
        session.rollback()
    else:
        session.commit()
    session.close()