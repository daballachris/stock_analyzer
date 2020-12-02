import requests
import numpy as np
import pandas as pd

from stock_analyzer import config


def lookup_ticker(ticker: str,
                  period: int = 2,
                  period_type: str = "month",
                  frequency: int = 1,
                  frequency_type: str = "daily",
                  num_entries_to_analyze:int = 40) -> pd.DataFrame:
    """
    A function to retrieve historical price data from the TD Ameritrade API.

    Good parameters to use:
        2, month, 1, daily -> 2 months worth of daily ticks
        2, day, 1, minute -> 2 days worth of minute ticks

    :param ticker: A stock ticker. Example: 'AAPL'
    :param period: The number of periods worth of data being requested.
    :param period_type: The type of period. Valid values are "day", "month",
                        "year" or "ytd".
    :param frequency: The number of frequency types to be included in 1 data point.
    :param frequency_type: The type of frequency. Valid values are "minute", "daily",
                           "weekly", "monthly".
    :param num_entries_to_analyze: Used to look at the most recent number of data points.
                                   Ameritrade's API doesn't allow you to specify 40 days,
                                   since you have to specify 1 month or 2.
    :return: A Pandas Dataframe containing the following fields:
                                    'datetime', 'open', 'high', 'low', 'close', 'volume'
    """

    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory"
    payload = {
        'apikey': config.config['AMERITRADE']['API_KEY'],
        'period': period,
        'periodType': period_type,
        'frequency': frequency,
        'frequencyType': frequency_type,
        'needExtendedHoursData': 'false',
    }

    # TODO: Exception handling
    content = requests.get(url=endpoint, params=payload)
    data = content.json()

    ohlc = pd.DataFrame.from_records(data['candles'])

    if ohlc.empty:
        return None

    ohlc = ohlc[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    ohlc = ohlc[-num_entries_to_analyze:]

    # Reset index after slice, drop old index
    ohlc = pd.DataFrame.reset_index(ohlc, drop=True)

    return ohlc


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


class TrendLine:
    def __init__(self, b, m, touches, first_day):
        self.b = b
        self.m = m
        self.touches = touches
        self.first_day = first_day

    def __str__(self):
        return


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
