"""Test Algorand integration with the arbitrage system."""
import pytest
import asyncio
from core.main_arbitrage_system import MainArbitrageSystem
from utils.config import DEX_CONFIG, DEFAULT_SYMBOLS


class DummyAI:
    """Deterministic AI stub for testing."""
    def __init__(self):
        self._loaded = True

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

    async def rank_opportunities(self, opportunities):
        return sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)


@pytest.mark.asyncio
async def test_algorand_dex_in_config():
    """Test that Algorand DEX protocols are configured."""
    assert 'tinyman' in DEX_CONFIG
    assert 'pact' in DEX_CONFIG
    assert DEX_CONFIG['tinyman']['network'] == 'algorand'
    assert DEX_CONFIG['pact']['network'] == 'algorand'
    # Verify low gas costs
    assert DEX_CONFIG['tinyman']['gas_cost_usd'] <= 0.01
    assert DEX_CONFIG['pact']['gas_cost_usd'] <= 0.01


@pytest.mark.asyncio
async def test_algo_in_default_symbols():
    """Test that ALGO is in default trading pairs."""
    assert 'ALGO/USDT' in DEFAULT_SYMBOLS


@pytest.mark.asyncio
async def test_data_engine_has_algorand_protocols():
    """Test that DataEngine includes Algorand protocols."""
    main = MainArbitrageSystem(start_capital_usd=1000)
    data_engine = main.data_engine
    
    assert 'tinyman' in data_engine.dex_protocols
    assert 'pact' in data_engine.dex_protocols
    assert data_engine.dex_protocols['tinyman']['network'] == 'algorand'
    assert data_engine.dex_protocols['pact']['network'] == 'algorand'


@pytest.mark.asyncio
async def test_dex_cex_strategy_includes_algorand():
    """Test that DEX/CEX strategy includes Algorand DEX protocols."""
    main = MainArbitrageSystem(start_capital_usd=1000)
    dex_cex_strategy = main.strategies['dex_cex']
    
    assert 'tinyman' in dex_cex_strategy.dex_protocols
    assert 'pact' in dex_cex_strategy.dex_protocols


@pytest.mark.asyncio
async def test_algo_price_generation():
    """Test that ALGO prices can be generated."""
    main = MainArbitrageSystem(start_capital_usd=1000)
    data_engine = main.data_engine
    
    # Test fallback ticker
    algo_ticker = data_engine.generate_fallback_ticker('ALGO/USDT')
    assert algo_ticker['bid'] > 0
    assert algo_ticker['ask'] > 0
    assert algo_ticker['last'] > 0
    assert algo_ticker['bid'] <= algo_ticker['last'] <= algo_ticker['ask']
    
    # Test DEX price
    algo_dex = data_engine.generate_simulated_dex_price('ALGO/USDT')
    assert algo_dex['bid'] > 0
    assert algo_dex['ask'] > 0
    assert algo_dex['last'] > 0
    assert 'fee' in algo_dex
    assert 'liquidity' in algo_dex


@pytest.mark.asyncio
async def test_full_scan_with_algo():
    """Test full arbitrage scan with ALGO trading pair."""
    # Create system with dummy AI
    main = MainArbitrageSystem(start_capital_usd=1000)
    main.ai = DummyAI()
    main.detector.ai = DummyAI()
    
    # Replace AI in all strategies
    for strategy in main.strategies.values():
        strategy.ai = DummyAI()
    
    # Create synthetic price data with ALGO
    price_data = {
        'tokens': ['ALGO', 'USDT'],
        'cex': {
            'binance': {
                'ALGO/USDT': {'bid': 0.18, 'ask': 0.1805, 'last': 0.1802, 'volume': 1000, 'timestamp': 1000000},
                'ALGO': {'bid': 0.18, 'ask': 0.1805, 'last': 0.1802, 'volume': 1000, 'timestamp': 1000000, 'mapped_from_pair': 'ALGO/USDT'}
            },
            'kraken': {
                'ALGO/USDT': {'bid': 0.181, 'ask': 0.182, 'last': 0.1815, 'volume': 500, 'timestamp': 1000000},
                'ALGO': {'bid': 0.181, 'ask': 0.182, 'last': 0.1815, 'volume': 500, 'timestamp': 1000000, 'mapped_from_pair': 'ALGO/USDT'}
            }
        },
        'dex': {
            'tinyman': {
                'ALGO/USDT': {'bid': 0.185, 'ask': 0.186, 'last': 0.1855, 'volume': 300, 'timestamp': 1000000, 'fee': 0.0025, 'liquidity': 50000},
                'ALGO': {'bid': 0.185, 'ask': 0.186, 'last': 0.1855, 'volume': 300, 'timestamp': 1000000, 'fee': 0.0025, 'liquidity': 50000}
            },
            'pact': {
                'ALGO/USDT': {'bid': 0.184, 'ask': 0.185, 'last': 0.1845, 'volume': 200, 'timestamp': 1000000, 'fee': 0.003, 'liquidity': 40000},
                'ALGO': {'bid': 0.184, 'ask': 0.185, 'last': 0.1845, 'volume': 200, 'timestamp': 1000000, 'fee': 0.003, 'liquidity': 40000}
            }
        },
        'timestamp': None,
        'pairs': ['ALGO/USDT']
    }
    
    # Override fetch_all_market_data to return synthetic data
    async def _fetch_all_market_data(_trading_pairs):
        return price_data
    
    main.data_engine.fetch_all_market_data = _fetch_all_market_data
    
    # Run scan with ALGO
    enabled_strategies = ['dex_cex', 'cross_exchange']
    trading_pairs = ['ALGO/USDT']
    
    opportunities = await main.run_full_arbitrage_scan(enabled_strategies, trading_pairs, min_profit_threshold=0.1)
    
    # System should run without errors
    assert isinstance(opportunities, list)
    assert main.graph_builder.graph is not None
    
    # Check that graph contains ALGO nodes
    graph = main.graph_builder.graph
    algo_nodes = [n for n in graph.nodes() if 'ALGO' in n]
    assert len(algo_nodes) > 0, "Graph should contain ALGO nodes"
    
    # Check for Algorand DEX nodes
    algorand_nodes = [n for n in graph.nodes() if 'tinyman' in n or 'pact' in n]
    assert len(algorand_nodes) > 0, "Graph should contain Algorand DEX nodes"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
