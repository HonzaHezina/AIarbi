"""
Test the profit calculation fix
Ensures that profit is calculated correctly by tracking token quantities
instead of mixing up USD values with token amounts.
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
            'confidence': 0.9,
            'risk_level': 'LOW',
            'risk_score': 1,
            'risk_factors': [],
            'execution_time': 30,
            'recommended_capital': 100
        }
    
    async def rank_opportunities(self, opportunities):
        return sorted(opportunities, key=lambda x: x.get('profit_pct', 0), reverse=True)


def create_test_system(start_capital=1000.0):
    """Create a test system with mocked AI to avoid HuggingFace dependencies"""
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
async def test_triangular_arbitrage_profit_calculation():
    """
    Test triangular arbitrage profit calculation.
    
    Scenario:
    - Start with 1000 USDT
    - Trade USDT -> BTC -> ETH -> USDT
    - Prices create a small arbitrage opportunity
    
    Expected: Profit should be positive but reasonable (not 36000%!)
    """
    # Create price data with a small triangular opportunity
    # USDT -> BTC: 1 BTC = 50,000 USDT
    # BTC -> ETH: 1 BTC = 16.67 ETH
    # ETH -> USDT: 1 ETH = 3,100 USDT
    # 
    # Circle: 50,000 USDT -> 1 BTC -> 16.67 ETH -> 51,677 USDT
    # Profit before fees: 1,677 / 50,000 = 3.35%
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {
                    'bid': 50000.0,
                    'ask': 50000.0,
                    'fee': 0.001
                },
                'ETH/BTC': {
                    'bid': 0.06,      # 1 ETH = 0.06 BTC
                    'ask': 0.06,
                    'fee': 0.001
                },
                'ETH/USDT': {
                    'bid': 3100.0,
                    'ask': 3100.0,
                    'fee': 0.001
                }
            }
        },
        'dex': {}
    }
    
    # Create arbitrage cycle
    cycle = {
        'path': ['USDT@binance', 'BTC@binance', 'ETH@binance', 'USDT@binance'],
        'edge_data': {
            'USDT@binance->BTC@binance': {
                'rate': 1.0 / 50000.0,  # 1 USDT = 0.00002 BTC
                'fee': 0.001,
                'weight': -math.log((1.0 / 50000.0) * (1 - 0.001))
            },
            'BTC@binance->ETH@binance': {
                'rate': 16.67,  # 1 BTC = 16.67 ETH
                'fee': 0.001,
                'weight': -math.log(16.67 * (1 - 0.001))
            },
            'ETH@binance->USDT@binance': {
                'rate': 3100.0,  # 1 ETH = 3,100 USDT
                'fee': 0.001,
                'weight': -math.log(3100.0 * (1 - 0.001))
            }
        }
    }
    
    # Use test system to avoid HuggingFace dependency
    system = create_test_system(start_capital=1000.0)
    
    profit = await system.calculate_cycle_profit(cycle, price_data)
    
    # Assertions
    assert profit['profit_pct'] > 0, "Profit should be positive"
    assert profit['profit_pct'] < 5.0, "Profit should be less than 5% (not 36000%!)"
    assert profit['profit_usd'] > 0, "Profit in USD should be positive"
    assert profit['profit_usd'] < 50, "Profit should be reasonable, not $362,201!"
    
    # The profit should be around 2.7% after fees (3.35% - 0.3% fees)
    expected_profit_range = (2.0, 3.5)
    assert expected_profit_range[0] < profit['profit_pct'] < expected_profit_range[1], \
        f"Expected profit between {expected_profit_range[0]}% and {expected_profit_range[1]}%, got {profit['profit_pct']:.2f}%"
    
    print(f"✓ Test PASSED: Profit = {profit['profit_pct']:.2f}% (${profit['profit_usd']:.2f})")


@pytest.mark.asyncio  
async def test_no_arbitrage_break_even():
    """
    Test that break-even cycles (no arbitrage) result in 0% or negative profit.
    
    Scenario:
    - BTC price is same on both exchanges
    - Transfer between exchanges has fees
    
    Expected: Small negative profit due to fees
    """
    price_data = {
        'tokens': ['BTC', 'USDT'],
        'cex': {
            'binance': {
                'BTC/USDT': {
                    'bid': 50000.0,
                    'ask': 50000.0,
                    'fee': 0.001
                }
            },
            'kraken': {
                'BTC/USDT': {
                    'bid': 50000.0,  # Same price
                    'ask': 50000.0,
                    'fee': 0.001
                }
            }
        },
        'dex': {}
    }
    
    # Cycle: BTC@binance -> BTC@kraken -> BTC@binance
    cycle = {
        'path': ['BTC@binance', 'BTC@kraken', 'BTC@binance'],
        'edge_data': {
            'BTC@binance->BTC@kraken': {
                'rate': 1.0,
                'fee': 0.002,  # 0.2% transfer fee
                'weight': -math.log(1.0 * (1 - 0.002))
            },
            'BTC@kraken->BTC@binance': {
                'rate': 1.0,
                'fee': 0.002,
                'weight': -math.log(1.0 * (1 - 0.002))
            }
        }
    }
    
    system = create_test_system(start_capital=1000.0)
    
    profit = await system.calculate_cycle_profit(cycle, price_data)
    
    # Should be negative due to fees
    assert profit['profit_pct'] < 0.1, "Profit should be near zero or negative due to fees"
    assert profit['profit_usd'] < 1, "Profit should be minimal"
    
    print(f"✓ Test PASSED: No arbitrage results in {profit['profit_pct']:.2f}% profit (break-even)")


@pytest.mark.asyncio
async def test_conversion_rates_applied_correctly():
    """
    Test that conversion rates are applied correctly to token quantities.
    
    This is the core fix - ensuring we multiply token amounts by rates,
    not USD amounts by rates.
    """
    price_data = {
        'tokens': ['LINK', 'USDC'],
        'cex': {
            'binance': {
                'LINK/USDC': {
                    'bid': 15.0,  # 1 LINK = 15 USDC
                    'ask': 15.0,
                    'fee': 0.001
                }
            }
        },
        'dex': {
            'oneinch': {
                'LINK/USDC': {
                    'bid': 15.5,  # 1 LINK = 15.5 USDC (slightly higher)
                    'ask': 15.5,
                    'fee': 0.003
                }
            }
        }
    }
    
    # Cycle: Buy LINK on Binance, sell on 1inch
    # LINK@binance -> USDC@binance -> USDC@oneinch -> LINK@oneinch -> LINK@binance
    cycle = {
        'path': ['LINK@binance', 'USDC@binance', 'USDC@oneinch', 'LINK@oneinch', 'LINK@binance'],
        'edge_data': {
            'LINK@binance->USDC@binance': {
                'rate': 15.0,  # 1 LINK = 15 USDC
                'fee': 0.001,
                'weight': -math.log(15.0 * (1 - 0.001))
            },
            'USDC@binance->USDC@oneinch': {
                'rate': 1.0,  # 1:1 stablecoin transfer
                'fee': 0.0001,  # Minimal transfer fee
                'weight': -math.log(1.0 * (1 - 0.0001))
            },
            'USDC@oneinch->LINK@oneinch': {
                'rate': 1.0 / 15.5,  # 1 USDC = 0.0645 LINK
                'fee': 0.003,
                'weight': -math.log((1.0 / 15.5) * (1 - 0.003))
            },
            'LINK@oneinch->LINK@binance': {
                'rate': 1.0,  # 1:1 LINK transfer
                'fee': 0.002,
                'weight': -math.log(1.0 * (1 - 0.002))
            }
        }
    }
    
    system = create_test_system(start_capital=1000.0)
    
    profit = await system.calculate_cycle_profit(cycle, price_data)
    
    # The profit should be small (could be negative after all the fees)
    # (15.5 - 15) / 15 = 3.33% before fees, but fees eat into it
    # The important thing is that profit is NOT 36000%!
    assert profit['profit_pct'] > -10.0, "Should not have huge losses (got {:.2f}%)".format(profit['profit_pct'])
    assert profit['profit_pct'] < 10.0, "Should not have unrealistic profits (got {:.2f}%)".format(profit['profit_pct'])
    
    # Most importantly: profit should not be 36000%!
    assert abs(profit['profit_pct']) < 100, "Profit should be reasonable, not thousands of percent! (got {:.2f}%)".format(profit['profit_pct'])
    
    print(f"✓ Test PASSED: Conversion rates applied correctly, profit = {profit['profit_pct']:.2f}%")
    print(f"  (Small loss is OK - it means the cycle has high fees, not wildly wrong calculations)")


def test_token_usd_price_helper():
    """Test the get_token_usd_price helper function"""
    system = create_test_system(start_capital=1000.0)
    
    price_data = {
        'tokens': ['BTC', 'ETH', 'USDT', 'USDC'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 49000.0, 'ask': 50000.0},
                'ETH/USDT': {'bid': 2900.0, 'ask': 3000.0}
            }
        },
        'dex': {}
    }
    
    # Test stablecoins
    assert system.get_token_usd_price('USDT', 'binance', price_data) == 1.0
    assert system.get_token_usd_price('USDC', 'binance', price_data) == 1.0
    
    # Test BTC (should return mid price)
    btc_price = system.get_token_usd_price('BTC', 'binance', price_data)
    assert 49000 < btc_price < 50000, f"BTC price should be between bid and ask, got {btc_price}"
    
    # Test ETH
    eth_price = system.get_token_usd_price('ETH', 'binance', price_data)
    assert 2900 < eth_price < 3000, f"ETH price should be between bid and ask, got {eth_price}"
    
    print("✓ Test PASSED: Token USD price helper works correctly")
