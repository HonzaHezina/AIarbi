import pytest
from utils import config

def test_exchange_endpoints_present():
    expected = {
        'binance', 'coinbase', 'kraken', 'kucoin', 'bybit',
        'okx', 'bitfinex', 'gateio', 'coingecko', 'coinmarketcap'
    }
    configured = set(config.EXCHANGE_ENDPOINTS.keys())
    assert expected.issubset(configured), f"Missing endpoints: {expected - configured}"

def test_base_urls_and_paths():
    for name, entry in config.EXCHANGE_ENDPOINTS.items():
        assert isinstance(entry, dict), f"Entry for {name} must be a dict"
        assert entry.get('base_url'), f"{name} missing base_url"
        # public_ticker_path may be optional if prefer_ccxt or requires_api_key, but check presence
        assert 'public_ticker_path' in entry or entry.get('prefer_ccxt') or entry.get('requires_api_key'), f"{name} should define public_ticker_path or prefer_ccxt/requires_api_key"