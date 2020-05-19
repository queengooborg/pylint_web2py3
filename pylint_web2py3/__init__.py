## -*- coding: utf-8 -*-

'''
This plugin minimizes Pylint's complaints about web2py code.
Web2py executes user code in special environment populated with predefined objects and types and with objects defined in model files.
Also it has magic import mechanism which knows some special places where to find modules.

Pylint doesn't know about these details -- its parser is unable to find these objects and modules, resulting in a flood of laments.
This plugin:
- adds variables defined in models to other models' and controllers' scope
- adds definition of some predefined global objects to models and controllers
- adds web2py module paths to PYTHONPATH
'''

VERSION_INFO = (0, 9, 1)
__name__ = 'pylint_web2py3'
__doc__ = 'pylint_web2py3 is a disciple of pylint-web2py and pylint_web2py2 with better web2py support'
__author__ = ['Vinyl Darkscratch']
__version__ = '.'.join([str(i) for i in VERSION_INFO])
__license__ = 'GPL'
__maintainer__ = 'Vinyl Darkscratch'
__email__ = ['vinyldarkscratch@gooborg.com']
__status__ = 'Beta'

import os
import re
import sys
from astroid import MANAGER, scoped_nodes
from astroid.builder import AstroidBuilder
from pylint.lint import PyLinter
from pylint.checkers.base import ComparisonChecker
from pylint.checkers.variables import VariablesChecker
from pylint.interfaces import UNDEFINED
from pylint.utils import ASTWalker

def register(_):
	'''Register web2py transformer, called by pylint'''
	MANAGER.register_transform(scoped_nodes.Module, web2py_transform)

def web2py_transform(module):
	'''Add imports and some default objects, add custom module paths to pythonpath'''

	if module.file:
		#Check if this file belongs to web2py
		web2py_match = re.match(r'(.+?)/applications/(.+?)/(.+?)/', module.file)
		if web2py_match:
			web2py_path, app_name, subfolder = web2py_match.group(1), web2py_match.group(2), web2py_match.group(3)
			return transformer.transform_module(module, web2py_path, app_name, subfolder)

class Web2PyTransformer(object):
	'''Transforms web2py modules code'''
	# This dummy code is copied from gluon/__init__.py and gluon/compileapp.py
	# First two lines are copied from ALL array in gluon.html, gluon.validators, and pydal.validators
	fake_code = '''
from gluon.html import A, ASSIGNJS, B, BEAUTIFY, BODY, BR, BUTTON, CENTER, CAT, CODE, COL, COLGROUP, DIV, EM, EMBED, FIELDSET, FORM, H1, H2, H3, H4, H5, H6, HEAD, HR, HTML, I, IFRAME, IMG, INPUT, LABEL, LEGEND, LI, LINK, OL, UL, MARKMIN, MENU, META, OBJECT, ON, OPTION, P, PRE, SCRIPT, OPTGROUP, SELECT, SPAN, STRONG, STYLE, TABLE, TAG, TD, TEXTAREA, TH, THEAD, TBODY, TFOOT, TITLE, TR, TT, URL, XHTML, XML, xmlescape, embed64
from gluon.validators import ANY_OF, CLEANUP, CRYPT, IS_ALPHANUMERIC, IS_DATE_IN_RANGE, IS_DATE, IS_DATETIME_IN_RANGE, IS_DATETIME, IS_DECIMAL_IN_RANGE, IS_EMAIL, IS_LIST_OF_EMAILS, IS_EMPTY_OR, IS_EXPR, IS_FILE, IS_FLOAT_IN_RANGE, IS_IMAGE, IS_IN_DB, IS_IN_SET, IS_INT_IN_RANGE, IS_IPV4, IS_IPV6, IS_IPADDRESS, IS_LENGTH, IS_LIST_OF, IS_LOWER, IS_MATCH, IS_EQUAL_TO, IS_NOT_EMPTY, IS_NOT_IN_DB, IS_NULL_OR, IS_SLUG, IS_STRONG, IS_TIME, IS_UPLOAD_FILENAME, IS_UPPER, IS_URL, IS_JSON, simple_hash, get_digest, Validator, ValidationError, translate

from gluon.http import redirect, HTTP
from gluon.dal import DAL, Field
from gluon.sqlhtml import SQLFORM, SQLTABLE
from gluon.compileapp import LOAD, local_import_aux

from gluon.globals import Request, Response, Session
from gluon.cache import Cache
from gluon.languages import translator
from gluon.tools import Auth, Crud, Mail, Service, PluginManager

SQLDB = DAL

# API objects
request = Request()
response = Response()
session = Session()
cache = Cache(request)
T = translator(request)
local_import = lambda name, reload=False, app=request.application:\
		local_import_aux(name, reload, app)
'''

	def __init__(self):
		'''
		self.top_level: are we dealing with the original passed file?
		Pylint will recursively parse imports and models, we don't want to transform them
		'''
		self.is_pythonpath_modified = False
		self.app_model_names = []
		self.top_level = True

	def transform_module(self, module_node, web2py_path, app_name, subfolder):
		'''Determine the file type (model, controller or module) and transform it'''
		if not self.top_level:
			return module_node

		#Add web2py modules paths to sys.path
		self._add_paths(web2py_path, app_name)

		if subfolder in ['models', 'controllers']:
			self.top_level = False
			transformed_module = self._trasform(module_node, subfolder)
			self.top_level = True
		else:
			transformed_module = module_node

		return transformed_module

	def _add_paths(self, web2py_path, app_name):
		'''Add web2py module paths models path to sys.path to be able to import it from the fake code'''
		if not self.is_pythonpath_modified:
			gluon_path = os.path.join(web2py_path, 'gluon')
			site_packages_path = os.path.join(web2py_path, 'site-packages')
			app_modules_path = os.path.join(web2py_path, 'applications', app_name, 'modules')
			app_models_path = os.path.join(web2py_path, 'applications', app_name, 'models') #Add models to import them them in controllers

			for module_path in [gluon_path, site_packages_path, app_modules_path, app_models_path, web2py_path]:
				sys.path.append(module_path)

			self._fill_app_model_names(app_models_path)

			self.is_pythonpath_modified = True


	def _trasform(self, module_node, subfolder):
		'''Add globals from fake code + import code from models'''
		models_import = self._gen_models_import_code(module_node.name if subfolder == 'models' else None)
		fake_code = self.fake_code + models_import
		
		fake = AstroidBuilder(MANAGER).string_build(fake_code)
		module_node.globals.update(fake.globals)

		module_node = self._remove_unused_imports(module_node, fake)

		return module_node

	def _gen_models_import_code(self, current_model=None):
		'''Generate import code for models (only previous in alphabetical order if called by model)'''
		code = ''
		for model_name in self.app_model_names:
			if current_model and model_name == current_model:
				break
			code += 'from %s import *\n' % model_name

		return code

	def _fill_app_model_names(self, app_models_path):
		'''Save model names for later use'''
		model_files = os.listdir(app_models_path)
		model_files = [model_file for model_file in model_files if re.match(r'.+?\.py$', model_file)] #Only top-level models
		model_files = sorted(model_files) #Models are executed in alphabetical order
		self.app_model_names = [re.match(r'^(.+?)\.py$', model_file).group(1) for model_file in model_files]

	def _remove_unused_imports(self, module_node, fake_node):
		'''We import objects from fake code and from models, so pylint doesn't complain about undefined objects.
But now it complains a lot about unused imports.
We cannot suppress it, so we call VariableChecker with fake linter to intercept and collect all such error messages,
and then use them to remove unused imports.'''
		#Needed for removal of unused import messages
		sniffer = MessageSniffer() #Our linter substitution
		walker = ASTWalker(sniffer)
		var_checker = VariablesChecker(sniffer)
		comp_checker = ComparisonChecker(sniffer)
		walker.add_checker(var_checker)
		walker.add_checker(comp_checker)

		#Collect unused import messages
		sniffer.set_fake_node(fake_node)
		sniffer.check_astroid_module(module_node, walker, [], [])

		# Remove unneeded globals imported from fake code
		# XXX Disabled due to an Astroid bug where module_node.globals is module_node.locals
		# for name in sniffer.unused:
		# 	if name in fake_node.globals and \
		# 	  name in module_node.globals: #Maybe it's already deleted
		# 		del module_node.globals[name]

		return module_node

class MessageSniffer(PyLinter):
	'''Special class to mimic PyLinter to intercept messages from checkers. Here we use it to collect info about unused imports and singleton comparsons in db queries'''
	def __init__(self):
		super(MessageSniffer, self).__init__()
		self.unused = set()
		self.walker = None
		self.fake_node = None

	def set_fake_node(self, fake_node):
		'''We need fake node to distinguish real unused imports in user code from unused imports induced by our fake code'''
		self.fake_node = fake_node
		self.unused = set()

	def add_message(self, msg_descr, line=None, node=None, args=None, confidence=UNDEFINED, col_offset=None):
		'''Message interceptor'''
		if msg_descr == 'unused-wildcard-import':
			self.unused.add(args)

		elif msg_descr == 'unused-import':
			#Unused module or unused symbol from module, extract with regex
			sym_match = re.match(r'^(.+?)\ imported\ from', args)
			if sym_match:
				sym_name = sym_match.group(1)
			else:
				module_match = re.match(r'^import\ (.+?)$', args)
				assert module_match
				sym_name = module_match.group(1)

			if sym_name in self.fake_node.globals:
				self.unused.add(sym_name)

		elif msg_descr == 'singleton-comparison':
			if node.as_string().startswith("db"):
				pass # XXX Ignore singleton here

transformer = Web2PyTransformer()
