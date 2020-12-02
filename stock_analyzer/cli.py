from stock_analyzer import core
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from mpl_finance import candlestick_ohlc


def main():
    stock_symbol = input("Enter stock symbol: ")

    print(f"Looking up historical price data for {stock_symbol}")
    price_history = core.lookup_ticker(stock_symbol)

    # Convert datetime (TODO: Understand the different timestamps used)
    price_history['datetime'] = mdates.epoch2num(price_history['datetime'] / 1000)

    support_points, resistance_points = core.get_supports_and_resistances(price_history, 2)

    best_support_line = core.best_fit_line(price_history['low'], support_points)
    best_resistance_line = core.best_fit_line(price_history['high'], resistance_points, False)

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


if __name__ == "__main__":
    main()
