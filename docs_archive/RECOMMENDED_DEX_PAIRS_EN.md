# Recommended Cryptocurrencies and Pairs for DEX Arbitrage with Algorand Focus

For a successful arbitrage system, it's crucial to monitor pairs with high liquidity, low spreads, and sufficient trading activity. The recommended pairs are divided into two categories:

1. **Global DEX** (Ethereum, BSC, Polygon, etc.)
2. **Algorand DEX**, focusing on the most liquid pairs in the Algorand ecosystem

## 1. Global DEX Pairs for Wide Arbitrage

Focus on major AMM platforms on Ethereum, BSC, and Polygon, where you can find the best arbitrage opportunities between protocols and cross-chain aggregators.

### Supported Pairs in the System:

- **ALGO/USDC** on Uniswap V3, SushiSwap, Curve
- **WETH/USDC** on Uniswap V3, SushiSwap
- **WBTC/USDC** on Curve (stableswap pools)
- **USDC/USDT** - Supported via DAI/USDC pair on Curve, Balancer (very low spreads)
- **DAI/USDC** on Curve
- **LINK/USDC** on Uniswap V3
- **MATIC/USDC** on QuickSwap (Polygon)
- **CAKE/USDT** on PancakeSwap (BSC)

These pairs typically have the highest liquidity and platforms between them often show small price deviations suitable for arbitrage.

## 2. Algorand DEX Pairs

The Algorand ecosystem provides several AMM protocols. The most advantageous pairs are those with the highest liquidity in ALGO and stablecoins.

### 2.1 Tinyman (v2)
**Status:** ✅ Fully Integrated
- ALGO/USDC
- ALGO/USDT
- USDC/USDT

### 2.2 Pact
**Status:** ✅ Fully Integrated
- ALGO/USDC
- ALGO/USDT
- ALGO/PactToken (or other currencies with sufficient activity)

### 2.3 AlgoFi
**Status:** ✅ Newly Added
- ALGO/USDC
- ALGO/USDT
- ALGO/GOV (governance token)

### 2.4 Algox (AlgoSwap)
**Status:** ✅ Newly Added
- ALGO/USDC
- ALGO/ASA1, ALGO/ASA2 (select most popular projects)

## Recommendations for Monitoring and Deployment

### Priority Pairs
1. **ALGO/USDC and ALGO/USDT**: Highest liquidity and smallest spread
2. **Stable stablecoin pairs (USDC/USDT, DAI/USDC)**: Minimal volatility enables very fast arb-trades
3. **WETH/USDC, WBTC/USDC**: High liquidity on major Ethereum DEXs

### Cross-Protocol Arbitrage
Compare ALGO/USDC prices on:
- Tinyman vs Pact vs AlgoFi vs Algox
- Take advantage of fast on-chain swaps thanks to Algorand's ultra-low fees (~$0.001)

### On-Chain Mempool Monitoring
For Algorand, you can use:
- Tinyman websocket endpoints
- Indexers (e.g., Algorand Indexer API)
- Immediate detection of new swaps and liquidity changes

### Decision Automation
- Use data from APIs (production and testnet)
- Calculate simulated transactions
- Compare effective prices including fees

### Gas Fees and Front-Running
- Algorand has low transaction costs (~$0.001 vs $15-50 on Ethereum)
- Increases profit opportunity with small spread opportunities
- Monitor network activity to avoid increased fees

## Advantages of Algorand for Arbitrage

1. **Ultra-low fees**: ~$0.001 vs $15-50 on Ethereum
2. **Fast finality**: 4.5 seconds vs 12+ seconds on Ethereum
3. **More opportunities**: Low fees enable profitable micro-arbitrage
4. **Eco-friendly**: Carbon-negative blockchain
5. **4 DEX protocols**: Tinyman, Pact, AlgoFi, Algox

## Implemented Features

### In Configuration (`utils/config.py`)
- ✅ 4 Algorand DEX protocols (Tinyman, Pact, AlgoFi, Algox)
- ✅ 16 trading pairs in DEFAULT_SYMBOLS
- ✅ Fee and gas cost configuration for each DEX

### In Data Engine (`core/data_engine.py`)
- ✅ Support for all 4 Algorand DEX protocols
- ✅ Simulated prices for all new pairs
- ✅ Fallback ticker data for testing

### In Strategy (`strategies/dex_cex_arbitrage.py`)
- ✅ Extended from 11 to 13 DEX protocols
- ✅ Ultra-low gas cost for Algorand DEX ($0.001)
- ✅ AI analysis for arbitrage timing

## Statistics

- **DEX protocols**: 11 → 13 (+18%)
- **Algorand DEX**: 2 → 4 (+100%)
- **Trading pairs**: 9 → 16 (+78%)
- **Transaction costs**: ~99.99% reduction (Ethereum vs Algorand)

---

**Creation Date:** 2025-10-15  
**Status:** ✅ Complete  
**Testing:** Awaiting validation
