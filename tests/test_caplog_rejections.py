import logging
import pytest
import asyncio

from strategies.dex_cex_arbitrage import DEXCEXArbitrage
from core.graph_builder import GraphBuilder
from core.bellman_ford_detector import BellmanFordDetector

@pytest.mark.asyncio
async def test_dex_cex_direct_detection_logs_rejections(caplog):
    """
    Ensure direct detection logs rejection reasons for unprofitable candidates.
    """
    caplog.set_level(logging.DEBUG)
    price_data = {
        'tokens': ['BTC'],
        'cex': {
            'binance': {
                # ask is higher -> buying on cex is more expensive
                'BTC/USDT': {'bid': 100.0, 'ask': 101.0},
            }
        },
        'dex': {
            'uniswap_v3': {
                # dex bid is lower than cex ask -> not profitable
                'BTC/USDT': {'bid': 100.5, 'ask': 100.0, 'fee': 0.003},
            }
        }
    }

    dex_cex = DEXCEXArbitrage(ai_model=None)
    ops = await dex_cex.detect_direct_opportunities(price_data)

    # No opportunities expected
    assert isinstance(ops, list)
    assert len(ops) == 0

    # Ensure rejection debug messages were emitted
    logs = caplog.text
    assert "Direct-detect rejected cex->dex candidate" in logs or "Direct-detect rejected dex->cex candidate" in logs

def test_bellman_ford_emits_edge_sampling(caplog):
    """
    Ensure Bellman-Ford detector logs a top-10 lightest edges sampling for diagnostics.
    """
    caplog.set_level(logging.DEBUG)

    # Build small price_data to create nodes and some edges
    price_data = {
        'tokens': ['A', 'B'],
        'cex': {
            'binance': {
                'A/B': {'bid': 2.0, 'ask': 2.1},
            }
        },
        'dex': {
            'uniswap_v3': {
                'A/B': {'bid': 2.05, 'ask': 2.0, 'fee': 0.003},
            }
        }
    }

    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)

    detector = BellmanFordDetector(ai_model=None)
    # run detection (synchronous)
    detector.detect_all_cycles(G)

    logs = caplog.text
    assert "Top-10 lightest edges" in logs or "Top-10 lightest edges (possible arbitrage contributors)" in logs