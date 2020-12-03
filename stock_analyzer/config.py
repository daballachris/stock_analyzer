import os
import configparser

# Read user configuration data from configuration.ini
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), './', 'configuration.ini'))
