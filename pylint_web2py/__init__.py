from astroid import MANAGER
from astroid import scoped_nodes
from astroid.builder import AstroidBuilder
from os.path import join
import re
import sys
import pdb

is_pythonpath_modified = False

def web2py_transform(module):
    'Add imports and some default objects, add custom module paths to pythonpath'
    global is_pythonpath_modified
    if module.file:
        #Check if this file module belongs to web2py
        match = re.match(r'(.+?)/applications/(.+?)/', module.file)
        if match:
            if not is_pythonpath_modified:
                add_custom_module_paths(match.group(1), match.group(2))
            # This dummy code is copied from gluon/__init__.py
            fake = AstroidBuilder(MANAGER).string_build('''
from gluon.globals import current
from gluon.html import *
from gluon.validators import *
from gluon.http import redirect, HTTP
from gluon.dal import DAL, Field
from gluon.sqlhtml import SQLFORM, SQLTABLE
from gluon.compileapp import LOAD

from gluon.globals import Request, Response, Session
from gluon.cache import Cache
from gluon.languages import translator
from gluon.tools import Auth, Crud, Mail, Service, PluginManager

# API objects
request = Request()
response = Response()
session = Session()
cache = Cache(request)
T = translator(request)

# Objects commonly defined in application model files
# (names are conventions only -- not part of API)
db = DAL()
auth = Auth(db)
crud = Crud(db)
mail = Mail()
service = Service()
plugins = PluginManager()
    ''')
            module.locals.update(fake.locals)

def register(linter):
    'Register web2py transformer, called by pylint'
    MANAGER.register_transform(scoped_nodes.Module, web2py_transform)

def add_custom_module_paths(web2py_dir, app_name):
    'Add web2py module dirs (gluon, site-packages and app\'s module dir) to python path'
    global is_pythonpath_modified

    gluon_path = join(web2py_dir, 'gluon')
    site_packages_path = join(web2py_dir, 'site-packages')
    app_modules_path = join(web2py_dir, 'applications', app_name, 'modules')

    for module_path in [gluon_path, site_packages_path, app_modules_path, web2py_dir]:
        sys.path.append(module_path)
    is_pythonpath_modified = True

