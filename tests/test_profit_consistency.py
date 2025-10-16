"""
Test to ensure profit calculations are consistent between:
1. calculate_cycle_profit (backend calculation)
2. UI display calculation in app.py

This test verifies the fix for the issue where "Expected Profit" and "Net Profit"
showed different values due to missing slippage in UI calculation.
"""

import pytest
import asyncio
from core.graph_builder import GraphBuilder
from core.bellman_ford_detector import BellmanFordDetector
from core.main_arbitrage_system import MainArbitrageSystem
from strategies.triangular_arbitrage import TriangularArbitrage


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
            'recommended_capital': 1000
        }
    
    async def rank_opportunities(self, opportunities):
        return opportunities


@pytest.mark.asyncio
async def test_triangular_profit_consistency():
    """
    Test that profit calculated by calculate_cycle_profit matches
    the profit that would be calculated by UI display logic.
    
    This ensures "Expected Profit" = "Net Profit" in the output.
    """
    
    # Create price data matching the example from the issue
    price_data = {
        'tokens': ['USDC', 'LINK', 'USDT', 'ALGO'],
        'cex': {
            'coinbase': {
                'LINK/USDC': {'bid': 0.055331, 'ask': 1/0.055331, 'fee': 0.001},
                'LINK/USDT': {'bid': 18.060000, 'ask': 1/18.060000, 'fee': 0.001},
                'ALGO/USDT': {'bid': 1/5.546870, 'ask': 5.546870, 'fee': 0.001},
                'ALGO/USDC': {'bid': 0.195300, 'ask': 1/0.195300, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph and add triangular edges
    gb = GraphBuilder(ai_model=None)
    graph = gb.build_unified_graph(price_data)
    
    strategy = TriangularArbitrage(ai_model=None)
    await strategy.add_strategy_edges(graph, price_data)
    
    # Detect cycles using Bellman-Ford
    detector = BellmanFordDetector(ai_model=None)
    cycles = detector.detect_all_cycles(graph)
    
    print(f"\nFound {len(cycles)} cycles")
    
    # For each cycle, verify profit consistency
    arbitrage_system = MainArbitrageSystem()
    arbitrage_system.start_capital_usd = 1000.0
    
    for i, cycle in enumerate(cycles):
        print(f"\n=== Cycle {i+1} ===")
        print(f"Path: {' -> '.join(cycle.get('path', []))}")
        
        # Calculate profit using backend method
        profit_analysis = await arbitrage_system.calculate_cycle_profit(cycle, price_data)
        backend_profit_pct = profit_analysis.get('profit_pct', 0)
        backend_profit_usd = profit_analysis.get('profit_usd', 0)
        
        print(f"Backend calculation: {backend_profit_pct:.4f}% (${backend_profit_usd:.2f})")
        
        # Simulate UI calculation
        path = cycle.get('path', [])
        edge_data = cycle.get('edge_data', {})
        
        start_amount = 1000.0
        current_amount = start_amount
        
        for j in range(len(path) - 1):
            edge_key = f"{path[j]}->{path[j+1]}"
            edge_info = edge_data.get(edge_key, {})
            
            rate = edge_info.get('rate', 1.0)
            fee = edge_info.get('fee', 0.001)
            slippage = edge_info.get('estimated_slippage', 0.0005)
            
            # UI calculation (after fix)
            current_amount = current_amount * rate * (1 - fee - slippage)
            
            print(f"  Step {j+1}: {edge_key}")
            print(f"    Rate: {rate:.6f}, Fee: {fee*100:.2f}%, Slippage: {slippage*100:.2f}%")
            print(f"    Amount: {current_amount:.8f}")
        
        ui_profit_usd = current_amount - start_amount
        ui_profit_pct = (ui_profit_usd / start_amount) * 100
        
        print(f"UI calculation: {ui_profit_pct:.4f}% (${ui_profit_usd:.2f})")
        
        # Verify they match (within 0.01% tolerance for rounding)
        diff_pct = abs(backend_profit_pct - ui_profit_pct)
        diff_usd = abs(backend_profit_usd - ui_profit_usd)
        
        print(f"Difference: {diff_pct:.4f}% (${diff_usd:.2f})")
        
        assert diff_pct < 0.01, (
            f"Profit calculations don't match! "
            f"Backend: {backend_profit_pct:.4f}%, UI: {ui_profit_pct:.4f}%, "
            f"Difference: {diff_pct:.4f}%"
        )
        
        assert diff_usd < 0.10, (
            f"Profit USD calculations don't match! "
            f"Backend: ${backend_profit_usd:.2f}, UI: ${ui_profit_usd:.2f}, "
            f"Difference: ${diff_usd:.2f}"
        )
    
    print("\n✓ All profit calculations are consistent!")


@pytest.mark.asyncio
async def test_slippage_is_applied():
    """
    Test that slippage is properly applied in all calculations.
    Without slippage, the profit would be higher.
    """
    
    # Simple triangular cycle
    price_data = {
        'tokens': ['USDT', 'BTC', 'ETH'],
        'cex': {
            'binance': {
                'BTC/USDT': {'bid': 50000.0, 'ask': 50000.0, 'fee': 0.001},
                'BTC/ETH': {'bid': 16.8, 'ask': 16.8, 'fee': 0.001},
                'ETH/USDT': {'bid': 3020.0, 'ask': 3020.0, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    graph = gb.build_unified_graph(price_data)
    
    strategy = TriangularArbitrage(ai_model=None)
    await strategy.add_strategy_edges(graph, price_data)
    
    # Get cycles
    detector = BellmanFordDetector(ai_model=None)
    cycles = detector.detect_all_cycles(graph)
    
    if len(cycles) == 0:
        print("No cycles found, skipping slippage test")
        return
    
    cycle = cycles[0]
    
    # Calculate profit with slippage
    arbitrage_system = MainArbitrageSystem()
    arbitrage_system.start_capital_usd = 1000.0
    profit_with_slippage = await arbitrage_system.calculate_cycle_profit(cycle, price_data)
    
    # Manually calculate without slippage to verify it's being applied
    path = cycle.get('path', [])
    edge_data = cycle.get('edge_data', {})
    
    current_amount = 1000.0
    for j in range(len(path) - 1):
        edge_key = f"{path[j]}->{path[j+1]}"
        edge_info = edge_data.get(edge_key, {})
        rate = edge_info.get('rate', 1.0)
        fee = edge_info.get('fee', 0.001)
        # Calculate WITHOUT slippage
        current_amount = current_amount * rate * (1 - fee)
    
    profit_without_slippage = ((current_amount - 1000.0) / 1000.0) * 100
    
    print(f"\nProfit with slippage: {profit_with_slippage['profit_pct']:.4f}%")
    print(f"Profit without slippage: {profit_without_slippage:.4f}%")
    
    # Profit with slippage should be LESS than profit without slippage
    assert profit_with_slippage['profit_pct'] < profit_without_slippage, (
        f"Slippage is not being applied correctly! "
        f"With slippage: {profit_with_slippage['profit_pct']:.4f}%, "
        f"Without: {profit_without_slippage:.4f}%"
    )
    
    # The difference should be roughly the cumulative slippage effect
    # For 3 trades with 0.05% slippage each: (1-0.0005)^3 ≈ 0.9985
    # Profit reduction ≈ 0.15%
    expected_reduction = 0.10  # At least 0.1% reduction
    actual_reduction = profit_without_slippage - profit_with_slippage['profit_pct']
    
    print(f"Profit reduction from slippage: {actual_reduction:.4f}%")
    
    assert actual_reduction >= expected_reduction, (
        f"Slippage effect is too small! Expected at least {expected_reduction}% reduction, "
        f"got {actual_reduction:.4f}%"
    )
    
    print("✓ Slippage is being applied correctly!")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_triangular_profit_consistency())
    asyncio.run(test_slippage_is_applied())
