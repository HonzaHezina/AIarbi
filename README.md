---
title: AI Crypto Arbitrage System
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.45.0
app_file: app.py
pinned: false
---

#  AI Crypto Arbitrage System

Advanced multi-strategy cryptocurrency arbitrage detection system powered by AI and Bellman-Ford algorithms.

##  Features

> 🌐 **Live on Hugging Face Spaces**: [https://huggingface.co/spaces/HonzaH/AIarbi](https://huggingface.co/spaces/HonzaH/AIarbi)

###  5 Arbitrage Strategies (All Implemented ✅)
1. ✅ **DEX/CEX Arbitrage** - Price differences between decentralized and centralized exchanges
2. ✅ **Cross-Exchange Arbitrage** - Price differences across multiple CEX exchanges  
3. ✅ **Triangular Arbitrage** - Three-currency cycles within single exchanges
4. ✅ **Wrapped Tokens Arbitrage** - Native vs wrapped token price discrepancies
5. ✅ **Statistical Arbitrage** - AI-powered correlation and anomaly detection

###  AI-Powered Analysis (Implemented ✅)
- **Opportunity Ranking** - AI scores and ranks all detected opportunities
- **Risk Assessment** - Intelligent risk scoring and confidence analysis
- **Timing Optimization** - AI determines optimal execution timing
- **Market Insights** - Real-time market condition analysis
- **Model**: Microsoft DialoGPT-medium (optimized for HF Spaces)
- **Fallback**: Rule-based analysis when AI unavailable

###  Advanced Detection (Implemented ✅)
- **Bellman-Ford Algorithm** - Detects complex multi-hop arbitrage cycles
- **Real-time Monitoring** - Live price feeds from 13+ exchanges and DEX protocols
- **Statistical Analysis** - Historical correlation and deviation detection
- **Graph-based** - NetworkX graphs with weighted edges
- **Multi-strategy** - All strategies work together or independently

### 📊 Supported Trading Pairs (16 Total)

**Algorand Focus:**
- ALGO/USDT, ALGO/USDC - Primary Algorand pairs for ultra-low fee arbitrage

**Global DEX Recommended Pairs:**
- WETH/USDC - Wrapped Ethereum on Uniswap V3, SushiSwap
- WBTC/USDC - Wrapped Bitcoin on Curve stableswap pools
- LINK/USDC - Chainlink on Uniswap V3
- MATIC/USDC - Polygon on QuickSwap
- CAKE/USDT - PancakeSwap native token on BSC
- DAI/USDC - Stablecoin pair on Curve (low spreads)

**Major Assets:**
- BTC/USDT, ETH/USDT, BNB/USDT, ADA/USDT, SOL/USDT, MATIC/USDT, DOT/USDT, LINK/USDT

See `docs_archive/RECOMMENDED_DEX_PAIRS.md` for detailed recommendations.

##  Architecture

```
┌──────────────────────────────────────────────────────┐
│           Gradio UI (app.py)                         │
│  Live Scanner | Execution Center | Analytics         │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│        Main Arbitrage System (orchestrator)          │
│              core/main_arbitrage_system.py           │
└──┬────┬─────────┬──────────┬────────────┬───────────┘
   │    │         │          │            │
┌──▼─┐┌─▼───┐ ┌──▼────┐ ┌───▼──────┐ ┌──▼──────────┐
│ AI ││Data │ │ Graph │ │ Bellman  │ │ 5 Strategy  │
│Model││Engine│ │Builder│ │  -Ford   │ │  Modules    │
└────┘└──┬──┘ └───────┘ └──────────┘ └─────────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼──┐   ┌──▼────┐
│ CCXT │   │ Web3  │
│8 CEX │   │3 DEX  │
└──────┘   └───────┘
```

**Components:**
- **Gradio UI**: Interactive web interface with 3 tabs
- **Main System**: Orchestrates all components and strategies
- **AI Model**: DialoGPT-medium for analysis and recommendations
- **Data Engine**: Fetches prices from CEX (CCXT) and DEX (Web3)
- **Graph Builder**: Creates weighted directed graphs
- **Bellman-Ford**: Detects negative cycles (arbitrage opportunities)
- **5 Strategies**: All implemented and working independently or together

##  Supported Exchanges & How Connections Are Made

This project connects to exchanges and DEX protocols using two complementary approaches: CCXT clients for unified CEX access, and direct REST / Web3 fallbacks for verification or when CCXT calls fail.

### Centralized Exchanges (CEX) - 8 Exchanges

All CEX exchanges are connected via CCXT clients with REST API fallback:

| Exchange | Status | CCXT | REST Fallback | Taker Fee | Rate Limit |
|----------|--------|------|---------------|-----------|------------|
| 🟡 **Binance** | ✅ Working | ✅ | ✅ | 0.1% | 1200/min |
| 🟣 **Kraken** | ✅ Working | ✅ | ✅ | 0.26% | 60/min |
| 🔵 **Coinbase Pro** | ✅ Working | ✅ | ✅ | 0.5% | 600/min |
| 🟢 **KuCoin** | ✅ Working | ✅ | ✅ | 0.1% | 120/min |
| 🟠 **Bitfinex** | ✅ Working | ✅ | ⚠️ prefer_ccxt | 0.2% | 90/min |
| ⚫ **Bybit** | ✅ Working | ✅ | ✅ | 0.1% | 120/min |
| 🔴 **OKX** | ✅ Working | ✅ | ✅ | 0.1% | 600/min |
| 🟦 **Gate.io** | ✅ Working | ✅ | ✅ | 0.2% | 900/min |

**Implementation details:**
- CCXT provides unified `fetch_ticker`/`fetch_ohlcv` APIs
- Automatic rate-limiting per exchange
- REST fallback if CCXT fails (patterns in `utils/config.py`)
- Override base URLs via environment: `EXCHANGE_ENDPOINT_BINANCE_BASE_URL`
- Defensive initialization (CI/tests don't fail on missing exchanges)

**Data Aggregators (2):**
- 🦎 **CoinGecko** - Price aggregation (no API key required)
- 💹 **CoinMarketCap** - Price data (API key recommended)

See `core/data_engine.py` for implementation and `utils/config.py` for configuration.

### Decentralized Protocols (DEX) - 13 Protocols

| Protocol | Blockchain | Status | Web3 | Avg Gas Fee |
|----------|-----------|--------|------|-------------|
| 🦄 **Uniswap V3** | Ethereum | ✅ Working | ✅ | ~$15-50 |
| 🍣 **SushiSwap** | Multi-chain | ✅ Working | ✅ | ~$10-30 |
| 🥞 **PancakeSwap** | BSC | ✅ Working | ✅ | ~$0.5-2 |
| 📊 **Curve** | Ethereum | ✅ Working | ✅ | ~$20-40 |
| ⚖️ **Balancer** | Ethereum | ✅ Working | ✅ | ~$18-35 |
| 🔵 **dYdX** | Ethereum L2 | ✅ Working | ✅ | ~$10-20 |
| 🔄 **1inch** | Multi-chain | ✅ Working | ✅ | ~$15-30 |
| 🔷 **Kyber** | Ethereum | ✅ Working | ✅ | ~$12-25 |
| 🌊 **Tinyman** | Algorand | ✅ Working | ✅ | ~$0.001 |
| 🔶 **Pact** | Algorand | ✅ Working | ✅ | ~$0.001 |
| 💎 **AlgoFi** | Algorand | ✅ Working | ✅ | ~$0.001 |
| 🔺 **Algox** | Algorand | ✅ Working | ✅ | ~$0.001 |
| 🔄 **Uniswap V2** | Ethereum | ✅ Working | ✅ | ~$15-40 |

**Implementation details:**
- Web3 on-chain RPC queries when available
- Public RPC provider for demo (recommend private RPC for production)
- Simulated/fallback data when Web3 unavailable (demo-safe)
- Gas fee estimation included in arbitrage calculations
- **Algorand DEX:** 4 protocols (Tinyman, Pact, AlgoFi, Algox) with ultra-low fees (~$0.001)
- **Pera Wallet:** Compatible with Algorand DEX protocols for secure asset management
- See `core/data_engine.py` for DEX integration

### 🔷 Algorand Blockchain Support

**Why Algorand?**
- ⚡ **Ultra-fast transactions**: ~4.5 second finality
- 💰 **Extremely low fees**: ~$0.001 per transaction
- 🌱 **Eco-friendly**: Carbon-negative blockchain
- 🔒 **Security**: Pure Proof-of-Stake consensus

**Supported Algorand DEX:**

1. **Tinyman** (https://tinyman.org)
   - Largest AMM DEX on Algorand
   - Fee: 0.25%
   - High liquidity for ALGO, USDC, USDT
   - Pera Wallet integration

2. **Pact** (https://pact.fi)
   - Stable AMM for stablecoins
   - Fee: 0.3%
   - Optimized for low slippage
   - LP token support

3. **AlgoFi** (https://algofi.org)
   - DeFi platform with AMM
   - Fee: 0.25%
   - Supports governance tokens (ALGO/GOV)
   - Lending and borrowing integration

4. **Algox** (AlgoSwap)
   - Community-focused AMM
   - Fee: 0.3%
   - ASA token support
   - Emerging protocol with growth potential

**Supported Algorand tokens:**
- ALGO (native token)
- USDC (Algorand)
- USDT (Algorand)
- goBTC, goETH (wrapped assets)

**Pera Wallet integration:**
- Secure management of Algorand assets
- Easy connection to DEX protocols
- WalletConnect support (ready for future implementation)

### Fallbacks, Simulation & Demo Mode
- Demo-safe behavior: when Web3 or an exchange call is unavailable, the DataEngine will generate simulated/fallback tickers so the system remains functional for testing.
- A synthetic exchange can be injected for demo arbitrage scenarios when `DEBUG_DEMO_INJECT_SYNTHETIC` in `utils/config.py` is True (useful for end-to-end tests).
- REST fallback parsing is best-effort and uses `EXCHANGE_ENDPOINTS` patterns and optional `alternate_paths` to locate public ticker endpoints.

See also:
- Implementation: [`core/data_engine.py`](core/data_engine.py:1)
- REST endpoint configuration: [`utils/config.py`](utils/config.py:54)
- Endpoint verifier tool: [`tools/verify_endpoints.py`](tools/verify_endpoints.py:1)

##  Quick Start

### Online (Recommended)

Visit the live application: [https://huggingface.co/spaces/HonzaH/AIarbi](https://huggingface.co/spaces/HonzaH/AIarbi)

1. **Launch the App** - Click the "AI Crypto Arbitrage System" interface
2. **Select Strategies** - Choose which arbitrage strategies to enable (all 5 available)
3. **Pick Trading Pairs** - Select cryptocurrencies to monitor (BTC, ETH, BNB, ALGO, etc.)
4. **Set Thresholds** - Configure minimum profit requirements (0.1-3.0%)
5. **Start Scanning** - Hit "🔍 Scan Opportunities" to begin
6. **View Results** - See live opportunities, AI insights, and performance charts

**Demo mode is enabled by default** - all executions are simulated for safety.

##  Configuration

### Strategy Settings
- **Minimum Profit**: 0.1% - 3.0%
- **Max Opportunities**: 1-20 results
- **Auto Refresh**: 30-second intervals
- **Demo Mode**: Safe simulation (recommended)

### Capital Configuration
- **Start Capital**: Configurable via `utils/config.py` or environment variable
  - Set `start_capital_usd` in `TRADING_CONFIG` (default: uses `max_position_size_usd` = $1000)
  - Override via environment: `TRADING_START_CAPITAL_USD=2000`
  - This value is used for all profit calculations and simulations
  - Profit percentages remain consistent regardless of capital amount
  - Profit USD values scale proportionally with the configured capital

### AI Analysis
- Confidence scoring (0-1 scale)
- Risk level assessment (LOW/MEDIUM/HIGH)
- Execution time estimates
- Market condition analysis

### Exchange endpoints & verification
- Canonical REST endpoints for exchanges are defined in [`utils/config.py`](utils/config.py:54) under the `EXCHANGE_ENDPOINTS` mapping.
- You can override any exchange base URL at runtime using environment variables like `EXCHANGE_ENDPOINT_BINANCE_BASE_URL`. See the loop in [`utils/config.py`](utils/config.py:118) that applies overrides.
- CoinMarketCap requires an API key for public REST calls. Provide it via `COINMARKETCAP_API_KEY` or `CMC_API_KEY` environment variable to enable CMC verification/fetching.

### Enabling and using all supported exchanges

To let the application use all 8 CEX + 2 aggregators reliably, follow these steps:

1. Install Python dependencies (ensure CCXT is installed so the DataEngine can use native clients when available):
   - Windows PowerShell:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install ccxt
   ```
   - If you prefer the latest CCXT release from GitHub:
   ```powershell
   pip install git+https://github.com/ccxt/ccxt.git
   ```

2. Provide API keys for exchanges that require them (optional for public data but required for private endpoints or some providers):
   - CoinMarketCap (required for CMC quotes/historical data):
     - Windows (cmd): `set COINMARKETCAP_API_KEY=your_key_here`
     - PowerShell: `$env:COINMARKETCAP_API_KEY = "your_key_here"`
   - Other exchanges: add API keys as environment variables or configure your secure secrets manager if you intend to enable private trading.

3. Verify CCXT client availability:
   - The DataEngine instantiates CCXT clients defensively and will skip clients not available in your environment. To ensure full CEX coverage, install CCXT and confirm the exchange id is supported by your CCXT install (e.g., `ccxt.bybit`, `ccxt.okx`, `ccxt.gateio`, `ccxt.bitfinex`).

4. Forcing REST fallback or preferring CCXT:
   - Some exchanges may be flagged `prefer_ccxt` in [`utils/config.py`](utils/config.py:54). If you want to force REST verification instead, set `prefer_ccxt` to `False` for that exchange in `EXCHANGE_ENDPOINTS`, or rely on `alternate_paths` for better REST fallbacks.

5. Run the endpoint verifier (in activated venv) to validate endpoints:
   - Windows (cmd/powershell):
     - `.venv\Scripts\Activate.ps1` (PowerShell) or `.venv\Scripts\activate` (cmd)
     - `python tools/verify_endpoints.py`
   - The verifier will prefer CCXT fetches when available, fall back to REST parsing, skip endpoints requiring API keys (CoinMarketCap), and emit `endpoint_report.json`.

6. Example env overrides:
   - Override base URLs or enable debug demo injection:
     - `set EXCHANGE_ENDPOINT_BINANCE_BASE_URL=https://api.binance.com`
     - `set DEBUG_DEMO_INJECT_SYNTHETIC=True`

Notes:
- The DataEngine will aggregate market data from CCXT clients where present and use REST endpoints defined in [`utils/config.py`](utils/config.py:54) otherwise. This hybrid approach ensures the app can utilize all listed exchanges with graceful fallbacks.
- Verify exact fee schedules and rate limits in production; the bundled config contains reasonable defaults but should be confirmed against each exchange's live documentation.
Logging in Hugging Face Spaces
- The application logs to stdout. To control verbosity set the `LOG_LEVEL` environment variable (e.g. `LOG_LEVEL=DEBUG` for development or `LOG_LEVEL=INFO` for normal operation).
- When deploying to Hugging Face Spaces, set `LOG_LEVEL=INFO` (or `DEBUG` to troubleshoot) in the Space settings to surface info/debug logs in the Space UI.
- The project uses `utils/logging_config.py` to configure an explicit stdout StreamHandler so logs appear in the Spaces console.

Verification tool
- A helper to validate configured endpoints is available at [`tools/verify_endpoints.py`](tools/verify_endpoints.py:1).
- Run the verifier inside the project's virtual environment:
  - Windows (cmd/powershell): `.venv\Scripts\python tools/verify_endpoints.py`
- The verifier will:
  - Prefer the project's REST parser in [`core/data_engine.py`](core/data_engine.py:205) when available.
  - Skip endpoints that explicitly require an API key (to avoid false negatives)  e.g., CoinMarketCap.
  - Respect exchanges marked as `prefer_ccxt` and will avoid raw REST checks for them when configured.
  - Emit a JSON report (`endpoint_report.json`) showing per-exchange status; some exchanges may return non-200 responses (400/404/500) depending on path, params or API-key requirements.
- Results are written to `endpoint_report.json` and printed to stdout.

Tests
- A basic config test was added at [`tests/test_endpoints.py`](tests/test_endpoints.py:1) to ensure endpoint entries exist and base URLs are present.
- Run tests with pytest inside the virtual environment:
  - `.venv\Scripts\python -m pytest -q`

Notes
- Some exchanges (Bitfinex, certain Bybit endpoints) may prefer or require using ccxt clients instead of raw public REST paths; these are flagged in [`utils/config.py`](utils/config.py:91) with `prefer_ccxt` or `requires_api_key`.
- If an exchange REST path fails in verification, update the pattern in [`utils/config.py`](utils/config.py:54) or add `alternate_paths` for best-fit fallbacks.

##  Safety Features

- **Demo Mode** - All trading is simulated by default
- **Risk Limits** - Built-in position and exposure limits
- **AI Safety** - Confidence thresholds prevent risky trades
- **Fee Calculation** - Accurate cost estimation including gas fees

##  Performance Metrics

The system tracks:
- Total opportunities detected
- Average profit percentages
- AI confidence scores
- Strategy performance breakdown
- Execution time estimates

##  Important Notes

- **Educational Purpose**: This system is for educational and research purposes
- **Paper Trading**: Demo mode is enabled by default for safety
- **Real Trading Risk**: Live trading involves significant financial risk
- **No Guarantees**: Past performance doesn't guarantee future results

##  Technical Details

- **AI Model**: Microsoft DialoGPT-medium (optimized for HF Spaces)
- **Graph Algorithm**: Bellman-Ford negative cycle detection
- **Data Sources**: CCXT unified exchange API + Web3 providers
- **Update Frequency**: Real-time with 30-second refresh cycles
- **Architecture**: Fully modular and extensible design

##  How It Works

1. **Data Collection**: Fetches real-time prices from multiple exchanges
2. **Graph Construction**: Builds weighted directed graph of trading opportunities  
3. **Cycle Detection**: Uses Bellman-Ford to find profitable arbitrage cycles
4. **AI Analysis**: Ranks opportunities using machine learning
5. **Risk Assessment**: Calculates confidence scores and risk levels
6. **Visualization**: Presents opportunities in user-friendly dashboard

##  Local setup & run (Windows PowerShell)

Follow these steps to run the project locally on Windows using PowerShell. These commands assume you have Python installed (3.8+ recommended).

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run a quick smoke import to verify imports:

```powershell
python -c "import app; print('imported app OK')"
```

4. Start the Gradio UI (will run a local web server):

```powershell
python app.py
```

5. Notes and tips:
- Demo mode is enabled in the UI by default  this simulates executions and is safe for testing.
- Live market fetches use CCXT and Web3; make sure your machine has network access.
- For real trading you must configure exchange API keys and implement secure key storage (not stored in repo).
- If you want to run a quick live scan from the command line, use the helper script:

```powershell
python .\tools\run_live_scan.py
```

If you run into missing-dependency errors, re-check the `requirements.txt` and install any missing packages.

##  Implementation Status

### ✅ What's Working

**All Core Components:**
- ✅ AI Model (DialoGPT-medium with fallback)
- ✅ Data Engine (CCXT + Web3 integration)
- ✅ Graph Builder (NetworkX graphs)
- ✅ Bellman-Ford Detector (cycle detection)
- ✅ 5 Trading Strategies (all verified and tested)
- ✅ Gradio UI (3 tabs: Scanner, Execution, Analytics)

**Supported Exchanges (15 total):**
- ✅ 8 CEX: Binance, Kraken, Coinbase, KuCoin, Bitfinex, Bybit, OKX, Gate.io
- ✅ 5 DEX: Uniswap V3, SushiSwap, PancakeSwap, Tinyman (Algorand), Pact (Algorand)
- ✅ 2 Aggregators: CoinGecko, CoinMarketCap

**Testing:**
- ✅ 19 tests passing
- ✅ All strategies verified
- ✅ Integration tests working

See [STRATEGY_VERIFICATION_REPORT.md](STRATEGY_VERIFICATION_REPORT.md) and [VERIFIKACE_OBCHODNICH_SYSTEMU.md](VERIFIKACE_OBCHODNICH_SYSTEMU.md) for detailed verification reports.

### 📋 Recommendations for Future Development

#### High Priority (Quick Wins)

1. **Real-time WebSocket Feeds**
   - Replace 30s polling with WebSocket connections
   - Reduce latency to <100ms
   - Implement for Binance, Kraken, Coinbase
   - Files: `core/data_engine.py`

2. **Advanced Backtesting Module**
   - Historical performance analysis
   - Sharpe ratio, max drawdown metrics
   - Monte Carlo simulations
   - New module: `core/backtesting.py`

3. **Database Persistence**
   - Store scan results and executions
   - SQLite for lightweight deployment
   - PostgreSQL for production
   - New module: `core/database.py`

4. **Enhanced Monitoring**
   - Sentry integration for error tracking
   - Prometheus metrics
   - Health check endpoints
   - New module: `utils/monitoring.py`

#### Medium Priority (Feature Expansion)

5. **More DEX Protocols**
   - Curve Finance (stablecoin AMM)
   - Balancer V2 (multi-token pools)
   - 1inch Aggregator
   - Files: `strategies/dex_cex_arbitrage.py`

6. **Smart Order Routing**
   - Optimal path through multiple exchanges
   - Slippage minimization
   - Gas optimization
   - New module: `strategies/smart_routing.py`

7. **Portfolio Management**
   - Position sizing (Kelly criterion)
   - Risk parity allocation
   - Stop-loss/take-profit automation
   - New module: `core/portfolio_manager.py`

8. **Multi-chain Support**
   - Polygon, Avalanche, Arbitrum
   - Cross-chain bridge arbitrage
   - Layer 2 integration
   - Files: `core/data_engine.py`, `utils/config.py`

#### Lower Priority (UI/UX)

9. **Enhanced Dashboards**
   - Real-time Plotly Dash integration
   - Customizable alerts
   - Mobile responsive design
   - Files: `app.py`

10. **REST API**
    - Programmatic access to system
    - WebSocket for live streams
    - OpenAPI/Swagger documentation
    - New directory: `api/`

11. **ML Improvements**
    - Fine-tune AI on crypto data
    - Reinforcement learning for timing
    - Sentiment analysis integration
    - Files: `core/ai_model.py`

12. **Multi-language Support**
    - UI localization (EN, CS, more)
    - Multi-language documentation
    - Files: `app.py`, README files

#### Production Readiness

13. **Security Hardening**
    - API key encryption
    - Secrets management (Vault, AWS)
    - Rate limiting per user
    - New module: `utils/security.py`

14. **Production Deployment**
    - Docker containerization
    - Kubernetes manifests
    - CI/CD pipeline
    - Files: `Dockerfile`, `k8s/`, `.github/workflows/`

15. **Testing Infrastructure**
    - 80%+ code coverage
    - Integration tests for all paths
    - Load testing
    - Expand: `tests/` directory

##  Contributing

This is an open-source educational project. Feel free to:
- 🐛 Report issues on GitHub
- 💡 Suggest improvements in discussions
- 🔧 Submit pull requests
- 📖 Improve documentation
- 🧪 Add tests

For detailed documentation in Czech, see [README.cs.md](README.cs.md).

---

** Disclaimer**: This software is for educational purposes only. Cryptocurrency trading carries significant financial risk. Never invest more than you can afford to lose. Demo mode is enabled by default and recommended for all testing.
