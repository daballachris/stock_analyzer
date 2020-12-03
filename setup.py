import configparser
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme_text = f.read()

with open('LICENSE') as f:
    license_text = f.read()

setup(
    name='stock_analyzer',
    version='0.0.1',  # TODO: Read the version from a file
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
