import numpy as np
import pandas as pd
import requests
import configparser

config = configparser.ConfigParser()
config['API_KEY'] = ''

with open('./configuration') as config_file:
    config.write(config_file)


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
    end_date = ''

    endpoint = f"https://api.tdameritrade.com/v1/marketdata/{ticker}/pricehistory"
    payload = {
        'apikey': configuration['API_KEY'],
        'period': tda_period,
        'periodType': tda_period_type,
        'frequency': tda_frequency,
        'frequencyType': tda_frequency_type,
        'needExtendedHoursData': 'false',
        'endDate': end_date,
    }

    content = requests.get(url = endpoint, params = payload)
    data = content.json()
    ohlc = pd.DataFrame.from_records(data['candles'])
    ohlc = ohlc[['datetime', 'open', 'high', 'low', 'close', 'volume']]

    return ohlc


if __name__ == "__main__":
    print("nothing")
