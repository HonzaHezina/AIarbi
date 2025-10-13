import os
import sys
# Ensure project root is on sys.path so tests can import local packages (core, strategies, etc.)
import types
# Provide a minimal fake ccxt module so tests run without external dependency
_ccxt = types.ModuleType("ccxt")
class _DummyExchange:
    def __init__(self, conf=None):
        self.symbols = []
    def fetch_ticker(self, pair):
        return {'bid': 49500.0, 'ask': 50000.0, 'last': 49750.0, 'baseVolume': 100}
def _make_exchange(conf=None):
    return _DummyExchange(conf)
_ccxt.binance = lambda conf=None: _DummyExchange(conf)
_ccxt.kraken = lambda conf=None: _DummyExchange(conf)
_ccxt.coinbase = lambda conf=None: _DummyExchange(conf)
_ccxt.kucoin = lambda conf=None: _DummyExchange(conf)
import sys as _sys
_sys.modules['ccxt'] = _ccxt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# python
import asyncio
import random
import logging
import pytest

from core.data_engine import DataEngine
from core.graph_builder import GraphBuilder
from core.bellman_ford_detector import BellmanFordDetector
from core.main_arbitrage_system import MainArbitrageSystem
from strategies.dex_cex_arbitrage import DEXCEXArbitrage
import utils.config as config

logging.getLogger().setLevel(logging.DEBUG)


@pytest.mark.asyncio
async def test_bellman_ford_vs_direct_detector_repro():
    """
    Deterministic reproduction test:
    - Enables synthetic injection used by the demo harness
    - Seeds randomness for stable fallback/dex simulation
    - Builds graph, runs Bellman-Ford detector
    - Runs direct dex/cex detector and explicit profit computations
    The test asserts Bellman-Ford finds at least one cycle while the direct detector
    returns no direct opportunities (reproducing the observed discrepancy).
    It prints both calculations so maintainers can compare math.
    """

    # Make demo deterministic
    random.seed(0)
    config.DEBUG_DEMO_INJECT_SYNTHETIC = True

    # Prepare deterministic fallback market data (only BTC/USDT needed)
    trading_pairs = ['BTC/USDT']
    de = DataEngine()
    price_data = de.get_fallback_data(trading_pairs)

    # Build unified graph and run Bellman-Ford
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)

    detector = BellmanFordDetector(ai_model=None)
    cycles = detector.detect_all_cycles(G)

    # Basic sanity
    assert isinstance(cycles, list)

    # Run direct detector
    dex_cex = DEXCEXArbitrage(ai_model=None)
    direct_ops = await dex_cex.detect_direct_opportunities(price_data)

    # Print summary for debugging comparison
    print("=== Bellman-Ford cycles found:", len(cycles))
    for i, c in enumerate(cycles):
        print(f"Cycle[{i}]: path={c.get('path')}, weight={c.get('weight')}, profit_estimate={c.get('profit_estimate')}")
        # Also simulate detailed profit using main system simulator
        main = MainArbitrageSystem(start_capital_usd=1000)
        profit_calc = await main.calculate_cycle_profit(c, price_data)
        print(f"  -> simulate profit_pct={profit_calc['profit_pct']:.6f} profit_usd={profit_calc['profit_usd']:.6f} final_amount={profit_calc['final_amount']:.6f}")

    print("=== Direct detector opportunities found:", len(direct_ops))
    for op in direct_ops:
        print("Direct-op:", op)

    # Additionally compute per-pair calculate_arbitrage_profit outputs for each cex/dex pair
    print("=== Per-pair direct profit breakdown (deterministic):")
    tokens = price_data.get('tokens', [])
    for token in tokens:
        cex_prices = price_data.get('cex', {})
        dex_prices = price_data.get('dex', {})
        for cex_name, cex_data in cex_prices.items():
            cex_info = cex_data.get('BTC/USDT') or cex_data.get(token)
            if not cex_info:
                continue
            for dex_name, dex_data in dex_prices.items():
                dex_info = dex_data.get('BTC/USDT') or dex_data.get(token)
                if not dex_info:
                    continue

                # cex -> dex
                res1 = await dex_cex.calculate_arbitrage_profit(token, cex_name, dex_name, cex_info, dex_info, 'cex_to_dex')
                # dex -> cex
                res2 = await dex_cex.calculate_arbitrage_profit(token, dex_name, cex_name, dex_info, cex_info, 'dex_to_cex')

                print(f"Token={token} CEX={cex_name} DEX={dex_name} cex->dex: profit_pct={res1.get('profit_pct'):.6f} profit_usd={res1.get('profit_usd'):.6f} profitable={res1.get('profitable')}")
                print(f"Token={token} CEX={cex_name} DEX={dex_name} dex->cex: profit_pct={res2.get('profit_pct'):.6f} profit_usd={res2.get('profit_usd'):.6f} profitable={res2.get('profitable')}")

    # Reproduce observed discrepancy: Bellman-Ford detects at least one but direct detector returns none
    assert len(cycles) > 0
    assert len(direct_ops) == 0