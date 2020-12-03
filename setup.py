import os
import codecs
import configparser
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme_text = f.read()

with open('LICENSE') as f:
    license_text = f.read()


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

setup(
    name='stock_analyzer',
    version=get_version('stock_analyzer/__init__.py'),
    description='A package for analyzing stock patterns',
    long_description=readme_text,
    author='Christopher Duane Smith',
    entry_points={'console_scripts': ['stock_analyzer=stock_analyzer.cli:main']},
    author_email='daballachris@protonmail.com',
    url='https://github.com/daballachris/stock_analyzer',
    license=license_text,
    packages=find_packages(exclude=('tests',)),
)

config = configparser.ConfigParser()
config['AMERITRADE'] = {'API_KEY': ''}

with open('./stock_analyzer/configuration.ini', 'w') as config_file:
    config.write(config_file)
