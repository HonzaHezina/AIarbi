import math
import asyncio
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WrappedTokensArbitrage:
    """
    Strategy 4: Wrapped Tokens Arbitrage
    Exploits price differences between native tokens and their wrapped versions
    """

    def __init__(self, ai_model):
        self.ai = ai_model
        self.strategy_name = "wrapped_tokens"

        # Native to wrapped token mappings
        self.wrapped_pairs = {
            'BTC': 'wBTC',
            'ETH': 'wETH', 
            'BNB': 'wBNB'
        }

        # Reverse mapping
        self.native_pairs = {v: k for k, v in self.wrapped_pairs.items()}
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information for UI display"""
        return {
            'name': 'Wrapped Tokens Arbitrage',
            'key': 'wrapped_tokens',
            'description': 'Exploits price differences between native tokens and their wrapped versions',
            'how_it_works': 'Wrapped tokens should have 1:1 value with native tokens, but market inefficiencies create opportunities. Example: Buy wBTC at discount, unwrap to BTC, sell for profit.',
            'supported_pairs': list(self.wrapped_pairs.items()),
            'typical_profit': '0.05% - 0.5%',
            'execution_speed': 'Medium (5-15 seconds)',
            'risk_level': 'Very Low',
            'capital_required': '$1,000 - $50,000',
            'fees': {
                'Wrap/Unwrap': 'Gas fees only ($5-30)',
                'Trading': '0.1%',
            },
            'best_conditions': 'Network congestion, liquidity imbalances',
            'status': 'Active ✅'
        }

    async def add_strategy_edges(self, graph, price_data: Dict[str, Any]):
        """Add wrapped token arbitrage edges to the graph"""

        try:
            logger.info(" Adding wrapped token arbitrage edges...")
 
            edges_added = 0
 
            # Add wrap/unwrap edges within DEX protocols
            edges_added += await self.add_wrap_unwrap_edges(graph, price_data)
 
            # Add cross-exchange edges for wrapped tokens
            edges_added += await self.add_wrapped_cross_exchange_edges(graph, price_data)
 
            # Add native vs wrapped arbitrage edges
            edges_added += await self.add_native_wrapped_arbitrage_edges(graph, price_data)
 
            logger.info(" Added %d wrapped token edges", edges_added)
 
        except Exception as e:
            logger.exception(" Error adding wrapped token edges: %s", str(e))

    async def add_wrap_unwrap_edges(self, graph, price_data: Dict[str, Any]) -> int:
        """Add wrap/unwrap edges within DEX protocols"""

        edges_added = 0

        try:
            dex_protocols = price_data.get('dex', {})

            for protocol_name, protocol_data in dex_protocols.items():
                for native_token, wrapped_token in self.wrapped_pairs.items():

                    native_node = f"{native_token}@{protocol_name}"
                    wrapped_node = f"{wrapped_token}@{protocol_name}"

                    if not (graph.has_node(native_node) and graph.has_node(wrapped_node)):
                        continue

                    # Estimate wrap/unwrap costs
                    wrap_cost = await self.estimate_wrap_cost(protocol_name, native_token)

                    if wrap_cost['feasible']:
                        # Native -> Wrapped (wrap operation)
                        wrap_rate = 1.0 - wrap_cost['fee_pct'] - wrap_cost['gas_cost_pct']
                        wrap_weight = -math.log(wrap_rate)

                        graph.add_edge(native_node, wrapped_node,
                                     weight=wrap_weight,
                                     rate=wrap_rate,
                                     strategy='wrapped_tokens',
                                     operation='wrap',
                                     protocol=protocol_name,
                                     gas_cost_usd=wrap_cost['gas_cost_usd'],
                                     fee_pct=wrap_cost['fee_pct'])
                        edges_added += 1

                        # Wrapped -> Native (unwrap operation)
                        unwrap_rate = 1.0 - wrap_cost['fee_pct'] - wrap_cost['gas_cost_pct']
                        unwrap_weight = -math.log(unwrap_rate)

                        graph.add_edge(wrapped_node, native_node,
                                     weight=unwrap_weight,
                                     rate=unwrap_rate,
                                     strategy='wrapped_tokens',
                                     operation='unwrap',
                                     protocol=protocol_name,
                                     gas_cost_usd=wrap_cost['gas_cost_usd'],
                                     fee_pct=wrap_cost['fee_pct'])
                        edges_added += 1

            return edges_added

        except Exception as e:
            logger.exception(" Error adding wrap/unwrap edges: %s", str(e))
            return 0

    async def add_wrapped_cross_exchange_edges(self, graph, price_data: Dict[str, Any]) -> int:
        """Add arbitrage edges between wrapped tokens on different exchanges"""

        edges_added = 0

        try:
            for native_token, wrapped_token in self.wrapped_pairs.items():

                # Get all exchanges/protocols that support this wrapped token
                wrapped_locations = []

                # Check CEX exchanges
                for exchange, exchange_data in price_data.get('cex', {}).items():
                    if self.token_available(exchange_data, wrapped_token):
                        wrapped_locations.append({
                            'name': exchange,
                            'type': 'cex',
                            'data': self.get_token_price_info(exchange_data, wrapped_token)
                        })

                # Check DEX protocols
                for protocol, protocol_data in price_data.get('dex', {}).items():
                    if self.token_available(protocol_data, wrapped_token):
                        wrapped_locations.append({
                            'name': protocol,
                            'type': 'dex', 
                            'data': self.get_token_price_info(protocol_data, wrapped_token)
                        })

                # Add arbitrage edges between locations
                for i, loc1 in enumerate(wrapped_locations):
                    for j, loc2 in enumerate(wrapped_locations):
                        if i >= j:
                            continue

                        node1 = f"{wrapped_token}@{loc1['name']}"
                        node2 = f"{wrapped_token}@{loc2['name']}"

                        if graph.has_node(node1) and graph.has_node(node2):

                            # Add bidirectional edges
                            edge1_added = await self.add_wrapped_exchange_edge(
                                graph, node1, node2, loc1, loc2, wrapped_token
                            )
                            edge2_added = await self.add_wrapped_exchange_edge(
                                graph, node2, node1, loc2, loc1, wrapped_token
                            )

                            edges_added += edge1_added + edge2_added

            return edges_added

        except Exception as e:
            logger.exception(" Error adding wrapped cross-exchange edges: %s", str(e))
            return 0

    async def add_wrapped_exchange_edge(self, graph, from_node: str, to_node: str,
                                       from_loc: Dict, to_loc: Dict, token: str) -> int:
        """Add single wrapped token exchange edge"""

        try:
            buy_price = from_loc['data'].get('ask', 0)
            sell_price = to_loc['data'].get('bid', 0)

            if buy_price <= 0 or sell_price <= 0:
                return 0

            # Calculate transfer and trading costs
            transfer_cost = await self.calculate_wrapped_transfer_cost(
                token, from_loc['name'], to_loc['name'], from_loc['type'], to_loc['type']
            )

            if not transfer_cost['feasible']:
                return 0

            # Calculate effective rate
            buy_fee = 0.001 if from_loc['type'] == 'cex' else from_loc['data'].get('fee', 0.003)
            sell_fee = 0.001 if to_loc['type'] == 'cex' else to_loc['data'].get('fee', 0.003)

            buy_cost = buy_price * (1 + buy_fee)
            transfer_cost_total = transfer_cost['cost_usd'] + transfer_cost['gas_cost_usd']
            sell_proceeds = sell_price * (1 - sell_fee) - transfer_cost_total

            if sell_proceeds > buy_cost:
                rate = sell_proceeds / buy_cost
                
                # Validation: Same wrapped token transfers should have rates close to 1.0
                # Maximum reasonable difference: ~5% after all costs
                if rate < 0.8 or rate > 1.1:
                    logger.warning(
                        "Skipping wrapped token transfer with unrealistic rate token=%s from=%s to=%s rate=%s buy_cost=%s sell_proceeds=%s",
                        token, from_loc['name'], to_loc['name'], rate, buy_cost, sell_proceeds
                    )
                    return 0
                
                weight = -math.log(rate)

                graph.add_edge(from_node, to_node,
                             weight=weight,
                             rate=rate,
                             strategy='wrapped_tokens',
                             operation='transfer',
                             from_exchange=from_loc['name'],
                             to_exchange=to_loc['name'],
                             transfer_cost=transfer_cost_total,
                             transfer_time=transfer_cost['time_minutes'])
                return 1

            return 0

        except Exception as e:
            logger.exception(" Error adding wrapped exchange edge: %s", str(e))
            return 0

    async def add_native_wrapped_arbitrage_edges(self, graph, price_data: Dict[str, Any]) -> int:
        """Add arbitrage edges between native and wrapped versions across exchanges"""

        edges_added = 0

        try:
            for native_token, wrapped_token in self.wrapped_pairs.items():

                # Find native token on CEX
                native_locations = []
                for exchange, exchange_data in price_data.get('cex', {}).items():
                    if self.token_available(exchange_data, native_token):
                        native_locations.append({
                            'name': exchange,
                            'type': 'cex',
                            'token': native_token,
                            'data': self.get_token_price_info(exchange_data, native_token)
                        })

                # Find wrapped token on DEX
                wrapped_locations = []
                for protocol, protocol_data in price_data.get('dex', {}).items():
                    if self.token_available(protocol_data, wrapped_token):
                        wrapped_locations.append({
                            'name': protocol,
                            'type': 'dex',
                            'token': wrapped_token,
                            'data': self.get_token_price_info(protocol_data, wrapped_token)
                        })

                # Create arbitrage paths: CEX native <-> DEX wrapped
                for native_loc in native_locations:
                    for wrapped_loc in wrapped_locations:

                        native_node = f"{native_token}@{native_loc['name']}"
                        wrapped_node = f"{wrapped_token}@{wrapped_loc['name']}"

                        if graph.has_node(native_node) and graph.has_node(wrapped_node):

                            # Path 1: Native CEX -> Wrapped DEX (buy native, wrap, sell wrapped)
                            path1_edges = await self.create_native_to_wrapped_path(
                                graph, native_node, wrapped_node, native_loc, wrapped_loc
                            )
                            edges_added += path1_edges

                            # Path 2: Wrapped DEX -> Native CEX (buy wrapped, unwrap, sell native)
                            path2_edges = await self.create_wrapped_to_native_path(
                                graph, wrapped_node, native_node, wrapped_loc, native_loc
                            )
                            edges_added += path2_edges

            return edges_added

        except Exception as e:
            logger.exception(" Error adding native-wrapped arbitrage edges: %s", str(e))
            return 0

    async def create_native_to_wrapped_path(self, graph, native_node: str, wrapped_node: str,
                                          native_loc: Dict, wrapped_loc: Dict) -> int:
        """Create path from native token to wrapped token"""

        try:
            native_price = native_loc['data'].get('ask', 0)  # Buy native
            wrapped_price = wrapped_loc['data'].get('bid', 0)  # Sell wrapped

            if native_price <= 0 or wrapped_price <= 0:
                return 0

            # Calculate costs
            native_fee = 0.001  # CEX fee
            wrapped_fee = wrapped_loc['data'].get('fee', 0.003)  # DEX fee

            # Wrap cost
            wrap_cost = await self.estimate_wrap_cost(wrapped_loc['name'], native_loc['token'])

            # Transfer cost (native CEX -> DEX)
            transfer_cost = await self.estimate_native_transfer_cost(native_loc['token'])

            # Calculate effective rate
            buy_cost = native_price * (1 + native_fee) + transfer_cost['cost_usd']
            wrap_cost_total = wrap_cost['gas_cost_usd']
            sell_proceeds = wrapped_price * (1 - wrapped_fee - wrap_cost['fee_pct'])

            if sell_proceeds > (buy_cost + wrap_cost_total):
                rate = sell_proceeds / (buy_cost + wrap_cost_total)
                
                # Validation: Native<->Wrapped conversions should have rates close to 1.0
                # Maximum reasonable difference: ~5% after all costs
                if rate < 0.8 or rate > 1.1:
                    logger.warning(
                        "Skipping native->wrapped with unrealistic rate token=%s rate=%s buy_cost=%s sell_proceeds=%s native_price=%s wrapped_price=%s",
                        native_loc['token'], rate, buy_cost, sell_proceeds, native_price, wrapped_price
                    )
                    return 0
                
                weight = -math.log(rate)

                graph.add_edge(native_node, wrapped_node,
                             weight=weight,
                             rate=rate,
                             strategy='wrapped_tokens',
                             operation='native_to_wrapped',
                             wrap_cost=wrap_cost_total,
                             transfer_cost=transfer_cost['cost_usd'])
                return 1

            return 0

        except Exception as e:
            logger.exception(" Error creating native to wrapped path: %s", str(e))
            return 0

    async def create_wrapped_to_native_path(self, graph, wrapped_node: str, native_node: str,
                                          wrapped_loc: Dict, native_loc: Dict) -> int:
        """Create path from wrapped token to native token"""

        try:
            wrapped_price = wrapped_loc['data'].get('ask', 0)  # Buy wrapped
            native_price = native_loc['data'].get('bid', 0)    # Sell native

            if wrapped_price <= 0 or native_price <= 0:
                return 0

            # Calculate costs
            wrapped_fee = wrapped_loc['data'].get('fee', 0.003)  # DEX fee
            native_fee = 0.001  # CEX fee

            # Unwrap cost
            unwrap_cost = await self.estimate_wrap_cost(wrapped_loc['name'], native_loc['token'])

            # Transfer cost (DEX -> native CEX)
            transfer_cost = await self.estimate_native_transfer_cost(native_loc['token'])

            # Calculate effective rate
            buy_cost = wrapped_price * (1 + wrapped_fee)
            unwrap_cost_total = unwrap_cost['gas_cost_usd'] 
            sell_proceeds = native_price * (1 - native_fee) - transfer_cost['cost_usd']

            if sell_proceeds > (buy_cost + unwrap_cost_total):
                rate = sell_proceeds / (buy_cost + unwrap_cost_total)
                
                # Validation: Native<->Wrapped conversions should have rates close to 1.0
                # Maximum reasonable difference: ~5% after all costs
                if rate < 0.8 or rate > 1.1:
                    logger.warning(
                        "Skipping wrapped->native with unrealistic rate token=%s rate=%s buy_cost=%s sell_proceeds=%s wrapped_price=%s native_price=%s",
                        wrapped_loc['token'], rate, buy_cost, sell_proceeds, wrapped_price, native_price
                    )
                    return 0
                
                weight = -math.log(rate)

                graph.add_edge(wrapped_node, native_node,
                             weight=weight,
                             rate=rate,
                             strategy='wrapped_tokens',
                             operation='wrapped_to_native',
                             unwrap_cost=unwrap_cost_total,
                             transfer_cost=transfer_cost['cost_usd'])
                return 1

            return 0

        except Exception as e:
            logger.exception(" Error creating wrapped to native path: %s", str(e))
            return 0

    def token_available(self, exchange_data: Dict, token: str) -> bool:
        """Check if token is available on exchange"""

        if token in exchange_data:
            return True

        for pair in exchange_data.keys():
            if '/' in pair and pair.split('/')[0] == token:
                return True

        return False

    def get_token_price_info(self, exchange_data: Dict, token: str) -> Optional[Dict]:
        """Get price info for token"""

        if token in exchange_data:
            return exchange_data[token]

        for pair, price_info in exchange_data.items():
            if '/' in pair and pair.split('/')[0] == token:
                return price_info

        return None

    async def estimate_wrap_cost(self, protocol: str, token: str) -> Dict[str, Any]:
        """Estimate cost of wrap/unwrap operations"""

        # Gas costs for different protocols (USD)
        gas_costs = {
            'uniswap_v3': 15.0,
            'sushiswap': 12.0,
            'pancakeswap': 0.5  # BSC is cheaper
        }

        base_gas_cost = gas_costs.get(protocol, 10.0)

        # Wrap/unwrap typically cheaper than swaps
        wrap_gas_cost = base_gas_cost * 0.6

        # Fee percentage (usually minimal for wrap/unwrap)
        fee_pct = 0.0001  # 0.01%

        # Convert to percentage of token value
        token_values = {'BTC': 50000, 'ETH': 3000, 'BNB': 300}
        token_value = token_values.get(token, 1000)
        gas_cost_pct = wrap_gas_cost / token_value

        return {
            'feasible': wrap_gas_cost < (token_value * 0.01),  # Gas cost < 1% of token value
            'gas_cost_usd': wrap_gas_cost,
            'gas_cost_pct': gas_cost_pct,
            'fee_pct': fee_pct
        }

    async def calculate_wrapped_transfer_cost(self, token: str, from_exchange: str, 
                                            to_exchange: str, from_type: str, to_type: str) -> Dict[str, Any]:
        """Calculate transfer cost for wrapped tokens"""

        # Base transfer costs
        base_costs = {
            'wBTC': 0.0001,  # BTC network fee
            'wETH': 0.005,   # ETH network fee  
            'wBNB': 0.001    # BSC network fee
        }

        base_cost_pct = base_costs.get(token, 0.01)

        # Gas costs for different networks
        if 'wBTC' in token:
            gas_cost = 5.0  # Lower for BTC transfers
        elif 'wETH' in token:
            gas_cost = 15.0  # Higher for ETH
        else:
            gas_cost = 10.0

        # Time estimates
        time_minutes = 30 if from_type == 'dex' or to_type == 'dex' else 15

        return {
            'feasible': True,
            'cost_pct': base_cost_pct,
            'cost_usd': base_cost_pct * 1000,  # Assume $1000 value
            'gas_cost_usd': gas_cost,
            'time_minutes': time_minutes
        }

    async def estimate_native_transfer_cost(self, token: str) -> Dict[str, Any]:
        """Estimate transfer cost for native tokens"""

        costs = {
            'BTC': {'cost_usd': 5.0, 'time_minutes': 60},
            'ETH': {'cost_usd': 15.0, 'time_minutes': 15},
            'BNB': {'cost_usd': 0.5, 'time_minutes': 5}
        }

        return costs.get(token, {'cost_usd': 10.0, 'time_minutes': 30})

    async def detect_direct_opportunities(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Direct detection of wrapped token opportunities"""

        opportunities = []

        try:
            for native_token, wrapped_token in self.wrapped_pairs.items():

                # Find native prices on CEX
                native_prices = {}
                for exchange, exchange_data in price_data.get('cex', {}).items():
                    price_info = self.get_token_price_info(exchange_data, native_token)
                    if price_info:
                        native_prices[exchange] = price_info

                # Find wrapped prices on DEX
                wrapped_prices = {}
                for protocol, protocol_data in price_data.get('dex', {}).items():
                    price_info = self.get_token_price_info(protocol_data, wrapped_token)
                    if price_info:
                        wrapped_prices[protocol] = price_info

                # Calculate arbitrage opportunities
                for native_exchange, native_price in native_prices.items():
                    for wrapped_protocol, wrapped_price in wrapped_prices.items():

                        # Native -> Wrapped opportunity
                        opp1 = await self.calculate_native_wrapped_profit(
                            native_token, wrapped_token, native_exchange, wrapped_protocol,
                            native_price, wrapped_price, 'native_to_wrapped'
                        )

                        if opp1['profitable']:
                            opportunities.append({
                                'strategy': 'wrapped_tokens',
                                'direction': 'native_to_wrapped',
                                'native_token': native_token,
                                'wrapped_token': wrapped_token,
                                'buy_exchange': native_exchange,
                                'sell_exchange': wrapped_protocol,
                                'profit_pct': opp1['profit_pct'],
                                'total_costs': opp1['total_costs']
                            })

                        # Wrapped -> Native opportunity
                        opp2 = await self.calculate_native_wrapped_profit(
                            wrapped_token, native_token, wrapped_protocol, native_exchange,
                            wrapped_price, native_price, 'wrapped_to_native'
                        )

                        if opp2['profitable']:
                            opportunities.append({
                                'strategy': 'wrapped_tokens',
                                'direction': 'wrapped_to_native',
                                'native_token': native_token,
                                'wrapped_token': wrapped_token,
                                'buy_exchange': wrapped_protocol,
                                'sell_exchange': native_exchange,
                                'profit_pct': opp2['profit_pct'],
                                'total_costs': opp2['total_costs']
                            })

            opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
            return opportunities[:8]  # Top 8

        except Exception as e:
            logger.exception(" Error detecting wrapped token opportunities: %s", str(e))
            return []

    async def calculate_native_wrapped_profit(self, buy_token: str, sell_token: str,
                                            buy_exchange: str, sell_exchange: str,
                                            buy_price_info: Dict, sell_price_info: Dict,
                                            direction: str) -> Dict[str, Any]:
        """Calculate profit for native-wrapped arbitrage"""

        try:
            investment = 1000  # $1000

            buy_price = buy_price_info.get('ask', 0)
            sell_price = sell_price_info.get('bid', 0)

            if buy_price <= 0 or sell_price <= 0:
                return {'profitable': False}

            # Calculate all costs
            if direction == 'native_to_wrapped':
                buy_fee = 0.001  # CEX fee
                sell_fee = sell_price_info.get('fee', 0.003)  # DEX fee
                wrap_cost = await self.estimate_wrap_cost(sell_exchange, buy_token.replace('w', ''))
                transfer_cost = await self.estimate_native_transfer_cost(buy_token)

                total_costs = (investment * buy_fee + 
                             wrap_cost['gas_cost_usd'] + 
                             transfer_cost['cost_usd'] +
                             sell_price * sell_fee)

            else:  # wrapped_to_native
                buy_fee = buy_price_info.get('fee', 0.003)  # DEX fee
                sell_fee = 0.001  # CEX fee
                unwrap_cost = await self.estimate_wrap_cost(buy_exchange, sell_token)
                transfer_cost = await self.estimate_native_transfer_cost(sell_token)

                total_costs = (investment * buy_fee + 
                             unwrap_cost['gas_cost_usd'] + 
                             transfer_cost['cost_usd'] +
                             sell_price * sell_fee)

            # Calculate profit
            tokens_bought = investment / buy_price
            sell_proceeds = tokens_bought * sell_price
            net_profit = sell_proceeds - investment - total_costs
            profit_pct = (net_profit / investment) * 100 if investment > 0 else 0

            return {
                'profitable': profit_pct > 0.2,  # At least 0.2%
                'profit_pct': profit_pct,
                'net_profit': net_profit,
                'total_costs': total_costs
            }

        except Exception as e:
            logger.exception(" Error calculating wrapped profit: %s", str(e))
            return {'profitable': False}
