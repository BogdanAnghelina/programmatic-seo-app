from database import Template, session

# Query all templates
templates = session.query(Template).all()

# Print the templates to see the data
for template in templates:
    print(f"Template ID: {template.id}")
    print(f"Template Name: {template.template_name}")
    print(f"Template Content: {template.template_content}")
    print(f"Template Variables: {template.template_variables}")
    print("-----")
