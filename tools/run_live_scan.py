import asyncio
import os
import sys
import logging

# Ensure project root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.main_arbitrage_system import MainArbitrageSystem
from utils.logging_config import setup_logging

# Initialize logging for scripts
setup_logging()
logger = logging.getLogger(__name__)


async def main():
    system = MainArbitrageSystem()

    # Choose a small set of pairs (modify as needed)
    trading_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

    # Enable core strategies
    enabled = ['dex_cex', 'cross_exchange', 'wrapped_tokens', 'triangular']

    logger.info(" Running live arbitrage scan (this will call exchanges/DEXes via DataEngine)")
    opportunities = await system.run_full_arbitrage_scan(enabled, trading_pairs, min_profit_threshold=0.0)

    logger.info(" Live scan complete. Found %d opportunities", len(opportunities))
    for i, opp in enumerate(opportunities):
        logger.info("--- Opportunity %d ---", i + 1)
        logger.info("strategy: %s", opp.get('strategy'))
        logger.info("profit_pct: %s", opp.get('profit_pct'))
        logger.info("path: %s", opp.get('path'))


if __name__ == '__main__':
    asyncio.run(main())
