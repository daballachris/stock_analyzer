import sys
import os
import configparser

# Read user configuration data from configuration.ini
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), './', 'configuration.ini'))

if not config['AMERITRADE']['API_KEY']:
    print("You must specify your Ameritrade API key in configuration.ini first.")
    sys.exit(0)
