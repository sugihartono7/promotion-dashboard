import imp
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

wsgi = imp.load_source('wsgi', 'app.py')
application = wsgi.application

activate_this = '/path/to/env/bin/activate_this.py'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))