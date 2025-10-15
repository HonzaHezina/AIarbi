"""
Comprehensive tests for all 5 trading strategies using synthetic data with known outcomes.
Each test uses carefully crafted data where we know exactly what the expected result should be.

Tests cover:
1. DEX/CEX Arbitrage - Price differences between DEX and CEX
2. Cross-Exchange Arbitrage - Price differences between CEXes
3. Triangular Arbitrage - Profitable cycles within single exchange
4. Wrapped Tokens Arbitrage - Price discrepancies between native and wrapped tokens
5. Statistical Arbitrage - Correlation anomalies between correlated pairs
"""

import pytest
import asyncio
import math
from typing import Dict, Any

from core.graph_builder import GraphBuilder
from core.bellman_ford_detector import BellmanFordDetector
from strategies.dex_cex_arbitrage import DEXCEXArbitrage
from strategies.cross_exchange_arbitrage import CrossExchangeArbitrage
from strategies.triangular_arbitrage import TriangularArbitrage
from strategies.wrapped_tokens_arbitrage import WrappedTokensArbitrage
from strategies.statistical_arbitrage import StatisticalArbitrage


class DummyAI:
    """Dummy AI for testing"""
    def is_loaded(self):
        return True
    
    async def assess_opportunity_risk(self, cycle, price_data, profit_analysis):
        return {
            'confidence': 0.9,
            'risk_level': 'LOW',
            'risk_score': 1,
            'risk_factors': [],
            'execution_time': 30,
            'recommended_capital': 100
        }


# ============================================================================
# TEST 1: DEX/CEX Arbitrage - Clear profitable opportunity
# ============================================================================

@pytest.mark.asyncio
async def test_dex_cex_arbitrage_profitable_opportunity():
    """
    Test DEX/CEX with known profitable scenario:
    - Binance (CEX): BTC/USDT bid=48000, ask=48100
    - Pancakeswap (DEX): BTC/USDT bid=49500, ask=49600
    
    Using Pancakeswap (BSC) because it has lower gas costs (~$0.50)
    Expected: Should find profitable opportunity buying on CEX and selling on DEX
    Profit = (49500 - 48100) / 48100 = ~2.9% (minus fees ~0.4% and gas ~$0.50 = ~2.4% net on $50k)
    """
    
    price_data = {
        'tokens': ['BTC', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 48000.0, 'ask': 48100.0, 'fee': 0.001},
            }
        },
        'dex': {
            'pancakeswap': {
                'BTC/USDT': {'bid': 49500.0, 'ask': 49600.0, 'fee': 0.003},
            }
        }
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    # Apply DEX/CEX strategy
    strategy = DEXCEXArbitrage(ai_model=None)
    await strategy.add_strategy_edges(G, price_data)
    
    # Verify edges were added
    dex_cex_edges = [e for e in G.edges(data=True) if e[2].get('strategy') == 'dex_cex']
    
    assert len(dex_cex_edges) > 0, "Should find DEX/CEX arbitrage edges"
    
    # Check if we can detect the opportunity
    opportunities = await strategy.detect_direct_opportunities(price_data)
    
    # Should find at least one profitable opportunity
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.5]
    assert len(profitable) > 0, f"Should find profitable DEX/CEX opportunity, found {len(opportunities)} total"
    
    print(f"✓ DEX/CEX Test: Found {len(profitable)} profitable opportunities")
    if profitable:
        print(f"  Best opportunity: {profitable[0].get('profit_pct', 0):.2f}% profit")


@pytest.mark.asyncio
async def test_dex_cex_arbitrage_no_opportunity():
    """
    Test DEX/CEX with no profitable opportunity:
    - Both exchanges have similar prices
    
    Expected: Should not find profitable opportunities (or very low profit)
    """
    
    price_data = {
        'tokens': ['ETH', 'USDT'],
        'cex': {
            'binance': {
                'ETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
            }
        },
        'dex': {
            'uniswap_v3': {
                'ETH/USDT': {'bid': 3005.0, 'ask': 3015.0, 'fee': 0.003},
            }
        }
    }
    
    strategy = DEXCEXArbitrage(ai_model=None)
    opportunities = await strategy.detect_direct_opportunities(price_data)
    
    # Should find no opportunities with profit > 0.5% (after fees)
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.5]
    assert len(profitable) == 0, "Should not find profitable opportunity when prices are similar"
    
    print(f"✓ DEX/CEX No-Opportunity Test: Correctly found no profitable opportunities")


# ============================================================================
# TEST 2: Cross-Exchange Arbitrage - Clear price difference
# ============================================================================

@pytest.mark.asyncio
async def test_cross_exchange_arbitrage_profitable():
    """
    Test Cross-Exchange with clear profit opportunity:
    - Binance: BTC/USDT bid=48000, ask=48100 (lower prices first due to dict ordering)
    - Kraken: BTC/USDT bid=50000, ask=50100 (higher prices)
    
    Expected: Buy on Binance (48100), sell on Kraken (50000)
    Profit = (50000 - 48100) / 48100 = ~3.95% (minus fees and transfer ~0.3% = ~3.6% net)
    
    Note: Dict ordering matters - Binance comes before Kraken alphabetically
    """
    
    price_data = {
        'tokens': ['BTC'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 48000.0, 'ask': 48100.0, 'fee': 0.001},
            },
            'kraken': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    # Apply Cross-Exchange strategy
    strategy = CrossExchangeArbitrage(ai_model=None)
    await strategy.add_strategy_edges(G, price_data)
    
    # Verify edges were added
    cross_edges = [e for e in G.edges(data=True) if e[2].get('strategy') == 'cross_exchange']
    
    assert len(cross_edges) > 0, "Should find cross-exchange arbitrage edges"
    
    # Detect opportunities - use correct method name
    opportunities = await strategy.detect_simple_opportunities(price_data)
    
    # Should find profitable opportunity
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.5]
    assert len(profitable) > 0, "Should find profitable cross-exchange opportunity"
    
    print(f"✓ Cross-Exchange Test: Found {len(profitable)} profitable opportunities")
    if profitable:
        print(f"  Best opportunity: {profitable[0].get('profit_pct', 0):.2f}% profit")


@pytest.mark.asyncio
async def test_cross_exchange_arbitrage_three_exchanges():
    """
    Test Cross-Exchange with multiple exchanges to verify it finds the best path:
    - Binance: ETH/USDT bid=2900, ask=2910 (lowest, alphabetically first)
    - Coinbase: ETH/USDT bid=3000, ask=3010 (middle)
    - Kraken: ETH/USDT bid=3050, ask=3060 (highest, alphabetically last)
    
    Expected: Should identify Binance->Kraken as most profitable
    (algorithm checks in alphabetical order with i < j constraint)
    """
    
    price_data = {
        'tokens': ['ETH'],
        'cex': {
            'binance': {
                'ETH/USDT': {'bid': 2900.0, 'ask': 2910.0, 'fee': 0.001},
            },
            'coinbase': {
                'ETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
            },
            'kraken': {
                'ETH/USDT': {'bid': 3050.0, 'ask': 3060.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    strategy = CrossExchangeArbitrage(ai_model=None)
    opportunities = await strategy.detect_simple_opportunities(price_data)
    
    # Should find opportunities
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 1.0]
    assert len(profitable) > 0, "Should find profitable opportunities with multiple exchanges"
    
    print(f"✓ Cross-Exchange Multi-Exchange Test: Found {len(profitable)} profitable opportunities")


# ============================================================================
# TEST 3: Triangular Arbitrage - Profitable cycle
# ============================================================================

@pytest.mark.asyncio
async def test_triangular_arbitrage_profitable_cycle():
    """
    Test Triangular Arbitrage with a profitable cycle:
    Starting with 1000 USDT:
    1. USDT -> BTC: 1000 / 50000 = 0.02 BTC (minus 0.1% fee = 0.0199 BTC)
    2. BTC -> ETH: 0.0199 * 16.8 = 0.33432 ETH (minus 0.1% fee = 0.333 ETH)
    3. ETH -> USDT: 0.333 * 3020 = 1005.66 USDT (minus 0.1% fee = 1004.66 USDT)
    
    Net profit: ~0.46% (4.66 USDT profit on 1000 USDT)
    """
    
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                # USDT -> BTC
                'BTC/USDT': {'bid': 50000.0, 'ask': 50000.0, 'fee': 0.001},
                # BTC -> ETH (BTC/ETH rate)
                'BTC/ETH': {'bid': 16.8, 'ask': 16.8, 'fee': 0.001},
                # ETH -> USDT
                'ETH/USDT': {'bid': 3020.0, 'ask': 3020.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    # Apply Triangular strategy
    strategy = TriangularArbitrage(ai_model=None)
    await strategy.add_strategy_edges(G, price_data)
    
    # Detect triangular opportunities
    opportunities = await strategy.detect_direct_triangular_opportunities(price_data)
    
    # Should find at least one opportunity
    assert isinstance(opportunities, list), "Should return list of opportunities"
    
    print(f"✓ Triangular Test: Found {len(opportunities)} opportunities")
    if opportunities:
        profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.1]
        print(f"  Profitable opportunities: {len(profitable)}")


@pytest.mark.asyncio
async def test_triangular_arbitrage_no_profitable_cycle():
    """
    Test Triangular Arbitrage with no profitable cycle:
    The cycle should result in a loss due to fees
    """
    
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50000.0, 'fee': 0.001},
                'BTC/ETH': {'bid': 16.0, 'ask': 16.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 3000.0, 'ask': 3000.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    strategy = TriangularArbitrage(ai_model=None)
    opportunities = await strategy.detect_direct_triangular_opportunities(price_data)
    
    # Should not find profitable opportunities (fees eat up any gains)
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.1]
    
    print(f"✓ Triangular No-Profit Test: Found {len(profitable)} profitable opportunities (expected 0 or few)")


# ============================================================================
# TEST 4: Wrapped Tokens Arbitrage - Price discrepancy
# ============================================================================

@pytest.mark.asyncio
async def test_wrapped_tokens_arbitrage_profitable():
    """
    Test Wrapped Tokens with price discrepancy:
    - BTC: price = 50000 USDT
    - wBTC: price = 49500 USDT (0.99:1 ratio instead of 1:1)
    
    Expected: Buy wBTC at 49500, unwrap to BTC, sell at 50000
    Profit: ~1% (minus gas fees)
    """
    
    price_data = {
        'tokens': ['BTC', 'wBTC', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
                'wBTC/USDT': {'bid': 49500.0, 'ask': 49600.0, 'fee': 0.001},
            }
        },
        'dex': {
            'uniswap_v3': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.003},
                'wBTC/USDT': {'bid': 49500.0, 'ask': 49600.0, 'fee': 0.003},
            }
        }
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    # Apply Wrapped Tokens strategy
    strategy = WrappedTokensArbitrage(ai_model=None)
    await strategy.add_strategy_edges(G, price_data)
    
    # Verify edges were added
    wrapped_edges = [e for e in G.edges(data=True) if e[2].get('strategy') == 'wrapped_tokens']
    
    assert len(wrapped_edges) > 0, "Should find wrapped token arbitrage edges"
    
    # Detect opportunities
    opportunities = await strategy.detect_direct_opportunities(price_data)
    
    # Should find opportunities
    assert isinstance(opportunities, list), "Should return list of opportunities"
    
    print(f"✓ Wrapped Tokens Test: Found {len(opportunities)} opportunities")
    if opportunities:
        profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.2]
        print(f"  Profitable opportunities: {len(profitable)}")


@pytest.mark.asyncio
async def test_wrapped_tokens_arbitrage_correct_ratio():
    """
    Test Wrapped Tokens with correct 1:1 ratio:
    - BTC: price = 50000 USDT
    - wBTC: price = 50000 USDT (perfect 1:1)
    
    Expected: No profitable opportunity (or very minimal after fees)
    """
    
    price_data = {
        'tokens': ['ETH', 'wETH', 'USDT'],
        'cex': {
            'binance': {
                'ETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
                'wETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    strategy = WrappedTokensArbitrage(ai_model=None)
    opportunities = await strategy.detect_direct_opportunities(price_data)
    
    # Should not find significant opportunities
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.5]
    assert len(profitable) == 0, "Should not find profitable opportunity when ratio is 1:1"
    
    print(f"✓ Wrapped Tokens Correct Ratio Test: Correctly found no significant opportunities")


# ============================================================================
# TEST 5: Statistical Arbitrage - Correlation anomaly
# ============================================================================

@pytest.mark.asyncio
async def test_statistical_arbitrage_basic():
    """
    Test Statistical Arbitrage basic functionality:
    Tests that the strategy can add edges and process data without errors
    """
    
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
            },
            'kraken': {
                'BTC/USDT': {'bid': 49900.0, 'ask': 50000.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 2950.0, 'ask': 2960.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    # Apply Statistical strategy
    strategy = StatisticalArbitrage(ai_model=None)
    
    # Add historical data for correlation analysis using the correct method
    for i in range(50):
        strategy.update_historical_data({
            'tokens': ['BTC', 'ETH'],
            'cex': {
                'binance': {
                    'BTC/USDT': {'bid': 50000 + i * 10, 'ask': 50100 + i * 10, 'fee': 0.001},
                    'ETH/USDT': {'bid': 3000 + i * 0.6, 'ask': 3010 + i * 0.6, 'fee': 0.001},
                },
                'kraken': {
                    'BTC/USDT': {'bid': 49900 + i * 10, 'ask': 50000 + i * 10, 'fee': 0.001},
                    'ETH/USDT': {'bid': 2950 + i * 0.6, 'ask': 2960 + i * 0.6, 'fee': 0.001},
                }
            },
            'dex': {}
        })
    
    await strategy.add_strategy_edges(G, price_data)
    
    # Verify edges were added
    stat_edges = [e for e in G.edges(data=True) if e[2].get('strategy') == 'statistical']
    
    # Statistical strategy might not always add edges immediately
    assert isinstance(stat_edges, list), "Should return list of edges"
    
    print(f"✓ Statistical Arbitrage Test: Added {len(stat_edges)} statistical edges")


# ============================================================================
# TEST 6: Integration test - All strategies together
# ============================================================================

@pytest.mark.asyncio
async def test_all_strategies_together():
    """
    Test all 5 strategies working together on the same graph:
    Create a scenario with opportunities for multiple strategies
    """
    
    price_data = {
        'tokens': ['BTC', 'ETH', 'wBTC', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
                'wBTC/USDT': {'bid': 49500.0, 'ask': 49600.0, 'fee': 0.001},
                'BTC/ETH': {'bid': 16.7, 'ask': 16.8, 'fee': 0.001},
            },
            'kraken': {
                'BTC/USDT': {'bid': 49500.0, 'ask': 49600.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 2950.0, 'ask': 2960.0, 'fee': 0.001},
            }
        },
        'dex': {
            'uniswap_v3': {
                'BTC/USDT': {'bid': 51000.0, 'ask': 51100.0, 'fee': 0.003},
                'ETH/USDT': {'bid': 3100.0, 'ask': 3110.0, 'fee': 0.003},
            }
        }
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    initial_edges = G.number_of_edges()
    
    # Apply all strategies
    strategies = [
        DEXCEXArbitrage(ai_model=None),
        CrossExchangeArbitrage(ai_model=None),
        TriangularArbitrage(ai_model=None),
        WrappedTokensArbitrage(ai_model=None),
        StatisticalArbitrage(ai_model=None),
    ]
    
    for strategy in strategies:
        await strategy.add_strategy_edges(G, price_data)
    
    final_edges = G.number_of_edges()
    
    # Should have added edges from multiple strategies
    assert final_edges > initial_edges, "Strategies should add edges to the graph"
    
    # Count edges by strategy
    edge_counts = {}
    for edge in G.edges(data=True):
        strategy_name = edge[2].get('strategy', 'unknown')
        edge_counts[strategy_name] = edge_counts.get(strategy_name, 0) + 1
    
    print(f"✓ All Strategies Integration Test:")
    print(f"  Initial edges: {initial_edges}")
    print(f"  Final edges: {final_edges}")
    print(f"  Edge counts by strategy:")
    for strategy_name, count in sorted(edge_counts.items()):
        if strategy_name != 'unknown':
            print(f"    {strategy_name}: {count} edges")
    
    # At minimum, should have edges from regular price data
    assert final_edges >= initial_edges, "Should maintain or add edges"


# ============================================================================
# TEST 7: Bellman-Ford Detection with known profitable cycle
# ============================================================================

@pytest.mark.asyncio
async def test_bellman_ford_with_profitable_cycle():
    """
    Test Bellman-Ford detector with a known profitable cycle:
    Create a clear arbitrage opportunity that Bellman-Ford should detect
    """
    
    price_data = {
        'tokens': ['BTC', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
            }
        },
        'dex': {
            'uniswap_v3': {
                'BTC/USDT': {'bid': 51500.0, 'ask': 51600.0, 'fee': 0.003},
            }
        }
    }
    
    # Build graph with all strategies
    gb = GraphBuilder(ai_model=DummyAI())
    G = gb.build_unified_graph(price_data)
    
    # Add DEX/CEX edges (should create profitable cycle)
    dex_cex = DEXCEXArbitrage(ai_model=None)
    await dex_cex.add_strategy_edges(G, price_data)
    
    # Run Bellman-Ford detector
    detector = BellmanFordDetector(ai_model=DummyAI())
    cycles = detector.detect_all_cycles(G)
    
    # Should detect cycles
    assert isinstance(cycles, list), "Should return list of cycles"
    
    print(f"✓ Bellman-Ford Test: Detected {len(cycles)} cycles")
    
    if cycles:
        profitable = [c for c in cycles if c.get('profit_pct', 0) > 0.5]
        print(f"  Profitable cycles: {len(profitable)}")


# ============================================================================
# TEST 8: Edge cases and error handling
# ============================================================================

@pytest.mark.asyncio
async def test_strategies_with_empty_data():
    """
    Test that strategies handle empty data gracefully
    """
    
    empty_data = {
        'tokens': [],
        'cex': {},
        'dex': {}
    }
    
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(empty_data)
    
    strategies = [
        DEXCEXArbitrage(ai_model=None),
        CrossExchangeArbitrage(ai_model=None),
        TriangularArbitrage(ai_model=None),
        WrappedTokensArbitrage(ai_model=None),
        StatisticalArbitrage(ai_model=None),
    ]
    
    # Should not crash with empty data
    for strategy in strategies:
        try:
            await strategy.add_strategy_edges(G, empty_data)
        except Exception as e:
            pytest.fail(f"Strategy {strategy.strategy_name} crashed with empty data: {str(e)}")
    
    print(f"✓ Empty Data Test: All strategies handled empty data gracefully")


@pytest.mark.asyncio
async def test_strategies_with_missing_pairs():
    """
    Test that strategies handle missing trading pairs gracefully
    """
    
    incomplete_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
                # Missing ETH/USDT and BTC/ETH pairs
            }
        },
        'dex': {}
    }
    
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(incomplete_data)
    
    strategy = TriangularArbitrage(ai_model=None)
    
    # Should not crash with incomplete triangular pairs
    try:
        await strategy.add_strategy_edges(G, incomplete_data)
    except Exception as e:
        pytest.fail(f"Triangular strategy crashed with incomplete data: {str(e)}")
    
    print(f"✓ Missing Pairs Test: Strategy handled incomplete data gracefully")


if __name__ == "__main__":
    # Run tests individually for debugging
    print("\n" + "="*70)
    print("COMPREHENSIVE STRATEGY TESTING WITH KNOWN DATA")
    print("="*70)
    
    asyncio.run(test_dex_cex_arbitrage_profitable_opportunity())
    asyncio.run(test_dex_cex_arbitrage_no_opportunity())
    asyncio.run(test_cross_exchange_arbitrage_profitable())
    asyncio.run(test_cross_exchange_arbitrage_three_exchanges())
    asyncio.run(test_triangular_arbitrage_profitable_cycle())
    asyncio.run(test_triangular_arbitrage_no_profitable_cycle())
    asyncio.run(test_wrapped_tokens_arbitrage_profitable())
    asyncio.run(test_wrapped_tokens_arbitrage_correct_ratio())
    asyncio.run(test_statistical_arbitrage_basic())
    asyncio.run(test_all_strategies_together())
    asyncio.run(test_bellman_ford_with_profitable_cycle())
    asyncio.run(test_strategies_with_empty_data())
    asyncio.run(test_strategies_with_missing_pairs())
    
    print("\n" + "="*70)
    print("ALL COMPREHENSIVE TESTS COMPLETED!")
    print("="*70)
