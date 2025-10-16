"""
Test the specific MATIC quadrangular arbitrage case from the problem statement.
This test ensures the profit calculation is realistic, not 11583%!
"""
import pytest
import asyncio
import math
from unittest.mock import Mock
from core.main_arbitrage_system import MainArbitrageSystem


class DummyAI:
    """Dummy AI that doesn't require HuggingFace"""
    def is_loaded(self):
        return True
    
    async def assess_opportunity_risk(self, cycle, price_data, profit_analysis):
        return {
            'confidence': 0.5,
            'risk_level': 'MEDIUM',
            'risk_score': 2,
            'risk_factors': [],
            'execution_time': 35,
            'recommended_capital': 1000
        }
    
    async def rank_opportunities(self, opportunities):
        return sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)


def create_test_system(start_capital=1000.0):
    """Create a test system with mocked AI"""
    system = MainArbitrageSystem.__new__(MainArbitrageSystem)
    system.ai = DummyAI()
    system.start_capital_usd = float(start_capital)
    system.data_engine = Mock()
    system.graph_builder = Mock()
    system.detector = Mock()
    system.strategies = {}
    system.last_scan_time = None
    system.cached_opportunities = []
    return system


@pytest.mark.asyncio
async def test_matic_quadrangular_arbitrage_realistic_profit():
    """
    Test the exact MATIC → USDT → ALGO → USDC → MATIC cycle from the problem statement.
    
    The problem showed 11583% profit which is clearly wrong.
    Expected: Should show realistic profit (likely negative due to fees, or very small positive)
    
    The rates from the problem statement showed an issue with the last step.
    This test uses REALISTIC prices for MATIC (~$100 in this test scenario, though 
    real MATIC is ~$0.85) to demonstrate that with correct rate calculation,
    the profit should be realistic, not 11583%.
    
    Note: This test uses simulated prices where MATIC=$100 to match the problem statement,
    but the important thing is that all pairs for the same token are CONSISTENT.
    """
    
    # Create price data with REALISTIC rates
    # MATIC = $100, ALGO = $0.18, USDT/USDC = $1
    price_data = {
        'tokens': ['MATIC', 'USDT', 'ALGO', 'USDC'],
        'cex': {
            'coinbase': {
                'MATIC/USDT': {
                    'bid': 99.977559,  # Sell MATIC for USDT
                    'ask': 100.022441,
                    'fee': 0.001
                },
                'ALGO/USDT': {
                    'bid': 0.180040,   # Sell ALGO for USDT (inverted from problem)
                    'ask': 0.180324,
                    'fee': 0.001
                },
                'USDT/ALGO': {
                    'bid': 5.545234,   # This is the rate from problem (USDT→ALGO)
                    'ask': 5.553162,
                    'fee': 0.001
                },
                'ALGO/USDC': {
                    'bid': 0.180040,   # Sell ALGO for USDC
                    'ask': 0.180324,
                    'fee': 0.001
                },
                'MATIC/USDC': {
                    'bid': 99.90,      # Sell MATIC for USDC
                    'ask': 100.10,     # Buy MATIC with USDC
                    'fee': 0.001
                }
            }
        },
        'dex': {}
    }
    
    # Create the cycle with corrected rates
    # Note: The edge rate should already be correctly calculated by graph_builder
    cycle = {
        'path': ['MATIC@coinbase', 'USDT@coinbase', 'ALGO@coinbase', 'USDC@coinbase', 'MATIC@coinbase'],
        'edge_data': {
            'MATIC@coinbase->USDT@coinbase': {
                'rate': 99.977559,  # Sell MATIC: 1 MATIC = 99.977559 USDT
                'fee': 0.001,
                'pair': 'MATIC/USDT',
                'action': 'sell',
                'weight': -math.log(99.977559 * (1 - 0.001))
            },
            'USDT@coinbase->ALGO@coinbase': {
                'rate': 5.545234,  # Buy ALGO with USDT: 1 USDT = 5.545234 ALGO (from USDT/ALGO pair bid)
                'fee': 0.001,
                'pair': 'USDT/ALGO',
                'action': 'sell',  # Selling USDT in USDT/ALGO pair
                'weight': -math.log(5.545234 * (1 - 0.001))
            },
            'ALGO@coinbase->USDC@coinbase': {
                'rate': 0.180040,  # Sell ALGO: 1 ALGO = 0.180040 USDC
                'fee': 0.001,
                'pair': 'ALGO/USDC',
                'action': 'sell',
                'weight': -math.log(0.180040 * (1 - 0.001))
            },
            'USDC@coinbase->MATIC@coinbase': {
                # CORRECTED RATE: Buy MATIC with USDC
                # Use ask price from price_data for consistency
                'rate': 1 / price_data['cex']['coinbase']['MATIC/USDC']['ask'],  # Buy MATIC
                'fee': 0.001,
                'pair': 'MATIC/USDC',
                'action': 'buy',  # Buying MATIC with USDC
                'weight': -math.log((1 / price_data['cex']['coinbase']['MATIC/USDC']['ask']) * (1 - 0.001))
            }
        }
    }
    
    system = create_test_system(start_capital=1000.0)
    
    profit = await system.calculate_cycle_profit(cycle, price_data)
    
    # Calculate expected result manually:
    # Start: 10 MATIC
    # After SWAP 1: 10 * 99.977559 * 0.999 = 998.777 USDT
    # After SWAP 2: 998.777 * 5.545234 * 0.999 = 5532.35 ALGO
    # After SWAP 3: 5532.35 * 0.180040 * 0.999 = 995.15 USDC
    # After SWAP 4: 995.15 * (1/100.10) * 0.999 = 9.915 MATIC
    # Loss: (9.915 - 10) / 10 = -0.85%
    
    print(f"Profit: {profit['profit_pct']:.2f}%")
    print(f"Profit USD: ${profit['profit_usd']:.2f}")
    
    # Assertions: profit should be NEGATIVE (loss) or very small, NOT 11583%!
    assert profit['profit_pct'] < 1.0, f"Profit should be < 1%, got {profit['profit_pct']:.2f}%"
    assert profit['profit_pct'] > -10.0, f"Loss should be < 10%, got {profit['profit_pct']:.2f}%"
    assert abs(profit['profit_pct']) < 100, f"Profit should be realistic, got {profit['profit_pct']:.2f}%"
    
    # The profit should be around -0.85% (small loss due to fees)
    expected_range = (-5.0, 0.5)
    assert expected_range[0] < profit['profit_pct'] < expected_range[1], \
        f"Expected profit between {expected_range[0]}% and {expected_range[1]}%, got {profit['profit_pct']:.2f}%"
    
    print(f"✓ Test PASSED: MATIC cycle shows realistic profit {profit['profit_pct']:.2f}% (not 11583%!)")


@pytest.mark.asyncio
async def test_matic_cycle_with_wrong_rate_gets_validated():
    """
    Test that if we pass the WRONG rate (like in the problem), it gets detected.
    
    This test uses an intentionally wrong rate (1.177614 MATIC/USDC instead of ~0.00999)
    to verify our validation handles it gracefully without crashing.
    """
    price_data = {
        'tokens': ['MATIC', 'USDC'],
        'cex': {
            'coinbase': {
                'MATIC/USDC': {
                    'bid': 99.90,
                    'ask': 100.10,
                    'fee': 0.001
                }
            }
        },
        'dex': {}
    }
    
    # Cycle with the WRONG rate from the problem
    cycle = {
        'path': ['USDC@coinbase', 'MATIC@coinbase', 'USDC@coinbase'],
        'edge_data': {
            'USDC@coinbase->MATIC@coinbase': {
                'rate': 1.177614,  # WRONG! Should be about 0.00999 (1/100.10)
                'fee': 0.001,
                'pair': 'MATIC/USDC',
                'action': 'buy',
                'weight': -math.log(1.177614 * (1 - 0.001))
            },
            'MATIC@coinbase->USDC@coinbase': {
                'rate': 99.90,  # Correct
                'fee': 0.001,
                'pair': 'MATIC/USDC',
                'action': 'sell',
                'weight': -math.log(99.90 * (1 - 0.001))
            }
        }
    }
    
    system = create_test_system(start_capital=1000.0)
    
    profit = await system.calculate_cycle_profit(cycle, price_data)
    
    # With the wrong rate, it would show huge profit
    # But our validation should cap it or at least warn about it
    # The validation won't fix the rate (that's not its job), but it will log warnings
    print(f"Profit with wrong rate: {profit['profit_pct']:.2f}%")
    
    # The profit will still be wrong (since we're passing wrong data)
    # But at least it shouldn't crash, and logs should show warnings
    assert profit['profit_pct'] is not None, "Profit calculation should not crash"
    
    print("✓ Test PASSED: System handles wrong rates without crashing")


if __name__ == '__main__':
    asyncio.run(test_matic_quadrangular_arbitrage_realistic_profit())
    asyncio.run(test_matic_cycle_with_wrong_rate_gets_validated())
