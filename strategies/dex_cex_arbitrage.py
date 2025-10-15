import math
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DEXCEXArbitrage:
    """
    Strategy 1: DEX/CEX Arbitrage
    Exploits price differences between decentralized and centralized exchanges
    """

    def __init__(self, ai_model):
        self.ai = ai_model
        self.strategy_name = "dex_cex"

        # DEX protocols we support (extended with new protocols)
        self.dex_protocols = [
            'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
            'dydx', 'curve', 'balancer', 'oneinch', 'kyber',
            'tinyman', 'pact', 'algofi', 'algox'
        ]

        # CEX exchanges we support  
        self.cex_exchanges = ['binance', 'kraken', 'coinbase', 'kucoin']
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information for UI display"""
        return {
            'name': 'DEX/CEX Arbitrage',
            'key': 'dex_cex',
            'description': 'Exploits price differences between decentralized exchanges (DEX) and centralized exchanges (CEX)',
            'how_it_works': 'Finds opportunities to buy a token on one exchange type and sell it on another for profit. For example: Buy BTC on Binance (CEX) for $50,000, sell on Uniswap (DEX) for $50,500.',
            'supported_exchanges': {
                'CEX': self.cex_exchanges,
                'DEX': self.dex_protocols
            },
            'typical_profit': '0.3% - 2%',
            'execution_speed': 'Medium (5-30 seconds)',
            'risk_level': 'Medium',
            'capital_required': '$500 - $10,000',
            'fees': {
                'CEX': '0.1%',
                'DEX': '0.3% + gas fees ($5-50)',
            },
            'best_conditions': 'High market volatility, network congestion differences',
            'status': 'Active ✅'
        }

    async def add_strategy_edges(self, graph, price_data: Dict[str, Any]):
        """
        Add DEX/CEX arbitrage edges to the graph
        """
        try:
            logger.info("Adding DEX/CEX arbitrage edges...")
    
            tokens = price_data.get('tokens', [])
    
            for token in tokens:
                # Add edges between CEX and DEX for the same token
                await self.add_cex_to_dex_edges(graph, price_data, token)
                await self.add_dex_to_cex_edges(graph, price_data, token)
    
            logger.info("Added DEX/CEX edges for %d tokens", len(tokens))
    
        except Exception as e:
            logger.exception("Error adding DEX/CEX edges: %s", str(e))

    async def add_cex_to_dex_edges(self, graph, price_data: Dict[str, Any], token: str):
        """Add edges from CEX to DEX for arbitrage opportunities"""

        for cex_exchange in self.cex_exchanges:
            for dex_protocol in self.dex_protocols:
                cex_node = f"{token}@{cex_exchange}"
                dex_node = f"{token}@{dex_protocol}"

                # Check if both nodes exist in graph
                if not (graph.has_node(cex_node) and graph.has_node(dex_node)):
                    continue

                # Get price data
                cex_data = price_data.get('cex', {}).get(cex_exchange, {})
                dex_data = price_data.get('dex', {}).get(dex_protocol, {})

                cex_price_info = self.get_token_price_info(cex_data, token)
                dex_price_info = self.get_token_price_info(dex_data, token)

                if not (cex_price_info and dex_price_info):
                    continue

                # Helpful raw logging when provenance is missing (common source of malformed candidates)
                if token == 'ADA':
                    logger.debug("RAW ADA cex_price_info=%s dex_price_info=%s exchange=%s dex=%s", cex_price_info, dex_price_info, cex_exchange, dex_protocol)

                # Calculate arbitrage potential: Buy on CEX, Sell on DEX
                if cex_price_info['ask'] > 0 and dex_price_info['bid'] > 0:
                    # Buy on CEX (use ask price)
                    cex_buy_price = cex_price_info['ask']
                    cex_fee = 0.001  # 0.1% CEX fee

                    # Sell on DEX (use bid price)
                    dex_sell_price = dex_price_info['bid']
                    dex_fee = dex_price_info.get('fee', 0.003)  # DEX fee

                    # Calculate gas cost for DEX transaction
                    gas_cost = await self.estimate_dex_gas_cost(dex_protocol, token)

                    # AI analysis for optimal timing
                    timing_analysis = await self.ai_analyze_dex_cex_timing(
                        cex_exchange, dex_protocol, token, cex_buy_price, dex_sell_price
                    )

                    # Calculate effective rate
                    buy_cost = cex_buy_price * (1 + cex_fee)
                    sell_proceeds = dex_sell_price * (1 - dex_fee) - gas_cost

                    # Sanity checks to avoid spurious extreme rates from malformed data
                    EPS = 1e-8
                    if buy_cost <= EPS or sell_proceeds <= EPS:
                        logger.warning(
                            "Skipping cex->dex candidate due to near-zero cost/proceeds token=%s buy=%s sell=%s buy_cost=%s sell_proceeds=%s source_cex_pair=%s source_dex_pair=%s",
                            token, cex_exchange, dex_protocol, buy_cost, sell_proceeds,
                            self._get_price_origin(cex_price_info),
                            self._get_price_origin(dex_price_info)
                        )
                    else:
                        rate = sell_proceeds / buy_cost
                        profit_pct = (sell_proceeds - buy_cost) / buy_cost * 100 if buy_cost > 0 else 0.0

                        # Additional validation: For same-token transfers between exchanges,
                        # the rate should be very close to 1.0 (allowing for fees).
                        # A rate far from 1.0 indicates bad price data.
                        # Maximum reasonable profit for same-token transfer: ~5% after fees
                        # So rate should be between 0.8 and 1.1
                        if rate < 0.8 or rate > 1.1:
                            logger.warning(
                                "Skipping cex->dex candidate with unrealistic same-token transfer rate token=%s buy=%s sell=%s rate=%s profit_pct=%s buy_cost=%s sell_proceeds=%s cex_buy_price=%s dex_sell_price=%s source_cex_pair=%s source_dex_pair=%s",
                                token, cex_exchange, dex_protocol, rate, profit_pct, buy_cost, sell_proceeds, cex_buy_price, dex_sell_price,
                                self._get_price_origin(cex_price_info),
                                self._get_price_origin(dex_price_info)
                            )
                            continue

                        # Reject obviously invalid/excessive rates
                        if not (0 < rate < 1e4) or abs(profit_pct) > 5000:
                            logger.warning(
                                "Skipping cex->dex candidate with abnormal rate/profit token=%s buy=%s sell=%s rate=%s profit_pct=%s buy_cost=%s sell_proceeds=%s source_cex_pair=%s source_dex_pair=%s",
                                token, cex_exchange, dex_protocol, rate, profit_pct, buy_cost, sell_proceeds,
                                self._get_price_origin(cex_price_info),
                                self._get_price_origin(dex_price_info)
                            )
                        else:
                            weight = -math.log(max(rate * timing_analysis.get('confidence', 1.0), EPS))

                            logger.info(
                                "Adding edge cex->dex token=%s buy=%s sell=%s profit_pct=%.4f ai_confidence=%.3f gas_cost=%.2f total_fees=%.6f",
                                token, cex_exchange, dex_protocol, profit_pct, timing_analysis.get('confidence', 0.5), gas_cost, (cex_fee + dex_fee)
                            )

                            # Diagnostic: detailed arithmetic and units before adding edge (include pair origin info)
                            try:
                                logger.debug(
                                    "DIAG cex->dex token=%s buy_price=%.8f sell_price=%.8f buy_cost=%.8f sell_proceeds=%.8f rate=%.8f profit_pct=%.6f fees_cex=%.6f fees_dex=%.6f gas_cost=%.4f ai_conf=%s src_cex_pair=%s src_dex_pair=%s",
                                    token,
                                    cex_buy_price,
                                    dex_sell_price,
                                    buy_cost,
                                    sell_proceeds,
                                    rate,
                                    profit_pct,
                                    cex_fee,
                                    dex_fee,
                                    gas_cost,
                                    timing_analysis,
                                    self._get_price_origin(cex_price_info),
                                    self._get_price_origin(dex_price_info)
                                )
                            except Exception:
                                logger.debug("DIAG cex->dex (unable to format detailed values)")

                            graph.add_edge(cex_node, dex_node,
                                         weight=weight,
                                         rate=rate,
                                         strategy='dex_cex',
                                         direction='cex_to_dex',
                                         buy_exchange=cex_exchange,
                                         sell_exchange=dex_protocol,
                                         buy_price=cex_buy_price,
                                         sell_price=dex_sell_price,
                                         total_fees=cex_fee + dex_fee,
                                         gas_cost=gas_cost,
                                         ai_confidence=timing_analysis.get('confidence', 0.5))

    async def add_dex_to_cex_edges(self, graph, price_data: Dict[str, Any], token: str):
        """Add edges from DEX to CEX for arbitrage opportunities"""

        for dex_protocol in self.dex_protocols:
            for cex_exchange in self.cex_exchanges:
                dex_node = f"{token}@{dex_protocol}"
                cex_node = f"{token}@{cex_exchange}"

                if not (graph.has_node(dex_node) and graph.has_node(cex_node)):
                    continue

                # Get price data
                dex_data = price_data.get('dex', {}).get(dex_protocol, {})
                cex_data = price_data.get('cex', {}).get(cex_exchange, {})

                dex_price_info = self.get_token_price_info(dex_data, token)
                cex_price_info = self.get_token_price_info(cex_data, token)

                if not (dex_price_info and cex_price_info):
                    continue

                # Helpful raw logging when provenance is missing (common source of malformed candidates)
                if token == 'ADA':
                    logger.debug("RAW ADA dex_price_info=%s cex_price_info=%s dex=%s exchange=%s", dex_price_info, cex_price_info, dex_protocol, cex_exchange)

                # Calculate arbitrage: Buy on DEX, Sell on CEX
                if dex_price_info['ask'] > 0 and cex_price_info['bid'] > 0:
                    # Buy on DEX
                    dex_buy_price = dex_price_info['ask']
                    dex_fee = dex_price_info.get('fee', 0.003)

                    # Sell on CEX
                    cex_sell_price = cex_price_info['bid']
                    cex_fee = 0.001

                    # Gas cost
                    gas_cost = await self.estimate_dex_gas_cost(dex_protocol, token)

                    # AI timing analysis
                    timing_analysis = await self.ai_analyze_dex_cex_timing(
                        dex_protocol, cex_exchange, token, dex_buy_price, cex_sell_price
                    )

                    # Calculate effective rate
                    buy_cost = dex_buy_price * (1 + dex_fee) + gas_cost
                    sell_proceeds = cex_sell_price * (1 - cex_fee)

                    # Sanity checks to avoid spurious extreme rates from malformed data
                    EPS = 1e-8
                    if buy_cost <= EPS or sell_proceeds <= EPS:
                        logger.warning(
                            "Skipping dex->cex candidate due to near-zero cost/proceeds token=%s buy=%s sell=%s buy_cost=%s sell_proceeds=%s source_dex_pair=%s source_cex_pair=%s",
                            token, dex_protocol, cex_exchange, buy_cost, sell_proceeds,
                            self._get_price_origin(dex_price_info),
                            self._get_price_origin(cex_price_info)
                        )
                    else:
                        rate = sell_proceeds / buy_cost
                        profit_pct = (sell_proceeds - buy_cost) / buy_cost * 100 if buy_cost > 0 else 0.0

                        # Additional validation: For same-token transfers between exchanges,
                        # the rate should be very close to 1.0 (allowing for fees).
                        # A rate far from 1.0 indicates bad price data.
                        # Maximum reasonable profit for same-token transfer: ~5% after fees
                        # So rate should be between 0.8 and 1.1
                        if rate < 0.8 or rate > 1.1:
                            logger.warning(
                                "Skipping dex->cex candidate with unrealistic same-token transfer rate token=%s buy=%s sell=%s rate=%s profit_pct=%s buy_cost=%s sell_proceeds=%s dex_buy_price=%s cex_sell_price=%s source_dex_pair=%s source_cex_pair=%s",
                                token, dex_protocol, cex_exchange, rate, profit_pct, buy_cost, sell_proceeds, dex_buy_price, cex_sell_price,
                                self._get_price_origin(dex_price_info),
                                self._get_price_origin(cex_price_info)
                            )
                            continue

                        # Reject obviously invalid/excessive rates
                        if not (0 < rate < 1e4) or abs(profit_pct) > 5000:
                            logger.warning(
                                "Skipping dex->cex candidate with abnormal rate/profit token=%s buy=%s sell=%s rate=%s profit_pct=%s buy_cost=%s sell_proceeds=%s source_dex_pair=%s source_cex_pair=%s",
                                token, dex_protocol, cex_exchange, rate, profit_pct, buy_cost, sell_proceeds,
                                self._get_price_origin(dex_price_info),
                                self._get_price_origin(cex_price_info)
                            )
                        else:
                            weight = -math.log(max(rate * timing_analysis.get('confidence', 1.0), EPS))

                            logger.info(
                                "Adding edge dex->cex token=%s buy=%s sell=%s profit_pct=%.4f ai_confidence=%.3f gas_cost=%.2f total_fees=%.6f",
                                token, dex_protocol, cex_exchange, profit_pct, timing_analysis.get('confidence', 0.5), gas_cost, (dex_fee + cex_fee)
                            )

                            # Diagnostic: detailed arithmetic and units before adding edge (include pair origin info)
                            try:
                                logger.debug(
                                    "DIAG dex->cex token=%s buy_price=%.8f sell_price=%.8f buy_cost=%.8f sell_proceeds=%.8f rate=%.8f profit_pct=%.6f fees_dex=%.6f fees_cex=%.6f gas_cost=%.4f ai_conf=%s src_dex_pair=%s src_cex_pair=%s",
                                    token,
                                    dex_buy_price,
                                    cex_sell_price,
                                    buy_cost,
                                    sell_proceeds,
                                    rate,
                                    profit_pct,
                                    dex_fee,
                                    cex_fee,
                                    gas_cost,
                                    timing_analysis,
                                    self._get_price_origin(dex_price_info),
                                    self._get_price_origin(cex_price_info)
                                )
                            except Exception:
                                logger.debug("DIAG dex->cex (unable to format detailed values)")

                            graph.add_edge(dex_node, cex_node,
                                         weight=weight,
                                         rate=rate,
                                         strategy='dex_cex',
                                         direction='dex_to_cex',
                                         buy_exchange=dex_protocol,
                                         sell_exchange=cex_exchange,
                                         buy_price=dex_buy_price,
                                         sell_price=cex_sell_price,
                                         total_fees=dex_fee + cex_fee,
                                         gas_cost=gas_cost,
                                         ai_confidence=timing_analysis.get('confidence', 0.5))

    def get_token_price_info(self, exchange_data: Dict, token: str) -> Optional[Dict]:
        """Extract price info for a token from exchange data.
        Supports token being either the base or the quote in a pair. If the token
        is the quote side the returned price_info is inverted so that 'bid'/'ask'
        are expressed as the requested token per counter token (consistent view).
        This method also preserves provenance fields emitted by core.data_engine
        (pair, mapped_from_pair, source) and adds a safe inverted 'pair' when inversion occurs.
        """
        if not isinstance(exchange_data, dict):
            return None

        # Direct token lookup (core.data_engine maps base token -> pair data)
        if token in exchange_data:
            info = exchange_data[token]
            # Raw debug for ADA issues
            if token == 'ADA':
                logger.debug("RAW ADA direct lookup price_info=%s", info)
            # Ensure provenance fields exist
            copy = dict(info) if isinstance(info, dict) else {}
            if 'pair' not in copy:
                # Try to infer pair from mapped_from_pair
                if 'mapped_from_pair' in copy:
                    copy['pair'] = copy.get('mapped_from_pair')
                else:
                    copy['pair'] = None
            if 'source' not in copy:
                copy['source'] = copy.get('source')
            return self._normalize_price_info(copy)

        # Try token pair lookup and handle base/quote positions
        for pair, price_info in exchange_data.items():
            if '/' in pair and isinstance(price_info, dict):
                base_token, quote_token = pair.split('/')
                # Direct base token match
                if base_token == token:
                    # Attach pair/source if missing to aid downstream diagnostics
                    copy = dict(price_info)
                    copy['pair'] = pair
                    copy['source'] = copy.get('source')
                    if token == 'ADA':
                        logger.debug("RAW ADA base-pair price_info from pair=%s -> %s", pair, copy)
                    return self._normalize_price_info(copy)

                # If token is quote, invert the pair
                if quote_token == token:
                    # Invert prices so that returned dict represents the token requested
                    try:
                        bid = float(price_info.get('bid') or 0.0)
                        ask = float(price_info.get('ask') or 0.0)
                    except Exception:
                        bid = 0.0
                        ask = 0.0
                    inv_bid = 1.0 / ask if ask > 0 else 0.0
                    inv_ask = 1.0 / bid if bid > 0 else 0.0
                    inverted = dict(price_info)
                    inverted['bid'] = inv_bid
                    inverted['ask'] = inv_ask
                    inverted['inverted_from'] = pair
                    # Construct a sensible inverted pair string (e.g., if pair is BASE/QUOTE and token==QUOTE -> QUOTE/BASE)
                    inverted['pair'] = f"{token}/{base_token}"
                    inverted['source'] = inverted.get('source')
                    if token == 'ADA':
                        logger.debug("RAW ADA inverted price_info from pair=%s -> %s", pair, inverted)
                    return self._normalize_price_info(inverted)

        return None

    def _normalize_price_info(self, info: Dict) -> Dict:
        """Ensure numeric bid/ask/fee and consistent ordering (bid <= ask inverted view).
        Preserve provenance fields such as 'pair','source','mapped_from_pair','inverted_from' when present.
        """
        normalized = dict(info) if isinstance(info, dict) else {}
        try:
            normalized['bid'] = float(normalized.get('bid', 0) or 0.0)
            normalized['ask'] = float(normalized.get('ask', 0) or 0.0)
            normalized['fee'] = float(normalized.get('fee', 0) or 0.0)
        except (ValueError, TypeError):
            normalized['bid'] = 0.0
            normalized['ask'] = 0.0
            normalized['fee'] = 0.0

        # Ensure bid <= ask; if not, swap (protect against malformed data)
        if normalized['bid'] > 0 and normalized['ask'] > 0 and normalized['bid'] > normalized['ask']:
            logger.warning(f"In _normalize_price_info detected bid>ask for pair={normalized.get('pair')} swapping")
            normalized['bid'], normalized['ask'] = normalized['ask'], normalized['bid']

        # Ensure last/volume/timestamp are numeric if present
        try:
            if 'last' in normalized:
                normalized['last'] = float(normalized.get('last') or 0.0)
        except Exception:
            normalized['last'] = normalized.get('bid') or 0.0

        try:
            if 'volume' in normalized:
                normalized['volume'] = float(normalized.get('volume') or 0.0)
        except Exception:
            normalized['volume'] = 0.0

        try:
            if 'timestamp' in normalized:
                normalized['timestamp'] = int(normalized.get('timestamp') or int(0))
        except Exception:
            normalized['timestamp'] = int(0)

        # Preserve provenance keys if present, otherwise ensure they exist (None)
        for k in ('pair', 'source', 'mapped_from_pair', 'inverted_from'):
            if k not in normalized:
                normalized[k] = None

        return normalized

    def _get_price_origin(self, info: Optional[Dict]) -> Optional[str]:
        """Return best-effort origin/pair string for a normalized price_info dict."""
        if not isinstance(info, dict):
            return None
        # Prefer explicit inverted_from, then mapped_from_pair, then pair, then source
        for k in ('inverted_from', 'mapped_from_pair', 'pair', 'source'):
            v = info.get(k)
            if v:
                return v
        return None

    async def estimate_dex_gas_cost(self, dex_protocol: str, token: str) -> float:
        """Estimate gas cost for DEX operations in USD"""

        # Base gas estimates (in USD) - extended with new protocols
        base_gas_costs = {
            'uniswap_v3': 15.0,    # $15 average
            'uniswap': 15.0,       # $15 average
            'sushiswap': 12.0,     # $12 average  
            'pancakeswap': 0.5,    # $0.50 on BSC
            'dydx': 10.0,          # $10 average (Layer 2)
            'curve': 20.0,         # $20 average (complex math operations)
            'balancer': 18.0,      # $18 average
            'oneinch': 15.0,       # $15 average (aggregator)
            'kyber': 12.0,         # $12 average
            'tinyman': 0.001,      # $0.001 on Algorand
            'pact': 0.001,         # $0.001 on Algorand
            'algofi': 0.001,       # $0.001 on Algorand
            'algox': 0.001,        # $0.001 on Algorand
        }

        base_cost = base_gas_costs.get(dex_protocol, 10.0)

        # Adjust for network congestion (simplified)
        congestion_multiplier = 1.5  # Assume moderate congestion

        # Adjust for token type
        if token in ['USDT', 'USDC']:  # Stablecoins might be cheaper
            token_multiplier = 0.8
        else:
            token_multiplier = 1.0

        return base_cost * congestion_multiplier * token_multiplier

    async def ai_analyze_dex_cex_timing(self, from_exchange: str, to_exchange: str, 
                                       token: str, buy_price: float, sell_price: float) -> Dict[str, Any]:
        """AI analysis for DEX/CEX arbitrage timing"""

        try:
            # Calculate base profitability
            profit_ratio = sell_price / buy_price if buy_price > 0 else 1.0

            # Base confidence from profit size
            base_confidence = min(1.0, max(0.1, (profit_ratio - 1) * 100))  # Convert to 0-1 scale

            # Exchange reliability factors (extended with new protocols)
            reliable_cex = ['binance', 'coinbase', 'kraken']
            reliable_dex = [
                'uniswap_v3', 'uniswap', 'sushiswap', 'pancakeswap',
                'dydx', 'curve', 'balancer', 'oneinch', 'kyber'
            ]

            reliability_score = 1.0
            if from_exchange.lower() in reliable_cex or from_exchange.lower() in reliable_dex:
                reliability_score *= 1.1
            if to_exchange.lower() in reliable_cex or to_exchange.lower() in reliable_dex:
                reliability_score *= 1.1

            # Volatility adjustment
            volatile_tokens = ['BTC', 'ETH']
            volatility_adjustment = 0.9 if token in volatile_tokens else 1.0

            # Final confidence
            final_confidence = min(1.0, base_confidence * reliability_score * volatility_adjustment)

            return {
                'confidence': final_confidence,
                'profit_ratio': profit_ratio,
                'reliability_score': reliability_score,
                'volatility_adjustment': volatility_adjustment,
                'recommended_execution': final_confidence > 0.6
            }

        except Exception as e:
            logger.exception("Error in AI timing analysis: %s", str(e))
            return {'confidence': 0.5, 'recommended_execution': False}

    async def detect_direct_opportunities(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Direct detection of DEX/CEX opportunities without Bellman-Ford
        Adds diagnostic logging for rejected candidates (no behavior change).
        """
        opportunities = []

        try:
            tokens = price_data.get('tokens', [])

            for token in tokens:
                # Get all CEX prices for this token
                cex_prices = {}
                for exchange, exchange_data in price_data.get('cex', {}).items():
                    price_info = self.get_token_price_info(exchange_data, token)
                    if price_info:
                        cex_prices[exchange] = price_info

                # Get all DEX prices for this token
                dex_prices = {}
                for protocol, protocol_data in price_data.get('dex', {}).items():
                    price_info = self.get_token_price_info(protocol_data, token)
                    if price_info:
                        dex_prices[protocol] = price_info

                # Find best arbitrage opportunities
                for cex_exchange, cex_price in cex_prices.items():
                    for dex_protocol, dex_price in dex_prices.items():

                        # CEX -> DEX opportunity
                        cex_to_dex_profit = await self.calculate_arbitrage_profit(
                            token, cex_exchange, dex_protocol,
                            cex_price, dex_price, 'cex_to_dex'
                        )

                        if cex_to_dex_profit.get('profitable'):
                            opportunities.append({
                                'strategy': 'dex_cex',
                                'token': token,
                                'direction': 'cex_to_dex',
                                'buy_exchange': cex_exchange,
                                'sell_exchange': dex_protocol,
                                'profit_pct': cex_to_dex_profit.get('profit_pct', 0),
                                'profit_usd': cex_to_dex_profit.get('profit_usd', 0),
                                'ai_confidence': cex_to_dex_profit.get('confidence')
                            })
                        else:
                            # Diagnostic logging: why candidate rejected
                            logger.debug(
                                "Direct-detect rejected cex->dex candidate: token=%s buy=%s sell=%s profit_pct=%s profit_usd=%s confidence=%s details=%s",
                                token,
                                cex_exchange,
                                dex_protocol,
                                cex_to_dex_profit.get('profit_pct'),
                                cex_to_dex_profit.get('profit_usd'),
                                cex_to_dex_profit.get('confidence'),
                                {k: v for k, v in cex_to_dex_profit.items() if k not in ('profitable',)}
                            )

                        # DEX -> CEX opportunity
                        dex_to_cex_profit = await self.calculate_arbitrage_profit(
                            token, dex_protocol, cex_exchange,
                            dex_price, cex_price, 'dex_to_cex'
                        )

                        if dex_to_cex_profit.get('profitable'):
                            opportunities.append({
                                'strategy': 'dex_cex',
                                'token': token,
                                'direction': 'dex_to_cex',
                                'buy_exchange': dex_protocol,
                                'sell_exchange': cex_exchange,
                                'profit_pct': dex_to_cex_profit.get('profit_pct', 0),
                                'profit_usd': dex_to_cex_profit.get('profit_usd', 0),
                                'ai_confidence': dex_to_cex_profit.get('confidence')
                            })
                        else:
                            # Diagnostic logging: why candidate rejected
                            logger.debug(
                                "Direct-detect rejected dex->cex candidate: token=%s buy=%s sell=%s profit_pct=%s profit_usd=%s confidence=%s details=%s",
                                token,
                                dex_protocol,
                                cex_exchange,
                                dex_to_cex_profit.get('profit_pct'),
                                dex_to_cex_profit.get('profit_usd'),
                                dex_to_cex_profit.get('confidence'),
                                {k: v for k, v in dex_to_cex_profit.items() if k not in ('profitable',)}
                            )

            # Sort by profit percentage
            opportunities.sort(key=lambda x: x.get('profit_pct', 0), reverse=True)
            return opportunities[:10]  # Return top 10

        except Exception as e:
            logger.exception("Error detecting direct DEX/CEX opportunities: %s", str(e))
            return []

    async def calculate_arbitrage_profit(self, token: str, buy_exchange: str, sell_exchange: str,
                                       buy_price_info: Dict, sell_price_info: Dict, 
                                       direction: str) -> Dict[str, Any]:
        """Calculate detailed profit for arbitrage opportunity"""

        try:
            investment_amount = 1000  # $1000 USD equivalent

            if direction == 'cex_to_dex':
                # Buy on CEX, sell on DEX
                buy_price = buy_price_info.get('ask', 0)
                sell_price = sell_price_info.get('bid', 0)
                buy_fee = 0.001  # CEX fee
                sell_fee = sell_price_info.get('fee', 0.003)  # DEX fee
                gas_cost = await self.estimate_dex_gas_cost(sell_exchange, token)

            else:  # dex_to_cex
                # Buy on DEX, sell on CEX
                buy_price = buy_price_info.get('ask', 0)
                sell_price = sell_price_info.get('bid', 0)
                buy_fee = buy_price_info.get('fee', 0.003)  # DEX fee
                sell_fee = 0.001  # CEX fee
                gas_cost = await self.estimate_dex_gas_cost(buy_exchange, token)

            if buy_price <= 0 or sell_price <= 0:
                return {'profitable': False, 'profit_pct': 0}

            # Calculate costs and proceeds
            buy_cost = investment_amount * (1 + buy_fee) + (gas_cost if 'dex' in direction else 0)
            tokens_bought = investment_amount / buy_price

            sell_proceeds = tokens_bought * sell_price * (1 - sell_fee)
            if 'dex' in direction and direction != 'dex_to_cex':
                sell_proceeds -= gas_cost

            # Calculate profit
            profit_usd = sell_proceeds - buy_cost
            profit_pct = (profit_usd / buy_cost) * 100 if buy_cost > 0 else 0

            # AI confidence assessment
            timing_analysis = await self.ai_analyze_dex_cex_timing(
                buy_exchange, sell_exchange, token, buy_price, sell_price
            )

            return {
                'profitable': profit_pct > 0.1,  # At least 0.1% profit
                'profit_pct': profit_pct,
                'profit_usd': profit_usd,
                'buy_cost': buy_cost,
                'sell_proceeds': sell_proceeds,
                'total_fees': buy_fee + sell_fee,
                'gas_cost': gas_cost,
                'confidence': timing_analysis['confidence']
            }

        except Exception as e:
            logger.exception("Error calculating arbitrage profit: %s", str(e))
            return {'profitable': False, 'profit_pct': 0}
