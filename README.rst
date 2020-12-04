**************
Stock Analyzer
**************

A Python package for analyzing stock patterns.

Installation
############
After running setup.py, configuration.ini will be created. Enter your TD Ameritrade developer API key here.


Usage
#####
    Running from the command line:
    cli.py
    cli.py -h|--help
    cli.py -v|--version
    cli.py -e|--endDate
    cli.py -s|--symbol

    Options:
        -h --help Show this screen
        -v --version Show the version number
        -e --endDate Last day of data being requested. Default is today.
        -s --symbol Stock symbol you want to analyze. If not provided, you will be prompted for it.
    
    Examples:
        cli.py -s AAPL
        cli.py --endDate=12-1-2020 --symbol=CHTR

TD Ameritrade API
#################

You can create a free developer account and register for an API key `here <https://developer.tdameritrade.com/apis/>`_.