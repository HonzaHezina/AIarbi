"""
Comprehensive test to verify all 5 trading strategies are properly implemented and integrated.
This test validates:
1. All strategies are registered in MainArbitrageSystem
2. Each strategy has required methods (add_strategy_edges)
3. Strategies can be enabled in the application
4. Each strategy can add edges to the graph
"""
import pytest
import asyncio
import os

# Set offline mode to avoid slow HuggingFace model loading during tests
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

from core.main_arbitrage_system import MainArbitrageSystem
from core.graph_builder import GraphBuilder
from strategies.dex_cex_arbitrage import DEXCEXArbitrage
from strategies.cross_exchange_arbitrage import CrossExchangeArbitrage
from strategies.triangular_arbitrage import TriangularArbitrage
from strategies.wrapped_tokens_arbitrage import WrappedTokensArbitrage
from strategies.statistical_arbitrage import StatisticalArbitrage


def test_all_five_strategies_registered():
    """Verify all 5 strategies are registered in MainArbitrageSystem"""
    system = MainArbitrageSystem()
    
    # According to README, there should be exactly 5 strategies
    expected_strategies = {
        'dex_cex': DEXCEXArbitrage,
        'cross_exchange': CrossExchangeArbitrage,
        'triangular': TriangularArbitrage,
        'wrapped_tokens': WrappedTokensArbitrage,
        'statistical': StatisticalArbitrage
    }
    
    assert len(system.strategies) == 5, f"Expected 5 strategies but found {len(system.strategies)}"
    
    for strategy_name, strategy_class in expected_strategies.items():
        assert strategy_name in system.strategies, f"Strategy '{strategy_name}' not found in system.strategies"
        assert isinstance(system.strategies[strategy_name], strategy_class), \
            f"Strategy '{strategy_name}' is not an instance of {strategy_class.__name__}"
    
    print(f"✓ All 5 strategies are properly registered: {list(system.strategies.keys())}")


def test_all_strategies_have_required_methods():
    """Verify each strategy implements required methods"""
    system = MainArbitrageSystem()
    
    required_methods = ['add_strategy_edges']
    
    for strategy_name, strategy_instance in system.strategies.items():
        for method_name in required_methods:
            assert hasattr(strategy_instance, method_name), \
                f"Strategy '{strategy_name}' missing required method '{method_name}'"
            assert callable(getattr(strategy_instance, method_name)), \
                f"Strategy '{strategy_name}' method '{method_name}' is not callable"
    
    print(f"✓ All strategies have required methods: {required_methods}")


def test_all_strategies_have_strategy_name():
    """Verify each strategy has a strategy_name attribute"""
    system = MainArbitrageSystem()
    
    for strategy_key, strategy_instance in system.strategies.items():
        assert hasattr(strategy_instance, 'strategy_name'), \
            f"Strategy '{strategy_key}' missing 'strategy_name' attribute"
        assert strategy_instance.strategy_name == strategy_key, \
            f"Strategy '{strategy_key}' has mismatched strategy_name: '{strategy_instance.strategy_name}'"
    
    print(f"✓ All strategies have correct strategy_name attributes")


@pytest.mark.asyncio
async def test_all_strategies_can_add_edges():
    """Verify each strategy can add edges to a graph without errors"""
    system = MainArbitrageSystem()
    
    # Create minimal test price data
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50100.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 3000.0, 'ask': 3010.0, 'fee': 0.001},
                'BTC/ETH': {'bid': 16.5, 'ask': 16.6, 'fee': 0.001},
            },
            'kraken': {
                'BTC/USDT': {'bid': 50200.0, 'ask': 50300.0, 'fee': 0.001},
                'ETH/USDT': {'bid': 3020.0, 'ask': 3030.0, 'fee': 0.001},
            }
        },
        'dex': {
            'uniswap_v3': {
                'BTC/USDT': {'bid': 50150.0, 'ask': 50250.0, 'fee': 0.003},
                'ETH/USDT': {'bid': 3005.0, 'ask': 3015.0, 'fee': 0.003},
            }
        }
    }
    
    # Build initial graph
    graph = system.graph_builder.build_unified_graph(price_data)
    initial_edge_count = graph.number_of_edges()
    
    print(f"\nInitial graph: {graph.number_of_nodes()} nodes, {initial_edge_count} edges")
    
    # Test each strategy
    for strategy_name, strategy_instance in system.strategies.items():
        try:
            await strategy_instance.add_strategy_edges(graph, price_data)
            print(f"✓ Strategy '{strategy_name}' successfully added edges")
        except Exception as e:
            pytest.fail(f"Strategy '{strategy_name}' failed to add edges: {str(e)}")
    
    final_edge_count = graph.number_of_edges()
    print(f"Final graph: {graph.number_of_nodes()} nodes, {final_edge_count} edges")
    print(f"✓ All strategies can add edges to graph")


@pytest.mark.asyncio
async def test_strategies_can_be_used_in_full_scan():
    """Verify all strategies can be used in a full arbitrage scan"""
    system = MainArbitrageSystem()
    
    # Test with all strategies enabled
    all_strategies = ['dex_cex', 'cross_exchange', 'triangular', 'wrapped_tokens', 'statistical']
    pairs = ['BTC/USDT', 'ETH/USDT']
    
    try:
        # This should work without errors even if no opportunities are found
        opportunities = await system.run_full_arbitrage_scan(
            enabled_strategies=all_strategies,
            trading_pairs=pairs,
            min_profit_threshold=0.1
        )
        
        # Verify result is a list (may be empty)
        assert isinstance(opportunities, list), "run_full_arbitrage_scan should return a list"
        
        print(f"✓ Full scan with all 5 strategies completed successfully")
        print(f"  Found {len(opportunities)} opportunities")
        
    except Exception as e:
        pytest.fail(f"Full scan with all strategies failed: {str(e)}")


def test_strategy_names_match_ui_mapping():
    """Verify strategy names in code match the UI mapping in app.py"""
    # Expected mapping from app.py
    expected_ui_mapping = {
        "DEX/CEX Arbitrage": "dex_cex",
        "Cross-Exchange": "cross_exchange", 
        "Triangular": "triangular",
        "Wrapped Tokens": "wrapped_tokens",
        "Statistical AI": "statistical"
    }
    
    system = MainArbitrageSystem()
    
    # Verify all UI-mapped strategies exist in the system
    for ui_name, strategy_key in expected_ui_mapping.items():
        assert strategy_key in system.strategies, \
            f"UI strategy '{ui_name}' maps to '{strategy_key}' which is not in system.strategies"
    
    print(f"✓ All UI strategy mappings are valid")
    print(f"  UI strategies: {list(expected_ui_mapping.keys())}")
    print(f"  Backend strategies: {list(system.strategies.keys())}")


if __name__ == "__main__":
    # Run tests individually for debugging
    print("\n" + "="*70)
    print("COMPREHENSIVE STRATEGY IMPLEMENTATION TEST")
    print("="*70)
    
    print("\n1. Testing strategy registration...")
    test_all_five_strategies_registered()
    
    print("\n2. Testing required methods...")
    test_all_strategies_have_required_methods()
    
    print("\n3. Testing strategy names...")
    test_all_strategies_have_strategy_name()
    
    print("\n4. Testing UI mapping...")
    test_strategy_names_match_ui_mapping()
    
    print("\n5. Testing edge addition...")
    asyncio.run(test_all_strategies_can_add_edges())
    
    print("\n6. Testing full scan integration...")
    asyncio.run(test_strategies_can_be_used_in_full_scan())
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED! ✓")
    print("All 5 trading strategies are correctly implemented and integrated.")
    print("="*70)
