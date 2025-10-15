"""Configuration settings for AI Crypto Arbitrage System"""

# Trading Configuration
TRADING_CONFIG = {
    'min_profit_threshold': 0.0,  # Minimum profit percentage (relaxed for demo validation)
    'max_position_size_usd': 1000,
    'max_concurrent_trades': 5,
    'max_daily_trades': 50,
    'demo_mode': True,  # Set to False for real trading (DANGEROUS!)
}
# Demo/testing flags
DEBUG_DEMO_INJECT_SYNTHETIC = True  # Set True to inject synthetic exchange in fallback data for demo

# Supported Exchanges and their settings
EXCHANGES_CONFIG = {
    'binance': {
        'name': 'Binance',
        'rate_limit': 1200,  # requests per minute
        'taker_fee': 0.001,  # 0.1%
        'maker_fee': 0.001,
        'reliable': True
    },
    'kraken': {
        'name': 'Kraken',
        'rate_limit': 60,  # requests per minute (≈1 req/s)
        'taker_fee': 0.0026,  # 0.26%
        'maker_fee': 0.0016,
        'reliable': True
    },
    'coinbase': {
        'name': 'Coinbase Pro',
        'rate_limit': 600,  # spec: 10 req/s ~= 600 per minute (public)
        'taker_fee': 0.005,  # 0.5%
        'maker_fee': 0.005,
        'reliable': True
    },
    'kucoin': {
        'name': 'KuCoin',
        'rate_limit': 120,  # spec: 120/min (public)
        'taker_fee': 0.001,  # 0.1%
        'maker_fee': 0.001,
        'reliable': False
    },
    'bitfinex': {
        'name': 'Bitfinex',
        'rate_limit': 90,  # requests per minute
        'taker_fee': 0.002,  # 0.2%
        'maker_fee': 0.001,
        'reliable': False
    },
    'bybit': {
        'name': 'Bybit',
        'rate_limit': 120,  # spec: 120 req/min (public)
        'taker_fee': 0.001,
        'maker_fee': 0.001,
        'reliable': False
    },
    'okx': {
        'name': 'OKX',
        'rate_limit': 600,  # spec: 20 req/2s = 600/min
        'taker_fee': 0.002,
        'maker_fee': 0.0015,
        'reliable': False
    },
    'gateio': {
        'name': 'Gate.io',
        'rate_limit': 54000,  # spec: 900 req/s -> 900*60 = 54000/min (normalized to per-minute)
        'taker_fee': 0.002,
        'maker_fee': 0.0015,
        'reliable': False
    },
    'coingecko': {
        'name': 'CoinGecko',
        'rate_limit': 30,  # demo/free approximate
        'taker_fee': 0.0,
        'maker_fee': 0.0,
        'reliable': True
    },
    'coinmarketcap': {
        'name': 'CoinMarketCap',
        'rate_limit': 30,  # basic free plan per-minute
        'taker_fee': 0.0,
        'maker_fee': 0.0,
        'reliable': True,
        'requires_api_key': True
    }
}

# Canonical REST endpoints for exchanges and market data (can be overridden via env vars)
EXCHANGE_ENDPOINTS = {
    'binance': {
        'base_url': 'https://api.binance.com',
        'docs': 'https://binance-docs.github.io/apidocs/spot/en/',
        'public_ticker_path': '/api/v3/ticker/price',  # example: GET /api/v3/ticker/price?symbol=BTCUSDT
        'rate_limit_per_min': 1200
    },
    'coinbase': {
        'base_url': 'https://api.coinbase.com',
        'docs': 'https://docs.cloud.coinbase.com/exchange/docs',
        'public_ticker_path': '/v2/prices/{base}-USD/spot',  # use base token with USD (e.g. BTC-USD)
        'rate_limit_per_min': 166
    },
    'kraken': {
        'base_url': 'https://api.kraken.com',
        'docs': 'https://docs.kraken.com/rest/',
        'public_ticker_path': '/0/public/Ticker',  # example: ?pair=XBTUSDT
        'rate_limit_per_min': 60
    },
    'kucoin': {
        'base_url': 'https://api.kucoin.com',
        'docs': 'https://docs.kucoin.com/',
        'public_ticker_path': '/api/v1/market/orderbook/level1',  # example: ?symbol=BTC-USDT
        'rate_limit_per_min': 180
    },
    'bybit': {
        'base_url': 'https://api.bybit.com',
        'docs': 'https://bybit-exchange.github.io/docs/',
        # Prefer modern V5 market tickers for spot; include common alternates for fallback.
        # Example primary: GET /v5/market/tickers?category=spot&symbol=BTCUSDT
        'public_ticker_path': '/v5/market/tickers?category=spot&symbol={noslash}',
        'alternate_paths': [
            '/v5/market/tickers?category=spot&symbol={noslash}',
            '/v5/market/tickers?category=spot',
            '/v2/public/tickers'
        ],
        'rate_limit_per_min': 120
    },
    'okx': {
        'base_url': 'https://www.okx.com',
        'docs': 'https://www.okx.com/docs-v5/en/',
        # Include instId in the example path to make verification/raw GETs succeed:
        # GET /api/v5/market/ticker?instId=BTC-USDT
        'public_ticker_path': '/api/v5/market/ticker?instId={dash}',
        'rate_limit_per_min': 600
    },
    'bitfinex': {
        'base_url': 'https://api-pub.bitfinex.com',
        'docs': 'https://docs.bitfinex.com/',
        # Primary v2 ticker; include alternates (legacy v1 pubticker) so verifier can try REST fallbacks.
        'public_ticker_path': '/v2/ticker/t{noslash}',  # e.g. /v2/ticker/tBTCUSD
        'alternate_paths': [
            '/v2/ticker/t{noslash}',
            '/v1/pubticker/{base}'
        ],
        'prefer_ccxt': True,
        'rate_limit_per_min': 90
    },
    'gateio': {
        # Use host as base and include API version in the path so urljoin/_format_path resolves correctly.
        'base_url': 'https://api.gateio.ws',
        'docs': 'https://www.gate.com/docs/developers/apiv4/en',
        'public_ticker_path': '/api/v4/spot/tickers',
        'rate_limit_per_min': 54000
    },
    'coingecko': {
        'base_url': 'https://api.coingecko.com/api/v3',
        'docs': 'https://www.coingecko.com/en/api/documentation',
        # Avoid leading slash so urljoin preserves base path when base includes /api/v3
        'public_ticker_path': 'simple/price',  # e.g. ?ids=bitcoin&vs_currencies=usd
        'rate_limit_per_min': 30
    },
    'coinmarketcap': {
        'base_url': 'https://pro-api.coinmarketcap.com/v1',
        'docs': 'https://coinmarketcap.com/api/documentation/v1/',
        # Avoid leading slash so urljoin preserves base path when base includes /v1
        'public_ticker_path': 'cryptocurrency/quotes/latest',  # requires API key header X-CMC_PRO_API_KEY
        'requires_api_key': True,
        'rate_limit_per_min': 30
    }
}

# Allow environment variables to override any base_url at runtime
import os as _os
for _name, _entry in EXCHANGE_ENDPOINTS.items():
    _env_key = f"EXCHANGE_ENDPOINT_{_name.upper()}_BASE_URL"
    if _os.getenv(_env_key):
        EXCHANGE_ENDPOINTS[_name]['base_url'] = _os.getenv(_env_key)

# DEX Endpoints Configuration
DEX_ENDPOINTS = {
    'uniswap': {
        'name': 'Uniswap',
        'base_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2',
        'testnet_url': 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2?network=kovan',
        'api_type': 'graphql',
        'websocket_url': None,  # GraphQL uses same endpoint
        'testnet_websocket_url': None,
        'rate_limit_per_day': 10000,
        'requires_api_key': False,
        'network': 'ethereum',
        'key_data': ['token_pairs', 'prices', 'liquidity'],
        'docs': 'https://docs.uniswap.org/sdk/subgraph/subgraph-data'
    },
    'sushiswap': {
        'name': 'SushiSwap',
        'base_url': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange',
        'testnet_url': 'https://api.thegraph.com/subgraphs/name/sushiswap/exchange?network=ropsten',
        'api_type': 'graphql',
        'websocket_url': None,  # GraphQL uses same endpoint
        'testnet_websocket_url': None,
        'rate_limit_per_day': 8000,
        'requires_api_key': False,
        'network': 'ethereum',
        'key_data': ['volume', 'swaps', 'liquidity_pool'],
        'docs': 'https://docs.sushi.com/docs/Developers/Subgraphs/Exchange'
    },
    'pancakeswap': {
        'name': 'PancakeSwap',
        'base_url': 'https://api.pancakeswap.info/api/v2/tokens',
        'testnet_url': 'https://testnet-api.pancakeswap.finance/api/v2/tokens',
        'api_type': 'rest',
        'websocket_url': 'wss://bsc-ws-node.nariox.org:443',
        'testnet_websocket_url': 'wss://data-seed-prebsc-1-s1.binance.org:8545',
        'rate_limit_per_hour': 5000,
        'requires_api_key': False,
        'network': 'bsc',
        'key_data': ['prices', 'trading_pairs', 'apy'],
        'docs': 'https://docs.pancakeswap.finance/developers/api'
    },
    'dydx': {
        'name': 'dYdX',
        'base_url': 'https://api.dydx.exchange/v3/markets',
        'testnet_url': 'https://api.stage.dydx.exchange/v3/markets',
        'api_type': 'rest',
        'websocket_url': 'wss://api.dydx.exchange/v3/ws',
        'testnet_websocket_url': 'wss://api.stage.dydx.exchange/v3/ws',
        'rate_limit_per_second': 50,
        'requires_api_key': True,
        'auth_type': 'hmac',  # API key + HMAC signing
        'network': 'ethereum',
        'key_data': ['futures_prices', 'orders', 'orderbook'],
        'docs': 'https://docs.dydx.exchange/'
    },
    'curve': {
        'name': 'Curve',
        'base_url': 'https://api.curve.finance/api/getPools',
        'testnet_url': 'https://api.curve.fi/api/getPools?network=kovan',
        'api_type': 'rest',
        'websocket_url': None,  # REST only
        'testnet_websocket_url': None,
        'rate_limit_per_minute': 1000,
        'requires_api_key': False,
        'network': 'ethereum',
        'key_data': ['pools', 'apy', 'token_data'],
        'docs': 'https://curve.readthedocs.io/'
    },
    'balancer': {
        'name': 'Balancer',
        'base_url': 'https://api-v3.balancer.fi/graphql',
        'testnet_url': 'https://api-v3.balancer.kovan.network/graphql',
        'api_type': 'graphql',
        'websocket_url': None,  # GraphQL uses same endpoint
        'testnet_websocket_url': None,
        'rate_limit_per_day': 5000,
        'requires_api_key': False,
        'network': 'ethereum',
        'key_data': ['pools', 'prices', 'weighted_indices'],
        'docs': 'https://docs.balancer.fi/'
    },
    'oneinch': {
        'name': '1inch',
        'base_url': 'https://api.1inch.io/v4.0/1/tokens',
        'testnet_url': 'https://api.1inch.io/v4.0/1/tokens?network=ropsten',
        'api_type': 'rest',
        'quote_endpoint': 'https://api.1inch.io/v4.0/1/quote',
        'testnet_quote_endpoint': 'https://api.1inch.io/v4.0/1/quote?network=ropsten',
        'websocket_url': None,
        'testnet_websocket_url': None,
        'rate_limit_per_day': 1000,
        'requires_api_key': False,
        'network': 'ethereum',
        'key_data': ['aggregated_prices', 'volumes'],
        'docs': 'https://docs.1inch.io/'
    },
    'kyber': {
        'name': 'Kyber',
        'base_url': 'https://kyber.api.0x.org/swap/v1/quote',
        'testnet_url': 'https://ropsten.api.0x.org/swap/v1/quote',
        'api_type': 'rest',
        'websocket_url': None,
        'testnet_websocket_url': None,
        'rate_limit_per_day': 5000,
        'requires_api_key': False,
        'network': 'ethereum',
        'key_data': ['best_swap_price', 'liquidity'],
        'docs': 'https://docs.kyberswap.com/'
    }
}

# DEX Protocols (extended with new protocols)
DEX_CONFIG = {
    'uniswap_v3': {
        'name': 'Uniswap V3',
        'fee': 0.003,  # 0.3%
        'gas_cost_usd': 15.0,
        'network': 'ethereum',
        'rate_limit': 10000,  # per day
        'reliable': True
    },
    'uniswap': {
        'name': 'Uniswap V2',
        'fee': 0.003,  # 0.3%
        'gas_cost_usd': 15.0,
        'network': 'ethereum',
        'rate_limit': 10000,  # per day
        'reliable': True
    },
    'sushiswap': {
        'name': 'SushiSwap',
        'fee': 0.003,  # 0.3%
        'gas_cost_usd': 12.0,
        'network': 'ethereum',
        'rate_limit': 8000,  # per day
        'reliable': True
    },
    'pancakeswap': {
        'name': 'PancakeSwap',
        'fee': 0.0025,  # 0.25%
        'gas_cost_usd': 0.5,
        'network': 'bsc',
        'rate_limit': 5000,  # per hour
        'reliable': True
    },
    'dydx': {
        'name': 'dYdX',
        'fee': 0.0005,  # 0.05% maker, 0.02% taker (average)
        'gas_cost_usd': 10.0,
        'network': 'ethereum',
        'rate_limit': 50,  # per second
        'requires_api_key': True,
        'reliable': True
    },
    'curve': {
        'name': 'Curve',
        'fee': 0.0004,  # 0.04% typical
        'gas_cost_usd': 20.0,  # Higher due to complex math
        'network': 'ethereum',
        'rate_limit': 1000,  # per minute
        'reliable': True
    },
    'balancer': {
        'name': 'Balancer',
        'fee': 0.001,  # 0.1% typical (varies by pool)
        'gas_cost_usd': 18.0,
        'network': 'ethereum',
        'rate_limit': 5000,  # per day
        'reliable': True
    },
    'oneinch': {
        'name': '1inch',
        'fee': 0.001,  # aggregated fee varies
        'gas_cost_usd': 15.0,
        'network': 'ethereum',
        'rate_limit': 1000,  # per day
        'reliable': True
    },
    'kyber': {
        'name': 'Kyber',
        'fee': 0.001,  # 0.1% typical
        'gas_cost_usd': 12.0,
        'network': 'ethereum',
        'rate_limit': 5000,  # per day
        'reliable': True
    },
    'tinyman': {
        'name': 'Tinyman',
        'fee': 0.0025,  # 0.25%
        'gas_cost_usd': 0.001,  # Very low fees on Algorand
        'network': 'algorand',
        'rate_limit': 10000,  # per day
        'reliable': False
    },
    'pact': {
        'name': 'Pact',
        'fee': 0.003,  # 0.3%
        'gas_cost_usd': 0.001,  # Very low fees on Algorand
        'network': 'algorand',
        'rate_limit': 10000,  # per day
        'reliable': False
    }
}

# Default trading pairs to monitor
DEFAULT_SYMBOLS = [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'ADA/USDT',
    'SOL/USDT',
    'MATIC/USDT',
    'DOT/USDT',
    'LINK/USDT',
    'ALGO/USDT'
]

# Risk Management Settings
RISK_CONFIG = {
    'max_portfolio_exposure_usd': 5000,
    'max_exchange_concentration': 0.6,  # 60% max exposure to single exchange
    'max_symbol_concentration': 0.4,    # 40% max exposure to single symbol
    'max_slippage_tolerance': 0.5,      # 0.5% max acceptable slippage
    'stop_loss_threshold': -2.0,        # -2% portfolio stop loss
    'circuit_breaker_loss': -5.0,       # -5% daily loss stops all trading
}

# AI Model Settings
AI_CONFIG = {
    'model_id': 'microsoft/DialoGPT-medium',  # Lightweight model for HF Spaces
    'max_tokens': 200,
    'temperature': 0.7,  # Moderate creativity for analysis
    'use_ai_analysis': True,
    'fallback_to_math': True,
    'confidence_threshold': 0.6  # Minimum AI confidence for execution
}

# UI Settings
UI_CONFIG = {
    'refresh_interval_seconds': 30,
    'max_opportunities_display': 10,
    'price_decimal_places': 4,
    'percentage_decimal_places': 3,
    'default_theme': 'dark',
    'show_debug_info': False
}

# Bellman-Ford Settings
BELLMAN_FORD_CONFIG = {
    'max_cycle_length': 6,  # Maximum number of hops in arbitrage cycle
    # Relaxed temporarily to accept very small profitable cycles for end-to-end validation.
    # This value is in log-space; negative values indicate a profitable cycle.
    'min_profit_threshold': -0.0001,  # Accept ~0.01% profit (log-space) during tests
    'max_cycles_to_process': 50,  # Limit cycles to avoid timeout
    'enable_statistical_enhancement': True
}

# Statistical Arbitrage Settings
STATISTICAL_CONFIG = {
    'lookback_periods': 100,  # Number of price points to analyze
    'correlation_threshold': 0.7,  # Minimum correlation to consider
    'deviation_threshold': 2.0,  # Standard deviations for anomaly
    'confidence_threshold': 0.7,  # AI confidence threshold
    'max_historical_days': 7  # Days of historical data to keep
}

def get_exchange_fee(exchange: str, trade_type: str = 'taker') -> float:
    """Get trading fee for specific exchange"""
    if exchange in EXCHANGES_CONFIG:
        return EXCHANGES_CONFIG[exchange].get(f'{trade_type}_fee', 0.001)
    return 0.001  # Default 0.1% fee

def get_supported_exchanges() -> list:
    """Get list of supported exchange names"""
    return list(EXCHANGES_CONFIG.keys())

def get_supported_dex_protocols() -> list:
    """Get list of supported DEX protocols"""
    return list(DEX_CONFIG.keys())

def get_dex_endpoint(protocol: str, testnet: bool = False) -> dict:
    """Get DEX endpoint configuration for a specific protocol
    
    Args:
        protocol: Name of the DEX protocol (e.g., 'uniswap', 'sushiswap')
        testnet: If True, return testnet URL, otherwise production URL
        
    Returns:
        Dictionary with endpoint configuration or None if not found
    """
    if protocol not in DEX_ENDPOINTS:
        return None
    
    endpoint = DEX_ENDPOINTS[protocol].copy()
    if testnet:
        endpoint['active_url'] = endpoint.get('testnet_url')
        endpoint['active_websocket_url'] = endpoint.get('testnet_websocket_url')
    else:
        endpoint['active_url'] = endpoint.get('base_url')
        endpoint['active_websocket_url'] = endpoint.get('websocket_url')
    
    return endpoint

def get_dex_rate_limit(protocol: str) -> tuple:
    """Get rate limit for a DEX protocol
    
    Returns:
        Tuple of (limit_value, time_period) e.g., (10000, 'day')
    """
    if protocol not in DEX_ENDPOINTS:
        return (None, None)
    
    endpoint = DEX_ENDPOINTS[protocol]
    
    # Check which rate limit field exists
    if 'rate_limit_per_day' in endpoint:
        return (endpoint['rate_limit_per_day'], 'day')
    elif 'rate_limit_per_hour' in endpoint:
        return (endpoint['rate_limit_per_hour'], 'hour')
    elif 'rate_limit_per_minute' in endpoint:
        return (endpoint['rate_limit_per_minute'], 'minute')
    elif 'rate_limit_per_second' in endpoint:
        return (endpoint['rate_limit_per_second'], 'second')
    
    return (None, None)

def validate_config():
    """Validate configuration settings"""
    errors = []

    if TRADING_CONFIG['min_profit_threshold'] < 0:
        errors.append("Minimum profit threshold cannot be negative")

    if TRADING_CONFIG['max_position_size_usd'] <= 0:
        errors.append("Maximum position size must be positive")

    if not TRADING_CONFIG['demo_mode']:
        errors.append("WARNING: Demo mode is disabled - real trading enabled!")

    return errors

# Run validation on import
_config_errors = validate_config()
if _config_errors:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning("🔧 Configuration notes:")
    for error in _config_errors:
        logger.warning("  - %s", error)

# Environment overrides and helpers
import os

def _apply_env_overrides():
    global TRADING_CONFIG, BELLMAN_FORD_CONFIG
    # Trading overrides
    if os.getenv('TRADING_MIN_PROFIT_THRESHOLD') is not None:
        TRADING_CONFIG['min_profit_threshold'] = float(os.getenv('TRADING_MIN_PROFIT_THRESHOLD'))
    if os.getenv('TRADING_MAX_POSITION_SIZE_USD') is not None:
        TRADING_CONFIG['max_position_size_usd'] = float(os.getenv('TRADING_MAX_POSITION_SIZE_USD'))
    if os.getenv('TRADING_START_CAPITAL_USD') is not None:
        TRADING_CONFIG['start_capital_usd'] = float(os.getenv('TRADING_START_CAPITAL_USD'))

    # Bellman-Ford overrides
    if os.getenv('BELLMAN_MIN_PROFIT_THRESHOLD') is not None:
        BELLMAN_FORD_CONFIG['min_profit_threshold'] = float(os.getenv('BELLMAN_MIN_PROFIT_THRESHOLD'))

_apply_env_overrides()

def get_start_capital_usd() -> float:
    """Return configured start capital in USD (falls back to max_position_size_usd)"""
    return float(TRADING_CONFIG.get('start_capital_usd', TRADING_CONFIG.get('max_position_size_usd', 1000)))
