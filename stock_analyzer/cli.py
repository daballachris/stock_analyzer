from stock_analyzer import core


def main():
    stock_symbol = input("Enter stock symbol: ")

    print(f"Looking up historical price data for {stock_symbol}")
    price_history = core.lookup_ticker(stock_symbol)

    support_points, resistance_points = core.get_supports_and_resistances(price_history, 2)

    best_support_line = core.best_fit_line(price_history['low'],
                                           support_points)
    best_resistance_line = core.best_fit_line(price_history['high'],
                                              resistance_points,
                                              False)

    this_chart_data = core.Chart(stock_symbol, price_history,
                                 best_support_line, best_resistance_line,
                                 support_points, resistance_points)

    core.draw_chart(this_chart_data)


if __name__ == "__main__":
    main()
