# -*- coding: utf-8 -*-
import pylint_web2py3
from setuptools import setup, find_packages

_packages = find_packages()

with open('README.md') as f:
	readme = f.read()
with open('requirements.txt') as f:
	requires = [line.strip() for line in f if line.strip()]

setup(
	name=pylint_web2py3.__name__,
	url='https://github.com/vinyldarkscratch/pylint_web2py3',
	version=pylint_web2py3.__version__,
	description=pylint_web2py3.__doc__,
	long_description=readme,
	long_description_content_type="text/markdown",
	author=pylint_web2py3.__author__[0],
	author_email=pylint_web2py3.__email__[0],
	maintainer=pylint_web2py3.__maintainer__,
	maintainer_email=pylint_web2py3.__email__[0],
	license='http://www.gnu.org/copyleft/gpl.html',
	keywords='pylint web2py plugin',
	platforms=['any'],
	packages=_packages,
	install_requires=requires,
	zip_safe=False,
)
