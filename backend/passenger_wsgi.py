import importlib.machinery
import importlib.util
import os
import sys


# Add the project directory to the sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'medical.settings'

def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module

# Load Django WSGI application
wsgi = load_source('wsgi', 'medical/wsgi.py')
application = wsgi.application
