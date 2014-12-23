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
import pdb

# This dummy code is copied from gluon/__init__.py
fake_code = '''
#pylint: disable=unused-wildcard-import

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

is_pythonpath_modified = False

#Dictionary of lists, key (model name) -> val (model locals)
models_locals = {}

def web2py_transform(module):
    'Add imports and some default objects, add custom module paths to pythonpath'
    if module.file:
        #Check if this file belongs to web2py
        match = re.match(r'(.+?)/applications/(.+?)/', module.file)
        if match:
            #Add web2py modules paths to PYTHONPATH
            #This block will be executed only once
            if not is_pythonpath_modified:
                add_custom_module_paths(match.group(1), match.group(2))
                app_models_path = join(match.group(1), 'applications', match.group(2), 'models')
                collect_model_locals(app_models_path)
                #Add locals from models
                for model in models_locals.keys():
                    if model != module.name:
                        module.locals.update(models_locals[model])

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

    for module_path in [gluon_path, site_packages_path, app_modules_path, web2py_dir]:
        sys.path.append(module_path)
    is_pythonpath_modified = True

def collect_model_locals(app_models_path):
    '''
    Extract locals defined in model files and save them to models_locals per each model file
    '''
    global models_locals
    #Only top level models
    model_files = [m for m in os.listdir(app_models_path) if re.match(r'.+?\.py$', m)]
    model_files = sorted(model_files) #Models are executed in alphabetical order

    for model_file in model_files:
        module_name = splitext(model_file)[0]
        module_path = join(app_models_path, model_file)

        module_ast = AstroidBuilder(MANAGER).file_build(module_path, module_name)
        models_locals[module_name] = module_ast.locals
