import asyncio
import ccxt
try:
    from web3 import Web3  # web3 is optional for tests
except Exception:
    Web3 = None
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import logging
import os
from utils import config as config

# Module logger
logger = logging.getLogger(__name__)

class DataEngine:
    """
    Unified data fetching from CEX exchanges and DEX protocols
    """

    def __init__(self):
        # CEX exchanges (ccxt clients)
        # Instantiate common CEX clients used for real-time fetches where available.
        # Some CI / test environments may not have all exchange classes available in ccxt;
        # create clients defensively and skip ones that are missing to keep tests deterministic.
        self.cex_exchanges = {}
        _preferred_clients = {
            'binance': getattr(ccxt, 'binance', None),
            'kraken': getattr(ccxt, 'kraken', None),
            'coinbase': getattr(ccxt, 'coinbase', None),
            'kucoin': getattr(ccxt, 'kucoin', None),
            'bybit': getattr(ccxt, 'bybit', None),
            'okx': getattr(ccxt, 'okx', None),
            'bitfinex': getattr(ccxt, 'bitfinex', None),
            'gateio': getattr(ccxt, 'gateio', None),
        }
        for name, ctor in _preferred_clients.items():
            if ctor is None:
                logger.warning("CCXT client for %s not available in this environment; skipping ccxt client.", name)
                continue
            try:
                self.cex_exchanges[name] = ctor({'enableRateLimit': True})
            except Exception as e:
                logger.warning("Failed to initialize ccxt client for %s: %s -- falling back to REST parsing.", name, e)

        # REST endpoints configured in utils.config.EXCHANGE_ENDPOINTS (defined in utils/config.py)
        # Keep a mapping of base URLs for REST fallback and verification tools
        try:
            self.cex_endpoints = {
                name: config.EXCHANGE_ENDPOINTS.get(name, {}).get('base_url')
                for name in self.cex_exchanges.keys()
            }
        except Exception:
            self.cex_endpoints = {}

        # DEX protocols - extended with new protocols from config
        self.dex_protocols = {
            'uniswap_v3': {
                'name': 'Uniswap V3',
                'router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'factory': '0x1F98431c8aD98523631AE4a59f267346ea31F984'
            },
            'uniswap': {
                'name': 'Uniswap V2',
                'router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
            },
            'sushiswap': {
                'name': 'SushiSwap',
                'router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
                'factory': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac'
            },
            'pancakeswap': {
                'name': 'PancakeSwap',
                'router': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                'factory': '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73',
                'network': 'bsc'
            },
            'dydx': {
                'name': 'dYdX',
                'network': 'ethereum',
                'api_based': True  # Uses REST API instead of direct contract calls
            },
            'curve': {
                'name': 'Curve',
                'registry': '0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5',
                'network': 'ethereum'
            },
            'balancer': {
                'name': 'Balancer',
                'vault': '0xBA12222222228d8Ba445958a75a0704d566BF2C8',
                'network': 'ethereum'
            },
            'oneinch': {
                'name': '1inch',
                'router': '0x1111111254EEB25477B68fb85Ed929f73A960582',
                'network': 'ethereum',
                'api_based': True  # Aggregator uses REST API
            },
            'kyber': {
                'name': 'Kyber',
                'router': '0x6131B5fae19EA4f9D964eAc0408E4408b66337b5',
                'network': 'ethereum',
                'api_based': True  # Uses REST API
            },
            'tinyman': {
                'name': 'Tinyman',
                'network': 'algorand',
                'app_id': 552635992  # Tinyman AMM v1.1 app ID
            },
            'pact': {
                'name': 'Pact',
                'network': 'algorand',
                'app_id': 6  # Pact will be configured with proper app IDs
            },
            'algofi': {
                'name': 'AlgoFi',
                'network': 'algorand',
                'app_id': 'algofi_v1'  # AlgoFi AMM protocol
            },
            'algox': {
                'name': 'Algox',
                'network': 'algorand',
                'app_id': 'algox_v1'  # Algox (AlgoSwap) protocol
            }
        }

        # Web3 setup (using public RPC for demo) - optional for tests
        if Web3 is not None:
            try:
                self.w3 = Web3(Web3.HTTPProvider('https://eth-mainnet.public.blastapi.io'))
                self.web3_connected = self.w3.is_connected()
            except Exception:
                self.w3 = None
                self.web3_connected = False
                logger.warning("Web3 connection failed - DEX data will be simulated")
        else:
            self.w3 = None
            self.web3_connected = False
            logger.warning("Web3 not installed - DEX data will be simulated (tests)")

        self.last_fetch_time = None
        self.cached_data = {}

    async def fetch_all_market_data(self, trading_pairs: List[str]) -> Dict[str, Any]:
        """
        Fetch market data from all sources
        """
        try:
            logger.info("Fetching market data...")

            market_data = {
                'cex': {},
                'dex': {},
                'tokens': self.extract_tokens_from_pairs(trading_pairs),
                'timestamp': datetime.now(),
                'pairs': trading_pairs
            }

            # Fetch CEX data
            cex_data = await self.fetch_cex_data(trading_pairs)
            market_data['cex'] = cex_data

            # Fetch DEX data
            dex_data = await self.fetch_dex_data(trading_pairs)
            market_data['dex'] = dex_data

            # Cache the data
            self.cached_data = market_data
            self.last_fetch_time = datetime.now()

            logger.info(f"Market data fetched: {len(cex_data)} CEX, {len(dex_data)} DEX")

            # Debugging: Log the size of the market data being returned
            logger.debug(f"Debug: Returning market data of size: {len(str(market_data))} characters")
    
            # Debugging: Log the fetched CEX and DEX data
            logger.debug(f"Debug: CEX data: {cex_data}")
            logger.debug(f"Debug: DEX data: {dex_data}")
    
            # Debugging: Log raw CEX and DEX data responses
            logger.debug(f"Debug: Raw CEX data: {cex_data}")
            logger.debug(f"Debug: Raw DEX data: {dex_data}")

            # Validate fetched data
            if not cex_data:
                logger.warning("Warning: No CEX data fetched.")
            if not dex_data:
                logger.warning("Warning: No DEX data fetched.")

            return market_data

        except Exception as e:
            logger.exception(f" Error fetching market data: {str(e)}")
            return self.get_fallback_data(trading_pairs)

    async def fetch_cex_data(self, trading_pairs: List[str]) -> Dict[str, Dict]:
        """Fetch data from centralized exchanges"""
        cex_data = {}

        for exchange_name, exchange in self.cex_exchanges.items():
            cex_data[exchange_name] = {}
            
            # Load markets if not already loaded (required for symbols to be populated)
            try:
                if not getattr(exchange, 'symbols', None):
                    logger.debug(f"Loading markets for {exchange_name}...")
                    await asyncio.to_thread(exchange.load_markets)
                    logger.debug(f"Markets loaded for {exchange_name}, symbols count: {len(exchange.symbols) if exchange.symbols else 0}")
            except Exception as load_err:
                logger.warning(f"Failed to load markets for {exchange_name}: {load_err} - will use fallbacks")

            for pair in trading_pairs:
                try:
                    # Prepare base token for mapping
                    base_token = pair.split('/')[0]

                    # Validate exchange.symbols
                    if not getattr(exchange, 'symbols', None):
                        logger.debug(f"{exchange_name} symbols not available after load attempt - using fallback for {pair}")
                        fb = self.generate_fallback_ticker(pair)
                        # attach origin info so downstream code can show source pair
                        fb = dict(fb)
                        fb['pair'] = pair
                        fb['source'] = f"cex:{exchange_name}"
                        cex_data[exchange_name][pair] = fb
                        # also map base token to a copy so token lookups work consistently
                        cex_data[exchange_name][base_token] = dict(fb)
                        cex_data[exchange_name][base_token]['mapped_from_pair'] = pair
                        continue

                    # Check if the pair is unsupported for the exchange
                    if pair not in exchange.symbols:
                        logger.warning(f"{exchange_name} does not have market symbol {pair} - using fallback")
                        fb = self.generate_fallback_ticker(pair)
                        fb = dict(fb)
                        fb['pair'] = pair
                        fb['source'] = f"cex:{exchange_name}"
                        cex_data[exchange_name][pair] = fb
                        cex_data[exchange_name][base_token] = dict(fb)
                        cex_data[exchange_name][base_token]['mapped_from_pair'] = pair
                        continue

                    # Debugging: Log exchange symbols and pair
                    logger.debug(f"Debug: {exchange_name} symbols: {exchange.symbols}")
                    logger.debug(f"Debug: Checking pair {pair}")

                    # Additional error handling for fetch_ticker
                    try:
                        logger.debug(f"Debug: Attempting fetch_ticker for {pair} on {exchange_name}")
                        ticker = await asyncio.to_thread(exchange.fetch_ticker, pair)
                    except Exception as fetch_error:
                        logger.warning(f"Error fetching ticker for {pair} on {exchange_name}: {fetch_error}")
                        # Try REST fallback using configured endpoints before giving up
                        try:
                            rest_ticker = await asyncio.to_thread(self.rest_fetch_ticker, exchange_name, pair)
                            if rest_ticker:
                                logger.info(f"Using REST fallback for {pair} on {exchange_name}")
                                ticker = rest_ticker
                            else:
                                fb = self.generate_fallback_ticker(pair)
                                fb = dict(fb)
                                fb['pair'] = pair
                                fb['source'] = f"cex:{exchange_name}"
                                cex_data[exchange_name][pair] = fb
                                cex_data[exchange_name][base_token] = dict(fb)
                                cex_data[exchange_name][base_token]['mapped_from_pair'] = pair
                                continue
                        except Exception as rest_exc:
                            logger.warning(f"REST fallback failed for {exchange_name}: {rest_exc}")
                            fb = self.generate_fallback_ticker(pair)
                            fb = dict(fb)
                            fb['pair'] = pair
                            fb['source'] = f"cex:{exchange_name}"
                            cex_data[exchange_name][pair] = fb
                            cex_data[exchange_name][base_token] = dict(fb)
                            cex_data[exchange_name][base_token]['mapped_from_pair'] = pair
                            continue

                    # Informational: log a concise summary of the fetched ticker
                    try:
                        logger.info(
                            "Fetched ticker for %s %s -> bid=%s ask=%s last=%s",
                            exchange_name,
                            pair,
                            ticker.get('bid') if isinstance(ticker, dict) else None,
                            ticker.get('ask') if isinstance(ticker, dict) else None,
                            ticker.get('last') if isinstance(ticker, dict) else None,
                        )
                    except Exception:
                        logger.debug("Debug: Fetched ticker (unable to format summary)")

                    # Debugging: Log raw ticker response (extra raw logging for ADA to help diagnostics)
                    logger.debug(f"Debug: Raw ticker response for {pair} on {exchange_name}: {ticker}")
                    if 'ADA' in pair:
                        logger.debug(f"RAW ADA ticker @ {exchange_name} {pair}: {ticker}")

                    # Debugging: Log the type and structure of ticker data
                    logger.debug(f"Debug: Ticker type: {type(ticker)}")
                    logger.debug(f"Debug: Ticker content: {ticker}")

                    # Validate ticker data
                    if ticker is None:
                        logger.warning(f"{exchange_name} returned None for {pair}")
                        fb = self.generate_fallback_ticker(pair)
                        fb = dict(fb)
                        fb['pair'] = pair
                        fb['source'] = f"cex:{exchange_name}"
                        cex_data[exchange_name][pair] = fb
                        cex_data[exchange_name][base_token] = dict(fb)
                        cex_data[exchange_name][base_token]['mapped_from_pair'] = pair
                        continue

                    # Normalize and validate numeric fields (ensure bid <= ask, numeric types)
                    normalized = self._normalize_price_dict(ticker)
                    if not normalized:
                        logger.warning(f"{exchange_name} returned invalid numeric ticker for {pair}; using fallback")
                        fb = self.generate_fallback_ticker(pair)
                        fb = dict(fb)
                        fb['pair'] = pair
                        fb['source'] = f"cex:{exchange_name}"
                        cex_data[exchange_name][pair] = fb
                        cex_data[exchange_name][base_token] = dict(fb)
                        cex_data[exchange_name][base_token]['mapped_from_pair'] = pair
                    else:
                        # attach provenance so downstream strategies can identify originating pair
                        normalized = dict(normalized)
                        normalized['pair'] = pair
                        normalized['source'] = f"cex:{exchange_name}"
                        cex_data[exchange_name][pair] = normalized
                        # map base token to a separate copy with the mapped_from_pair marker
                        cex_data[exchange_name][base_token] = dict(normalized)
                        cex_data[exchange_name][base_token]['mapped_from_pair'] = pair

                except Exception as e:
                    logger.exception(f"Failed to fetch {pair} from {exchange_name}: {str(e)}")
                    # Use fallback data
                    fb = self.generate_fallback_ticker(pair)
                    fb = dict(fb)
                    fb['pair'] = pair
                    fb['source'] = f"cex:{exchange_name}"
                    cex_data[exchange_name][pair] = fb
                    base_token = pair.split('/')[0]
                    cex_data[exchange_name][base_token] = dict(fb)
                    cex_data[exchange_name][base_token]['mapped_from_pair'] = pair

                # Small delay to respect rate limits
                await asyncio.sleep(0.1)

        return cex_data

    def rest_fetch_ticker(self, exchange_name: str, pair: str) -> Optional[Dict]:
        """Attempt to fetch a public ticker via REST using configured EXCHANGE_ENDPOINTS.
        This is a best-effort parser for common public endpoints and returns a dict
        compatible with ccxt.fetch_ticker minimal fields: {'bid','ask','last','volume','timestamp'}
        Returns None if it cannot fetch/parse the response.
        """
        endpoints = getattr(config, 'EXCHANGE_ENDPOINTS', {})
        entry = endpoints.get(exchange_name)
        if not entry:
            return None

        base = entry.get('base_url', '').rstrip('/')
        path = entry.get('public_ticker_path', '')
        if not base or not path:
            return None

        # Prepare symbol variants
        symbol_noslash = pair.replace('/', '')
        symbol_dash = pair.replace('/', '-')
        base_token = pair.split('/')[0]
        # Format path with named placeholders if possible (supports {base},{noslash},{dash},{pair})
        try:
            formatted_path = path.format(base=base_token, noslash=symbol_noslash, dash=symbol_dash, pair=pair)
        except Exception:
            try:
                formatted_path = path.format(symbol_noslash) if '{}' in path else path
            except Exception:
                formatted_path = path

        # Build URL
        if formatted_path.startswith('/'):
            url = base + formatted_path
        else:
            url = base + '/' + formatted_path

        params = {}
        headers = {}
        # If endpoint requires API key, check env and set header
        if entry.get('requires_api_key'):
            api_key = os.getenv('COINMARKETCAP_API_KEY') or os.getenv('CMC_API_KEY')
            if not api_key:
                # Cannot call API without key
                return None
            headers['X-CMC_PRO_API_KEY'] = api_key

        # Exchange-specific common params
        if exchange_name == 'binance':
            params = {'symbol': symbol_noslash}
        elif exchange_name == 'coinbase':
            # coinbase path uses {base}-USD in path; no params needed
            params = {}
        elif exchange_name == 'kraken':
            params = {'pair': symbol_noslash}
        elif exchange_name == 'kucoin':
            params = {'symbol': symbol_dash}
        elif exchange_name == 'bybit':
            # spot quote endpoint accepts symbol=BTCUSDT
            params = {'symbol': symbol_noslash}
        elif exchange_name == 'okx':
            # okx uses instId like BTC-USDT
            params = {'instId': symbol_dash}
        elif exchange_name == 'bitfinex':
            # prefer ccxt for bitfinex if configured
            if entry.get('prefer_ccxt'):
                return None
            params = {}
        elif exchange_name == 'gateio':
            # gateio expects currency_pair like BTC_USDT
            params = {'currency_pair': pair.replace('/', '_')}
        elif exchange_name == 'coingecko':
            ids_map = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'BNB': 'binancecoin',
                       'ADA': 'cardano', 'SOL': 'solana', 'MATIC': 'matic-network', 'DOT': 'polkadot'}
            ids = ids_map.get(base_token, base_token.lower())
            params = {'ids': ids, 'vs_currencies': 'usd'}
        elif exchange_name == 'coinmarketcap':
            # CMC requires symbol param and convert
            params = {'symbol': base_token, 'convert': 'USD'}
        else:
            params = {}

        try:
            # Try primary configured path first with logging
            try:
                logger.debug("REST GET %s params=%s headers=%s", url, params, bool(headers))
                resp = requests.get(url, params=params, headers=headers or None, timeout=5)
                logger.info("REST ticker request %s %s -> status=%s url=%s", exchange_name, pair, resp.status_code, getattr(resp, 'url', url))
            except Exception as req_exc:
                logger.warning("REST request failed for %s %s: %s", exchange_name, pair, req_exc)
                return None

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # Log a short snippet to avoid huge logs
                    try:
                        snippet = str(data)[:200]
                        logger.debug("REST response snippet for %s %s: %s", exchange_name, pair, snippet)
                    except Exception:
                        logger.debug("REST response received (unable to serialize snippet)")
                except Exception:
                    logger.debug("REST response non-json for %s %s: %.200s", exchange_name, pair, resp.text)
                    data = None
            else:
                # If non-200 and alternates are provided, try them
                data = None
                alternates = entry.get('alternate_paths') or []
                for alt in alternates:
                    try:
                        # format alternate path similar to primary formatting
                        try:
                            alt_path = alt.format(base=base_token, noslash=symbol_noslash, dash=symbol_dash, pair=pair)
                        except Exception:
                            try:
                                alt_path = alt.format(symbol_noslash) if '{}' in alt else alt
                            except Exception:
                                alt_path = alt
                        if alt_path.startswith('/'):
                            alt_url = base + alt_path
                        else:
                            alt_url = base + '/' + alt_path
                        logger.debug("REST ALT GET %s params=%s", alt_url, params)
                        try:
                            alt_resp = requests.get(alt_url, params=params, headers=headers or None, timeout=5)
                            logger.info("REST alt request %s %s -> status=%s", exchange_name, pair, alt_resp.status_code)
                            if alt_resp.status_code == 200:
                                try:
                                    data = alt_resp.json()
                                    snippet = str(data)[:200]
                                    logger.debug("REST alt response snippet for %s %s: %s", exchange_name, pair, snippet)
                                except Exception:
                                    logger.debug("REST alt response non-json for %s %s: %.200s", exchange_name, pair, alt_resp.text)
                                break
                        except Exception as alt_req_exc:
                            logger.warning("REST alt request failed for %s alt=%s: %s", exchange_name, alt_url, alt_req_exc)
                            continue
                    except Exception:
                        continue
                if data is None:
                    logger.warning("REST endpoints returned no usable data for %s %s", exchange_name, pair)
                    return None
        except Exception as e:
            logger.exception(" Unexpected error in rest_fetch_ticker for %s %s: %s", exchange_name, pair, str(e))
            return None

        # Parse common response shapes (extended to handle list responses like Gate.io)
        try:
            # If API returns a list of tickers (e.g., gate.io), find matching pair
            if isinstance(data, list):
                target_cp = pair.replace('/', '_').upper()
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    cp = (item.get('currency_pair') or item.get('symbol') or item.get('s') or item.get('pair') or '').upper()
                    if not cp:
                        # Try to infer from fields that contain pair-like strings
                        continue
                    if cp == target_cp or cp == symbol_noslash.upper() or cp.replace('_', '-') == symbol_dash.upper():
                        # try common price fields
                        for key in ('last', 'price', 'last_price', 'last_trade_price'):
                            if key in item:
                                try:
                                    price = float(item.get(key))
                                    volume = float(item.get('baseVolume', 0) or item.get('volume', 0) or 0)
                                    return {'bid': price, 'ask': price, 'last': price, 'volume': volume, 'timestamp': int(time.time() * 1000)}
                                except Exception:
                                    continue

            # Simple price field (e.g., Binance / some endpoints)
            if isinstance(data, dict) and 'price' in data:
                price = float(data.get('price'))
                return {'bid': price, 'ask': price, 'last': price, 'volume': 0, 'timestamp': int(time.time() * 1000)}

            # Coinbase returns {'data': {'base': 'BTC', 'currency': 'USD', 'amount': '50000.00'}}
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict) and 'amount' in data['data']:
                price = float(data['data']['amount'])
                return {'bid': price, 'ask': price, 'last': price, 'volume': 0, 'timestamp': int(time.time() * 1000)}

            # Coingecko: {'bitcoin': {'usd': 50000}}
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, dict):
                        for sub in v.values():
                            try:
                                price = float(sub)
                                return {'bid': price, 'ask': price, 'last': price, 'volume': 0, 'timestamp': int(time.time() * 1000)}
                            except Exception:
                                continue

            # Kraken returns nested 'result' object
            if isinstance(data, dict) and 'result' in data and isinstance(data['result'], dict):
                first = next(iter(data['result'].values()))
                if isinstance(first, dict):
                    # Try common fields
                    if 'c' in first and isinstance(first['c'], list):
                        last = float(first['c'][0])
                        return {'bid': last, 'ask': last, 'last': last, 'volume': 0, 'timestamp': int(time.time() * 1000)}
                    if 'last' in first:
                        last = float(first['last'])
                        return {'bid': last, 'ask': last, 'last': last, 'volume': 0, 'timestamp': int(time.time() * 1000)}
        except Exception:
            return None

        # Fallback: unable to parse
        return None

    async def fetch_dex_data(self, trading_pairs: List[str]) -> Dict[str, Dict]:
        """Fetch data from decentralized exchanges"""
        dex_data = {}

        for protocol_name, protocol_info in self.dex_protocols.items():
            dex_data[protocol_name] = {}

            for pair in trading_pairs:
                try:
                    if self.web3_connected:
                        # Try to fetch real DEX data
                        price_data = await self.fetch_dex_price_real(protocol_info, pair)
                    else:
                        # Use simulated data
                        price_data = self.generate_simulated_dex_price(pair)
    
                    # Normalize DEX price entry (preserve fee/liquidity if present)
                    normalized = self._normalize_price_dict(price_data)
                    if not normalized:
                        logger.warning(f"Invalid DEX price for {pair} on {protocol_name}; using simulated fallback")
                        dex_data[protocol_name][pair] = self.generate_simulated_dex_price(pair)
                        # Add individual token data (same as success path)
                        base_token = pair.split('/')[0]
                        token_data = dict(dex_data[protocol_name][pair])
                        token_data['mapped_from_pair'] = pair
                        dex_data[protocol_name][base_token] = token_data
                        continue
                    else:
                        # Preserve extra fields commonly present in DEX entries
                        for extra in ('fee', 'liquidity'):
                            if isinstance(price_data, dict) and extra in price_data:
                                normalized[extra] = price_data[extra]
                        # Ensure pair and source are set (provenance tracking)
                        if 'pair' not in normalized or not normalized['pair']:
                            normalized['pair'] = pair
                        if 'source' not in normalized or not normalized['source']:
                            normalized['source'] = f"dex:{protocol_name}"
                        dex_data[protocol_name][pair] = normalized
                        
                        # Add individual token data
                        base_token = pair.split('/')[0]
                        token_data = dict(dex_data[protocol_name][pair])
                        token_data['mapped_from_pair'] = pair
                        dex_data[protocol_name][base_token] = token_data

                except Exception as e:
                    logger.exception(f"Failed to fetch {pair} from {protocol_name}: {str(e)}")
                    dex_data[protocol_name][pair] = self.generate_simulated_dex_price(pair)
                    # Add individual token data (same as success path)
                    base_token = pair.split('/')[0]
                    token_data = dict(dex_data[protocol_name][pair])
                    token_data['mapped_from_pair'] = pair
                    dex_data[protocol_name][base_token] = token_data

                await asyncio.sleep(0.1)

        return dex_data

    async def fetch_dex_price_real(self, protocol_info: Dict, pair: str) -> Dict:
        """Fetch real DEX prices using Web3"""
        try:
            # This is a simplified implementation
            # In production, you'd use proper DEX SDK or subgraph queries

            base_price = 50000 if 'BTC' in pair else 3000 if 'ETH' in pair else 300

            # Simulate some price variation for DEX vs CEX
            import random
            variation = random.uniform(0.995, 1.005)

            dex_price = base_price * variation
            spread = dex_price * 0.003  # 0.3% spread

            return {
                'bid': dex_price - spread/2,
                'ask': dex_price + spread/2,
                'last': dex_price,
                'volume': random.uniform(100, 1000),
                'timestamp': int(time.time() * 1000),
                'liquidity': random.uniform(10000, 100000),
                'fee': 0.003,  # 0.3% typical DEX fee
                'pair': pair,  # Include pair info for provenance tracking
                'source': f"dex:{protocol_info.get('name', 'unknown')}"
            }

        except Exception as e:
            logger.exception(f"Error fetching real DEX price: {str(e)}")
            return self.generate_simulated_dex_price(pair)

    def generate_simulated_dex_price(self, pair: str) -> Dict:
        """Generate simulated DEX price data for demo"""
        import random

        # Base prices for simulation (keep consistent across pairs)
        base_prices = {
            'BTC/USDT': 50000,
            'BTC/USDC': 50000,
            'ETH/USDT': 3000,
            'ETH/USDC': 3000,
            'BNB/USDT': 300,
            'BNB/USDC': 300,
            'ADA/USDT': 0.5,
            'ADA/USDC': 0.5,
            'SOL/USDT': 100,
            'SOL/USDC': 100,
            'ALGO/USDT': 0.18,
            'ALGO/USDC': 0.18,
            'WETH/USDC': 3000,
            'WETH/USDT': 3000,
            'WBTC/USDC': 50000,
            'WBTC/USDT': 50000,
            'LINK/USDC': 15.0,
            'LINK/USDT': 15.0,
            'MATIC/USDC': 0.85,
            'MATIC/USDT': 0.85,
            'CAKE/USDT': 3.5,
            'CAKE/USDC': 3.5,
            'DAI/USDC': 1.0,
            'DAI/USDT': 1.0,
            'USDT/USDC': 1.0,
            'USDC/USDT': 1.0
        }

        base_price = base_prices.get(pair, 100)

        # Add some randomness to simulate market conditions
        variation = random.uniform(0.99, 1.01)
        dex_price = base_price * variation

        # DEX typically has wider spreads
        spread = dex_price * 0.005  # 0.5% spread

        return {
            'bid': dex_price - spread/2,
            'ask': dex_price + spread/2,
            'last': dex_price,
            'volume': random.uniform(50, 500),
            'timestamp': int(time.time() * 1000),
            'liquidity': random.uniform(5000, 50000),
            'fee': 0.003,
            'pair': pair,  # Include pair info for provenance tracking
            'source': 'dex:simulated'
        }

    def generate_fallback_ticker(self, pair: str) -> Dict:
        """Generate fallback ticker data for demo"""
        import random

        # Base prices for fallback (keep consistent across pairs to avoid fake arbitrage)
        base_prices = {
            'BTC/USDT': 50000,
            'BTC/USDC': 50000,
            'ETH/USDT': 3000,
            'ETH/USDC': 3000,
            'BNB/USDT': 300,
            'BNB/USDC': 300,
            'ADA/USDT': 0.5,
            'ADA/USDC': 0.5,
            'SOL/USDT': 100,
            'SOL/USDC': 100,
            'ALGO/USDT': 0.18,
            'ALGO/USDC': 0.18,
            'WETH/USDC': 3000,
            'WETH/USDT': 3000,
            'WBTC/USDC': 50000,
            'WBTC/USDT': 50000,
            'LINK/USDC': 15.0,
            'LINK/USDT': 15.0,
            'MATIC/USDC': 0.85,
            'MATIC/USDT': 0.85,
            'CAKE/USDT': 3.5,
            'CAKE/USDC': 3.5,
            'DAI/USDC': 1.0,
            'DAI/USDT': 1.0,
            'USDT/USDC': 1.0,
            'USDC/USDT': 1.0
        }

        base_price = base_prices.get(pair, 100)
        variation = random.uniform(0.998, 1.002)
        price = base_price * variation

        spread = price * 0.001  # 0.1% spread for CEX

        return {
            'bid': price - spread/2,
            'ask': price + spread/2,
            'last': price,
            'volume': random.uniform(100, 1000),
            'timestamp': int(time.time() * 1000),
            'pair': pair,  # Include pair info for provenance tracking
            'source': 'cex:fallback'
        }

    def _normalize_price_dict(self, price_dict: Optional[Dict]) -> Optional[Dict]:
        """Normalize ticker-like dicts: ensure numeric bid/ask/last/volume/timestamp,
        ensure bid <= ask (swap if inverted), return None for clearly invalid entries."""
        try:
            if not isinstance(price_dict, dict):
                return None
            # Extract numeric fields safely
            bid = float(price_dict.get('bid') or 0.0)
            ask = float(price_dict.get('ask') or 0.0)
            # Prefer explicit 'last', otherwise average of bid/ask when available
            last_raw = price_dict.get('last')
            if last_raw is not None:
                try:
                    last = float(last_raw)
                except Exception:
                    last = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else max(bid, ask)
            else:
                last = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else max(bid, ask)
            volume = float(price_dict.get('volume') or price_dict.get('baseVolume') or 0.0)
            timestamp = int(price_dict.get('timestamp') or int(time.time() * 1000))
    
            # Discard completely empty/zero price entries
            if bid <= 0 and ask <= 0 and last <= 0:
                return None
    
            # If bid > ask, swap and log
            if bid > 0 and ask > 0 and bid > ask:
                logger.warning(f"Inverted bid/ask detected (bid={bid} > ask={ask}); swapping values")
                bid, ask = ask, bid
                # adjust last into the new range
                if last < bid:
                    last = bid
                if last > ask:
                    last = ask
    
            # Ensure last is within [bid, ask] when possible
            if bid > 0 and last < bid:
                last = bid
            if ask > 0 and last > ask:
                last = ask
    
            return {
                'bid': bid,
                'ask': ask,
                'last': last,
                'volume': volume,
                'timestamp': timestamp
            }
        except Exception:
            logger.exception(" Error normalizing price dict")
            return None
    
    def extract_tokens_from_pairs(self, trading_pairs: List[str]) -> List[str]:
        """Extract unique tokens from trading pairs"""
        tokens = set()
        for pair in trading_pairs:
            if '/' in pair:
                base, quote = pair.split('/')
                tokens.add(base)
                tokens.add(quote)
        return list(tokens)
    
    def validate_price_consistency(self, price_data: Dict[str, Any]) -> List[str]:
        """
        Validate that prices are consistent across different pairs.
        Detects when the same token has wildly different implied USD prices.
        
        Returns list of warnings about inconsistencies.
        """
        warnings = []
        
        try:
            # Extract all token prices relative to USD stablecoins
            token_prices = {}  # token -> list of (price, pair, exchange) tuples
            
            for exchange_type in ['cex', 'dex']:
                for exchange_name, exchange_data in price_data.get(exchange_type, {}).items():
                    for pair, pair_data in exchange_data.items():
                        if '/' not in pair or not isinstance(pair_data, dict):
                            continue
                        
                        base, quote = pair.split('/')
                        mid_price = (pair_data.get('bid', 0) + pair_data.get('ask', 0)) / 2
                        
                        if mid_price <= 0:
                            continue
                        
                        # If quote is a stablecoin, this gives us base's USD price
                        if quote in ['USDT', 'USDC', 'DAI', 'BUSD']:
                            if base not in token_prices:
                                token_prices[base] = []
                            token_prices[base].append((mid_price, pair, exchange_name))
                        
                        # If base is a stablecoin, this gives us quote's USD price (inverted)
                        if base in ['USDT', 'USDC', 'DAI', 'BUSD']:
                            if quote not in token_prices:
                                token_prices[quote] = []
                            token_prices[quote].append((1/mid_price, pair, exchange_name))
            
            # Check for inconsistencies
            for token, prices in token_prices.items():
                if len(prices) < 2:
                    continue
                
                # Calculate price range
                price_values = [p[0] for p in prices]
                min_price = min(price_values)
                max_price = max(price_values)
                
                # If prices differ by more than threshold, warn
                PRICE_CONSISTENCY_THRESHOLD = 0.05  # 5% max difference
                if max_price > 0 and (max_price - min_price) / min_price > PRICE_CONSISTENCY_THRESHOLD:
                    warning = f"Price inconsistency detected for {token}: "
                    warning += f"ranges from ${min_price:.2f} to ${max_price:.2f} "
                    warning += f"({(max_price/min_price - 1)*100:.1f}% difference). "
                    warning += "This may create fake arbitrage opportunities!"
                    warnings.append(warning)
                    logger.warning(warning)
                    
                    # Log details for debugging
                    for price, pair, exchange in prices:
                        logger.debug(f"  {token} price from {pair}@{exchange}: ${price:.4f}")
        
        except Exception as e:
            logger.exception(f"Error validating price consistency: {e}")
        
        return warnings

    def get_fallback_data(self, trading_pairs: List[str]) -> Dict[str, Any]:
        """Get fallback data when fetching fails"""
        logger.info("Using fallback market data...")

        fallback_data = {
            'cex': {},
            'dex': {},
            'tokens': self.extract_tokens_from_pairs(trading_pairs),
            'timestamp': datetime.now(),
            'pairs': trading_pairs
        }

        # Generate basic fallback data
        for exchange in self.cex_exchanges.keys():
            fallback_data['cex'][exchange] = {}
            for pair in trading_pairs:
                ticker = self.generate_fallback_ticker(pair)
                base_token = pair.split('/')[0]
                fallback_data['cex'][exchange][pair] = ticker
                # Also map base token for consistent lookups
                token_data = dict(ticker)
                token_data['mapped_from_pair'] = pair
                fallback_data['cex'][exchange][base_token] = token_data
 
        for protocol in self.dex_protocols.keys():
            fallback_data['dex'][protocol] = {}
            for pair in trading_pairs:
                dex_price = self.generate_simulated_dex_price(pair)
                base_token = pair.split('/')[0]
                fallback_data['dex'][protocol][pair] = dex_price
                # Also map base token for consistent lookups
                token_data = dict(dex_price)
                token_data['mapped_from_pair'] = pair
                fallback_data['dex'][protocol][base_token] = token_data
 
        # Inject a synthetic exchange with manipulated prices to create a detectable profitable cycle
        # This is for testing only and should be removed or behind a config flag in production.
        try:
            if getattr(config, 'DEBUG_DEMO_INJECT_SYNTHETIC', False):
                synthetic = {}
                for pair in trading_pairs:
                    if pair == 'BTC/USDT':
                        # Make BTC substantially cheaper on synthetic exchange to create arbitrage:
                        synthetic[pair] = {
                            'bid': 49500.0,
                            'ask': 49000.0,
                            'last': 49250.0,
                            'volume': 100.0,
                            'timestamp': int(time.time() * 1000)
                        }
                    else:
                        synthetic[pair] = self.generate_fallback_ticker(pair)
                fallback_data['cex']['synthetic'] = synthetic
                logger.info("Injected synthetic arbitrage exchange 'synthetic' for testing")
            else:
                logger.debug("Skipping synthetic arbitrage injection (DEBUG_DEMO_INJECT_SYNTHETIC=False)")
        except Exception:
            logger.exception("Failed to inject synthetic arbitrage data")
 
        return fallback_data

    def get_status(self) -> Dict[str, Any]:
        """Get data engine status"""
        return {
            'last_fetch': self.last_fetch_time,
            'cached_data_available': bool(self.cached_data),
            'cex_exchanges': len(self.cex_exchanges),
            'dex_protocols': len(self.dex_protocols),
            'web3_connected': self.web3_connected
        }

    async def get_historical_data(self, pair: str, timeframe: str = '1h', limit: int = 100) -> List[Dict]:
        """Get historical OHLCV data (simplified implementation)"""
        try:
            # Use Binance as primary source for historical data
            exchange = self.cex_exchanges['binance']
            ohlcv = await asyncio.to_thread(exchange.fetch_ohlcv, pair, timeframe, limit=limit)

            # Debugging: Log the type and content of ohlcv before processing
            logger.debug(f"Debug: OHLCV type: {type(ohlcv)}")
            logger.debug(f"Debug: OHLCV content: {ohlcv}")
    
            # Filter out invalid candles
            ohlcv = [candle for candle in ohlcv if all(candle)]
    
            if not ohlcv:
                raise ValueError("No valid historical data available")
    
            return [
                {
                    'timestamp': candle[0],
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
                for candle in ohlcv
            ]
    
        except Exception as e:
            logger.exception(f"Error fetching historical data: {str(e)}")
            return []
