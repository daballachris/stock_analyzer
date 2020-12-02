import time
import requests
import configparser
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates

# Read user configuration data from configuration.ini
config = configparser.ConfigParser()
config.read('configuration.ini')

num_entries_to_analyze = 40


def get_supports_and_resistances(ltp: np.array, n: int) -> (list, list):
    """
    This function takes a numpy array of last traded price and returns a list of support
    and resistance levels respectively.

    :param ltp:
    :param n: is the number of entries to be scanned.
    :return: A tuple of lists of points. First item is the support list, second is the resistance list.
    """
    from scipy.signal import savgol_filter as smooth

    # converting n to a nearest even number
    if n % 2 != 0:
        n += 1

    highs = ltp['high']
    lows = ltp['low']

    n_ltp = ltp.shape[0]

    # smoothening the curve
    highs_s = smooth(highs, (n + 1), 2)
    lows_s = smooth(lows, (n + 1), 2)

    # taking a simple derivative
    highs_d = np.zeros(n_ltp)
    highs_d[1:] = np.subtract(highs_s[1:], highs_s[:-1])
    lows_d = np.zeros(n_ltp)
    lows_d[1:] = np.subtract(lows_s[1:], lows_s[:-1])

    resistance = []
    support = []

    for i in range(n_ltp - n):
        lows_sl = lows_d[i:int(i + n)]
        lows_first = lows_sl[:int(n / 2)]  # first half
        lows_last = lows_sl[int(n / 2):]  # second half

        highs_sl = highs_d[i:int(i + n)]
        highs_first = highs_sl[:int(n / 2)]  # first half
        highs_last = highs_sl[int(n / 2):]  # second half

        r_1 = np.sum(highs_first > 0)
        r_2 = np.sum(highs_last < 0)

        s_1 = np.sum(lows_first < 0)
        s_2 = np.sum(lows_last > 0)

        # local maxima detection
        if (r_1 == (n / 2)) and (r_2 == (n / 2)):
            resistance.append(i + (int(n / 2) - 1))

        # local minima detection
        if (s_1 == (n / 2)) and (s_2 == (n / 2)):
            support.append(i + (int(n / 2) - 1))

    return support, resistance


def lookup_ticker(ticker: str) -> pd.DataFrame:
    """
    A function to retrieve historical price data from the TD Ameritrade API.

    :param ticker: A stock ticker. Example: 'AAPL'
    :return: A Pandas Dataframe containing the following fields:
                                    'datetime', 'open', 'high', 'low', 'close', 'volume'
    """

    print(f"Getting historical price data for {ticker}")

    # 2, month, 1, daily for good day candles
    # 2, day, 1, minute for day trading minutes
    tda_period = 3
    tda_period_type = "month"  # day, month, year, ytd
    tda_frequency = 1
    tda_frequency_type = "daily"  # minute, daily, weekly, monthly
    end_date = int(round(time.time() * 1000))

    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory"
    payload = {
        'apikey': config['AMERITRADE']['API_KEY'],
        'period': tda_period,
        'periodType': tda_period_type,
        'frequency': tda_frequency,
        'frequencyType': tda_frequency_type,
        'needExtendedHoursData': 'false',
        'end_date': end_date,
    }

    content = requests.get(url=endpoint, params=payload)
    data = content.json()

    ohlc = pd.DataFrame.from_records(data['candles'])
    ohlc = ohlc[['datetime', 'open', 'high', 'low', 'close', 'volume']]

    # Only look at last X entries
    ohlc = ohlc[-num_entries_to_analyze:]
    ohlc = pd.DataFrame.reset_index(ohlc, drop=True)  # Reset index, drop old index
    ohlc['datetime'] = mdates.epoch2num(ohlc['datetime'] / 1000)

    return ohlc


class TrendLine:
    def __init__(self, b, m, touches, first_day):
        self.b = b
        self.m = m
        self.touches = touches
        self.first_day = first_day


def best_fit_line(prices: list, derivatives: list, is_support: bool = True) -> TrendLine:

    best_count = 0
    best_trendline = None

    margin = 0.05
    price_margin = margin * (max(prices) - min(prices))

    # Try every combination of derivative points
    for derivative_start in range(len(derivatives)):
        # print(str(derivative_start), end=", ")
        for derivative_end in range(derivative_start + 1, len(derivatives)):

            # print(str(derivative_end), end=", ")

            # Calculate slope and y-intercept for these 2 derivative points
            m = (prices[derivatives[derivative_end]]
                 - prices[derivatives[derivative_start]]) / (
                        derivatives[derivative_end]
                        - derivatives[derivative_start])
            b = prices[derivatives[derivative_end]] - m * derivatives[derivative_end]

            # Loop through all prices to make sure none pass through this line
            for k in range(len(prices)):
                test_y = m * k + b
                if is_support:
                    test_y = test_y - price_margin
                else:
                    test_y = test_y + price_margin

                if prices[k] < test_y and is_support \
                        or prices[k] > test_y and not is_support:
                    break

            else:
                # No prices broke through the trendline, so count the number of times the
                # prices touch (come within price_margin) the trendline

                touch_count = 0
                for k in range(len(derivatives)):
                    test_y = m * derivatives[k] + b
                    if test_y - price_margin <= \
                            prices[derivatives[k]] <= test_y + price_margin:
                        touch_count += 1

                if touch_count >= best_count:
                    best_count = touch_count
                    best_trendline = TrendLine(b, m, best_count, derivatives[derivative_start])

    return best_trendline


if __name__ == "__main__":
    stock_symbol = input("Enter stock symbol: ")
    price_history = lookup_ticker(stock_symbol)

    support_points, resistance_points = get_supports_and_resistances(price_history, 2)

    best_support_line = best_fit_line(price_history['low'], support_points)
    best_resistance_line = best_fit_line(price_history['high'], resistance_points, False)

    fig = plt.figure()
    ax1 = plt.subplot2grid((1, 1), (0, 0))
    candlestick_ohlc(ax1, price_history.values, width=0.0001, colorup='g', colordown='r')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.title(stock_symbol)

    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(45)

    # Plot points for each maxima/minima found
    for i in support_points:
        plt.plot(price_history['datetime'][i], price_history['low'][i], 'b+')

    for i in resistance_points:
        plt.plot(price_history['datetime'][i], price_history['high'][i], 'y+')

    axes = plt.gca()

    ymin, ymax = axes.get_ylim()
    xmin, xmax = axes.get_xlim()

    x_vals = np.array(range(len(price_history['datetime'])))
    x_dates = np.array(price_history['datetime'])

    if best_resistance_line:
        y_vals_res = best_resistance_line.m * x_vals + best_resistance_line.b
        plt.plot(x_dates, y_vals_res, '--')

    if best_support_line:
        y_vals_sup = best_support_line.m * x_vals + best_support_line.b
        plt.plot(x_dates, y_vals_sup, '--')

    # re-set the y limits
    axes.set_ylim(ymin, ymax)
    axes.set_xlim(xmin, xmax)

    plt.show()
