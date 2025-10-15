import math
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from itertools import permutations

logger = logging.getLogger(__name__)

class TriangularArbitrage:
    """
    Strategy 3: Triangular Arbitrage
    Exploits price inefficiencies between three currency pairs on the same exchange
    """

    def __init__(self, ai_model):
        self.ai = ai_model
        self.strategy_name = "triangular"

        # Common trading currencies for triangular arbitrage
        self.major_currencies = ['BTC', 'ETH', 'USDT', 'USDC', 'BNB']
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information for UI display"""
        return {
            'name': 'Triangular Arbitrage',
            'key': 'triangular',
            'description': 'Exploits price inefficiencies between three currency pairs on the same exchange',
            'how_it_works': 'Creates a loop of 3 trades that results in profit. Example: USDT → BTC → ETH → USDT, exploiting the cross-rate differences.',
            'supported_exchanges': {
                'All': 'Any CEX or DEX with sufficient trading pairs'
            },
            'typical_profit': '0.1% - 0.8%',
            'execution_speed': 'Fast (1-5 seconds)',
            'risk_level': 'Low',
            'capital_required': '$500 - $20,000',
            'fees': {
                'Trading': '0.1% per trade (3 trades total)',
            },
            'best_conditions': 'High trading volume, active market',
            'status': 'Active ✅'
        }

    async def add_strategy_edges(self, graph, price_data: Dict[str, Any]):
        """Add triangular arbitrage edges to the graph"""
        try:
            logger.info(" Adding triangular arbitrage edges...")
 
            # Add edges for each exchange separately
            cex_exchanges = price_data.get('cex', {})
            dex_protocols = price_data.get('dex', {})
 
            edge_count = 0
            for exchange_name, exchange_data in cex_exchanges.items():
                edges_added = await self.add_triangular_edges_for_exchange(
                    graph, exchange_data, exchange_name, 'cex'
                )
                edge_count += edges_added
 
            for protocol_name, protocol_data in dex_protocols.items():
                edges_added = await self.add_triangular_edges_for_exchange(
                    graph, protocol_data, protocol_name, 'dex'
                )
                edge_count += edges_added
 
            logger.info(" Added %d triangular arbitrage edges", edge_count)
 
        except Exception as e:
            logger.exception(" Error adding triangular edges: %s", str(e))

    async def add_triangular_edges_for_exchange(self, graph, exchange_data: Dict, 
                                              exchange_name: str, exchange_type: str) -> int:
        """Add triangular edges for a specific exchange"""

        edges_added = 0

        try:
            # Extract available currency pairs
            available_pairs = {}
            currencies = set()

            for pair, price_info in exchange_data.items():
                if '/' in pair and 'bid' in price_info and 'ask' in price_info:
                    base, quote = pair.split('/')
                    available_pairs[pair] = price_info
                    currencies.add(base)
                    currencies.add(quote)

            # Focus on major currencies to reduce complexity
            major_currencies_present = [c for c in self.major_currencies if c in currencies]

            # Create triangular paths
            for base_currency in major_currencies_present:
                for intermediate_currency in major_currencies_present:
                    for final_currency in major_currencies_present:

                        if len({base_currency, intermediate_currency, final_currency}) < 3:
                            continue  # Need 3 different currencies

                        # Check if required pairs exist
                        pair1 = f"{base_currency}/{intermediate_currency}"
                        pair2 = f"{intermediate_currency}/{final_currency}" 
                        pair3 = f"{final_currency}/{base_currency}"

                        # Try alternative pair orientations
                        pair1_alt = f"{intermediate_currency}/{base_currency}"
                        pair2_alt = f"{final_currency}/{intermediate_currency}"
                        pair3_alt = f"{base_currency}/{final_currency}"

                        triangle_data = self.find_valid_triangle(
                            available_pairs, pair1, pair2, pair3, pair1_alt, pair2_alt, pair3_alt
                        )

                        if triangle_data:
                            # Add triangular cycle edges
                            cycle_edges = await self.create_triangular_cycle_edges(
                                graph, triangle_data, exchange_name, exchange_type
                            )
                            edges_added += cycle_edges

            return edges_added

        except Exception as e:
            logger.exception(" Error processing triangular edges for %s: %s", exchange_name, str(e))
            return 0

    def find_valid_triangle(self, available_pairs: Dict, pair1: str, pair2: str, pair3: str,
                           pair1_alt: str, pair2_alt: str, pair3_alt: str) -> Optional[Dict]:
        """
        Find a valid triangle configuration.
        
        For a triangular arbitrage path A → B → C → A:
        - We want pair A/B (to convert A to B)
        - We want pair B/C (to convert B to C)
        - We want pair C/A (to convert C to A)
        
        If the exact pairs aren't available, we try their inverses (B/A, C/B, A/C)
        and need to track which action to use for edge weight calculation.
        """

        # For each edge in the triangle, determine the correct action:
        # - 'sell' = selling the base currency of the pair (use bid price)
        # - 'buy' = buying the base currency of the pair (use ask price, then invert)
        #
        # For a triangular path A → B → C → A:
        # - Edge A→B: Want to convert A to B
        #   If pair is A/B: we sell A (action='sell', rate = bid)
        #   If pair is B/A: we buy A in reverse = sell B (action='buy', rate = 1/ask)
        # - Edge B→C: Want to convert B to C
        #   If pair is B/C: we sell B (action='sell', rate = bid)
        #   If pair is C/B: we buy B in reverse = sell C (action='buy', rate = 1/ask)
        # - Edge C→A: Want to convert C to A
        #   If pair is C/A: we sell C (action='sell', rate = bid)
        #   If pair is A/C: we buy C in reverse = sell A (action='buy', rate = 1/ask)
        #
        # IMPORTANT: All edges should use 'sell' if the pair orientation matches
        # the desired conversion direction!
        
        triangle_configs = [
            # Direct pairs: A/B, B/C, C/A - all aligned with conversion direction
            {'pair1': pair1, 'pair2': pair2, 'pair3': pair3, 
             'action1': 'sell', 'action2': 'sell', 'action3': 'sell'},
            # Mixed: B/A (inverted), B/C, A/C (inverted)
            {'pair1': pair1_alt, 'pair2': pair2, 'pair3': pair3_alt,
             'action1': 'buy', 'action2': 'sell', 'action3': 'buy'},
            # Mixed: A/B, C/B (inverted), A/C (inverted)  
            {'pair1': pair1, 'pair2': pair2_alt, 'pair3': pair3_alt,
             'action1': 'sell', 'action2': 'buy', 'action3': 'buy'},
            # Mixed: B/A (inverted), C/B (inverted), C/A
            {'pair1': pair1_alt, 'pair2': pair2_alt, 'pair3': pair3,
             'action1': 'buy', 'action2': 'buy', 'action3': 'sell'},
        ]

        for config in triangle_configs:
            p1, p2, p3 = config['pair1'], config['pair2'], config['pair3']

            if all(pair in available_pairs for pair in [p1, p2, p3]):
                return {
                    'pair1': p1,
                    'pair2': p2, 
                    'pair3': p3,
                    'price1': available_pairs[p1],
                    'price2': available_pairs[p2],
                    'price3': available_pairs[p3],
                    'action1': config['action1'],
                    'action2': config['action2'],
                    'action3': config['action3']
                }

        return None

    async def create_triangular_cycle_edges(self, graph, triangle_data: Dict, 
                                          exchange_name: str, exchange_type: str) -> int:
        """Create edges for triangular cycle"""

        try:
            # Extract currency names from pairs
            pair1 = triangle_data['pair1']  # e.g., BTC/ETH
            pair2 = triangle_data['pair2']  # e.g., ETH/USDT
            pair3 = triangle_data['pair3']  # e.g., USDT/BTC

            # Parse currencies
            curr1_base, curr1_quote = pair1.split('/')
            curr2_base, curr2_quote = pair2.split('/')
            curr3_base, curr3_quote = pair3.split('/')

            # Create nodes
            node1 = f"{curr1_base}@{exchange_name}"
            node2 = f"{curr1_quote}@{exchange_name}" 
            node3 = f"{curr2_quote}@{exchange_name}"

            # Ensure nodes exist in graph
            for node in [node1, node2, node3]:
                if not graph.has_node(node):
                    return 0

            # Calculate triangular profit potential
            profit_analysis = await self.calculate_triangular_profit(triangle_data, exchange_type)

            if not profit_analysis['profitable']:
                return 0

            # Add cycle edges with weights
            edges_added = 0
            
            # Get the action for each edge (determined by find_valid_triangle)
            action1 = triangle_data.get('action1', 'sell')
            action2 = triangle_data.get('action2', 'sell')
            action3 = triangle_data.get('action3', 'buy')

            # Edge 1: curr1_base -> curr1_quote (using pair1)
            rate1, weight1 = self.calculate_edge_weight(
                triangle_data['price1'], action1, exchange_type
            )
            if weight1 is not None:
                graph.add_edge(node1, node2,
                             weight=weight1,
                             rate=rate1,
                             strategy='triangular',
                             exchange=exchange_name,
                             pair=pair1,
                             step=1,
                             action=action1,
                             triangle_id=f"{curr1_base}-{curr1_quote}-{curr2_quote}")
                edges_added += 1

            # Edge 2: curr1_quote -> curr2_quote (using pair2)
            rate2, weight2 = self.calculate_edge_weight(
                triangle_data['price2'], action2, exchange_type
            )
            if weight2 is not None:
                graph.add_edge(node2, node3,
                             weight=weight2,
                             rate=rate2,
                             strategy='triangular', 
                             exchange=exchange_name,
                             pair=pair2,
                             step=2,
                             action=action2,
                             triangle_id=f"{curr1_base}-{curr1_quote}-{curr2_quote}")
                edges_added += 1

            # Edge 3: curr2_quote -> curr1_base (using pair3)
            rate3, weight3 = self.calculate_edge_weight(
                triangle_data['price3'], action3, exchange_type
            )
            if weight3 is not None:
                graph.add_edge(node3, node1,
                             weight=weight3,
                             rate=rate3,
                             strategy='triangular',
                             exchange=exchange_name, 
                             pair=pair3,
                             step=3,
                             action=action3,
                             triangle_id=f"{curr1_base}-{curr1_quote}-{curr2_quote}")
                edges_added += 1

            return edges_added

        except Exception as e:
            logger.exception(" Error creating triangular cycle edges: %s", str(e))
            return 0

    def calculate_edge_weight(self, price_info: Dict, action: str, exchange_type: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate edge weight for triangular arbitrage.
        
        Args:
            price_info: Dict with 'bid', 'ask', and optionally 'fee'
            action: 'sell' or 'buy' - determines which price to use
            exchange_type: 'dex' or 'cex' - determines default fee
            
        Returns:
            (rate, weight) tuple where:
            - rate: conversion rate (how many units of quote per unit of base)
            - weight: -log(effective_rate) for Bellman-Ford
        """
        try:
            # Get the appropriate rate based on action
            if action == 'sell':
                # Selling base currency for quote currency - use bid price
                rate = price_info.get('bid', 0)
            else:  # buy
                # Buying base currency with quote currency - use ask price
                # For 'buy', we need to invert: if BTC/USDT ask is 50000,
                # then buying BTC costs 50000 USDT per BTC, so the rate
                # from USDT to BTC is 1/50000 = 0.00002 BTC per USDT
                ask_price = price_info.get('ask', 0)
                if ask_price > 0:
                    rate = 1 / ask_price
                else:
                    return None, None

            # Validate rate
            if rate <= 0:
                logger.warning(f"Invalid rate {rate} for action '{action}' with price_info: {price_info}")
                return None, None
            
            # Check for extremely high or low rates that indicate data issues
            if rate > 1e6 or rate < 1e-6:
                logger.warning(f"Suspicious rate {rate} for action '{action}'. "
                             f"Price info: bid={price_info.get('bid')}, ask={price_info.get('ask')}. "
                             f"This may indicate price data issues.")
                # Still allow it but log the warning

            # Apply fees
            if exchange_type == 'dex':
                fee = price_info.get('fee', 0.003)  # 0.3% default DEX fee
            else:
                fee = 0.001  # 0.1% default CEX fee

            # Calculate effective rate after fees
            effective_rate = rate * (1 - fee)
            
            # Validate effective rate
            if effective_rate <= 0:
                logger.error(f"Negative or zero effective_rate: rate={rate}, fee={fee}")
                return None, None

            # Calculate weight for Bellman-Ford (negative log)
            weight = -math.log(effective_rate)

            return rate, weight

        except (ValueError, OverflowError, ZeroDivisionError) as e:
            logger.error(f"Math error in calculate_edge_weight: {e}. "
                        f"price_info={price_info}, action={action}")
            return None, None
        except Exception as e:
            logger.exception(f"Unexpected error calculating edge weight: {str(e)}")
            return None, None

    async def calculate_triangular_profit(self, triangle_data: Dict, exchange_type: str) -> Dict[str, Any]:
        """Calculate profit potential for triangular arbitrage"""

        try:
            starting_amount = 1.0  # Start with 1 unit of base currency

            # Step 1: Base -> Intermediate
            price1 = triangle_data['price1']
            rate1 = price1.get('bid', 0)
            fee1 = price1.get('fee', 0.003) if exchange_type == 'dex' else 0.001
            amount_after_step1 = starting_amount * rate1 * (1 - fee1)

            # Step 2: Intermediate -> Final  
            price2 = triangle_data['price2']
            rate2 = price2.get('bid', 0)
            fee2 = price2.get('fee', 0.003) if exchange_type == 'dex' else 0.001
            amount_after_step2 = amount_after_step1 * rate2 * (1 - fee2)

            # Step 3: Final -> Base
            price3 = triangle_data['price3']
            rate3 = price3.get('ask', 0)  # We're buying base currency
            fee3 = price3.get('fee', 0.003) if exchange_type == 'dex' else 0.001

            if rate3 > 0:
                final_amount = amount_after_step2 / rate3 * (1 - fee3)
            else:
                final_amount = 0

            # Calculate profit
            profit = final_amount - starting_amount
            profit_pct = (profit / starting_amount) * 100 if starting_amount > 0 else 0

            return {
                'profitable': profit_pct > 0.1,  # At least 0.1% profit
                'profit_pct': profit_pct,
                'final_amount': final_amount,
                'steps': [
                    {'step': 1, 'rate': rate1, 'fee': fee1, 'amount': amount_after_step1},
                    {'step': 2, 'rate': rate2, 'fee': fee2, 'amount': amount_after_step2}, 
                    {'step': 3, 'rate': rate3, 'fee': fee3, 'amount': final_amount}
                ]
            }

        except Exception as e:
            logger.exception(" Error calculating triangular profit: %s", str(e))
            return {'profitable': False, 'profit_pct': 0}

    async def detect_direct_triangular_opportunities(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Direct detection of triangular opportunities without graph"""

        opportunities = []

        try:
            # Check CEX exchanges
            for exchange_name, exchange_data in price_data.get('cex', {}).items():
                exchange_opportunities = await self.find_triangular_on_exchange(
                    exchange_data, exchange_name, 'cex'
                )
                opportunities.extend(exchange_opportunities)

            # Check DEX protocols
            for protocol_name, protocol_data in price_data.get('dex', {}).items():
                protocol_opportunities = await self.find_triangular_on_exchange(
                    protocol_data, protocol_name, 'dex'
                )
                opportunities.extend(protocol_opportunities)

            # Sort by profit
            opportunities.sort(key=lambda x: x.get('profit_pct', 0), reverse=True)
            return opportunities[:10]  # Top 10

        except Exception as e:
            logger.exception(" Error detecting triangular opportunities: %s", str(e))
            return []

    async def find_triangular_on_exchange(self, exchange_data: Dict, exchange_name: str, 
                                        exchange_type: str) -> List[Dict[str, Any]]:
        """Find triangular opportunities on a single exchange"""

        opportunities = []

        try:
            # Get available pairs
            available_pairs = {pair: info for pair, info in exchange_data.items() 
                             if '/' in pair and 'bid' in info and 'ask' in info}

            # Extract currencies
            currencies = set()
            for pair in available_pairs:
                base, quote = pair.split('/')
                currencies.add(base)
                currencies.add(quote)

            major_currencies = [c for c in self.major_currencies if c in currencies]

            # Test all possible triangular combinations
            for base_curr in major_currencies[:5]:  # Limit to avoid too many combinations
                for inter_curr in major_currencies:
                    for final_curr in major_currencies:

                        if len({base_curr, inter_curr, final_curr}) < 3:
                            continue

                        triangle_data = self.find_valid_triangle(
                            available_pairs,
                            f"{base_curr}/{inter_curr}",
                            f"{inter_curr}/{final_curr}",
                            f"{final_curr}/{base_curr}",
                            f"{inter_curr}/{base_curr}",
                            f"{final_curr}/{inter_curr}",
                            f"{base_curr}/{final_curr}"
                        )

                        if triangle_data:
                            profit_analysis = await self.calculate_triangular_profit(
                                triangle_data, exchange_type
                            )

                            if profit_analysis['profitable']:
                                opportunities.append({
                                    'strategy': 'triangular',
                                    'exchange': exchange_name,
                                    'exchange_type': exchange_type,
                                    'base_currency': base_curr,
                                    'intermediate_currency': inter_curr,
                                    'final_currency': final_curr,
                                    'profit_pct': profit_analysis['profit_pct'],
                                    'cycle_path': f"{base_curr}  {inter_curr}  {final_curr}  {base_curr}",
                                    'pairs_used': [triangle_data['pair1'], triangle_data['pair2'], triangle_data['pair3']],
                                    'execution_steps': profit_analysis.get('steps', [])
                                })

            return opportunities

        except Exception as e:
            logger.exception(" Error finding triangular on %s: %s", exchange_name, str(e))
            return []
