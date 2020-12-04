import datetime
import os
import sys
import time
import requests
import json
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from mpl_finance import candlestick_ohlc
import matplotlib.dates as mdates
from stock_analyzer import config


def load_patterns() -> list:
    """A function that loads pattern data.

    Patterns are store in /data/patterns directories, in json format.

    :return: List of Pattern objects
    """

    patterns = []
    pattern_directory = os.path.join(os.path.dirname(__file__), './data/patterns')
    for filename in os.listdir(pattern_directory):
        with open(os.path.join(pattern_directory, filename)) as json_file:
            try:
                data = json.load(json_file)

                pattern_name = data['pattern_name']

                sups = []
                for json_support in data['sups']:
                    sup = TrendLineCriteria(
                        json_support['id'],
                        'SUPPORT',
                        json_support['slope_min'],
                        json_support['slope_max'],
                    )
                    sups.append(sup)

                ress = []
                for json_support in data['ress']:
                    res = TrendLineCriteria(
                        json_support['id'],
                        'RESISTANCE',
                        json_support['slope_min'],
                        json_support['slope_max'],
                    )
                    ress.append(res)

                intercepts = []
                for json_support in data['intercepts']:
                    intercept = InterceptCriteria(
                        json_support['id'],
                        json_support['sup'],
                        json_support['res'],
                        json_support['periods_till_intercept'],
                    )
                    intercepts.append(intercept)

                pattern = Pattern(pattern_name, sups, ress, intercepts)
                patterns.append(pattern)
            except (KeyError, json.decoder.JSONDecodeError) as err:
                print(f"Error in {load_patterns.__name__}: "
                      f"{filename} incorrectly formatted.", end=" ")
                print(err)

    return patterns


class TrendLineCriteria:
    """Object that stores trendline criteria for support and resistance lines"""

    def __init__(self,
                 tlc_id: int,
                 tlc_type: str,
                 slope_min: float,
                 slope_max: float):
        self.tlc_id = tlc_id
        self.tlc_type = tlc_type
        self.slope_min = slope_min
        self.slope_max = slope_max


class InterceptCriteria:
    """Object that stores intercept criteria for support and resistance lines"""

    def __init__(self,
                 int_id: int,
                 sup_id: int,
                 res_id: int,
                 periods_till_intercept: int):
        self.int_id = int_id
        self.sup_id = sup_id
        self.res_id = res_id
        self.periods_till_intercept = periods_till_intercept


class Pattern:
    """Object to store chart pattern"""

    def __init__(self, pattern_name: str,
                 sups: [TrendLineCriteria],
                 ress: [TrendLineCriteria],
                 intercepts: [InterceptCriteria]):
        self.pattern_name = pattern_name
        self.sups = sups
        self.ress = ress
        self.intercepts = intercepts

    def __str__(self):
        return f"name: {self.intercepts}, " \
               f"sups: {len(self.sups)}, " \
               f"ress: {len(self.ress)}, " \
               f"intercepts: {len(self.intercepts)}"


class TrendLine:
    """Object that defines a trendline on a chart"""

    def __init__(self, b, m, touches, first_day):
        self.b = b
        self.m = m
        self.touches = touches
        self.first_day = first_day

    def __repr__(self):
        return f"TrendLine({self.b}, {self.m}, {self.touches}, {self.first_day})"

    def intercept_point(self, other_line) -> (float, float):
        """A function to calculate the intercept point between two trendlines.

        :param other_line: A trendline
        :return: A tuple in the form (x, y). None if other_trendline is None.
        """

        if other_line is None:
            return None

        intercept_x = (self.b - other_line.b) / (other_line.m - self.m)
        intercept_y = self.b * intercept_x + self.b

        return intercept_x, intercept_y


class Chart:
    """Object that holds all information needed to draw a chart"""

    def __init__(self, symbol: str, prices: list, support: TrendLine,
                 resistance: TrendLine, support_points: list, resistance_points: list,
                 patterns: [Pattern]):

        self.symbol = symbol
        self.prices = prices
        self.support = support
        self.resistance = resistance
        self.support_points = support_points
        self.resistance_points = resistance_points
        self.patterns = patterns
        self.detected_patterns = []
        self.detect_pattern()

    def __repr__(self):
        return f"TrendLine({self.symbol}, {self.prices}, " \
               f"{self.support}, {self.resistance}), " \
               f"{self.support_points}, {self.resistance_points}" \
               f", {self.patterns})"

    def detect_pattern(self):
        for pattern in self.patterns:
            pattern_found = True

            for sup in pattern.sups:
                if self.support:
                    if sup.slope_min:
                        if self.support.m < sup.slope_min:
                            pattern_found = False
                    if sup.slope_max:
                        if self.support.m > sup.slope_max:
                            pattern_found = False
                else:
                    pattern_found = False

            for res in pattern.ress:
                if self.resistance:
                    if res.slope_min:
                        if self.resistance.m < res.slope_min:
                            pattern_found = False

                    if res.slope_max:
                        if self.resistance.m > res.slope_max:
                            pattern_found = False
                else:
                    pattern_found = False

            for intercept in pattern.intercepts:
                intercept_point = self.support.intercept_point(self.resistance)

                if intercept_point:
                    detected_periods_till_intercept = intercept_point[0] - len(
                        self.prices)

                    if intercept_point:
                        if detected_periods_till_intercept > intercept.periods_till_intercept:
                            pattern_found = False
                else:
                    pattern_found = False

            trade_criteria = None
            if pattern_found:
                height_ratio = 0.70
                buy_threshold = 0.01

                print("Pattern Found - " + pattern.pattern_name)

                resistance_price = self.resistance.m * self.support.first_day \
                                   + self.resistance.b
                support_price = self.support.m * self.support.first_day + self.support.b

                triangle_height = resistance_price - support_price
                print("Triangle Height: " + str(round(triangle_height, 2)))

                buy_price = resistance_price + (triangle_height * buy_threshold)
                print("Buy price: " + str(round(buy_price, 2)))

                sell_price = height_ratio * triangle_height + resistance_price
                print("Target price: " + str(round(sell_price, 2)))

                stop_price = resistance_price - (triangle_height * .1)
                print("Stop price: " + str(round(stop_price, 2)))

                profit_margin = (sell_price - buy_price) / buy_price * 100
                print("Profit Margin: " + str(round(profit_margin, 1)) + "%")

                loss_margin = (stop_price - buy_price) / buy_price * 100
                print("Down Side: " + str(round(loss_margin, 1)) + "%")

                self.detected_patterns.append(trade_criteria)


def lookup_prices(symbol: str,
                  period: int = 2,
                  period_type: str = "month",
                  frequency: int = 1,
                  frequency_type: str = "daily",
                  end_date: str = "",
                  num_entries_to_analyze: int = 40) -> pd.DataFrame:
    """
    A function to retrieve historical price data from the TD Ameritrade API.

    Good parameters to use:
        2, month, 1, daily -> 2 months worth of daily ticks
        2, day, 1, minute -> 2 days worth of minute ticks

    :param symbol: A stock symbol. Example: 'AAPL'
    :param period: The number of periods worth of data being requested.
    :param period_type: The type of period. Valid values are "day", "month",
                        "year" or "ytd".
    :param frequency: The number of frequency types to be included in 1 data point.
    :param frequency_type: The type of frequency. Valid values are "minute", "daily",
                           "weekly", "monthly".
    :param num_entries_to_analyze: Used to look at the most recent number of data points.
                                   Ameritrade's API doesn't allow you to specify 40 days,
                                   since you have to specify 1 month or 2.
    :param end_date: The last date of the data being requested.
    :return: A Pandas Dataframe containing the following fields:
                                    'datetime', 'open', 'high', 'low', 'close', 'volume'
    """

    if end_date == "":
        end_date = int(round(time.time() * 1000))
    else:
        end_date = int(
            round(datetime.datetime.strptime(end_date, '%m-%d-%Y').timestamp() * 1000))

    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory"
    payload = {
        'apikey': config.config['AMERITRADE']['API_KEY'],
        'period': period,
        'periodType': period_type,
        'frequency': frequency,
        'frequencyType': frequency_type,
        'endDate': end_date,
        'needExtendedHoursData': 'false',
    }

    # TODO: Add more exception handling
    try:
        content = requests.get(url=endpoint, params=payload)
    except requests.exceptions.ProxyError:
        print("ProxyError, maybe you need to connect to to your proxy server?")
        sys.exit()

    try:
        data = content.json()
    except json.decoder.JSONDecodeError:
        print("Error, API Request Returned: " + str(content))
        print("Endpoint: " + endpoint)
        print("payload:: " + str(payload))
        return None

    candle_data = pd.DataFrame.from_records(data['candles'])

    if candle_data.empty:
        return None

    candle_data = candle_data[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    candle_data = candle_data[-num_entries_to_analyze:]
    candle_data = pd.DataFrame.reset_index(candle_data, drop=True)

    # Convert datetime TODO: Understand the different timestamps used
    candle_data['datetime'] = mdates.epoch2num(candle_data['datetime'] / 1000)

    return candle_data


def get_supports_and_resistances(ltp: np.array, n: int) -> (list, list):
    """
    This function takes a numpy array of last traded price and returns a list of support
    and resistance levels respectively.

    :param ltp:
    :param n: is the number of entries to be scanned.
    :return: A tuple of lists of points. First item is the support list, second is the
             resistance list.
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


def best_fit_line(prices: list, derivatives: list, is_support: bool = True) -> TrendLine:
    """
    A function to find the best support/resistance line for a set of prices.

    :param prices: A list of prices.
    :param derivatives: A list of identified local minima/maxima.
    :param is_support: Boolean to indicate if this is a support line or not.
    :return: Trendline object.
    """

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
                    best_trendline = TrendLine(b, m, best_count,
                                               derivatives[derivative_start])

    return best_trendline


def draw_chart(chart_data: Chart) -> None:
    """
    A function that draws the data on a matplotlib chart.

    :param chart_data: A Chart object containing all data needed to render a chart.
    :return: None.
    """

    ax1 = plt.subplot2grid((1, 1), (0, 0))
    candlestick_ohlc(ax1, chart_data.prices.values, width=0.0001, colorup='g',
                     colordown='r')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.title(chart_data.symbol)

    for label in ax1.xaxis.get_ticklabels():
        label.set_rotation(45)

    # Plot points for each maxima/minima found
    for i in chart_data.support_points:
        plt.plot(chart_data.prices['datetime'][i], chart_data.prices['low'][i], 'b+')

    for i in chart_data.resistance_points:
        plt.plot(chart_data.prices['datetime'][i], chart_data.prices['high'][i], 'y+')

    axes = plt.gca()

    ymin, ymax = axes.get_ylim()
    xmin, xmax = axes.get_xlim()

    x_vals = np.array(range(len(chart_data.prices['datetime'])))
    x_dates = np.array(chart_data.prices['datetime'])

    if chart_data.resistance:
        y_vals_res = chart_data.resistance.m * x_vals + chart_data.resistance.b
        plt.plot(x_dates, y_vals_res, '--')

    if chart_data.support:
        y_vals_sup = chart_data.support.m * x_vals + chart_data.support.b
        plt.plot(x_dates, y_vals_sup, '--')

    # re-set the y limits
    axes.set_ylim(ymin, ymax)
    axes.set_xlim(xmin, xmax)

    print("Close chart to continue...")
    plt.show()
