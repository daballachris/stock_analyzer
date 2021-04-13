import sys
import os
import configparser

# Read user configuration data from configuration.ini
config = configparser.ConfigParser()
file_name = './stock_analyzer/configuration.ini'
config.read(file_name)

if not config['AMERITRADE']['API_KEY']:
    print("You must specify your Ameritrade API key in configuration.ini first.")
    sys.exit(0)
