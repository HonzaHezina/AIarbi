# Core Components

This directory contains the core system components that orchestrate arbitrage detection.

## Components

### 1. AI Model (`ai_model.py`)
**Class**: `ArbitrageAI`  
**Status**: ✅ Implemented and working

AI-powered analysis using HuggingFace transformers.

**Key Features**:
- Microsoft DialoGPT-medium model
- Automatic fallback to rule-based analysis
- Optimized for HuggingFace Spaces (float16/float32)
- Opportunity analysis and recommendations

**Key Methods**:
```python
load_model()              # Load AI model with fallback
analyze_opportunity()     # Analyze single opportunity
rank_opportunities()      # Rank multiple opportunities
generate_insights()       # Generate market insights
is_loaded()              # Check if model is loaded
```

**Optional Dependencies**: transformers, torch (graceful fallback if missing)

---

### 2. Data Engine (`data_engine.py`)
**Class**: `DataEngine`  
**Status**: ✅ Implemented and working

Fetches real-time and historical market data from exchanges.

**Key Features**:
- CCXT integration for 8 CEX exchanges
- Web3 integration for 3 DEX protocols
- REST API fallback mechanism
- Rate limiting and error handling
- Simulated data for demo mode

**Supported Exchanges**:
- **CEX**: Binance, Kraken, Coinbase, KuCoin, Bitfinex, Bybit, OKX, Gate.io
- **DEX**: Uniswap V3, SushiSwap, PancakeSwap

**Key Methods**:
```python
async fetch_all_market_data(symbols)  # Fetch from all sources
async fetch_cex_prices(symbols)       # CEX prices via CCXT
async fetch_dex_prices(symbols)       # DEX prices via Web3
get_historical_data(exchange, symbol) # Historical OHLCV data
```

---

### 3. Graph Builder (`graph_builder.py`)
**Class**: `GraphBuilder`  
**Status**: ✅ Implemented and working

Builds weighted directed graphs for arbitrage detection.

**Key Features**:
- NetworkX graphs for market representation
- Logarithmic edge weights for negative cycle detection
- Metadata tracking for strategies
- Multi-source graph construction

**Key Methods**:
```python
build_graph(market_data, symbols, strategies)  # Build complete graph
add_edge(from, to, weight, metadata)           # Add single edge
calculate_edge_weight(price, fee)              # Calculate log weight
get_graph()                                    # Return NetworkX graph
```

**Graph Structure**:
- Nodes: Tokens (BTC, ETH, USDT, etc.)
- Edges: Trading pairs with weights
- Weight: -log(price * (1 - fee))
- Negative cycles = Arbitrage opportunities

---

### 4. Bellman-Ford Detector (`bellman_ford_detector.py`)
**Class**: `BellmanFordDetector`  
**Status**: ✅ Implemented and working

Detects arbitrage opportunities using Bellman-Ford algorithm.

**Key Features**:
- Negative cycle detection in weighted graphs
- Multi-source analysis for all tokens
- AI scoring and ranking
- Risk assessment

**Key Methods**:
```python
detect_arbitrage_opportunities(graph, symbols)  # Detect all opportunities
bellman_ford(graph, source)                     # Run algorithm from source
extract_negative_cycle(graph, predecessor)      # Extract arbitrage cycle
calculate_cycle_profit(cycle, graph)            # Calculate expected profit
```

**Algorithm**:
1. Run Bellman-Ford from each token
2. Detect negative cycles
3. Extract trading paths
4. Calculate profits
5. Rank by AI confidence

---

### 5. Main Arbitrage System (`main_arbitrage_system.py`)
**Class**: `MainArbitrageSystem`  
**Status**: ✅ Implemented and working

Orchestrates all components and strategies.

**Key Features**:
- Component initialization and coordination
- Strategy registration and management
- Asynchronous scanning
- Performance tracking

**Key Methods**:
```python
async scan_opportunities(strategies, symbols, min_profit)  # Full scan
get_strategy(name)                                         # Get strategy instance
register_strategy(name, strategy)                          # Add new strategy
get_performance_metrics()                                  # Get system metrics
```

**Registered Strategies**:
1. dex_cex - DEX/CEX Arbitrage
2. cross_exchange - Cross-Exchange Arbitrage
3. triangular - Triangular Arbitrage
4. wrapped_tokens - Wrapped Tokens Arbitrage
5. statistical - Statistical AI Arbitrage

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────┐
│         Main Arbitrage System                       │
│              (orchestrator)                         │
└──┬──────────┬──────────┬───────────┬──────────────┘
   │          │          │           │
   ▼          ▼          ▼           ▼
┌──────┐ ┌────────┐ ┌─────────┐ ┌─────────────┐
│  AI  │ │  Data  │ │  Graph  │ │  Bellman    │
│Model │ │ Engine │ │ Builder │ │   -Ford     │
└──────┘ └────┬───┘ └─────────┘ └─────────────┘
              │
      ┌───────┴────────┐
      │                │
  ┌───▼───┐      ┌────▼────┐
  │ CCXT  │      │  Web3   │
  │8 CEX  │      │ 3 DEX   │
  └───────┘      └─────────┘
```

## Workflow

1. **Data Collection**: DataEngine fetches prices from all exchanges
2. **Graph Construction**: GraphBuilder creates weighted directed graph
3. **Edge Addition**: Each strategy adds its specific edges
4. **Cycle Detection**: BellmanFordDetector finds negative cycles
5. **AI Analysis**: ArbitrageAI ranks and analyzes opportunities
6. **Results**: Return top opportunities with confidence scores

## Configuration

Core components use configuration from `utils/config.py`:

- Exchange settings (fees, rate limits)
- Trading thresholds
- Demo mode flags
- Logging configuration

## Testing

Core components are tested in:
- `tests/test_all_strategies_complete.py` - Integration tests
- `tests/test_endpoints.py` - Configuration tests

Run tests:
```bash
pytest tests/ -v
```

## Dependencies

**Required**:
- networkx - Graph algorithms
- ccxt - Exchange API (optional, graceful fallback)
- aiohttp - Async HTTP requests

**Optional**:
- transformers - AI model
- torch - PyTorch for AI
- web3 - Ethereum/DEX integration

## Performance

**Typical Scan**:
- 5 strategies: ~3-5 seconds
- 10 trading pairs: ~8-12 seconds
- Auto-refresh: 30 seconds

**Memory Usage**:
- Base: ~500 MB
- With AI: ~1-2 GB
- Peak: ~2.5 GB

## Error Handling

All components implement graceful error handling:
- CCXT failures → REST fallback
- Web3 unavailable → Simulated data
- AI unavailable → Rule-based analysis
- Rate limits → Exponential backoff

## Extending the System

To add new functionality:

1. **New Data Source**: Extend `DataEngine`
2. **New Detection Algorithm**: Extend `BellmanFordDetector`
3. **New Strategy**: Add to `strategies/` and register
4. **New AI Feature**: Extend `ArbitrageAI`

## Documentation

See parent README files:
- [README.md](../README.md) - Main documentation
- [README.cs.md](../README.cs.md) - Czech documentation
- [STRATEGY_VERIFICATION_REPORT.md](../STRATEGY_VERIFICATION_REPORT.md)
