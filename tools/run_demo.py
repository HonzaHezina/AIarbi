import asyncio
import os
import sys
import logging

# Ensure project root is on path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.main_arbitrage_system import MainArbitrageSystem
# Enable debug logging for demo diagnostics
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

async def main():
    system = MainArbitrageSystem()
    pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT"]
    strategies = ["dex_cex", "cross_exchange", "triangular", "wrapped_tokens", "statistical"]

    # Monkeypatch the data engine to use fallback data to avoid network/API delays in demo
    async def fetch_fallback(trading_pairs):
        # Use the synchronous fallback generator wrapped for async
        return system.data_engine.get_fallback_data(trading_pairs)

    system.data_engine.fetch_all_market_data = fetch_fallback

    logging.info("Starting demo run (using fallback data)...")
    results = await system.run_full_arbitrage_scan(strategies, pairs, min_profit_threshold=0.0)

    logging.info(f"Demo run complete. Found {len(results)} opportunities")
    for i, opp in enumerate(results, 1):
        logging.info(f"{i}. {opp.get('strategy')} | {opp.get('token')} | {opp.get('profit_pct'):.4f}% | {opp.get('ai_confidence'):.2f}")

    # Additional diagnostics: build graph and show stats
    logging.info("\n Building graph for diagnostics...")
    price_data = system.data_engine.get_fallback_data(pairs)
    G = system.graph_builder.build_unified_graph(price_data)

    # Try adding cross-exchange and wrapped edges for completeness
    try:
        system.graph_builder.add_cross_exchange_edges(G, price_data)
        system.graph_builder.add_wrapped_token_edges()
    except Exception:
        # Some methods may depend on state; ignore for diagnostics
        pass

    stats = system.graph_builder.get_graph_statistics()
    logging.info(f"Graph stats: {stats}")

    # Run direct DEX/CEX detector for quick check
    logging.info("\n Running direct DEX/CEX detector...")
    direct_results = await system.strategies['dex_cex'].detect_direct_opportunities(price_data)
    logging.info(f"Direct detector found {len(direct_results)} opportunities")
    for dr in direct_results[:10]:
        logging.info(f"- {dr['token']} {dr['direction']} profit {dr['profit_pct']:.4f}% confidence {dr.get('ai_confidence', 0):.2f}")

if __name__ == '__main__':
    asyncio.run(main())
