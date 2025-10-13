import pytest
import asyncio

from core.graph_builder import GraphBuilder
from strategies.dex_cex_arbitrage import DEXCEXArbitrage
from strategies.cross_exchange_arbitrage import CrossExchangeArbitrage
from strategies.triangular_arbitrage import TriangularArbitrage

@pytest.mark.asyncio
async def test_dex_cex_and_cross_exchange_add_edges():
    """
    Build a small deterministic price_data fixture and assert that:
    - DEX/CEX strategy adds edges with strategy == 'dex_cex'
    - Cross-exchange strategy adds edges with strategy == 'cross_exchange'
    """
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50500.0, 'ask': 50000.0},
                'ETH/USDT': {'bid': 3200.0, 'ask': 3150.0},
                'BTC/ETH': {'bid': 16.0, 'ask': 15.8},
            },
            'kraken': {
                'BTC/USDT': {'bid': 51000.0, 'ask': 50600.0},
                'ETH/USDT': {'bid': 3220.0, 'ask': 3180.0},
                'BTC/ETH': {'bid': 16.2, 'ask': 16.0},
            }
        },
        'dex': {
            'uniswap_v3': {
                'BTC/USDT': {'bid': 52000.0, 'ask': 51900.0, 'fee': 0.003},
                'ETH/USDT': {'bid': 3300.0, 'ask': 3290.0, 'fee': 0.003},
            },
            'sushiswap': {
                'BTC/USDT': {'bid': 51900.0, 'ask': 51850.0, 'fee': 0.003},
                'ETH/USDT': {'bid': 3290.0, 'ask': 3280.0, 'fee': 0.003},
            }
        }
    }

    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)

    edges_before = list(G.edges(data=True))

    # Instantiate strategies with a dummy AI
    dex_cex = DEXCEXArbitrage(ai_model=None)
    cross = CrossExchangeArbitrage(ai_model=None)

    # Apply strategy edges
    await dex_cex.add_strategy_edges(G, price_data)
    await cross.add_strategy_edges(G, price_data)

    edges_after = list(G.edges(data=True))

    # Ensure edges were added (graph may have had price edges already; check for strategy tags)
    dex_cex_edges = [e for e in edges_after if e[2].get('strategy') == 'dex_cex']
    cross_edges = [e for e in edges_after if e[2].get('strategy') == 'cross_exchange']

    assert isinstance(dex_cex_edges, list), "DEX/CEX edges list should be a list"
    assert isinstance(cross_edges, list), "Cross-exchange edges list should be a list"

    # Expect at least one edge for each strategy given the synthetic prices
    assert len(dex_cex_edges) > 0, "Expected at least one dex_cex edge to be added"
    assert len(cross_edges) > 0, "Expected at least one cross_exchange edge to be added"

@pytest.mark.asyncio
async def test_triangular_detector_runs_and_returns_list():
    """
    Ensure triangular detector does not crash and returns a list (may be empty)
    for the provided synthetic data.
    """
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            # Provide triangle pairs on binance to allow triangular detection attempt
            'binance': {
                'BTC/ETH': {'bid': 16.5, 'ask': 16.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 3300.0, 'ask': 3290.0, 'fee': 0.001},
                'USDT/BTC': {'bid': 1/50400.0, 'ask': 1/50000.0, 'fee': 0.001},
            },
        },
        'dex': {
            'uniswap_v3': {
                'BTC/ETH': {'bid': 16.8, 'ask': 16.7, 'fee': 0.003},
                'ETH/USDT': {'bid': 3350.0, 'ask': 3340.0, 'fee': 0.003},
                'USDT/BTC': {'bid': 1/50000.0, 'ask': 1/49500.0, 'fee': 0.003},
            }
        }
    }

    tri = TriangularArbitrage(ai_model=None)

    result = await tri.detect_direct_triangular_opportunities(price_data)

    assert isinstance(result, list), "Triangular detection should return a list"
    # It's possible no profitable triangle exists; the important part is no crash.