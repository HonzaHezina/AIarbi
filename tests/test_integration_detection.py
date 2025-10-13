import pytest
import asyncio

from core.main_arbitrage_system import MainArbitrageSystem

class DummyAI:
    """Deterministic AI stub used in tests to avoid heavy model loading."""
    def __init__(self):
        self._loaded = True

    def is_loaded(self):
        return True

    async def assess_opportunity_risk(self, cycle, price_data, profit_analysis):
        # Return a simple low-risk deterministic assessment
        return {
            'confidence': 0.9,
            'risk_level': 'LOW',
            'risk_score': 1,
            'risk_factors': [],
            'execution_time': 30,
            'recommended_capital': 100
        }

    async def rank_opportunities(self, opportunities):
        # Stable ranking: sort by profit_pct desc
        return sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)

@pytest.mark.asyncio
async def test_full_scan_integration_with_synthetic_data():
    """
    Integration test:
    - Builds MainArbitrageSystem
    - Injects DummyAI and overrides DataEngine.fetch_all_market_data to return synthetic price data
    - Runs run_full_arbitrage_scan enabling dex_cex and cross_exchange strategies
    - Asserts the system runs end-to-end and returns a list (possibly empty) and does not crash.
    """
    # Synthetic price data designed to include profitable DEX/CEX spread
    price_data = {
        'tokens': ['BTC'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 100.0, 'ask': 99.0},
            },
            'kraken': {
                'BTC/USDT': {'bid': 101.0, 'ask': 100.0},
            }
        },
        'dex': {
            'uniswap_v3': {
                'BTC/USDT': {'bid': 103.0, 'ask': 102.0, 'fee': 0.003},
            },
            'sushiswap': {
                'BTC/USDT': {'bid': 102.5, 'ask': 102.0, 'fee': 0.003},
            }
        }
    }

    main = MainArbitrageSystem(start_capital_usd=1000)

    # Inject deterministic AI stub so ranking/assessment is stable and no HF model is loaded
    main.ai = DummyAI()
    main.graph_builder.ai = main.ai
    main.detector.ai = main.ai
    for s in main.strategies.values():
        s.ai = main.ai

    # Override data engine fetch to return our synthetic fixture
    async def _fetch_all_market_data(_trading_pairs):
        return price_data
    main.data_engine.fetch_all_market_data = _fetch_all_market_data

    enabled_strategies = ['dex_cex', 'cross_exchange', 'triangular', 'wrapped_tokens', 'statistical']
    trading_pairs = ['BTC/USDT']

    opportunities = await main.run_full_arbitrage_scan(enabled_strategies, trading_pairs, min_profit_threshold=0.1)

    assert isinstance(opportunities, list)
    # At minimum ensure the graph was built and stored
    assert main.graph_builder.graph is not None
    # Ensure detector ran and produced cached opportunities (may be empty if thresholds filter)
    assert isinstance(main.cached_opportunities, list)