import getopt
import sys
from stock_analyzer import core


def main():
    """
    Command Line Interface for stock_analyzer

    Usage:
        cli.py
        cli.py -h|--help
        cli.py -v|--version
        cli.py -e|--endDate
        cli.py -s|--symbol

    Options:
        -h --help Show this screen
        -v --version Show the version number
        -e --endDate Last day of data being requested. Default is today.
        -s --symbol Stock symbol you want to analyze. If not provided, you will be """\
                  """prompted for it.
    
    Examples:
        cli.py -s AAPL
        cli.py --endDate=12-1-2020 --symbol=CHTR
    """

    argv = sys.argv

    patterns = core.load_patterns()
    stock_symbol = ""
    end_date = ""

    try:
        opts, args = getopt.getopt(argv[1:], "es:hv", ["help", "endDate=", "symbol=", "version"])
    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(main.__doc__)
            sys.exit(0)
        elif opt in ('-e', '--endDate'):
            end_date = arg
        elif opt in ('-s', '--symbol'):
            stock_symbol = arg
        elif opt in ('-v', '--version'):
            from stock_analyzer import __version__
            print(__version__)
            sys.exit(0)

    if not stock_symbol:
        stock_symbol = input("Enter stock symbol: ")

    print(f"Looking up historical price data for {stock_symbol}")
    price_history = core.lookup_ticker(stock_symbol, end_date=end_date)

    if price_history is None:
        print("Nothing found!")
        sys.exit(0)

    support_points, resistance_points = \
        core.get_supports_and_resistances(price_history, 2)

    best_support_line = core.best_fit_line(price_history['low'],
                                           support_points)
    best_resistance_line = core.best_fit_line(price_history['high'],
                                              resistance_points,
                                              False)

    this_chart_data = core.Chart(stock_symbol, price_history,
                                 best_support_line, best_resistance_line,
                                 support_points, resistance_points,
                                 patterns)

    core.draw_chart(this_chart_data)


if __name__ == "__main__":
    main()
