from setuptools import setup, find_packages

_version = '0.3'
_packages = find_packages()
_short_description = 'pylint-web2py2 is a disciple of pylint-web2py with better web2py support'

setup(
    name='pylint-web2py2',
    url='https://github.com/flagist0/pylint-web2py',
    author='Alexander Presnyakov',
    author_email='flagist0@gmail.com',
    description=_short_description,
    version=_version,
    packages=_packages,
    install_requires=['astroid>=1.3.0',
                      'pylint>=1.2.0'],
    license='GPLv2',
    keywords='pylint web2py plugin',
)
