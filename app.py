from flask import Flask, render_template, request
from view import auth, dashboard, user
import os

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY = 'Y0PR0M0'
)

def get_resource_as_string(name, charset='utf-8'):
    with app.open_resource(name) as f:
        return f.read().decode(charset)

app.jinja_env.globals['get_resource_as_string'] = get_resource_as_string

app.register_blueprint(auth.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(user.bp)
application = app 

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
    
