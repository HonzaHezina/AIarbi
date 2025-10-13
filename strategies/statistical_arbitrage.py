import math
import asyncio
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

class StatisticalArbitrage:
    """
    Strategy 5: Statistical Arbitrage with AI
    Uses historical data and AI to detect price correlation anomalies
    """

    def __init__(self, ai_model):
        self.ai = ai_model
        self.strategy_name = "statistical"

        # Historical data storage
        self.price_history = {}  # {token@exchange: deque of prices}
        self.correlation_cache = {}

        # Parameters
        self.lookback_periods = 100  # Number of data points to analyze
        self.correlation_threshold = 0.7  # Minimum correlation to consider
        self.deviation_threshold = 2.0  # Standard deviations for anomaly

    async def add_strategy_edges(self, graph, price_data: Dict[str, Any]):
        """Add statistical arbitrage signals as edge weight modifications"""

        try:
            logger.info(" Adding statistical arbitrage signals...")

            # Update historical data first
            self.update_historical_data(price_data)

            # Detect statistical anomalies
            anomalies = await self.detect_statistical_anomalies(price_data)

            # Modify existing graph edges based on statistical signals
            edges_modified = self.apply_statistical_signals_to_graph(graph, anomalies)

            logger.info(f" Applied statistical signals to {edges_modified} edges")

        except Exception as e:
            logger.exception(f" Error adding statistical arbitrage signals: {str(e)}")

    def update_historical_data(self, price_data: Dict[str, Any]):
        """Update historical price data for statistical analysis"""

        try:
            timestamp = datetime.now()
    
            # Ensure price_data is a dictionary
            if not isinstance(price_data, dict):
                raise TypeError(" Expected price_data to be a dictionary, but got a different type")
    
            # Debugging: Log the type of price_data
            logger.debug(f" Debug: price_data type: {type(price_data)}")
     
            # Debugging: Log the structure of price_data
            logger.debug(f" Debug: price_data content: {price_data}")
    
            # Validate price data sections (only 'cex' and 'dex' expected to contain pair dicts)
            cex_section = price_data.get('cex', {})
            dex_section = price_data.get('dex', {})
    
            if not isinstance(cex_section, dict) or not isinstance(dex_section, dict):
                raise ValueError(" Price data missing 'cex' or 'dex' dictionary sections")
    
            # Helper to check if a market section contains at least one exchange with pair dicts
            def _has_valid_market(section):
                for exchange_data in section.values():
                    if isinstance(exchange_data, dict) and any(isinstance(v, dict) for v in exchange_data.values()):
                        return True
                return False
    
            if not (_has_valid_market(cex_section) or _has_valid_market(dex_section)):
                raise ValueError(" Price data contains no valid market pair data")

            # Update CEX data
            for exchange, exchange_data in price_data.get('cex', {}).items():
                # Debugging: Log the type of exchange_data
                logger.debug(f" Debug: {exchange} data type: {type(exchange_data)}")
 
                # Ensure exchange_data is a dictionary
                if not isinstance(exchange_data, dict):
                    logger.warning(f" Error: Expected dictionary for {exchange}, but got {type(exchange_data)}")
                    continue

                for pair, price_info in exchange_data.items():
                    if '/' in pair:
                        token = pair.split('/')[0]
                        key = f"{token}@{exchange}"

                        if key not in self.price_history:
                            self.price_history[key] = deque(maxlen=self.lookback_periods)

                        price = price_info.get('last', (price_info.get('bid', 0) + price_info.get('ask', 0)) / 2)

                        if price > 0:
                            self.price_history[key].append({
                                'price': price,
                                'timestamp': timestamp,
                                'volume': price_info.get('volume', 0)
                            })

            # Update DEX data
            for protocol, protocol_data in price_data.get('dex', {}).items():
                # Debugging: Log the type of protocol_data
                logger.debug(f" Debug: {protocol} data type: {type(protocol_data)}")
 
                # Ensure protocol_data is a dictionary
                if not isinstance(protocol_data, dict):
                    logger.warning(f" Error: Expected dictionary for {protocol}, but got {type(protocol_data)}")
                    continue

                for pair, price_info in protocol_data.items():
                    if '/' in pair:
                        token = pair.split('/')[0]
                        key = f"{token}@{protocol}"

                        if key not in self.price_history:
                            self.price_history[key] = deque(maxlen=self.lookback_periods)

                        price = price_info.get('last', (price_info.get('bid', 0) + price_info.get('ask', 0)) / 2)

                        if price > 0:
                            self.price_history[key].append({
                                'price': price,
                                'timestamp': timestamp,
                                'volume': price_info.get('volume', 0)
                            })

        except Exception as e:
            logger.exception(f" Error updating historical data: {str(e)}")

    async def detect_statistical_anomalies(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect statistical anomalies between correlated trading pairs"""

        anomalies = []

        try:
            tokens = price_data.get('tokens', [])

            for token in tokens:
                # Get all exchanges/protocols for this token
                token_locations = []

                for exchange in price_data.get('cex', {}):
                    key = f"{token}@{exchange}"
                    if key in self.price_history and len(self.price_history[key]) > 20:
                        token_locations.append({
                            'key': key,
                            'exchange': exchange,
                            'type': 'cex',
                            'current_price': self.get_current_price(key)
                        })

                for protocol in price_data.get('dex', {}):
                    key = f"{token}@{protocol}"
                    if key in self.price_history and len(self.price_history[key]) > 20:
                        token_locations.append({
                            'key': key,
                            'exchange': protocol,
                            'type': 'dex',
                            'current_price': self.get_current_price(key)
                        })

                # Analyze correlations and deviations
                for i, loc1 in enumerate(token_locations):
                    for j, loc2 in enumerate(token_locations):
                        if i >= j:
                            continue

                        anomaly = await self.analyze_price_pair_correlation(loc1, loc2, token)

                        if anomaly:
                            anomalies.append(anomaly)

            return anomalies

        except Exception as e:
            logger.exception(f" Error detecting statistical anomalies: {str(e)}")
            return []

    async def analyze_price_pair_correlation(self, loc1: Dict, loc2: Dict, token: str) -> Optional[Dict[str, Any]]:
        """Analyze correlation between two price series"""

        try:
            key1, key2 = loc1['key'], loc2['key']

            # Get price series
            prices1 = [point['price'] for point in self.price_history[key1]]
            prices2 = [point['price'] for point in self.price_history[key2]]

            # Ensure same length
            min_length = min(len(prices1), len(prices2))
            if min_length < 20:
                return None

            prices1 = prices1[-min_length:]
            prices2 = prices2[-min_length:]

            # Calculate correlation
            correlation = np.corrcoef(prices1, prices2)[0, 1]

            if abs(correlation) < self.correlation_threshold:
                return None  # Not correlated enough

            # Calculate current deviation
            price_ratio = loc1['current_price'] / loc2['current_price'] if loc2['current_price'] > 0 else 1
            historical_ratios = [p1/p2 for p1, p2 in zip(prices1, prices2) if p2 > 0]

            if len(historical_ratios) < 10:
                return None

            mean_ratio = np.mean(historical_ratios)
            std_ratio = np.std(historical_ratios)

            if std_ratio == 0:
                return None

            z_score = (price_ratio - mean_ratio) / std_ratio

            if abs(z_score) > self.deviation_threshold:

                # AI analysis of the anomaly
                ai_assessment = await self.ai_assess_statistical_anomaly(
                    token, loc1, loc2, correlation, z_score, mean_ratio, price_ratio
                )

                return {
                    'token': token,
                    'location1': loc1,
                    'location2': loc2,
                    'correlation': correlation,
                    'z_score': z_score,
                    'current_ratio': price_ratio,
                    'mean_ratio': mean_ratio,
                    'deviation_sigma': abs(z_score),
                    'direction': 'overpriced' if z_score > 0 else 'underpriced',
                    'ai_confidence': ai_assessment['confidence'],
                    'predicted_reversion_time': ai_assessment['reversion_time_minutes'],
                    'recommended_action': ai_assessment['action']
                }

            return None

        except Exception as e:
            logger.exception(f" Error analyzing price pair correlation: {str(e)}")
            return None

    def get_current_price(self, key: str) -> float:
        """Get current price for a key"""
        if key in self.price_history and len(self.price_history[key]) > 0:
            return self.price_history[key][-1]['price']
        return 0

    async def ai_assess_statistical_anomaly(self, token: str, loc1: Dict, loc2: Dict,
                                          correlation: float, z_score: float,
                                          mean_ratio: float, current_ratio: float) -> Dict[str, Any]:
        """AI assessment of statistical anomaly"""

        try:
            # Base confidence from z-score magnitude
            base_confidence = min(1.0, abs(z_score) / 3.0)  # Higher z-score = higher confidence

            # Adjust for correlation strength
            correlation_adjustment = abs(correlation)

            # Adjust for exchange type combinations
            type_adjustment = 1.0
            if loc1['type'] != loc2['type']:  # CEX vs DEX
                type_adjustment = 1.2  # More interesting

            # Adjust for token volatility
            volatile_tokens = ['BTC', 'ETH']
            volatility_adjustment = 0.9 if token in volatile_tokens else 1.0

            final_confidence = min(1.0, base_confidence * correlation_adjustment * 
                                 type_adjustment * volatility_adjustment)

            # Predict reversion time (simplified)
            if abs(z_score) > 3.0:
                reversion_time = 30  # 30 minutes for extreme deviations
            elif abs(z_score) > 2.5:
                reversion_time = 60  # 1 hour
            else:
                reversion_time = 180  # 3 hours

            # Recommend action
            if z_score > 0:
                # loc1 overpriced relative to loc2
                action = f"SELL_{loc1['exchange']}_BUY_{loc2['exchange']}"
            else:
                # loc1 underpriced relative to loc2
                action = f"BUY_{loc1['exchange']}_SELL_{loc2['exchange']}"

            return {
                'confidence': final_confidence,
                'reversion_time_minutes': reversion_time,
                'action': action,
                'base_confidence': base_confidence,
                'correlation_strength': abs(correlation)
            }

        except Exception as e:
            logger.exception(f" Error in AI anomaly assessment: {str(e)}")
            return {
                'confidence': 0.5,
                'reversion_time_minutes': 120,
                'action': 'HOLD'
            }

    def apply_statistical_signals_to_graph(self, graph, anomalies: List[Dict[str, Any]]) -> int:
        """Apply statistical signals to modify graph edge weights"""

        edges_modified = 0

        try:
            for anomaly in anomalies:
                if anomaly['ai_confidence'] < 0.6:
                    continue  # Skip low confidence anomalies

                token = anomaly['token']
                loc1 = anomaly['location1']
                loc2 = anomaly['location2']

                node1 = f"{token}@{loc1['exchange']}"
                node2 = f"{token}@{loc2['exchange']}"

                # Check if edge exists in graph
                if graph.has_edge(node1, node2):
                    # Strengthen the edge based on statistical signal
                    current_weight = graph[node1][node2].get('weight', 0)

                    # Adjust weight based on anomaly strength and direction
                    confidence_multiplier = 1.0 - (anomaly['ai_confidence'] * 0.2)

                    if anomaly['direction'] == 'overpriced':
                        # Favor selling on node1, buying on node2
                        adjusted_weight = current_weight * confidence_multiplier
                    else:
                        # Favor buying on node1, selling on node2  
                        adjusted_weight = current_weight * confidence_multiplier

                    graph[node1][node2]['weight'] = adjusted_weight
                    graph[node1][node2]['statistical_signal'] = True
                    graph[node1][node2]['anomaly_confidence'] = anomaly['ai_confidence']

                    edges_modified += 1

                # Check reverse edge
                if graph.has_edge(node2, node1):
                    current_weight = graph[node2][node1].get('weight', 0)

                    confidence_multiplier = 1.0 - (anomaly['ai_confidence'] * 0.2)

                    if anomaly['direction'] == 'underpriced':
                        # Favor the reverse direction
                        adjusted_weight = current_weight * confidence_multiplier
                    else:
                        adjusted_weight = current_weight * confidence_multiplier

                    graph[node2][node1]['weight'] = adjusted_weight
                    graph[node2][node1]['statistical_signal'] = True
                    graph[node2][node1]['anomaly_confidence'] = anomaly['ai_confidence']

                    edges_modified += 1

            return edges_modified

        except Exception as e:
            logger.exception(f" Error applying statistical signals: {str(e)}")
            return 0

    async def detect_direct_statistical_opportunities(self, price_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Direct detection of statistical arbitrage opportunities"""

        opportunities = []

        try:
            # Update data and detect anomalies
            self.update_historical_data(price_data)
            anomalies = await self.detect_statistical_anomalies(price_data)

            for anomaly in anomalies:
                if anomaly['ai_confidence'] > 0.7:  # High confidence only

                    # Calculate expected profit from mean reversion
                    current_deviation = abs(anomaly['current_ratio'] - anomaly['mean_ratio'])
                    expected_reversion = current_deviation * 0.5  # Assume 50% reversion

                    profit_estimate = (expected_reversion / anomaly['mean_ratio']) * 100

                    opportunities.append({
                        'strategy': 'statistical',
                        'token': anomaly['token'],
                        'pair': f"{anomaly['location1']['exchange']} vs {anomaly['location2']['exchange']}",
                        'anomaly_type': anomaly['direction'],
                        'z_score': anomaly['z_score'],
                        'correlation': anomaly['correlation'],
                        'ai_confidence': anomaly['ai_confidence'],
                        'expected_profit_pct': profit_estimate,
                        'reversion_time_estimate': anomaly['predicted_reversion_time'],
                        'recommended_action': anomaly['recommended_action']
                    })

            # Sort by expected profit
            opportunities.sort(key=lambda x: x['expected_profit_pct'], reverse=True)
            return opportunities[:5]  # Top 5 statistical opportunities

        except Exception as e:
            logger.exception(f" Error detecting statistical opportunities: {str(e)}")
            return []

    def get_correlation_matrix(self, token: str) -> Dict[str, Any]:
        """Get correlation matrix for a token across exchanges"""

        try:
            token_keys = [key for key in self.price_history.keys() if key.startswith(f"{token}@")]

            if len(token_keys) < 2:
                return {}

            # Build correlation matrix
            correlations = {}
            for key1 in token_keys:
                correlations[key1] = {}
                for key2 in token_keys:
                    if key1 == key2:
                        correlations[key1][key2] = 1.0
                    else:
                        # Calculate correlation
                        prices1 = [p['price'] for p in self.price_history[key1]]
                        prices2 = [p['price'] for p in self.price_history[key2]]

                        min_len = min(len(prices1), len(prices2))
                        if min_len > 10:
                            corr = np.corrcoef(prices1[-min_len:], prices2[-min_len:])[0, 1]
                            correlations[key1][key2] = corr if not np.isnan(corr) else 0
                        else:
                            correlations[key1][key2] = 0

            return {
                'token': token,
                'correlations': correlations,
                'num_exchanges': len(token_keys),
                'data_points': min(len(self.price_history[key]) for key in token_keys) if token_keys else 0
            }

        except Exception as e:
            logger.exception(f" Error building correlation matrix: {str(e)}")
            return {}

    def clear_old_data(self, days_to_keep: int = 7):
        """Clear historical data older than specified days"""

        try:
            cutoff_time = datetime.now() - timedelta(days=days_to_keep)

            for key in self.price_history:
                # Filter out old data points
                filtered_data = deque(
                    [point for point in self.price_history[key] 
                     if point['timestamp'] > cutoff_time],
                    maxlen=self.lookback_periods
                )
                self.price_history[key] = filtered_data

            logger.info(f" Cleaned historical data older than {days_to_keep} days")

        except Exception as e:
            logger.exception(f" Error clearing old data: {str(e)}")
