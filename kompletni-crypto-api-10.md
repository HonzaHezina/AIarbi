# Kompletní specifikace API endpointů pro 10 kryptoměnových zdrojů

## 🔥 AKTUALIZOVANÝ SEZNAM - 8 BURZ + 2 AGREGÁTORY

---

## 1. BINANCE 🥇

### Základní informace
- **Base URL**: `https://api.binance.com`
- **Public URL**: `https://data-api.binance.vision` (pouze veřejná data)
- **Dokumentace**: https://binance-docs.github.io/apidocs/spot/en/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 1200 požadavků/min
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# Cena konkrétního páru
GET https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT

# Všechny ceny
GET https://api.binance.com/api/v3/ticker/price

# 24h ticker statistiky
GET https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT

# Informace o burze
GET https://api.binance.com/api/v3/exchangeInfo
```

---

## 2. COINBASE 🔶

### Základní informace
- **Base URL**: `https://api.coinbase.com` (Consumer API)
- **Exchange URL**: `https://api.exchange.coinbase.com` (Pro API)
- **Dokumentace**: https://docs.cdp.coinbase.com/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 10 req/s (veřejné), 5 req/s (privátní)
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# Spot cena
GET https://api.coinbase.com/v2/prices/BTC-USD/spot

# Exchange ticker
GET https://api.exchange.coinbase.com/products/BTC-USD/ticker

# Všechny produkty
GET https://api.exchange.coinbase.com/products
```

---

## 3. KRAKEN 🐙

### Základní informace
- **Base URL**: `https://api.kraken.com`
- **Dokumentace**: https://docs.kraken.com/rest/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 1 požadavek/s (veřejné)
- **Headers**: `User-Agent: YourApp/1.0`

### Klíčové Endpointy
```http
# Ticker data
GET https://api.kraken.com/0/public/Ticker?pair=XBTUSD

# Asset pairs
GET https://api.kraken.com/0/public/AssetPairs

# System status
GET https://api.kraken.com/0/public/SystemStatus
```

---

## 4. KUCOIN 🟢

### Základní informace
- **Base URL**: `https://api.kucoin.com`
- **Dokumentace**: https://docs.kucoin.com/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 120/min (veřejné), 600/min (privátní)
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# Single ticker
GET https://api.kucoin.com/api/v1/market/orderbook/level1?symbol=BTC-USDT

# All tickers
GET https://api.kucoin.com/api/v1/market/allTickers

# Available symbols
GET https://api.kucoin.com/api/v1/symbols
```

---

## 5. BYBIT 🟣

### Základní informace
- **Base URL**: `https://api.bybit.com`
- **Dokumentace**: https://bybit-exchange.github.io/docs/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 120 req/min (veřejné)
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# V5 API - Spot tickers
GET https://api.bybit.com/v5/market/tickers?category=spot&symbol=BTCUSDT

# V5 API - All spot tickers
GET https://api.bybit.com/v5/market/tickers?category=spot

# V2 API (legacy)
GET https://api.bybit.com/v2/public/tickers
```

---

## 6. OKX 🟡

### Základní informace
- **Base URL**: `https://www.okx.com`
- **Dokumentace**: https://www.okx.com/docs-v5/en/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 20 req/2s (veřejné)
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# Single instrument ticker
GET https://www.okx.com/api/v5/market/ticker?instId=BTC-USDT

# All spot tickers
GET https://www.okx.com/api/v5/market/tickers?instType=SPOT

# Available instruments
GET https://www.okx.com/api/v5/public/instruments?instType=SPOT
```

---

## 7. BITFINEX 🟢

### Základní informace
- **Base URL**: `https://api-pub.bitfinex.com`
- **Dokumentace**: https://docs.bitfinex.com/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 90 req/min (veřejné)
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# Single ticker
GET https://api-pub.bitfinex.com/v2/ticker/tBTCUSD

# Multiple tickers
GET https://api-pub.bitfinex.com/v2/tickers?symbols=tBTCUSD,tETHUSD

# All tickers
GET https://api-pub.bitfinex.com/v2/tickers?symbols=ALL
```

---

## 8. GATE.IO 🔵

### Základní informace
- **Base URL**: `https://api.gateio.ws`
- **Dokumentace**: https://www.gate.com/docs/developers/apiv4/en/
- **Autentifikace**: Nepotřeba pro veřejné endpointy
- **Rate limit**: 900 req/s (spot veřejné)
- **Headers**: `Content-Type: application/json`

### Klíčové Endpointy
```http
# Single ticker
GET https://api.gateio.ws/api/v4/spot/tickers?currency_pair=BTC_USDT

# All tickers
GET https://api.gateio.ws/api/v4/spot/tickers

# Currency pairs
GET https://api.gateio.ws/api/v4/spot/currency_pairs
```

---

# 🌟 BONUS: AGREGÁTORY KRYPTODAT

## 9. COINGECKO 🦎 **[NOVĚ PŘIDÁNO]**

### Základní informace
- **Base URL**: `https://api.coingecko.com/api/v3`
- **Dokumentace**: https://docs.coingecko.com
- **Autentifikace**: **100% ZDARMA** - nepotřeba API klíč
- **Pokrytí**: **7000+ kryptoměn, 400+ burz**
- **Rate limit**: 
  - **Free (bez účtu)**: 5-15 calls/min (nestabilní)
  - **Demo (s účtem)**: 30 calls/min, 10,000/měsíc
  - **Paid plans**: 500-1000 calls/min
- **Headers**: Žádné speciální

### Klíčové Endpointy
```http
# Simple price (nejpopulárnější endpoint)
GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd

# Coins list (mapování symbolů na IDs)
GET https://api.coingecko.com/api/v3/coins/list

# Market data (top kryptoměny s detaily)
GET https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1

# Single coin detail
GET https://api.coingecko.com/api/v3/coins/bitcoin

# Global stats
GET https://api.coingecko.com/api/v3/global

# Trending coins
GET https://api.coingecko.com/api/v3/search/trending
```

### Response formáty
```json
// Simple Price Response
{
  "bitcoin": {"usd": 43500},
  "ethereum": {"usd": 2800}
}

// Coins Markets Response
[
  {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 43500,
    "market_cap": 850000000000,
    "total_volume": 15000000000
  }
]
```

### AI Prompt pro CoinGecko:
```
Vytvoř CoinGecko API wrapper v Pythonu:
- Base URL: https://api.coingecko.com/api/v3
- Nejdůležitější endpoint: /simple/price?ids=bitcoin,ethereum&vs_currencies=usd
- ZDARMA - žádná autentifikace
- Rate limit 30 calls/min (s Demo účtem)
- Používá coin IDs (bitcoin, ethereum) místo symbolů (BTC, ETH)
- Nejdříve volej /coins/list pro mapování symbolů -> IDs
- Response: {"bitcoin":{"usd":43500},"ethereum":{"usd":2800}}
- Implementuj caching kvůli rate limitu
- Přidej retry logic s exponential backoff
```

---

## 10. COINMARKETCAP 💰 **[NOVĚ PŘIDÁNO]**

### Základní informace
- **Base URL**: `https://pro-api.coinmarketcap.com/v1`
- **Dokumentace**: https://coinmarketcap.com/api/documentation/v1/
- **Autentifikace**: **VYŽADUJE API KLÍČ** (i pro free plán)
- **Pokrytí**: **Komplexní tržní data od 2013, až 5 let historie**
- **Rate limit**: 
  - **Basic (Free)**: 30 req/min, 10,000 credits/měsíc
  - **Hobbyist**: $29/měsíc, 60 req/min, 200,000 credits/měsíc
  - **Startup**: $79/měsíc, 90 req/min, 500,000 credits/měsíc
  - **Professional**: 120+ req/min
- **Headers**: `X-CMC_PRO_API_KEY: YOUR_API_KEY`

### Klíčové Endpointy
```http
# Latest cryptocurrency listings
GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?start=1&limit=100&convert=USD

# Latest quotes pro konkrétní kryptoměny
GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC,ETH&convert=USD

# Crypto info/metadata
GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?symbol=BTC

# Global market metrics
GET https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest

# Map (ID mapping)
GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/map

# Historical data (OHLCV) - jen paid plans
GET https://pro-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical?symbol=BTC&time_start=2024-01-01&time_end=2024-12-31
```

### Response formáty
```json
// Latest Listings Response
{
  "status": {
    "timestamp": "2025-01-01T12:00:00.000Z",
    "error_code": 0,
    "credit_count": 1
  },
  "data": [
    {
      "id": 1,
      "name": "Bitcoin",
      "symbol": "BTC",
      "quote": {
        "USD": {
          "price": 43500,
          "volume_24h": 15000000000,
          "market_cap": 850000000000,
          "percent_change_24h": 2.5
        }
      }
    }
  ]
}
```

### AI Prompt pro CoinMarketCap:
```
Vytvoř CoinMarketCap API klient:
- Base URL: https://pro-api.coinmarketcap.com/v1
- POVINNÝ header: X-CMC_PRO_API_KEY: YOUR_API_KEY
- Hlavní endpoint: /cryptocurrency/listings/latest?start=1&limit=100&convert=USD
- Single quotes: /cryptocurrency/quotes/latest?symbol=BTC,ETH&convert=USD
- Vždy kontroluj status.error_code (0 = OK)
- Credit system: 1 credit = ~100 data points
- Rate limit podle plánu: Basic 30 req/min, Hobbyist 60 req/min
- Response má vždy status object s credit_count
- Free plán: pouze latest market data, BEZ historických dat
- Implementuj credit tracking a warning při 95% využití
```

---

# 📊 POROVNÁNÍ VŠECH 10 ZDROJŮ

| Zdroj | Typ | Autentifikace | Rate Limit | Pokrytí | Cena |
|-------|-----|---------------|------------|---------|------|
| **Binance** | Burza | Ne | 1200/min | Binance páry | Zdarma |
| **Coinbase** | Burza | Ne | 10 req/s | Coinbase páry | Zdarma |
| **Kraken** | Burza | Ne | 1 req/s | Kraken páry | Zdarma |
| **KuCoin** | Burza | Ne | 120/min | KuCoin páry | Zdarma |
| **Bybit** | Burza | Ne | 120/min | Bybit páry | Zdarma |
| **OKX** | Burza | Ne | 20 req/2s | OKX páry | Zdarma |
| **Bitfinex** | Burza | Ne | 90/min | Bitfinex páry | Zdarma |
| **Gate.io** | Burza | Ne | 900 req/s | Gate.io páry | Zdarma |
| **CoinGecko** | Agregátor | Ne | 30/min | 7000+ coinů | Zdarma |
| **CoinMarketCap** | Agregátor | Ano | 30/min | Všechny coiny | Free + Paid |

## 🎯 DOPORUČENÉ POUŽITÍ

### **Pro rychlé testování:**
1. **CoinGecko** - 100% zdarma, žádná registrace
2. **Binance** - nejrychlejší rate limit (1200/min)
3. **Gate.io** - extrémně rychlé (900 req/s)

### **Pro produkční použití:**
1. **CoinMarketCap** - nejkompletnější data, profesionální API
2. **Binance** - nejvíce likvidní trh
3. **CoinGecko** - nejširší pokrytí (7000+ coinů)

### **Pro arbitrážní obchodování:**
1. **Kombinace všech 8 burz** pro price comparison
2. **CoinGecko** pro discovery nových coinů
3. **CoinMarketCap** pro historická data

## 🚀 UNIVERZÁLNÍ AI PROMPT PRO VŠECH 10

```
Vytvoř UniversalCryptoAPI wrapper který:
1. Kombinuje všech 10 zdrojů (8 burz + 2 agregátory)
2. Automaticky vybere nejlepší zdroj podle požadavku
3. Implementuje fallback mezi zdroji
4. Standardizuje response format pro všechny
5. Mapuje různé symbol formáty (BTCUSDT, BTC-USD, tBTCUSD, BTC_USDT)
6. Respektuje rate limity každého zdroje
7. Poskytuje price comparison napříč burzami
8. Vrací unified response:
{
  "symbol": "BTC/USDT",
  "price": 43500.00,
  "source": "binance",
  "timestamp": 1672531200,
  "alternatives": [
    {"exchange": "coinbase", "price": 43505.00},
    {"exchange": "kraken", "price": 43498.00}
  ]
}

Priorita zdrojů:
1. Burzy pro real-time ceny
2. CoinGecko pro široké pokrytí
3. CoinMarketCap pro historická data
```

Tato specifikace ti poskytuje **kompletní přehled všech 10 hlavních kryptoměnových API** s přesnými endpointy, rate limity a AI prompty pro rychlé programování! 🎯