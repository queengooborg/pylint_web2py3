'''
This plugin minimizes Pylint's complaints about web2py code.
Web2py executes user code is special environment populated with predefined objects and types and with objects defined in model files.
Also it has magic import mechanism which knows some special places where to find modules.

Pylint doesn't know about these details -- its parser is unable to find these objects and modules, resulting in a flood of laments.
This plugin:
- adds variables defined in models to module scope
- adds definition of some predefined global objects to module scope
- adds web2py module paths to PYTHONPATH
'''
from astroid import MANAGER
from astroid import scoped_nodes
from astroid.builder import AstroidBuilder
from os.path import join, splitext
import os
import re
import sys
import ipdb

is_pythonpath_modified = False

def web2py_transform(module):
    'Add imports and some default objects, add custom module paths to pythonpath'
    # This dummy code is copied from gluon/__init__.py
    fake_code = '''
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
'''

    if module.file:
        #Check if this file belongs to web2py
        match = re.match(r'(.+?)/applications/(.+?)/', module.file)
        if match:
            if not is_pythonpath_modified:
                #Add web2py modules paths to PYTHONPATH
                add_custom_module_paths(match.group(1), match.group(2))

                #If this is controller file, add code to import locals from models
                controller_match = re.match(r'(.+?)/controllers/', module.file)
                if controller_match:
                    app_models_path = join(controller_match.group(1), 'models')
                    fake_code += gen_models_import_code(app_models_path)

                fake = AstroidBuilder(MANAGER).string_build(fake_code)
                module.locals.update(fake.locals)


def register(_):
    'Register web2py transformer, called by pylint'
    MANAGER.register_transform(scoped_nodes.Module, web2py_transform)

def add_custom_module_paths(web2py_dir, app_name):
    'Add web2py module dirs (gluon, site-packages and app\'s module dir) to python path'
    global is_pythonpath_modified

    gluon_path = join(web2py_dir, 'gluon')
    site_packages_path = join(web2py_dir, 'site-packages')
    app_modules_path = join(web2py_dir, 'applications', app_name, 'modules')
    app_models_path = join(web2py_dir, 'applications', app_name, 'models') #Add models to import them them in controllers

    for module_path in [gluon_path, site_packages_path, app_modules_path, app_models_path, web2py_dir]:
        sys.path.append(module_path)
    is_pythonpath_modified = True


def gen_models_import_code(app_models_path):
    model_files = os.listdir(app_models_path)
    model_files = [model_file for model_file in model_files if re.match(r'.+?\.py', model_file)] #Only top-level models
    model_files = sorted(model_files) #Models are executed in alphabetical order
    model_names = [re.match(r'^(.+?)\.py$', model_file).group(1) for model_file in model_files]

    code = '\n'.join(['from %s import *' % model_name for model_name in model_names])
    print code

    return code
