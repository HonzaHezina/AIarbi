# Profit Calculation Consistency Fix

**Date**: 2025-10-16  
**Issue**: Discrepancy between "Expected Profit" and "Net Profit" in arbitrage opportunity output

## Problem Description

The system was displaying two different profit values for the same arbitrage opportunity:

1. **Expected Profit**: Calculated by `calculate_cycle_profit()` in `core/main_arbitrage_system.py`
2. **Net Profit**: Recalculated by the UI display code in `app.py`

### Example from Issue

For a triangular arbitrage with 4 swaps:
- **Expected Profit**: 7.6044%
- **Net Profit**: 7.820%
- **Discrepancy**: ~0.22%

This ~0.22% difference was consistent across multiple opportunities, indicating a systematic calculation error rather than random rounding.

## Root Cause

The discrepancy was caused by **inconsistent slippage application**:

### Backend Calculation (`calculate_cycle_profit`)
```python
# Applied BOTH fee and slippage
current_token_amount = current_token_amount * conversion_rate * (1 - fee_pct - slippage)
```

### UI Display Calculation (app.py, before fix)
```python
# Only applied fee, missing slippage
next_token_amount = current_token_amount * rate * (1 - total_fees)
```

The default slippage of 0.05% (0.0005) per trade, applied over 4 trades, compounds to approximately:
- Cumulative effect: (1 - 0.0005)^4 ≈ 0.998
- Profit reduction: ~0.20%

This matched the observed discrepancy!

## Solution

### 1. Updated UI Display Calculation

**File**: `app.py` (lines 1424-1448)

**Before**:
```python
total_fees = edge_info.get('total_fees', 0)
if total_fees == 0:
    total_fees = edge_info.get('fee', 0.001)

fee_amount = current_token_amount * total_fees
details += f"  💸 **Total Fees**: {total_fees * 100:.4f}% ({fee_amount:.8f} {from_token})\n"
details += f"     📖 This includes all trading fees and slippage\n"

next_token_amount = current_token_amount * rate * (1 - total_fees)
```

**After**:
```python
total_fees = edge_info.get('total_fees', 0)
if total_fees == 0:
    total_fees = edge_info.get('fee', 0.001)

fee_amount = current_token_amount * total_fees
details += f"  💸 **Trading Fees**: {total_fees * 100:.4f}% ({fee_amount:.8f} {from_token})\n"

# Show slippage separately for transparency
slippage = edge_info.get('estimated_slippage', 0.0005)
slippage_amount = current_token_amount * slippage
details += f"  📉 **Estimated Slippage**: {slippage * 100:.4f}% ({slippage_amount:.8f} {from_token})\n"
details += f"     📖 Combined total impact: {(total_fees + slippage) * 100:.4f}%\n"

# Calculate amount after this step - must match calculate_cycle_profit logic
next_token_amount = current_token_amount * rate * (1 - total_fees - slippage)
```

### 2. Added Slippage to Edge Data

All strategy files now include `fee` and `estimated_slippage` fields when creating graph edges:

**Files Updated**:
- `strategies/triangular_arbitrage.py`
- `strategies/cross_exchange_arbitrage.py`
- `strategies/dex_cex_arbitrage.py`
- `strategies/wrapped_tokens_arbitrage.py`

**Example** (triangular_arbitrage.py):
```python
graph.add_edge(node1, node2,
    weight=weight1,
    rate=rate1,
    strategy='triangular',
    exchange=exchange_name,
    pair=pair1,
    step=1,
    action=action1,
    fee=fee1,                      # Added
    estimated_slippage=0.0005,     # Added
    triangle_id=f"{curr1_base}-{curr1_quote}-{curr2_quote}")
```

## Testing

### New Test: `tests/test_profit_consistency.py`

This test verifies that:
1. Backend profit calculation matches UI display calculation
2. Slippage is properly applied in both calculations
3. The difference between calculations is within 0.01% tolerance

**Test Results**:
```
✓ test_triangular_profit_consistency - PASSED
✓ test_slippage_is_applied - PASSED
```

### Existing Tests

All existing tests continue to pass:
```
tests/test_strategies_with_known_data.py - 13 tests PASSED
```

## Impact

### Before Fix
- Users saw two different profit numbers for the same opportunity
- "Expected Profit" was ~0.2% lower than "Net Profit" 
- This caused confusion and reduced trust in the system

### After Fix
- Both profit calculations now produce identical results (within 0.01% rounding tolerance)
- Slippage is explicitly shown in the UI for transparency
- Users can now trust that the displayed calculations are accurate

## Default Slippage Values

The system uses these default slippage estimates:
- **All strategies**: 0.05% (0.0005) per trade
- **Rationale**: Conservative estimate for typical market conditions
- **Future improvement**: Could be made dynamic based on market liquidity and volatility

## Code Review Recommendations

This fix addresses the specific issue raised. However, for further improvements:

1. **Dynamic Slippage**: Consider calculating slippage based on:
   - Trade size relative to liquidity
   - Market volatility
   - Historical slippage data

2. **Gas Cost Handling**: Currently gas costs are shown separately but not included in the final profit calculation. Verify this is intentional.

3. **Price Data Freshness**: Ensure price data timestamp is checked and stale data is rejected.

4. **Code Consolidation**: The `get_token_price_info` function appears in 3 strategy files with different implementations. While they serve different purposes, consider if any common logic can be extracted to a utility module.

## Senior Developer Checklist

As requested in the issue, here's a senior-level review checklist:

- [x] **Root cause identified**: Slippage missing from UI calculation
- [x] **Fix implemented**: UI now applies slippage consistently
- [x] **All strategies reviewed**: triangular, cross_exchange, dex_cex, wrapped_tokens all updated
- [x] **Data consistency**: No duplicate variables found; edge data now consistent
- [x] **Tests created**: New test validates the fix
- [x] **Tests pass**: All existing tests continue to pass
- [x] **Documentation**: This document explains the issue and fix
- [x] **Code quality**: Changes are minimal, surgical, and maintain existing patterns

## Conclusion

The profit calculation discrepancy has been fixed by ensuring both the backend `calculate_cycle_profit` and the UI display calculation apply the same fees and slippage. All strategies now consistently include this information in their edge data, and the fix is validated by comprehensive tests.
