# pylint_web2py3
A Pylint plugin that removes Pylint's complaints about web2py code.

## Description
Web2py executes user code in special environment populated with predefined objects and types and with objects defined in model files.  It also has magic import mechanism which knows some special places where to find modules.

Pylint doesn't know about these details -- its parser is unable to find these objects and modules, resulting in a flood of laments.
This plugin:
- Adds variables defined in models to other models' and controllers' scope
- Adds definition of some predefined global objects to models and controllers
- Adds web2py module paths to sys.path, so pylint is able to find them

## Installation

You can either install this plugin from Pip:

```sh
pip install pylint_web2py3
```

Or, you can install from source:
```sh
git clone https://github.com/vinyldarkscratch/pylint_web2py3
cd pylint_web2py3
python setup.py install
```

## Enabling Plugin
- Add `--load-plugins=pylint_web2py3` to pylint options
or
- Add `load-plugins=pylint_web2py3` to your .pylintrc
