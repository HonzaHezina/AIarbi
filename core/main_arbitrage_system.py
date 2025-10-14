import asyncio
# networkx is optional for tests; prefer installed networkx but fall back to
# the compatibility module exposed by core.graph_builder when unavailable.
try:
    import networkx as nx
except Exception:
    try:
        from core import graph_builder as _graph_builder
        nx = _graph_builder.nx
    except Exception:
        nx = None

import math
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

from .ai_model import ArbitrageAI
from .data_engine import DataEngine
from .graph_builder import GraphBuilder
from .bellman_ford_detector import BellmanFordDetector
from strategies.dex_cex_arbitrage import DEXCEXArbitrage
from strategies.cross_exchange_arbitrage import CrossExchangeArbitrage
from strategies.triangular_arbitrage import TriangularArbitrage
from strategies.wrapped_tokens_arbitrage import WrappedTokensArbitrage
from strategies.statistical_arbitrage import StatisticalArbitrage
from utils.config import get_start_capital_usd

# Module logger
logger = logging.getLogger(__name__)

class MainArbitrageSystem:
    def __init__(self, start_capital_usd: float = None):
        """
        Initialize the main system.
        start_capital_usd: optional override for the simulated execution capital (USD).
        If None, value is taken from utils.config.get_start_capital_usd().
        """
        # Initialize AI model
        self.ai = ArbitrageAI()

        # Configure start capital (exposed parameter)
        self.start_capital_usd = float(start_capital_usd) if start_capital_usd is not None else float(get_start_capital_usd())

        # Initialize core components
        self.data_engine = DataEngine()
        self.graph_builder = GraphBuilder(self.ai)
        self.detector = BellmanFordDetector(self.ai)

        # Initialize strategies
        self.strategies = {
            'dex_cex': DEXCEXArbitrage(self.ai),
            'cross_exchange': CrossExchangeArbitrage(self.ai),
            'triangular': TriangularArbitrage(self.ai),
            'wrapped_tokens': WrappedTokensArbitrage(self.ai),
            'statistical': StatisticalArbitrage(self.ai)
        }

        self.last_scan_time = None
        self.cached_opportunities = []

    async def run_full_arbitrage_scan(self, enabled_strategies: List[str], 
                                     trading_pairs: List[str], 
                                     min_profit_threshold: float = 0.5) -> List[Dict]:
        """
        Main function to run complete arbitrage scan with all enabled strategies
        """
        try:
            logger.info(f" Starting arbitrage scan with strategies: {enabled_strategies}")

            # 1. Fetch market data
            logger.info(" Fetching market data...")
            price_data = await self.data_engine.fetch_all_market_data(trading_pairs)

            if not price_data:
                logger.warning(" No market data available")
                return []

            # 2. Update statistical data if needed
            if 'statistical' in enabled_strategies:
                self.strategies['statistical'].update_historical_data(price_data)

            # 3. Build multi-strategy graph
            logger.info(" Building arbitrage graph...")
            graph = self.graph_builder.build_unified_graph(price_data)

            # 4. Add strategy-specific edges
            for strategy_name in enabled_strategies:
                if strategy_name in self.strategies:
                    logger.info(f" Adding {strategy_name} edges...")
                    await self.strategies[strategy_name].add_strategy_edges(graph, price_data)

            # 5. Run Bellman-Ford detection
            logger.info(" Running Bellman-Ford cycle detection...")
            
            # Store graph stats for UI display
            graph_stats = self.graph_builder.get_graph_statistics()
            self.last_graph_stats = graph_stats
            logger.info(f" Graph: {graph_stats.get('nodes', 0)} nodes, {graph_stats.get('edges', 0)} edges")
            
            raw_cycles = self.detector.detect_all_cycles(graph)

            # Debugging: Log raw cycles before processing
            logger.debug(f" Debug: Raw cycles detected: {len(raw_cycles)}")
            for cycle in raw_cycles[:5]:  # Log first 5 cycles for brevity
                logger.debug(f" Debug: Cycle: {cycle}")
            
            # Store for UI display
            self.last_raw_cycles_count = len(raw_cycles)
            logger.info(f" Bellman-Ford found {len(raw_cycles)} raw cycles")

            # 6. Process and filter opportunities
            logger.info(" Processing opportunities with AI...")
            opportunities = await self.process_and_rank_opportunities(
                raw_cycles, price_data, min_profit_threshold
            )

            # 7. Cache results
            self.cached_opportunities = opportunities
            self.last_scan_time = datetime.now()
 
            logger.info(f" Scan complete. Found {len(opportunities)} opportunities")
            return opportunities

        except Exception as e:
            logger.exception(f" Error in arbitrage scan: {str(e)}")
            return []

    async def process_and_rank_opportunities(self, raw_cycles: List[Dict], 
                                           price_data: Dict, 
                                           min_profit: float) -> List[Dict]:
        """
        Process raw Bellman-Ford cycles and rank them using AI
        """
        opportunities = []

        for cycle in raw_cycles:
            try:
                # Calculate actual profit with fees
                profit_analysis = await self.calculate_cycle_profit(cycle, price_data)

                if profit_analysis['profit_pct'] >= min_profit:
                    # AI risk assessment
                    risk_assessment = await self.ai.assess_opportunity_risk(
                        cycle, price_data, profit_analysis
                    )

                    # Create opportunity object
                    opportunity = {
                        'strategy': cycle.get('strategy_type', 'mixed'),
                        'token': self.extract_primary_token(cycle),
                        'path': cycle.get('path', []),
                        'path_summary': self.create_path_summary(cycle),
                        'profit_pct': profit_analysis['profit_pct'],
                        'profit_usd': profit_analysis.get('profit_usd', 0),
                        'ai_confidence': risk_assessment.get('confidence', 0),
                        'risk_level': risk_assessment.get('risk_level', 'UNKNOWN'),
                        'execution_time_estimate': risk_assessment.get('execution_time', 0),
                        'required_capital': profit_analysis.get('required_capital', 1000),
                        'fees_total': profit_analysis.get('total_fees', 0),
                        'status': 'Ready',
                        'timestamp': datetime.now(),
                        'cycle_data': cycle
                    }

                    opportunities.append(opportunity)

            except Exception as e:
                logger.exception(f" Error processing cycle: {str(e)}")
                continue

        # AI ranking of all opportunities
        if opportunities:
            ranked_opportunities = await self.ai.rank_opportunities(opportunities)
            return ranked_opportunities

        return opportunities

    async def calculate_cycle_profit(self, cycle: Dict, price_data: Dict) -> Dict:
        """
        Calculate actual profit for a cycle considering all fees and slippage
        """
        try:
            path = cycle.get('path', [])
            if len(path) < 2:
                return {'profit_pct': 0, 'profit_usd': 0}

            # Simulate execution through the cycle using configured start capital
            current_amount = float(self.start_capital_usd)
            total_fees = 0

            # Debugging: Log cycle path and initial amount
            logger.debug(f" Debug: Cycle path: {path}")
            logger.debug(f" Debug: Starting amount: {current_amount}")

            for i in range(len(path) - 1):
                current_node = path[i]
                next_node = path[i + 1]

                # Debugging: Log edge data
                edge_data = cycle.get('edge_data', {}).get(f"{current_node}->{next_node}", {})
                logger.debug(f" Debug: Edge data for {current_node}->{next_node}: {edge_data}")

                # Calculate conversion rate and fees
                conversion_rate = edge_data.get('rate', 1.0)
                fee_pct = edge_data.get('fee', 0.001)
                slippage = edge_data.get('estimated_slippage', 0.0005)

                # Debugging: Log conversion details
                logger.debug(f" Debug: Conversion rate: {conversion_rate}, Fee: {fee_pct}, Slippage: {slippage}")

                # Apply conversion
                fee_amount = current_amount * fee_pct
                slippage_amount = current_amount * slippage

                current_amount = current_amount * conversion_rate * (1 - fee_pct - slippage)
                total_fees += fee_amount + slippage_amount

                # Debugging: Log updated amount and fees
                logger.debug(f" Debug: Updated amount: {current_amount}, Total fees: {total_fees}")

            # Calculate profit
            profit_usd = current_amount - 1000
            profit_pct = (profit_usd / 1000) * 100

            return {
                'profit_pct': profit_pct,
                'profit_usd': profit_usd,
                'total_fees': total_fees,
                'final_amount': current_amount,
                'required_capital': self.start_capital_usd
            }

        except Exception as e:
            logger.exception(f" Error calculating cycle profit: {str(e)}")
            return {'profit_pct': 0, 'profit_usd': 0, 'total_fees': 0, 'required_capital': self.start_capital_usd}

    def extract_primary_token(self, cycle: Dict) -> str:
        """Extract the primary token from cycle path"""
        path = cycle.get('path', [])
        if not path:
            return 'UNKNOWN'

        # Extract token from first node
        first_node = path[0]
        if '@' in first_node:
            return first_node.split('@')[0]

        return 'UNKNOWN'

    def create_path_summary(self, cycle: Dict) -> str:
        """Create human-readable path summary"""
        path = cycle.get('path', [])
        if len(path) < 3:
            return 'N/A'

        # Simplify path for display
        exchanges = []
        for node in path:
            if '@' in node:
                exchange = node.split('@')[1]
                if exchange not in exchanges:
                    exchanges.append(exchange)

        if len(exchanges) <= 2:
            return f"{exchanges[0]}  {exchanges[1] if len(exchanges) > 1 else '?'}"
        else:
            return f"{exchanges[0]}  {exchanges[1]}  {exchanges[2]}"

    async def get_cached_opportunities(self) -> List[Dict]:
        """Get cached opportunities if recent enough"""
        if (self.last_scan_time and 
            (datetime.now() - self.last_scan_time).seconds < 60):  # 1 minute cache
            return self.cached_opportunities
        return []

    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'last_scan': self.last_scan_time,
            'cached_opportunities': len(self.cached_opportunities),
            'active_strategies': list(self.strategies.keys()),
            'data_engine_status': self.data_engine.get_status(),
            'ai_model_loaded': self.ai.is_loaded()
        }
    
    def get_all_strategies_info(self) -> List[Dict]:
        """Get detailed information about all strategies"""
        strategies_info = []
        for strategy_key, strategy_obj in self.strategies.items():
            try:
                if hasattr(strategy_obj, 'get_strategy_info'):
                    info = strategy_obj.get_strategy_info()
                    strategies_info.append(info)
                else:
                    # Fallback for strategies without get_strategy_info
                    strategies_info.append({
                        'name': strategy_key.replace('_', ' ').title(),
                        'key': strategy_key,
                        'description': 'No description available',
                        'status': 'Active ✅'
                    })
            except Exception as e:
                logger.error(f"Error getting info for strategy {strategy_key}: {str(e)}")
                strategies_info.append({
                    'name': strategy_key,
                    'key': strategy_key,
                    'description': 'Error loading strategy info',
                    'status': 'Error ❌'
                })
        return strategies_info
