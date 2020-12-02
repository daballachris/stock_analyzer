"""
Unit tests for core
"""

from stock_analyzer import core


def test_lookup_ticker():
    aapl_data = core.lookup_ticker('AAPL')
    assert len(aapl_data) == 40


def test_lookup_ticker_not_found():
    not_found_data = core.lookup_ticker('AAPLzjfkd')
    assert not_found_data is None
