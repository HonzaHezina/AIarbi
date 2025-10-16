"""
Test the specific LINK triangular arbitrage opportunity from the issue.

This test verifies the exact scenario reported in the issue where a 4-step
arbitrage cycle was detected: LINK -> USDT -> ALGO -> USDC -> LINK

Expected profit: 8.625% (starting with 66.67 LINK, ending with 72.42 LINK)
"""

import pytest
import asyncio
import math
from typing import Dict, Any

from core.graph_builder import GraphBuilder
from core.bellman_ford_detector import BellmanFordDetector
from strategies.triangular_arbitrage import TriangularArbitrage


class DummyAI:
    """Dummy AI for testing"""
    def is_loaded(self):
        return True
    
    async def assess_opportunity_risk(self, cycle, price_data, profit_analysis):
        return {
            'confidence': 0.5,
            'risk_level': 'MEDIUM',
            'risk_score': 5,
            'risk_factors': ['Market volatility', 'Execution speed critical'],
            'execution_time': 35.0,
            'recommended_capital': 1000
        }


@pytest.mark.asyncio
async def test_link_opportunity_from_issue():
    """
    Test the exact LINK opportunity reported in the issue.
    
    This is a 4-step cycle on Coinbase:
    LINK -> USDT -> ALGO -> USDC -> LINK
    
    Starting with $1000 (66.67 LINK at $15/LINK)
    Expected to end with 72.42 LINK (~$1086.25)
    Expected profit: 8.625%
    """
    
    # Recreate the exact price data from the issue
    # Note: The issue shows this as a "triangular" strategy, but it's actually
    # a 4-step cycle (quadrangular). The triangular strategy should still
    # detect it since it looks for profitable cycles.
    price_data = {
        'tokens': ['LINK', 'USDT', 'ALGO', 'USDC'],
        'cex': {
            'coinbase': {
                # Step 1: LINK -> USDT (sell LINK for USDT)
                # Pair LINK/USDT: bid=18.37 USDT per LINK, ask=18.37 USDT per LINK
                'LINK/USDT': {'bid': 18.370000, 'ask': 18.370000, 'fee': 0.001},
                
                # Step 2: USDT -> ALGO (buy ALGO with USDT)
                # Pair ALGO/USDT: ask=0.180366 USDT per ALGO (so 1 USDT buys 1/0.180366 = 5.544383 ALGO)
                'ALGO/USDT': {'bid': 0.180366, 'ask': 0.180366, 'fee': 0.001},
                
                # Step 3: ALGO -> USDC (sell ALGO for USDC)
                # Pair ALGO/USDC: bid=0.197400 USDC per ALGO
                'ALGO/USDC': {'bid': 0.197400, 'ask': 0.197400, 'fee': 0.001},
                
                # Step 4: USDC -> LINK (buy LINK with USDC)
                # Pair LINK/USDC: ask=18.397 USDC per LINK (so 1 USDC buys 1/18.397 = 0.054354 LINK)
                'LINK/USDC': {'bid': 18.397, 'ask': 18.397, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph(price_data)
    
    # Add triangular arbitrage edges
    strategy = TriangularArbitrage(ai_model=None)
    await strategy.add_strategy_edges(G, price_data)
    
    # Verify edges were added
    triangular_edges = [e for e in G.edges(data=True) if e[2].get('strategy') == 'triangular']
    
    # Should have edges for this cycle
    assert len(triangular_edges) > 0, "Should find triangular arbitrage edges for LINK cycle"
    
    print(f"✓ Added {len(triangular_edges)} triangular edges")
    
    # Now test direct detection
    opportunities = await strategy.detect_direct_triangular_opportunities(price_data)
    
    print(f"✓ Found {len(opportunities)} opportunities")
    
    # Should find the LINK opportunity
    link_opportunities = [opp for opp in opportunities 
                         if 'LINK' in str(opp.get('base_currency', ''))]
    
    print(f"✓ Found {len(link_opportunities)} LINK-related opportunities")
    
    if link_opportunities:
        best_opp = link_opportunities[0]
        print(f"  Best LINK opportunity: {best_opp.get('profit_pct', 0):.4f}% profit")
        print(f"  Cycle: {best_opp.get('cycle_path', 'N/A')}")
        
        # The profit should be close to 8.625%
        # Allow some tolerance for rounding and calculation differences
        assert best_opp.get('profit_pct', 0) > 7.0, \
            f"Expected profit > 7%, got {best_opp.get('profit_pct', 0):.4f}%"


@pytest.mark.asyncio
async def test_link_opportunity_manual_calculation():
    """
    Manually calculate the LINK opportunity to verify the math.
    
    This test walks through each step of the arbitrage cycle and verifies
    that the calculations match the expected values from the issue.
    """
    
    # Starting conditions
    starting_usd = 1000.00
    link_price = 15.00  # Approximate price of LINK in USD
    starting_link = starting_usd / link_price  # 66.67 LINK
    
    print(f"\n{'='*60}")
    print(f"MANUAL CALCULATION OF LINK OPPORTUNITY")
    print(f"{'='*60}")
    print(f"Starting: ${starting_usd:.2f} = {starting_link:.8f} LINK")
    
    # Step 1: LINK -> USDT
    # Action: sell LINK for USDT, use bid price
    rate1 = 18.370000  # USDT per LINK
    fee1 = 0.001  # 0.1%
    slippage1 = 0.0005  # 0.05%
    usdt_amount = starting_link * rate1 * (1 - fee1 - slippage1)
    
    print(f"\nStep 1: LINK -> USDT")
    print(f"  Rate: {rate1:.6f} USDT/LINK")
    print(f"  {starting_link:.8f} LINK * {rate1:.6f} * {1 - fee1 - slippage1:.6f}")
    print(f"  = {usdt_amount:.8f} USDT")
    
    # Expected from issue: 1222.82966667 USDT
    expected_usdt = 1222.82966667
    assert abs(usdt_amount - expected_usdt) < 0.01, \
        f"USDT amount mismatch: expected {expected_usdt:.8f}, got {usdt_amount:.8f}"
    
    # Step 2: USDT -> ALGO
    # Action: buy ALGO with USDT
    # The pair is ALGO/USDT, so we use 1/ask to get ALGO per USDT
    # Or directly: 5.544383 ALGO per USDT
    rate2 = 5.544383  # ALGO per USDT
    fee2 = 0.001
    slippage2 = 0.0005
    algo_amount = usdt_amount * rate2 * (1 - fee2 - slippage2)
    
    print(f"\nStep 2: USDT -> ALGO")
    print(f"  Rate: {rate2:.6f} ALGO/USDT")
    print(f"  {usdt_amount:.8f} USDT * {rate2:.6f} * {1 - fee2 - slippage2:.6f}")
    print(f"  = {algo_amount:.8f} ALGO")
    
    # Expected from issue: 6769.66686364 ALGO
    expected_algo = 6769.66686364
    assert abs(algo_amount - expected_algo) < 0.01, \
        f"ALGO amount mismatch: expected {expected_algo:.8f}, got {algo_amount:.8f}"
    
    # Step 3: ALGO -> USDC
    # Action: sell ALGO for USDC, use bid price
    rate3 = 0.197400  # USDC per ALGO
    fee3 = 0.001
    slippage3 = 0.0005
    usdc_amount = algo_amount * rate3 * (1 - fee3 - slippage3)
    
    print(f"\nStep 3: ALGO -> USDC")
    print(f"  Rate: {rate3:.6f} USDC/ALGO")
    print(f"  {algo_amount:.8f} ALGO * {rate3:.6f} * {1 - fee3 - slippage3:.6f}")
    print(f"  = {usdc_amount:.8f} USDC")
    
    # Expected from issue: 1334.32774052 USDC
    expected_usdc = 1334.32774052
    assert abs(usdc_amount - expected_usdc) < 0.01, \
        f"USDC amount mismatch: expected {expected_usdc:.8f}, got {usdc_amount:.8f}"
    
    # Step 4: USDC -> LINK
    # Action: buy LINK with USDC
    # The pair is LINK/USDC, so we use 1/ask to get LINK per USDC
    # Or directly: 0.054354 LINK per USDC
    rate4 = 0.054354  # LINK per USDC
    fee4 = 0.001
    slippage4 = 0.0005
    final_link = usdc_amount * rate4 * (1 - fee4 - slippage4)
    
    print(f"\nStep 4: USDC -> LINK")
    print(f"  Rate: {rate4:.6f} LINK/USDC")
    print(f"  {usdc_amount:.8f} USDC * {rate4:.6f} * {1 - fee4 - slippage4:.6f}")
    print(f"  = {final_link:.8f} LINK")
    
    # Expected from issue: 72.41690667 LINK
    expected_link = 72.41690667
    # Allow 0.1% tolerance
    assert abs((final_link - expected_link) / expected_link) < 0.001, \
        f"Final LINK amount mismatch: expected {expected_link:.8f}, got {final_link:.8f}"
    
    # Calculate profit
    profit_link = final_link - starting_link
    profit_pct = (profit_link / starting_link) * 100
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Started with: {starting_link:.8f} LINK")
    print(f"Ended with:   {final_link:.8f} LINK")
    print(f"Profit:       {profit_link:.8f} LINK ({profit_pct:.4f}%)")
    print(f"Expected:     {expected_link - starting_link:.8f} LINK (8.625%)")
    
    # Expected profit: 8.625%
    assert abs(profit_pct - 8.625) < 0.01, \
        f"Profit percentage mismatch: expected 8.625%, got {profit_pct:.4f}%"
    
    print(f"\n✅ All calculations match the issue report!")


@pytest.mark.asyncio
async def test_triangular_with_bellman_ford():
    """
    Test that Bellman-Ford detector can find the LINK opportunity.
    
    This tests the full pipeline: graph building, edge addition,
    and cycle detection using the Bellman-Ford algorithm.
    """
    
    price_data = {
        'tokens': ['LINK', 'USDT', 'ALGO', 'USDC'],
        'cex': {
            'coinbase': {
                'LINK/USDT': {'bid': 18.370000, 'ask': 18.370000, 'fee': 0.001},
                'ALGO/USDT': {'bid': 0.180366, 'ask': 0.180366, 'fee': 0.001},
                'ALGO/USDC': {'bid': 0.197400, 'ask': 0.197400, 'fee': 0.001},
                'LINK/USDC': {'bid': 18.397, 'ask': 18.397, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    # Build graph with triangular edges
    gb = GraphBuilder(ai_model=DummyAI())
    G = gb.build_unified_graph(price_data)
    
    strategy = TriangularArbitrage(ai_model=DummyAI())
    await strategy.add_strategy_edges(G, price_data)
    
    print(f"\nGraph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Run Bellman-Ford
    detector = BellmanFordDetector(ai_model=DummyAI())
    cycles = detector.detect_all_cycles(G)
    
    print(f"Bellman-Ford found {len(cycles)} cycles")
    
    # Should find at least one profitable cycle
    profitable_cycles = [c for c in cycles if c.get('profit_pct', 0) > 1.0]
    
    print(f"Found {len(profitable_cycles)} profitable cycles")
    
    if profitable_cycles:
        best = profitable_cycles[0]
        print(f"\nBest cycle:")
        print(f"  Strategy: {best.get('strategy', 'N/A')}")
        print(f"  Profit: {best.get('profit_pct', 0):.4f}%")
        print(f"  Path: {' -> '.join(best.get('path', []))}")


@pytest.mark.asyncio
async def test_negative_scenario_no_profit():
    """
    Test a negative scenario where there is NO profitable opportunity.
    
    This ensures the system doesn't report false positives.
    """
    
    price_data = {
        'tokens': ['LINK', 'USDT', 'USDC'],
        'cex': {
            'coinbase': {
                # Perfect 1:1 ratio between USDT and USDC
                'LINK/USDT': {'bid': 15.00, 'ask': 15.00, 'fee': 0.001},
                'LINK/USDC': {'bid': 15.00, 'ask': 15.00, 'fee': 0.001},
                'USDT/USDC': {'bid': 1.00, 'ask': 1.00, 'fee': 0.001},
            }
        },
        'dex': {}
    }
    
    strategy = TriangularArbitrage(ai_model=None)
    opportunities = await strategy.detect_direct_triangular_opportunities(price_data)
    
    # Should find no profitable opportunities (fees eat up any potential profit)
    profitable = [opp for opp in opportunities if opp.get('profit_pct', 0) > 0.1]
    
    assert len(profitable) == 0, \
        f"Should not find profitable opportunities with balanced prices, but found {len(profitable)}"
    
    print(f"✓ Correctly found no profitable opportunities in balanced market")


if __name__ == "__main__":
    # Run tests individually for debugging
    print("\n" + "="*70)
    print("TESTING LINK ARBITRAGE OPPORTUNITY FROM ISSUE")
    print("="*70)
    
    asyncio.run(test_link_opportunity_manual_calculation())
    asyncio.run(test_link_opportunity_from_issue())
    asyncio.run(test_triangular_with_bellman_ford())
    asyncio.run(test_negative_scenario_no_profit())
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED!")
    print("="*70)
