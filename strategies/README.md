# Trading Strategies

This directory contains all arbitrage trading strategy implementations.

## Strategy Modules

### 1. DEX/CEX Arbitrage (`dex_cex_arbitrage.py`)
**Class**: `DEXCEXArbitrage`  
**Status**: ✅ Implemented and working

Exploits price differences between decentralized (DEX) and centralized (CEX) exchanges.

**Key Methods**:
- `add_strategy_edges()` - Adds DEX/CEX arbitrage edges to the graph
- `calculate_arbitrage_profit()` - Calculates profit considering fees and gas costs
- `detect_direct_opportunities()` - Direct detection of arbitrage opportunities

**Supported**:
- DEX: Uniswap V3, SushiSwap, PancakeSwap
- CEX: Binance, Kraken, Coinbase, KuCoin

---

### 2. Cross-Exchange Arbitrage (`cross_exchange_arbitrage.py`)
**Class**: `CrossExchangeArbitrage`  
**Status**: ✅ Implemented and working

Exploits price differences across multiple centralized exchanges.

**Key Methods**:
- `add_strategy_edges()` - Adds cross-exchange arbitrage edges
- `add_cross_exchange_edges_for_token()` - Adds edges for specific tokens
- `calculate_arbitrage_profit()` - Calculates profit with transfer costs

**Supported**: Binance, Kraken, Coinbase, KuCoin, Bitfinex, Bybit, OKX, Gate.io

---

### 3. Triangular Arbitrage (`triangular_arbitrage.py`)
**Class**: `TriangularArbitrage`  
**Status**: ✅ Implemented and working

Three-currency cycles within single exchanges.

**Example**: BTC → ETH → USDT → BTC

**Key Methods**:
- `add_strategy_edges()` - Adds triangular arbitrage edges
- `find_triangular_on_exchange()` - Finds triangular opportunities on specific exchange
- `calculate_triangular_profit()` - Calculates profit for three-step cycles

---

### 4. Wrapped Tokens Arbitrage (`wrapped_tokens_arbitrage.py`)
**Class**: `WrappedTokensArbitrage`  
**Status**: ✅ Implemented and working

Native vs wrapped token price discrepancies.

**Supported Pairs**:
- BTC ↔ wBTC
- ETH ↔ wETH
- BNB ↔ wBNB

**Key Methods**:
- `add_strategy_edges()` - Adds wrapped token arbitrage edges
- `add_wrap_unwrap_edges()` - Adds wrap/unwrap operation edges
- `add_native_wrapped_arbitrage_edges()` - Adds native vs wrapped arbitrage edges

---

### 5. Statistical Arbitrage (`statistical_arbitrage.py`)
**Class**: `StatisticalArbitrage`  
**Status**: ✅ Implemented and working

AI-powered correlation and anomaly detection.

**Parameters**:
- Lookback period: 100 data points
- Correlation threshold: 0.7
- Deviation threshold: 2.0 standard deviations

**Key Methods**:
- `add_strategy_edges()` - Adds statistical arbitrage signals
- `detect_statistical_anomalies()` - Detects price correlation anomalies
- `calculate_correlation()` - Calculates price correlations between exchanges

---

## Common Interface

All strategies implement the following interface:

```python
class Strategy:
    def __init__(self, ai_model):
        self.ai = ai_model
        self.strategy_name = "strategy_name"
    
    def add_strategy_edges(self, graph, market_data, symbols):
        """Add strategy-specific edges to the graph"""
        pass
```

## Usage

Strategies are automatically registered in `core/main_arbitrage_system.py`:

```python
self.strategies = {
    'dex_cex': DEXCEXArbitrage(self.ai),
    'cross_exchange': CrossExchangeArbitrage(self.ai),
    'triangular': TriangularArbitrage(self.ai),
    'wrapped_tokens': WrappedTokensArbitrage(self.ai),
    'statistical': StatisticalArbitrage(self.ai)
}
```

Enable/disable strategies in the UI or via configuration.

## Testing

All strategies are tested in `tests/test_all_strategies_complete.py`:

- ✅ Registration verification
- ✅ Required methods check
- ✅ Strategy name validation
- ✅ UI mapping verification
- ✅ Edge addition testing
- ✅ Full scan integration

Run tests:
```bash
pytest tests/test_all_strategies_complete.py -v
```

## Adding New Strategies

To add a new strategy:

1. Create a new file: `strategies/your_strategy.py`
2. Implement the strategy class with required methods
3. Register in `core/main_arbitrage_system.py`
4. Add UI mapping in `app.py`
5. Add tests in `tests/`
6. Update this README

## Documentation

See parent README files for more details:
- [README.md](../README.md) - Main documentation (English)
- [README.cs.md](../README.cs.md) - Complete documentation (Czech)
- [STRATEGY_VERIFICATION_REPORT.md](../STRATEGY_VERIFICATION_REPORT.md) - Verification report
