from setuptools import setup, find_packages

_version = '0.1.2'
_packages = find_packages()
_short_description = 'pylint-web2py is a Pylint plugin to help reduce false ' \
    'positives due to web2py implicit imports'

setup(
    name='pylint-web2py',
    url='https://github.com/dsludwig/pylint-web2py',
    author='Derek Ludwig',
    author_email='derek.s.ludwig@gmail.com',
    description=_short_description,
    version=_version,
    packages=_packages,
    dependency_links=['hg+https://bitbucket.org/logilab/astroid/get/tip.zip#egg=astroid-1.2.2'],
    install_requires=['astroid>=1.2.2', #Hack for pip to use mercurial version. When 1.2.2 is out, pip will use it
                      'pylint>=1.2.0'],
    license='GPLv2',
    keywords='pylint web2py plugin',
)
