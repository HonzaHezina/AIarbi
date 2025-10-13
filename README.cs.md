# 🤖 AI Crypto Arbitrage System

**Pokročilý multi-strategický systém pro detekci arbitrážních příležitostí v kryptoměnách**

🌐 **Živá aplikace**: [https://huggingface.co/spaces/HonzaH/AIarbi](https://huggingface.co/spaces/HonzaH/AIarbi)

---

## 📋 Obsah

- [O projektu](#o-projektu)
- [Co je implementováno](#co-je-implementováno)
- [Architektura](#architektura)
- [Rychlý start](#rychlý-start)
- [Obchodní strategie](#obchodní-strategie)
- [Podporované burzy](#podporované-burzy)
- [Konfigurace](#konfigurace)
- [Doporučení pro další rozvoj](#doporučení-pro-další-rozvoj)
- [Technické detaily](#technické-detaily)

---

## 🎯 O projektu

AI Crypto Arbitrage System je pokročilá aplikace pro analýzu a detekci arbitrážních příležitostí na kryptoměnových trzích. Systém kombinuje:

- 🧠 **AI analýzu** pomocí DialoGPT-medium modelu
- 📊 **Bellman-Ford algoritmus** pro detekci arbitrážních cyklů
- 🔄 **5 obchodních strategií** pro různé typy arbitráží
- 🌐 **Gradio UI** pro interaktivní ovládání
- 📈 **Real-time monitoring** cen z 13+ zdrojů

**⚠️ DŮLEŽITÉ**: Aplikace je primárně určena pro **vzdělávací účely**. Demo režim je zapnutý ve výchozím nastavení pro bezpečné testování bez rizika.

---

## ✅ Co je implementováno

### 🎯 Obchodní strategie (5/5 fungující)

1. ✅ **DEX/CEX Arbitrage** (`strategies/dex_cex_arbitrage.py`)
   - Využívá cenové rozdíly mezi DEX a CEX burzami
   - Podporuje Uniswap V3, SushiSwap, PancakeSwap vs Binance, Kraken, atd.
   - Zahrnuje výpočet gas fees

2. ✅ **Cross-Exchange Arbitrage** (`strategies/cross_exchange_arbitrage.py`)
   - Cenové rozdíly napříč centralizovanými burzami
   - Pracuje s 8 CEX burzami současně
   - Optimalizuje pro nejnižší transfer fees

3. ✅ **Triangular Arbitrage** (`strategies/triangular_arbitrage.py`)
   - Trojúhelníkové cykly v rámci jedné burzy
   - Příklad: BTC → ETH → USDT → BTC
   - Detekuje komplexní víceúrovňové cykly

4. ✅ **Wrapped Tokens Arbitrage** (`strategies/wrapped_tokens_arbitrage.py`)
   - Arbitráž mezi nativními a wrapped tokeny
   - Podporuje BTC/wBTC, ETH/wETH, BNB/wBNB
   - Zahrnuje wrap/unwrap náklady

5. ✅ **Statistical AI Arbitrage** (`strategies/statistical_arbitrage.py`)
   - AI-řízená detekce korelací a anomálií
   - Historická analýza 100+ datových bodů
   - Práh korelace 0.7, deviace 2.0 σ

### 🔧 Komponenty systému

#### AI Model (`core/ai_model.py`)
✅ **Implementováno:**
- Microsoft DialoGPT-medium model
- Automatické načítání a fallback na rule-based analýzu
- Optimalizováno pro Hugging Face Spaces (float16/float32)
- Analýza příležitostí a generování doporučení

#### Data Engine (`core/data_engine.py`)
✅ **Implementováno:**
- CCXT integrace pro 8 CEX burz
- Web3 podpora pro DEX protokoly
- REST API fallback mechanismus
- Rate limiting a error handling
- Simulovaná data pro demo režim

#### Graph Builder (`core/graph_builder.py`)
✅ **Implementováno:**
- NetworkX grafy pro reprezentaci trhů
- Automatické přidávání hran všech strategií
- Váhování hran podle logaritmických cen
- Metadata pro tracking strategií

#### Bellman-Ford Detector (`core/bellman_ford_detector.py`)
✅ **Implementováno:**
- Detekce negativních cyklů v grafu
- Multi-source analýza pro všechny tokeny
- AI scoring a ranking příležitostí
- Risk assessment

#### Main Arbitrage System (`core/main_arbitrage_system.py`)
✅ **Implementováno:**
- Orchestrace všech komponent
- Asynchronní skenování příležitostí
- Konfigurovatelné strategie
- Performance tracking

### 🖥️ Uživatelské rozhraní (Gradio)

✅ **Implementované funkce:**

**Tab 1: Live Arbitrage Scanner**
- Výběr aktivních strategií (checkboxy)
- Výběr trading párů (BTC, ETH, BNB, atd.)
- Nastavení minimálního profitu (0.1-3.0%)
- Maximální počet příležitostí (1-20)
- Auto-refresh každých 30 sekund
- Demo mode přepínač
- Živá tabulka příležitostí
- AI analýza a doporučení
- Performance graf

**Tab 2: Execution Center**
- Manuální výběr příležitosti k exekuci
- Nastavení množství (10-10,000 USDT)
- Execute/Stop All tlačítka
- Historie exekucí

**Tab 3: Analytics & Insights**
- Porovnání výkonnosti strategií
- Market heatmap
- Risk analýza a varování

---

## 🏗️ Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                    Gradio UI (app.py)                       │
│  • Live Scanner  • Execution Center  • Analytics           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│           Main Arbitrage System                              │
│                 (orchestrátor)                               │
└─────┬────────┬─────────┬──────────┬───────────┬────────────┘
      │        │         │          │           │
┌─────▼───┐ ┌─▼─────┐ ┌─▼─────┐ ┌──▼──────┐ ┌─▼──────────┐
│   AI    │ │ Data  │ │ Graph │ │ Bellman │ │ 5 Strategy │
│  Model  │ │Engine │ │Builder│ │  -Ford  │ │  Modules   │
└─────────┘ └───┬───┘ └───────┘ └─────────┘ └────────────┘
                │
        ┌───────┴────────┐
        │                │
    ┌───▼───┐      ┌────▼────┐
    │ CCXT  │      │  Web3   │
    │8 CEX  │      │3 DEX    │
    └───────┘      └─────────┘
```

---

## 🚀 Rychlý start

### Online (doporučeno)

Aplikace běží na Hugging Face Spaces:
👉 [https://huggingface.co/spaces/HonzaH/AIarbi](https://huggingface.co/spaces/HonzaH/AIarbi)

1. Otevřete aplikaci v prohlížeči
2. Vyberte strategie, které chcete aktivovat
3. Zvolte trading páry (např. BTC/USDT, ETH/USDT)
4. Nastavte minimální profit (doporučeno 0.5%)
5. Klikněte "🔍 Scan Opportunities"
6. Prohlédněte si výsledky a AI doporučení

**Demo mode** je zapnutý automaticky - veškeré exekuce jsou simulované.

### Lokální instalace (Windows PowerShell)

```powershell
# 1. Klonovat repozitář
git clone https://github.com/HonzaHezina/AIarbi.git
cd AIarbi

# 2. Vytvořit virtuální prostředí
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalovat závislosti
pip install --upgrade pip
pip install -r requirements.txt

# 4. Ověřit import
python -c "import app; print('Import OK')"

# 5. Spustit aplikaci
python app.py
```

Aplikace se spustí na `http://localhost:7860`

---

## 📊 Obchodní strategie - detailní popis

### 1. DEX/CEX Arbitrage

**Princip:** Využívá cenové rozdíly mezi decentralizovanými (DEX) a centralizovanými (CEX) burzami.

**Příklad:**
```
ETH na Uniswap: $2,000
ETH na Binance: $2,010
Profit: $10 - fees = ~$7 (0.35%)
```

**Implementované funkce:**
- Srovnání cen napříč DEX (Uniswap V3, SushiSwap, PancakeSwap)
- Srovnání s CEX (Binance, Kraken, Coinbase, KuCoin)
- Automatický výpočet gas fees (Ethereum network)
- Zahrnuje trading fees obou stran

**Kód:** `strategies/dex_cex_arbitrage.py`

---

### 2. Cross-Exchange Arbitrage

**Princip:** Cenové neefektivity mezi různými centralizovanými burzami.

**Příklad:**
```
BTC na Kraken: $45,000
BTC na KuCoin: $45,200
Profit: $200 - fees = ~$180 (0.4%)
```

**Implementované funkce:**
- Monitoring 8 CEX burz současně
- Optimalizace pro nejnižší transfer fees
- Detekce nejlepších párů burz pro každý token
- Zahrnuje withdrawal a deposit fees

**Kód:** `strategies/cross_exchange_arbitrage.py`

---

### 3. Triangular Arbitrage

**Princip:** Tři-měnové cykly v rámci jedné burzy využívající nekonzistence směnných kurzů.

**Příklad:**
```
Start: 1 BTC
BTC → ETH: 1 BTC = 20 ETH
ETH → USDT: 20 ETH = $40,100
USDT → BTC: $40,100 = 1.002 BTC
Profit: 0.002 BTC (~0.2%)
```

**Implementované funkce:**
- Automatická detekce trojúhelníkových cyklů
- Funguje na každé burze samostatně
- Minimalizuje transfer rizika (vše na jedné burze)
- Rychlá exekuce možná

**Kód:** `strategies/triangular_arbitrage.py`

---

### 4. Wrapped Tokens Arbitrage

**Princip:** Cenové rozdíly mezi nativními tokeny a jejich wrapped verzemi.

**Příklad:**
```
ETH (native): $2,000
wETH (ERC-20): $2,003
Profit: $3 - gas fee = ~$2 (0.1%)
```

**Podporované páry:**
- BTC ↔ wBTC (Wrapped Bitcoin)
- ETH ↔ wETH (Wrapped Ether)
- BNB ↔ wBNB (Wrapped BNB)

**Implementované funkce:**
- Detekce wrap/unwrap arbitrážních příležitostí
- Native vs wrapped cross-exchange arbitráž
- Výpočet wrap/unwrap nákladů
- Smart contract interakce

**Kód:** `strategies/wrapped_tokens_arbitrage.py`

---

### 5. Statistical AI Arbitrage

**Princip:** AI-řízená analýza historických korelací a detekce cenových anomálií.

**Příklad:**
```
ETH/BTC normální korelace: 0.85
Současná korelace: 0.45
→ Anomálie detekována
→ Mean reversion očekáván
```

**Implementované funkce:**
- Korelační analýza mezi burzami
- 100-bodová historická analýza
- Detekce odchylek > 2σ (standardní odchylky)
- AI skóring příležitostí
- Mean reversion predikce

**Parametry:**
- Lookback period: 100 datových bodů
- Correlation threshold: 0.7
- Deviation threshold: 2.0 σ

**Kód:** `strategies/statistical_arbitrage.py`

---

## 🌐 Podporované burzy

### Centralized Exchanges (CEX) - 8 burz

| Burza | Status | CCXT | REST API | Fee (taker) |
|-------|--------|------|----------|-------------|
| 🟡 **Binance** | ✅ Funguje | ✅ | ✅ | 0.1% |
| 🟣 **Kraken** | ✅ Funguje | ✅ | ✅ | 0.26% |
| 🔵 **Coinbase** | ✅ Funguje | ✅ | ✅ | 0.5% |
| 🟢 **KuCoin** | ✅ Funguje | ✅ | ✅ | 0.1% |
| 🟠 **Bitfinex** | ✅ Funguje | ✅ | ⚠️ prefer_ccxt | 0.2% |
| ⚫ **Bybit** | ✅ Funguje | ✅ | ✅ | 0.1% |
| 🔴 **OKX** | ✅ Funguje | ✅ | ✅ | 0.1% |
| 🟦 **Gate.io** | ✅ Funguje | ✅ | ✅ | 0.2% |

### Decentralized Protocols (DEX) - 3 protokoly

| Protokol | Blockchain | Status | Web3 | Gas Fees |
|----------|-----------|--------|------|----------|
| 🦄 **Uniswap V3** | Ethereum | ✅ Funguje | ✅ | ~$15-50 |
| 🍣 **SushiSwap** | Multi-chain | ✅ Funguje | ✅ | ~$10-30 |
| 🥞 **PancakeSwap** | BSC | ✅ Funguje | ✅ | ~$0.5-2 |

### Data Agregátory - 2 služby

| Služba | Purpose | API Key | Status |
|--------|---------|---------|--------|
| 🦎 **CoinGecko** | Price aggregation | ❌ Ne | ✅ Funguje |
| 💹 **CoinMarketCap** | Price data | ⚠️ Doporučeno | ⚠️ Omezeno |

**Poznámky:**
- CCXT poskytuje unified API pro všechny CEX burzy
- REST API fallback funguje, pokud CCXT selže
- Web3 připojení používá public RPC (pro produkci doporučeno vlastní RPC)
- Demo mode funguje i bez živých dat (simulované ceny)

---

## ⚙️ Konfigurace

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG | INFO | WARNING | ERROR

# CoinMarketCap (volitelné)
COINMARKETCAP_API_KEY=your_key   # Vyžadováno pro CMC data

# Demo/Debug
DEBUG_DEMO_INJECT_SYNTHETIC=True  # Injektuje syntetická data pro testování

# Exchange API overrides (volitelné)
EXCHANGE_ENDPOINT_BINANCE_BASE_URL=https://api.binance.com
```

### Konfigurace v kódu

**Trading Config** (`utils/config.py`):
```python
TRADING_CONFIG = {
    'min_profit_threshold': 0.0,      # Minimální profit %
    'max_position_size_usd': 1000,    # Max pozice v USD
    'max_concurrent_trades': 5,       # Max současných obchodů
    'max_daily_trades': 50,           # Max denních obchodů
    'demo_mode': True,                # Demo režim (doporučeno)
}
```

### Hugging Face Spaces konfigurace

V nastavení Space na Hugging Face:

1. **Secrets/Environment Variables:**
   ```
   LOG_LEVEL=INFO
   COINMARKETCAP_API_KEY=your_key_if_needed
   ```

2. **Hardware:**
   - CPU Basic (postačuje)
   - Pro AI model: CPU Upgrade nebo GPU (volitelné)

3. **Visibility:**
   - Public (doporučeno pro demo)

---

## 🔮 Doporučení pro další rozvoj

### 🚀 Vysoká priorita (quick wins)

1. **Real-time WebSocket feeds**
   - Implementovat WebSocket pro Binance, Kraken
   - Nahradit 30s polling real-time updaty
   - Redukovat latenci na < 100ms
   - **Soubory:** `core/data_engine.py`

2. **Advanced backtesting modul**
   - Historický backtesting strategií
   - Performance metriky (Sharpe ratio, drawdown)
   - Monte Carlo simulace
   - **Nový modul:** `core/backtesting.py`

3. **Lepší error handling a monitoring**
   - Sentry integrace pro error tracking
   - Prometheus metriky
   - Health check endpoint
   - **Soubory:** `utils/monitoring.py` (nový)

4. **Database persistence**
   - SQLite/PostgreSQL pro ukládání výsledků
   - Historie skenů a exekucí
   - Performance tracking přes čas
   - **Nový modul:** `core/database.py`

### 💡 Střední priorita (rozšíření funkcí)

5. **Více DEX protokolů**
   - Curve Finance (stablecoin AMM)
   - Balancer V2 (multi-token pools)
   - 1inch Aggregator integration
   - **Soubory:** `strategies/dex_cex_arbitrage.py`

6. **Smart order routing**
   - Optimalizace cesty přes více burz
   - Minimalizace slippage
   - Gas optimization pro DEX
   - **Nový modul:** `strategies/smart_routing.py`

7. **Portfolio management**
   - Position sizing based on Kelly criterion
   - Risk parity allocation
   - Stop-loss/take-profit automation
   - **Nový modul:** `core/portfolio_manager.py`

8. **Multi-chain podpora**
   - Polygon, Avalanche, Arbitrum
   - Cross-chain bridge arbitráž
   - Layer 2 integrace
   - **Soubory:** `core/data_engine.py`, `utils/config.py`

### 🎨 Nízká priorita (UI/UX vylepšení)

9. **Vylepšené dashboardy**
   - Real-time grafy s Plotly Dash
   - Customizovatelné alerts
   - Mobile responsive design
   - **Soubory:** `app.py`

10. **API endpoint pro externí přístup**
    - REST API pro programatický přístup
    - WebSocket pro live stream
    - API dokumentace (OpenAPI/Swagger)
    - **Nový modul:** `api/` directory

11. **Machine Learning vylepšení**
    - Finetuning AI modelu na crypto data
    - Reinforcement learning pro execution timing
    - Sentiment analysis integrace
    - **Soubory:** `core/ai_model.py`

12. **Multi-language podpora**
    - Lokalizace UI (EN, CS, více)
    - Dokumentace v více jazycích
    - **Soubory:** `app.py`, všechny README

### 🔒 Bezpečnost a produkce

13. **Security hardening**
    - API key encryption
    - Secrets management (Vault, AWS Secrets)
    - Rate limiting per user
    - **Nový modul:** `utils/security.py`

14. **Production deployment**
    - Docker containerization
    - Kubernetes manifesty
    - CI/CD pipeline (GitHub Actions)
    - Load balancing
    - **Nové soubory:** `Dockerfile`, `k8s/`, `.github/workflows/`

15. **Testing infrastructure**
    - 80%+ code coverage
    - Integration tests pro všechny strategie
    - Load testing
    - **Rozšířit:** `tests/` directory

---

## 🛠️ Technické detaily

### Požadavky

**Python:** 3.8+

**Hlavní závislosti:**
```
gradio==5.45.0          # UI framework
transformers            # AI model (DialoGPT)
torch                   # PyTorch pro AI
ccxt                    # Exchange API
web3                    # Ethereum/DEX
networkx                # Graph algorithms
pandas                  # Data manipulation
plotly                  # Visualizace
```

### Výkon

**Scan rychlost:**
- 5 strategií: ~3-5 sekund
- 10 trading párů: ~8-12 sekund
- Auto-refresh: 30 sekund interval

**Paměť:**
- Základní: ~500 MB
- S AI modelem: ~1-2 GB
- Peak (full scan): ~2.5 GB

**AI Model:**
- Microsoft DialoGPT-medium
- ~350M parametrů
- Inference: ~1-2 sekundy
- Fallback na rule-based pokud AI nedostupné

### Testing

Spuštění testů:
```bash
# Aktivovat venv
.\.venv\Scripts\Activate.ps1

# Instalovat pytest
pip install pytest

# Spustit všechny testy
pytest -v

# Spustit specifický test
pytest tests/test_all_strategies_complete.py -v
```

**Test coverage:**
- 19 testů (všechny pass)
- 5 strategií ověřeno
- Integration tests fungují

**Test soubory:**
- `tests/test_all_strategies_complete.py` - kompletní test všech strategií
- `tests/test_endpoints.py` - endpoint konfigurace
- Další testy podle potřeby

### Deployment na Hugging Face Spaces

**Soubor:** `README.md` (YAML frontmatter)
```yaml
---
title: AI Crypto Arbitrage System
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.45.0
app_file: app.py
pinned: false
---
```

**Automatické deployment:**
1. Push do GitHub repozitáře
2. Hugging Face automaticky detekuje změny
3. Rebuild a redeploy (3-5 minut)
4. Aplikace dostupná na `https://huggingface.co/spaces/HonzaH/AIarbi`

**Logs:**
- Dostupné v HF Spaces UI (ikona "Logs")
- Nastavte `LOG_LEVEL=INFO` v Settings

---

## 📚 Dokumentace

### Hlavní soubory

- **README.md** - anglická dokumentace, Hugging Face frontmatter
- **README.cs.md** (tento soubor) - česká kompletní dokumentace
- **STRATEGY_VERIFICATION_REPORT.md** - anglický report o strategiích
- **VERIFIKACE_OBCHODNICH_SYSTEMU.md** - český report o strategiích
- **kompletni-crypto-api-10.md** - API specifikace pro burzy

### Kód struktura

```
AIarbi/
├── app.py                          # Gradio UI aplikace
├── requirements.txt                # Python závislosti
├── core/                           # Hlavní logika
│   ├── ai_model.py                 # AI model wrapper
│   ├── data_engine.py              # Data fetching (CCXT, Web3)
│   ├── graph_builder.py            # NetworkX grafy
│   ├── bellman_ford_detector.py    # Arbitrage detection
│   └── main_arbitrage_system.py    # System orchestrátor
├── strategies/                     # Trading strategie
│   ├── dex_cex_arbitrage.py
│   ├── cross_exchange_arbitrage.py
│   ├── triangular_arbitrage.py
│   ├── wrapped_tokens_arbitrage.py
│   └── statistical_arbitrage.py
├── utils/                          # Utility moduly
│   ├── config.py                   # Konfigurace
│   └── logging_config.py           # Logging setup
├── tests/                          # Test suite
│   ├── test_all_strategies_complete.py
│   └── test_endpoints.py
└── tools/                          # Helper skripty
    └── verify_endpoints.py         # Endpoint verifier
```

---

## ⚠️ Disclaimer

**DŮLEŽITÉ:**

- ⚠️ **Pouze pro vzdělávací účely**: Tento software je určen primárně pro učení a výzkum.
- 📝 **Demo mode doporučen**: Výchozí nastavení používá simulované obchody bez rizika.
- 💸 **Finanční riziko**: Skutečný trading s kryptoměnami nese významné finanční riziko.
- 🚫 **Žádné záruky**: Minulá výkonnost není zárukou budoucích výsledků.
- 🔐 **API klíče**: Nikdy nesdílejte API klíče s trading oprávněními.
- ⚡ **Rychlost exekuce**: Arbitrážní příležitosti mizí velmi rychle (sekundy).
- 📊 **Slippage**: Skutečné ceny se mohou lišit od zobrazených kvůli slippage.

**Před použitím s reálnými penězi:**
1. Důkladně otestujte v demo režimu
2. Pochopte všechny rizika
3. Začněte s minimálními částkami
4. Implementujte stop-loss mechanismy
5. Nikdy neinvestujte více, než můžete ztratit

---

## 🤝 Přispívání

Projekt je open-source a vítáme příspěvky:

- 🐛 **Hlášení chyb**: Otevřete Issue na GitHubu
- 💡 **Návrhy vylepšení**: Diskuze v Issues
- 🔧 **Pull requests**: Fork + PR s popisem změn
- 📖 **Dokumentace**: Vylepšení README, komentářů
- 🧪 **Testy**: Přidání nových testů

---

## 📞 Kontakt a odkazy

- 🌐 **Live aplikace**: [https://huggingface.co/spaces/HonzaH/AIarbi](https://huggingface.co/spaces/HonzaH/AIarbi)
- 💻 **GitHub repozitář**: [https://github.com/HonzaHezina/AIarbi](https://github.com/HonzaHezina/AIarbi)
- 👤 **Autor**: HonzaHezina

---

## 📜 License

[Uveďte licenci projektu - např. MIT, Apache 2.0, atd.]

---

**Poslední aktualizace**: 13. října 2025

**Verze**: 1.0.0

**Status**: ✅ Produkční (demo mode)
