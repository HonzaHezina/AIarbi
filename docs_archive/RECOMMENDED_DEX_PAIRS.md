# Doporučené kryptoměny a páry pro arbitráž na DEX s důrazem na Algorand

Pro úspěšný arbitrážní systém je klíčové sledovat páry s vysokou likviditou, nízkými spready a dostatečnou obchodní aktivitou. Níže jsou rozděleny doporučené páry do dvou kategorií:

1. **Celosvětové DEX** (Ethereum, BSC, Polygon apod.)
2. **Algorand DEX**, kde se zaměříte na nejlikvidnější páry v ekosystému Algorandu

## 1. Globální DEX páry pro širokou arbitráž

Zaměřte se na hlavní AMM platformy na Ethereum, BSC a Polygon, kde lze najít nejlepší příležitosti k arbitráži mezi protokoly i tzv. cross-chain agregátory.

### Podporované páry v systému:

- **ALGO/USDC** na Uniswap V3, SushiSwap, Curve
- **WETH/USDC** na Uniswap V3, SushiSwap
- **WBTC/USDC** na Curve (stableswap pooly)
- **USDC/USDT** - Podporováno přes DAI/USDC pair na Curve, Balancer (velmi nízké spready)
- **DAI/USDC** na Curve
- **LINK/USDC** na Uniswap V3
- **MATIC/USDC** na QuickSwap (Polygon)
- **CAKE/USDT** na PancakeSwap (BSC)

Tyto páry mají obvykle nejvyšší likviditu a platformy mezi nimi vykazují často drobné cenové odchilky vhodné pro arbitráž.

## 2. Algorand DEX páry

Ekosystém Algorand poskytuje několik AMM protokolů. Nejvýhodnější páry jsou ty s nejvyšší likviditou v ALGO a stablecoinech.

### 2.1 Tinyman (v2)
**Status:** ✅ Plně integrováno
- ALGO/USDC
- ALGO/USDT
- USDC/USDT

### 2.2 Pact
**Status:** ✅ Plně integrováno
- ALGO/USDC
- ALGO/USDT
- ALGO/PactToken (nebo jiné měny s dostatečnou aktivitou)

### 2.3 AlgoFi
**Status:** ✅ Nově přidáno
- ALGO/USDC
- ALGO/USDT
- ALGO/GOV (governance token)

### 2.4 Algox (AlgoSwap)
**Status:** ✅ Nově přidáno
- ALGO/USDC
- ALGO/ASA1, ALGO/ASA2 (vybírat nejpopulárnější projekty)

## Doporučení pro sledování a nasazení

### Priorita pár
1. **ALGO/USDC a ALGO/USDT**: Nejvyšší likvidita a nejmenší spread
2. **Stabilní stablecoin páry (USDC/USDT, DAI/USDC)**: Minimální volatilita umožňuje velmi rychlé arb-trades
3. **WETH/USDC, WBTC/USDC**: Vysoká likvidita na hlavních Ethereum DEX

### Cross-protocol arbitrage
Srovnávejte ceny ALGO/USDC na:
- Tinyman vs Pact vs AlgoFi vs Algox
- Využívejte rychlých on-chain swapů díky ultra-nízkým poplatkům Algorandu (~$0.001)

### Sledování on-chain mempoolu
Pro Algorand lze využít:
- Websocket endpointy Tinyman
- Indexery (např. Algorand Indexer API)
- Okamžité zjištění nových swapů a likviditních změn

### Automatizace rozhodování
- Využití dat z API (produkční i testnet)
- Kalkulace simulovaných transakcí
- Srovnání efektivních cen včetně poplatků

### Gas poplatky a front-running
- Algorand má nízké transakční náklady (~$0.001 vs $15-50 na Ethereum)
- Zvyšuje šanci na profit při malých spreadových příležitostech
- Sledování síťové aktivity pro předejití zvýšeným poplatkům

## Výhody Algorandu pro arbitráž

1. **Ultra-nízké poplatky**: ~$0.001 vs $15-50 na Ethereum
2. **Rychlá finalita**: 4.5 sekundy vs 12+ sekund na Ethereum
3. **Více příležitostí**: Nízké poplatky umožňují profitabilní mikro-arbitráž
4. **Ekologičnost**: Carbon-negative blockchain
5. **4 DEX protokoly**: Tinyman, Pact, AlgoFi, Algox

## Implementované funkce

### V konfiguraci (`utils/config.py`)
- ✅ 4 Algorand DEX protokoly (Tinyman, Pact, AlgoFi, Algox)
- ✅ 16 trading párů v DEFAULT_SYMBOLS
- ✅ Konfigurace poplatků a gas cost pro každý DEX

### V Data Engine (`core/data_engine.py`)
- ✅ Podpora všech 4 Algorand DEX protokolů
- ✅ Simulované ceny pro všechny nové páry
- ✅ Fallback ticker data pro testování

### Ve strategii (`strategies/dex_cex_arbitrage.py`)
- ✅ Rozšířeno z 11 na 13 DEX protokolů
- ✅ Ultra-nízké gas cost pro Algorand DEX ($0.001)
- ✅ AI analýza pro timing arbitráže

## Statistiky

- **DEX protokoly**: 11 → 13 (+18%)
- **Algorand DEX**: 2 → 4 (+100%)
- **Trading páry**: 9 → 16 (+78%)
- **Transakční náklady**: ~99.99% redukce (Ethereum vs Algorand)

---

**Datum vytvoření:** 2025-10-15  
**Status:** ✅ Kompletní  
**Testování:** Čeká na validaci
