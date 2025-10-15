# DEX API Endpoints Documentation

This document provides detailed information about the 8 decentralized exchange (DEX) API endpoints integrated into the arbitrage system.

## Overview

The system now supports 8 major DEX protocols with both production and testnet endpoints:

1. **Uniswap** - Leading Ethereum DEX with deep liquidity
2. **SushiSwap** - Community-driven DEX with extensive features
3. **PancakeSwap** - Leading BSC DEX with low fees
4. **dYdX** - Perpetual futures DEX with advanced trading
5. **Curve** - Stablecoin-focused DEX with low slippage
6. **Balancer** - Multi-token pools with weighted indices
7. **1inch** - DEX aggregator for best prices
8. **Kyber** - Liquidity protocol with dynamic fees

## Configuration Details

### 1. Uniswap

| Property | Value |
|----------|-------|
| Production API | https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2 |
| Testnet API | https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2?network=kovan |
| API Type | GraphQL |
| Rate Limit | 10,000 requests/day |
| Authentication | None (read-only) |
| Network | Ethereum |
| Key Data | Token pairs, prices, liquidity |
| Documentation | https://docs.uniswap.org/sdk/subgraph/subgraph-data |

**Features:**
- Token pair discovery and price tracking
- Real-time liquidity monitoring
- Historical price data via GraphQL
- No authentication required for read operations

---

### 2. SushiSwap

| Property | Value |
|----------|-------|
| Production API | https://api.thegraph.com/subgraphs/name/sushiswap/exchange |
| Testnet API | https://api.thegraph.com/subgraphs/name/sushiswap/exchange?network=ropsten |
| API Type | GraphQL |
| Rate Limit | 8,000 requests/day |
| Authentication | None (read-only) |
| Network | Ethereum |
| Key Data | Volume, swaps, liquidity pools |
| Documentation | https://docs.sushi.com/docs/Developers/Subgraphs/Exchange |

**Features:**
- Volume tracking across pools
- Swap history and analytics
- Liquidity pool composition
- GraphQL query flexibility

---

### 3. PancakeSwap

| Property | Value |
|----------|-------|
| Production API | https://api.pancakeswap.info/api/v2/tokens |
| Testnet API | https://testnet-api.pancakeswap.finance/api/v2/tokens |
| API Type | REST + WebSocket |
| Rate Limit | 5,000 requests/hour |
| Authentication | None (read-only) |
| Network | Binance Smart Chain (BSC) |
| WebSocket | wss://bsc-ws-node.nariox.org:443 |
| Testnet WS | wss://data-seed-prebsc-1-s1.binance.org:8545 |
| Key Data | Prices, trading pairs, APY |
| Documentation | https://docs.pancakeswap.finance/developers/api |

**Features:**
- Low-cost BSC transactions
- REST API for token prices
- WebSocket for real-time updates
- APY tracking for yield farming

---

### 4. dYdX

| Property | Value |
|----------|-------|
| Production API | https://api.dydx.exchange/v3/markets |
| Testnet API | https://api.stage.dydx.exchange/v3/markets |
| API Type | REST + WebSocket |
| Rate Limit | 50 requests/second |
| Authentication | **API key + HMAC signing** |
| Network | Ethereum (Layer 2) |
| WebSocket | wss://api.dydx.exchange/v3/ws |
| Testnet WS | wss://api.stage.dydx.exchange/v3/ws |
| Key Data | Futures prices, orders, orderbook |
| Documentation | https://docs.dydx.exchange/ |

**Features:**
- Perpetual futures trading
- High-frequency trading support (50 req/s)
- Requires API key authentication
- HMAC signature for secure requests
- Layer 2 scaling for low gas costs

**Authentication Setup:**
```python
# Set environment variables for dYdX authentication
export DYDX_API_KEY="your_api_key"
export DYDX_API_SECRET="your_api_secret"
export DYDX_STARK_PRIVATE_KEY="your_stark_key"
```

---

### 5. Curve

| Property | Value |
|----------|-------|
| Production API | https://api.curve.finance/api/getPools |
| Testnet API | https://api.curve.fi/api/getPools?network=kovan |
| API Type | REST only |
| Rate Limit | 1,000 requests/minute |
| Authentication | None (read-only) |
| Network | Ethereum |
| Key Data | Pools, APY, token data |
| Documentation | https://curve.readthedocs.io/ |

**Features:**
- Stablecoin-focused pools
- Low slippage for large trades
- Complex pool composition data
- APY tracking for liquidity providers
- No WebSocket support (REST only)

---

### 6. Balancer

| Property | Value |
|----------|-------|
| Production API | https://api-v3.balancer.fi/graphql |
| Testnet API | https://api-v3.balancer.kovan.network/graphql |
| API Type | GraphQL |
| Rate Limit | 5,000 requests/day |
| Authentication | None (read-only) |
| Network | Ethereum |
| Key Data | Pools, prices, weighted indices |
| Documentation | https://docs.balancer.fi/ |

**Features:**
- Multi-token pools with custom weights
- Weighted index tracking
- Smart pool management
- GraphQL for flexible queries

---

### 7. 1inch

| Property | Value |
|----------|-------|
| Production API | https://api.1inch.io/v4.0/1/tokens |
| Testnet API | https://api.1inch.io/v4.0/1/tokens?network=ropsten |
| API Type | REST |
| Rate Limit | 1,000 requests/day |
| Authentication | None (read-only) |
| Network | Ethereum (multi-chain support) |
| Quote Endpoint | https://api.1inch.io/v4.0/1/quote |
| Key Data | Aggregated prices, volumes |
| Documentation | https://docs.1inch.io/ |

**Features:**
- DEX aggregator for best prices
- Multi-source price comparison
- Optimal routing algorithms
- Gas optimization

---

### 8. Kyber

| Property | Value |
|----------|-------|
| Production API | https://kyber.api.0x.org/swap/v1/quote |
| Testnet API | https://ropsten.api.0x.org/swap/v1/quote |
| API Type | REST |
| Rate Limit | 5,000 requests/day |
| Authentication | None (read-only) |
| Network | Ethereum |
| Key Data | Best swap price, liquidity |
| Documentation | https://docs.kyberswap.com/ |

**Features:**
- Dynamic fee model
- Best swap price calculation
- Liquidity aggregation
- Simple REST interface

---

## Implementation Notes

### Rate Limit Management

The system implements intelligent rate limiting to respect each DEX's limits:

```python
from utils.config import get_dex_rate_limit

# Get rate limit for a protocol
limit, period = get_dex_rate_limit('uniswap')
print(f"Uniswap limit: {limit} requests per {period}")
```

### Testnet Usage

Always verify addresses and network parameters when using testnets:

```python
from utils.config import get_dex_endpoint

# Get production endpoint
prod_config = get_dex_endpoint('uniswap', testnet=False)

# Get testnet endpoint
test_config = get_dex_endpoint('uniswap', testnet=True)
```

### WebSocket Streaming

For low-latency data (market depth, trades), use WebSocket connections:

- **PancakeSwap**: Real-time BSC price updates
- **dYdX**: Orderbook and trade streaming
- Others use GraphQL or REST polling

### Authentication Requirements

Only **dYdX** requires authentication:
- API key management
- HMAC signature generation
- StarkEx key for Layer 2 operations

All other DEXs are read-only without authentication.

### Data Focus for Arbitrage

The system focuses on:

1. **High Liquidity Pairs** - Better execution prices
2. **Low Spreads** - Reduced slippage costs
3. **Real-time Updates** - Fast opportunity detection
4. **Gas Cost Awareness** - Network-specific optimization

### Network-Specific Considerations

| Network | DEX Examples | Avg Gas Cost | Considerations |
|---------|--------------|--------------|----------------|
| Ethereum | Uniswap, SushiSwap, Curve | $15-20 | High gas, deep liquidity |
| BSC | PancakeSwap | $0.50 | Low gas, fast finality |
| Layer 2 | dYdX | $10 | Medium gas, high throughput |
| Algorand | Tinyman, Pact | $0.001 | Very low cost |

## Usage Examples

### Get All DEX Protocols

```python
from utils.config import get_supported_dex_protocols

protocols = get_supported_dex_protocols()
print(f"Supported DEX protocols: {protocols}")
```

### Get Specific DEX Configuration

```python
from utils.config import DEX_CONFIG, DEX_ENDPOINTS

# Get protocol config (fees, gas costs)
uniswap_config = DEX_CONFIG['uniswap']
print(f"Uniswap fee: {uniswap_config['fee'] * 100}%")

# Get endpoint config (URLs, rate limits)
uniswap_endpoint = DEX_ENDPOINTS['uniswap']
print(f"Production API: {uniswap_endpoint['base_url']}")
```

### Estimate Gas Costs

```python
from strategies.dex_cex_arbitrage import DEXCEXArbitrage

strategy = DEXCEXArbitrage(ai_model)
gas_cost = await strategy.estimate_dex_gas_cost('pancakeswap', 'BTC')
print(f"Estimated gas cost: ${gas_cost}")
```

## Testing

Run the DEX endpoint tests to verify configuration:

```bash
python -m pytest tests/test_dex_endpoints.py -v
```

Expected test results:
- ✅ All 8 DEX endpoints configured
- ✅ Required fields present
- ✅ Valid rate limits
- ✅ Proper authentication settings
- ✅ Network consistency

## Best Practices

1. **Cache Data**: Reduce API calls by caching recent prices
2. **Respect Rate Limits**: Implement exponential backoff
3. **Use Testnet First**: Validate logic before production
4. **Monitor Gas Costs**: Track network congestion
5. **Handle Errors Gracefully**: DEX APIs can be unreliable

## Future Enhancements

Planned improvements for DEX integration:

- [ ] WebSocket connection pooling
- [ ] Advanced GraphQL query optimization
- [ ] Multi-chain routing support
- [ ] Historical data analysis
- [ ] MEV protection strategies
- [ ] Gas price prediction

## Support

For issues or questions:
- Check the DEX-specific documentation links above
- Review test files in `tests/test_dex_endpoints.py`
- See configuration in `utils/config.py`

---

**Last Updated**: 2025-10-15
**Version**: 1.0
