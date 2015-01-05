'''
This plugin minimizes Pylint's complaints about web2py code.
Web2py executes user code is special environment populated with predefined objects and types and with objects defined in model files.
Also it has magic import mechanism which knows some special places where to find modules.

Pylint doesn't know about these details -- its parser is unable to find these objects and modules, resulting in a flood of laments.
This plugin:
- adds variables defined in models to module scope
- adds definition of some predefined global objects to controllers
- adds web2py module paths to PYTHONPATH
'''
from astroid import MANAGER, scoped_nodes
from astroid.builder import AstroidBuilder
from pylint.lint import PyLinter
from pylint.checkers.variables import VariablesChecker
from pylint.interfaces import UNDEFINED
from os.path import join, splitext
import os
import re
import sys
import ipdb


def web2py_transform(module):
    'Add imports and some default objects, add custom module paths to pythonpath'

    if module.file:
        #Check if this file belongs to web2py
        web2py_match = re.match(r'(.+?)/applications/(.+?)/(.+?)/', module.file)
        if web2py_match:
            web2py_path, app_name, subfolder = web2py_match.group(1), web2py_match.group(2), web2py_match.group(3)
            return transformer.transform_module(module, web2py_path, app_name, subfolder)

        # if subfolder == 'models':
        #         #Include global objects and previous models
        #         fake_code += gen_models_import_code()
        #         pass

        #         #If this is controller file, add code to import locals from models
        #         controller_match = re.match(r'(.+?)/controllers/', module.file)
        #         if controller_match:
        #             app_models_path = join(controller_match.group(1), 'models')
        #             fake_code += gen_models_import_code(app_models_path)

        #         fake = AstroidBuilder(MANAGER).string_build(fake_code)
        #         # ipdb.set_trace()
        #         module.globals.update(fake.globals)

        #         #module = remove_unused_wildcard_imports(module)
        #         return module

class Web2PyTransformer(object):
    'Transforms web2py modules code'
    # This dummy code is copied from gluon/__init__.py
    fake_code = '''
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

    def __init__(self):
        self.is_pythonpath_modified = False
        self.web2py_path = ''
        self.app_model_names = []

    def transform_module(self, module_node, web2py_path, app_name, subfolder):
        #Add web2py modules paths to sys.path
        self._add_paths(web2py_path, app_name)

        if subfolder == 'models':
            transformed_module = self._trasform_model(module_node)
        elif subfolder == 'controllers':
            transformed_module = self._transform_controller(module_node)
        else:
            transformed_module = module_node

        #transformed_module = self._remove_unused_imports(transformed_module)
        return transformed_module

    def _add_paths(self, web2py_path, app_name):
        if not self.is_pythonpath_modified:
            self.web2py_path = web2py_path
            gluon_path = join(web2py_path, 'gluon')
            site_packages_path = join(web2py_path, 'site-packages')
            app_modules_path = join(web2py_path, 'applications', app_name, 'modules')
            app_models_path = join(web2py_path, 'applications', app_name, 'models') #Add models to import them them in controllers

            for module_path in [gluon_path, site_packages_path, app_modules_path, app_models_path, web2py_path]:
                sys.path.append(module_path)

            self._fill_app_model_names(app_models_path)

            self.is_pythonpath_modified = True


    def _trasform_model(self, module_node):
        fake_code = self.fake_code + self._gen_models_import_code(module_node.name)
        fake = AstroidBuilder(MANAGER).string_build(fake_code)
        module_node.locals.update(fake.globals)

        module_node = self._remove_unused_wildcard_imports(module_node, fake)
        return module_node

    def _transform_controller(self, module_node):
        fake_code = self.fake_code + self._gen_models_import_code()
        fake = AstroidBuilder(MANAGER).string_build(fake_code)
        module_node.locals.update(fake.globals)

        return module_node

    def _gen_models_import_code(self, current_model=None):
        code = ''
        for model_name in self.app_model_names:
            if current_model and model_name == current_model:
                break
            code += 'from %s import *\n' % model_name

        return code

    def _fill_app_model_names(self, app_models_path):
        model_files = os.listdir(app_models_path)
        model_files = [model_file for model_file in model_files if re.match(r'.+?\.py', model_file)] #Only top-level models
        model_files = sorted(model_files) #Models are executed in alphabetical order
        self.app_model_names = [re.match(r'^(.+?)\.py$', model_file).group(1) for model_file in model_files]

    def _remove_unused_wildcard_imports(self, module_node, fake_node):
        # sniffer = MessageSniffer()
        # var_checker = VariablesChecker(sniffer)
        # var_checker.visit_module(module_node)
        # var_checker.leave_module(module_node)
        # ipdb.set_trace()
        # for name in sniffer.unused:
        #     if name in fake_node.globals:
        #         del module_node.locals[name]
        return module_node


def register(_):
    'Register web2py transformer, called by pylint'
    MANAGER.register_transform(scoped_nodes.Module, web2py_transform)

class MessageSniffer(PyLinter):
    def __init__(self):
        super(MessageSniffer, self).__init__()
        self.unused = []

    def add_message(self, msg_descr, line=None, node=None, args=None, confidence=UNDEFINED):
        if msg_descr == 'unused-wildcard-import':
            # if args == 'db':
            #     ipdb.set_trace()
            self.unused.append(args)

transformer = Web2PyTransformer()
