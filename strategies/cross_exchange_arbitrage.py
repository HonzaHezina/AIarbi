import math
import asyncio
from typing import Dict, List, Any, Optional
import logging
from utils.config import get_exchange_fee

logger = logging.getLogger(__name__)

class CrossExchangeArbitrage:
    """
    Strategy 2: Cross-Exchange Arbitrage
    Exploits price differences between different centralized exchanges
    """

    def __init__(self, ai_model):
        self.ai = ai_model
        self.strategy_name = "cross_exchange"

        # Supported CEX exchanges
        self.cex_exchanges = ['binance', 'kraken', 'coinbase', 'kucoin', 'bitfinex']

        # Transfer fees and times (estimated)
        self.transfer_costs = {
            'BTC': {'fee_pct': 0.0001, 'time_minutes': 30},
            'ETH': {'fee_pct': 0.002, 'time_minutes': 15}, 
            'USDT': {'fee_pct': 0.0001, 'time_minutes': 10},
            'USDC': {'fee_pct': 0.0001, 'time_minutes': 10},
            'BNB': {'fee_pct': 0.001, 'time_minutes': 5}
        }
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """Get detailed strategy information for UI display"""
        return {
            'name': 'Cross-Exchange Arbitrage',
            'key': 'cross_exchange',
            'description': 'Exploits price differences between different centralized exchanges (CEX)',
            'how_it_works': 'Finds tokens that are cheaper on one CEX and more expensive on another. Example: Buy ETH on Kraken for $3,000, transfer to Binance and sell for $3,015.',
            'supported_exchanges': {
                'CEX': self.cex_exchanges
            },
            'typical_profit': '0.2% - 1.5%',
            'execution_speed': 'Slow (5-30 minutes)',
            'risk_level': 'Low-Medium',
            'capital_required': '$1,000 - $50,000',
            'fees': {
                'Trading': '0.1% per exchange',
                'Transfer': 'Varies by token (see transfer_costs)',
            },
            'best_conditions': 'Low volatility, price inefficiencies between exchanges',
            'status': 'Active ✅'
        }

    async def add_strategy_edges(self, graph, price_data: Dict[str, Any]):
        """
        Add cross-exchange arbitrage edges to the graph
        """
        try:
            logger.info(" Adding cross-exchange arbitrage edges...")
    
            tokens = price_data.get('tokens', [])
    
            for token in tokens:
                await self.add_cross_exchange_edges_for_token(graph, price_data, token)
    
            logger.info(" Added cross-exchange edges for %d tokens", len(tokens))
    
        except Exception as e:
            logger.exception(" Error adding cross-exchange edges: %s", str(e))

    async def add_cross_exchange_edges_for_token(self, graph, price_data: Dict[str, Any], token: str):
        """Add cross-exchange edges for a specific token"""

        # Get all CEX exchanges that have this token
        available_exchanges = []
        exchange_prices = {}

        for exchange in self.cex_exchanges:
            exchange_data = price_data.get('cex', {}).get(exchange, {})
            token_price = self.get_token_price_info(exchange_data, token)

            if token_price:
                available_exchanges.append(exchange)
                exchange_prices[exchange] = token_price

        # Add edges between all pairs of exchanges
        for i, exchange1 in enumerate(available_exchanges):
            for j, exchange2 in enumerate(available_exchanges):
                if i >= j:  # Avoid duplicates and self-loops
                    continue

                node1 = f"{token}@{exchange1}"
                node2 = f"{token}@{exchange2}"

                if not (graph.has_node(node1) and graph.has_node(node2)):
                    continue

                # Add edge in both directions
                await self.add_directional_edge(
                    graph, node1, node2, exchange1, exchange2, 
                    token, exchange_prices[exchange1], exchange_prices[exchange2]
                )

                await self.add_directional_edge(
                    graph, node2, node1, exchange2, exchange1,
                    token, exchange_prices[exchange2], exchange_prices[exchange1]
                )

    async def add_directional_edge(self, graph, from_node: str, to_node: str,
                                  from_exchange: str, to_exchange: str, token: str,
                                  from_price: Dict, to_price: Dict):
        """Add a directional edge between two exchanges"""

        try:
            # Calculate arbitrage potential: Buy on from_exchange, Sell on to_exchange
            buy_price = from_price.get('ask', 0)  # Buy at ask price
            sell_price = to_price.get('bid', 0)   # Sell at bid price

            if buy_price <= 0 or sell_price <= 0:
                return

            # Get fees and transfer costs
            buy_fee = get_exchange_fee(from_exchange, 'taker')
            sell_fee = get_exchange_fee(to_exchange, 'taker')

            transfer_info = await self.calculate_transfer_cost(token, from_exchange, to_exchange)

            # AI analysis for timing and risk
            ai_analysis = await self.ai_analyze_cross_exchange_opportunity(
                token, from_exchange, to_exchange, buy_price, sell_price, transfer_info
            )

            # Calculate effective rate after all costs
            buy_cost = buy_price * (1 + buy_fee)
            transfer_cost = transfer_info['cost_usd']
            sell_proceeds = sell_price * (1 - sell_fee) - transfer_cost

            if sell_proceeds > buy_cost:  # Profitable
                rate = sell_proceeds / buy_cost

                # Additional validation: For same-token transfers between exchanges,
                # the rate should be very close to 1.0 (allowing for fees and transfer costs).
                # A rate far from 1.0 indicates bad price data.
                # Maximum reasonable profit for cross-exchange: ~5% after all costs
                # So rate should be between 0.8 and 1.1
                if rate < 0.8 or rate > 1.1:
                    logger.warning(
                        "Skipping cross-exchange candidate with unrealistic same-token transfer rate token=%s from=%s to=%s rate=%s buy_cost=%s sell_proceeds=%s buy_price=%s sell_price=%s",
                        token, from_exchange, to_exchange, rate, buy_cost, sell_proceeds, buy_price, sell_price
                    )
                    return

                # Adjust weight with AI confidence and volatility risk
                volatility_risk = self.ai.calculate_volatility_risk(token, transfer_info['time_minutes'])
                adjusted_rate = rate * (1 - volatility_risk) * ai_analysis['confidence']

                weight = -math.log(adjusted_rate)

                graph.add_edge(from_node, to_node,
                             weight=weight,
                             rate=rate,
                             strategy='cross_exchange',
                             buy_exchange=from_exchange,
                             sell_exchange=to_exchange,
                             buy_price=buy_price,
                             sell_price=sell_price,
                             buy_fee=buy_fee,
                             sell_fee=sell_fee,
                             transfer_cost=transfer_cost,
                             transfer_time=transfer_info['time_minutes'],
                             volatility_risk=volatility_risk,
                             ai_confidence=ai_analysis['confidence'],
                             fee=buy_fee + sell_fee,
                             estimated_slippage=0.0005,
                             total_fees=buy_fee + sell_fee)

        except Exception as e:
            logger.exception(" Error adding directional edge %s->%s: %s", from_node, to_node, str(e))

    def get_token_price_info(self, exchange_data: Dict, token: str) -> Optional[Dict]:
        """Extract price info for a token from exchange data"""

        # Try direct token lookup
        if token in exchange_data:
            return exchange_data[token]

        # Try token pair lookup
        for pair, price_info in exchange_data.items():
            if '/' in pair:
                base_token = pair.split('/')[0]
                if base_token == token:
                    return price_info

        return None



    async def calculate_transfer_cost(self, token: str, from_exchange: str, to_exchange: str) -> Dict[str, Any]:
        """Calculate transfer cost and time between exchanges"""

        # Get base transfer info for token
        base_info = self.transfer_costs.get(token, {'fee_pct': 0.01, 'time_minutes': 60})

        # Base transfer fee
        base_fee_pct = base_info['fee_pct']
        base_time = base_info['time_minutes']

        # Exchange-specific adjustments
        fast_exchanges = ['binance', 'coinbase']  # Generally faster
        slow_exchanges = ['kraken']  # Generally slower

        time_multiplier = 1.0
        if from_exchange in slow_exchanges or to_exchange in slow_exchanges:
            time_multiplier *= 1.5
        if from_exchange in fast_exchanges and to_exchange in fast_exchanges:
            time_multiplier *= 0.8

        # Calculate final values
        transfer_time = int(base_time * time_multiplier)

        # Estimate cost in USD (simplified)
        token_prices = {'BTC': 50000, 'ETH': 3000, 'USDT': 1, 'USDC': 1, 'BNB': 300}
        token_price = token_prices.get(token, 100)
        cost_usd = base_fee_pct * token_price

        return {
            'fee_pct': base_fee_pct,
            'time_minutes': transfer_time,
            'cost_usd': cost_usd
        }

    async def ai_analyze_cross_exchange_opportunity(self, token: str, from_exchange: str,
                                                   to_exchange: str, buy_price: float, 
                                                   sell_price: float, transfer_info: Dict) -> Dict[str, Any]:
        """AI analysis for cross-exchange opportunity"""

        try:
            # Calculate raw profit potential
            raw_profit_pct = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0

            # Exchange reliability scoring
            reliable_exchanges = ['binance', 'coinbase', 'kraken']
            reliability_score = 1.0

            if from_exchange.lower() in reliable_exchanges:
                reliability_score *= 1.1
            if to_exchange.lower() in reliable_exchanges:
                reliability_score *= 1.1

            # Time risk scoring (longer transfers = higher risk)
            transfer_time = transfer_info.get('time_minutes', 60)
            time_risk = max(0.5, 1 - (transfer_time / 180))  # Risk increases after 3 hours

            # Volume and liquidity considerations (simplified)
            liquidity_score = 0.9  # Assume good liquidity for major exchanges

            # Calculate overall confidence
            base_confidence = min(1.0, max(0.1, raw_profit_pct / 2))  # Base on profit

            final_confidence = (base_confidence * reliability_score * 
                              time_risk * liquidity_score)

            final_confidence = min(1.0, max(0.1, final_confidence))

            return {
                'confidence': final_confidence,
                'raw_profit_pct': raw_profit_pct,
                'reliability_score': reliability_score,
                'time_risk': time_risk,
                'liquidity_score': liquidity_score,
                'recommended': final_confidence > 0.6 and raw_profit_pct > 0.3
            }

        except Exception as e:
            logger.exception(" Error in AI cross-exchange analysis: %s", str(e))
            return {'confidence': 0.5, 'recommended': False}

    async def detect_simple_opportunities(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simple detection of cross-exchange opportunities without graph
        """
        opportunities = []

        try:
            tokens = price_data.get('tokens', [])

            for token in tokens:
                # Get prices from all exchanges
                exchange_prices = {}

                for exchange in self.cex_exchanges:
                    exchange_data = price_data.get('cex', {}).get(exchange, {})
                    price_info = self.get_token_price_info(exchange_data, token)

                    if price_info and price_info.get('bid', 0) > 0 and price_info.get('ask', 0) > 0:
                        exchange_prices[exchange] = price_info

                if len(exchange_prices) < 2:
                    continue  # Need at least 2 exchanges

                # Find best buy and sell opportunities
                exchanges = list(exchange_prices.keys())

                for i, buy_exchange in enumerate(exchanges):
                    for j, sell_exchange in enumerate(exchanges):
                        if i >= j:  # Avoid duplicates
                            continue

                        buy_price = exchange_prices[buy_exchange]['ask']
                        sell_price = exchange_prices[sell_exchange]['bid']

                        # Calculate profit
                        profit_analysis = await self.calculate_detailed_profit(
                            token, buy_exchange, sell_exchange, 
                            exchange_prices[buy_exchange], exchange_prices[sell_exchange]
                        )

                        if profit_analysis['profitable']:
                            opportunities.append({
                                'strategy': 'cross_exchange',
                                'token': token,
                                'buy_exchange': buy_exchange,
                                'sell_exchange': sell_exchange,
                                'buy_price': buy_price,
                                'sell_price': sell_price,
                                'profit_pct': profit_analysis['profit_pct'],
                                'profit_usd': profit_analysis['profit_usd'],
                                'transfer_time': profit_analysis['transfer_time'],
                                'total_fees': profit_analysis['total_fees'],
                                'ai_confidence': profit_analysis['ai_confidence']
                            })

            # Sort by profit percentage
            opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
            return opportunities[:15]  # Return top 15

        except Exception as e:
            logger.exception(" Error detecting simple cross-exchange opportunities: %s", str(e))
            return []

    async def calculate_detailed_profit(self, token: str, buy_exchange: str, sell_exchange: str,
                                      buy_price_info: Dict, sell_price_info: Dict) -> Dict[str, Any]:
        """Calculate detailed profit analysis for cross-exchange arbitrage"""

        try:
            investment_amount = 1000  # $1000 USD

            buy_price = buy_price_info.get('ask', 0)
            sell_price = sell_price_info.get('bid', 0)

            if buy_price <= 0 or sell_price <= 0:
                return {'profitable': False, 'profit_pct': 0}

            # Calculate fees
            buy_fee = get_exchange_fee(buy_exchange, 'taker')
            sell_fee = get_exchange_fee(sell_exchange, 'taker')

            # Calculate transfer costs
            transfer_info = await self.calculate_transfer_cost(token, buy_exchange, sell_exchange)

            # Calculate costs and proceeds
            tokens_to_buy = investment_amount / buy_price
            buy_cost_total = investment_amount * (1 + buy_fee)

            # After transfer
            transfer_cost = transfer_info['cost_usd']
            tokens_after_transfer = tokens_to_buy  # Assuming no loss during transfer

            # Selling
            gross_sell_proceeds = tokens_after_transfer * sell_price
            net_sell_proceeds = gross_sell_proceeds * (1 - sell_fee) - transfer_cost

            # Calculate profit
            profit_usd = net_sell_proceeds - buy_cost_total
            profit_pct = (profit_usd / buy_cost_total) * 100 if buy_cost_total > 0 else 0

            # AI confidence analysis
            ai_analysis = await self.ai_analyze_cross_exchange_opportunity(
                token, buy_exchange, sell_exchange, buy_price, sell_price, transfer_info
            )

            return {
                'profitable': profit_pct > 0.2,  # At least 0.2% profit
                'profit_pct': profit_pct,
                'profit_usd': profit_usd,
                'buy_cost_total': buy_cost_total,
                'sell_proceeds': net_sell_proceeds,
                'total_fees': buy_fee + sell_fee,
                'transfer_cost': transfer_cost,
                'transfer_time': transfer_info['time_minutes'],
                'ai_confidence': ai_analysis['confidence']
            }

        except Exception as e:
            logger.exception(" Error calculating detailed profit: %s", str(e))
            return {'profitable': False, 'profit_pct': 0}
