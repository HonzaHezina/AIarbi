"""Test recommended DEX pairs and new Algorand protocols."""
import pytest
import asyncio
from core.data_engine import DataEngine
from strategies.dex_cex_arbitrage import DEXCEXArbitrage
from utils.config import DEX_CONFIG, DEFAULT_SYMBOLS


class DummyAI:
    """Deterministic AI stub for testing."""
    async def get_response(self, prompt: str):
        return "Confidence: 0.8"


@pytest.mark.asyncio
async def test_new_trading_pairs_in_config():
    """Test that new recommended trading pairs are in configuration."""
    # Check new global DEX pairs
    assert 'WETH/USDC' in DEFAULT_SYMBOLS
    assert 'WBTC/USDC' in DEFAULT_SYMBOLS
    assert 'LINK/USDC' in DEFAULT_SYMBOLS
    assert 'MATIC/USDC' in DEFAULT_SYMBOLS
    assert 'CAKE/USDT' in DEFAULT_SYMBOLS
    assert 'DAI/USDC' in DEFAULT_SYMBOLS
    
    # Check Algorand pairs
    assert 'ALGO/USDT' in DEFAULT_SYMBOLS
    assert 'ALGO/USDC' in DEFAULT_SYMBOLS
    
    # Verify total count
    assert len(DEFAULT_SYMBOLS) == 16, f"Expected 16 pairs, got {len(DEFAULT_SYMBOLS)}"


@pytest.mark.asyncio
async def test_new_algorand_dex_in_config():
    """Test that new Algorand DEX protocols are configured."""
    # Check AlgoFi
    assert 'algofi' in DEX_CONFIG
    assert DEX_CONFIG['algofi']['network'] == 'algorand'
    assert DEX_CONFIG['algofi']['gas_cost_usd'] <= 0.01
    
    # Check Algox
    assert 'algox' in DEX_CONFIG
    assert DEX_CONFIG['algox']['network'] == 'algorand'
    assert DEX_CONFIG['algox']['gas_cost_usd'] <= 0.01
    
    # Verify total Algorand DEX count
    algorand_dex = [k for k, v in DEX_CONFIG.items() if v.get('network') == 'algorand']
    assert len(algorand_dex) == 4, f"Expected 4 Algorand DEX, got {len(algorand_dex)}: {algorand_dex}"
    
    # Verify all 4 Algorand DEXs
    assert 'tinyman' in algorand_dex
    assert 'pact' in algorand_dex
    assert 'algofi' in algorand_dex
    assert 'algox' in algorand_dex


@pytest.mark.asyncio
async def test_data_engine_has_new_protocols():
    """Test that DataEngine includes new Algorand protocols."""
    engine = DataEngine()
    
    # Check new protocols exist
    assert 'algofi' in engine.dex_protocols
    assert 'algox' in engine.dex_protocols
    
    # Verify protocol details
    assert engine.dex_protocols['algofi']['network'] == 'algorand'
    assert engine.dex_protocols['algox']['network'] == 'algorand'
    
    # Verify total DEX protocols count
    assert len(engine.dex_protocols) >= 13, f"Expected at least 13 DEX protocols, got {len(engine.dex_protocols)}"


@pytest.mark.asyncio
async def test_dex_cex_strategy_includes_new_protocols():
    """Test that DEX/CEX strategy includes new Algorand DEX protocols."""
    ai = DummyAI()
    strategy = DEXCEXArbitrage(ai)
    
    # Check new protocols in strategy
    assert 'algofi' in strategy.dex_protocols
    assert 'algox' in strategy.dex_protocols
    
    # Verify total count
    assert len(strategy.dex_protocols) == 13, f"Expected 13 DEX protocols, got {len(strategy.dex_protocols)}"
    
    # Verify all Algorand DEXs
    algorand_protocols = ['tinyman', 'pact', 'algofi', 'algox']
    for protocol in algorand_protocols:
        assert protocol in strategy.dex_protocols, f"Missing {protocol} in strategy"


@pytest.mark.asyncio
async def test_new_pair_price_generation():
    """Test that new pairs can generate prices."""
    engine = DataEngine()
    
    # Test new global DEX pairs
    new_pairs = ['WETH/USDC', 'WBTC/USDC', 'LINK/USDC', 'MATIC/USDC', 'CAKE/USDT', 'DAI/USDC']
    
    for pair in new_pairs:
        # Generate DEX price
        dex_price = engine.generate_simulated_dex_price(pair)
        assert dex_price is not None
        assert 'bid' in dex_price
        assert 'ask' in dex_price
        assert 'last' in dex_price
        assert dex_price['bid'] > 0
        assert dex_price['ask'] > 0
        
        # Generate fallback ticker
        fallback = engine.generate_fallback_ticker(pair)
        assert fallback is not None
        assert 'bid' in fallback
        assert 'ask' in fallback
        assert fallback['bid'] > 0
        assert fallback['ask'] > 0


@pytest.mark.asyncio
async def test_algo_usdc_pair():
    """Test ALGO/USDC pair specifically."""
    engine = DataEngine()
    
    # Check ALGO/USDC is in DEFAULT_SYMBOLS
    assert 'ALGO/USDC' in DEFAULT_SYMBOLS
    
    # Test price generation
    dex_price = engine.generate_simulated_dex_price('ALGO/USDC')
    assert dex_price['last'] > 0
    assert dex_price['last'] < 10  # ALGO price should be reasonable
    
    fallback = engine.generate_fallback_ticker('ALGO/USDC')
    assert fallback['last'] > 0
    assert fallback['last'] < 10


@pytest.mark.asyncio
async def test_gas_cost_for_new_protocols():
    """Test gas cost estimation for new Algorand protocols."""
    ai = DummyAI()
    strategy = DEXCEXArbitrage(ai)
    
    # Test AlgoFi gas cost
    algofi_gas = await strategy.estimate_dex_gas_cost('algofi', 'ALGO')
    assert algofi_gas is not None
    assert algofi_gas < 0.01, f"AlgoFi gas cost should be < $0.01, got ${algofi_gas}"
    
    # Test Algox gas cost
    algox_gas = await strategy.estimate_dex_gas_cost('algox', 'ALGO')
    assert algox_gas is not None
    assert algox_gas < 0.01, f"Algox gas cost should be < $0.01, got ${algox_gas}"
    
    # Compare with Ethereum DEX
    uniswap_gas = await strategy.estimate_dex_gas_cost('uniswap_v3', 'ETH')
    assert uniswap_gas > 10, "Uniswap gas should be > $10"
    
    # Verify Algorand is significantly cheaper
    assert algofi_gas < uniswap_gas / 1000, "AlgoFi should be 1000x cheaper than Uniswap"


@pytest.mark.asyncio
async def test_full_scan_with_new_pairs():
    """Test full arbitrage scan with new trading pairs and protocols."""
    from core.main_arbitrage_system import MainArbitrageSystem
    
    # Create system
    main = MainArbitrageSystem(start_capital_usd=1000)
    main.ai = DummyAI()
    main.detector.ai = DummyAI()
    
    # Replace AI in all strategies
    for strategy in main.strategies.values():
        strategy.ai = DummyAI()
    
    # Create synthetic price data with new pairs
    price_data = {
        'tokens': ['ALGO', 'USDC', 'LINK'],
        'cex': {
            'binance': {
                'ALGO/USDC': {'bid': 0.18, 'ask': 0.1805, 'last': 0.1802, 'volume': 1000, 'timestamp': 1000000},
                'ALGO': {'bid': 0.18, 'ask': 0.1805, 'last': 0.1802, 'volume': 1000, 'timestamp': 1000000, 'mapped_from_pair': 'ALGO/USDC'},
                'LINK/USDC': {'bid': 15.0, 'ask': 15.05, 'last': 15.02, 'volume': 500, 'timestamp': 1000000},
                'LINK': {'bid': 15.0, 'ask': 15.05, 'last': 15.02, 'volume': 500, 'timestamp': 1000000, 'mapped_from_pair': 'LINK/USDC'}
            }
        },
        'dex': {
            'tinyman': {
                'ALGO/USDC': {'bid': 0.185, 'ask': 0.186, 'last': 0.1855, 'volume': 300, 'timestamp': 1000000, 'fee': 0.0025, 'liquidity': 50000},
                'ALGO': {'bid': 0.185, 'ask': 0.186, 'last': 0.1855, 'volume': 300, 'timestamp': 1000000, 'fee': 0.0025, 'liquidity': 50000}
            },
            'algofi': {
                'ALGO/USDC': {'bid': 0.184, 'ask': 0.185, 'last': 0.1845, 'volume': 200, 'timestamp': 1000000, 'fee': 0.0025, 'liquidity': 40000},
                'ALGO': {'bid': 0.184, 'ask': 0.185, 'last': 0.1845, 'volume': 200, 'timestamp': 1000000, 'fee': 0.0025, 'liquidity': 40000}
            },
            'algox': {
                'ALGO/USDC': {'bid': 0.183, 'ask': 0.184, 'last': 0.1835, 'volume': 150, 'timestamp': 1000000, 'fee': 0.003, 'liquidity': 30000},
                'ALGO': {'bid': 0.183, 'ask': 0.184, 'last': 0.1835, 'volume': 150, 'timestamp': 1000000, 'fee': 0.003, 'liquidity': 30000}
            },
            'uniswap_v3': {
                'LINK/USDC': {'bid': 15.1, 'ask': 15.15, 'last': 15.12, 'volume': 400, 'timestamp': 1000000, 'fee': 0.003, 'liquidity': 100000},
                'LINK': {'bid': 15.1, 'ask': 15.15, 'last': 15.12, 'volume': 400, 'timestamp': 1000000, 'fee': 0.003, 'liquidity': 100000}
            }
        },
        'timestamp': None,
        'pairs': ['ALGO/USDC', 'LINK/USDC']
    }
    
    # Override fetch_all_market_data to return synthetic data
    async def _fetch_all_market_data(_trading_pairs):
        return price_data
    
    main.data_engine.fetch_all_market_data = _fetch_all_market_data
    
    # Run scan with new pairs
    enabled_strategies = ['dex_cex']
    trading_pairs = ['ALGO/USDC', 'LINK/USDC']
    
    opportunities = await main.run_full_arbitrage_scan(enabled_strategies, trading_pairs, min_profit_threshold=0.1)
    
    # System should run without errors
    assert isinstance(opportunities, list)
    assert main.graph_builder.graph is not None
    
    # Check that graph contains nodes for new pairs
    graph = main.graph_builder.graph
    algo_nodes = [n for n in graph.nodes() if 'ALGO' in n]
    assert len(algo_nodes) > 0, "Graph should contain ALGO nodes"
    
    link_nodes = [n for n in graph.nodes() if 'LINK' in n]
    assert len(link_nodes) > 0, "Graph should contain LINK nodes"
    
    # Check for new Algorand DEX nodes (AlgoFi and Algox)
    algofi_nodes = [n for n in graph.nodes() if 'algofi' in n]
    algox_nodes = [n for n in graph.nodes() if 'algox' in n]
    assert len(algofi_nodes) > 0, "Graph should contain AlgoFi nodes"
    assert len(algox_nodes) > 0, "Graph should contain Algox nodes"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
