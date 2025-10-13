# python
import asyncio
import json
import logging
from pathlib import Path
import sys
import os

# Ensure project root is on sys.path so imports like `from core...` work when run as a script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.data_engine import DataEngine
from strategies.dex_cex_arbitrage import DEXCEXArbitrage

LOG = logging.getLogger("diagnose")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

OUTPUT_PATH = Path("tools/diagnostic_report.json")

# Diagnostics thresholds
PROFIT_PCT_THRESHOLD = 100.0  # report profit_pct > 100%
ABSOLUTE_PROFIT_PCT_THRESHOLD = 1000.0  # also report absurdly large values

TRADING_PAIRS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT",
    "SOL/USDT", "MATIC/USDT", "DOT/USDT", "LINK/USDT"
]


async def run_diagnostics():
    report = {
        "metadata": {
            "pairs": TRADING_PAIRS,
        },
        "exchanges": {},
        "anomalies": []
    }

    de = DataEngine()
    strategy = DEXCEXArbitrage(ai_model=None)

    LOG.info("Fetching market data for diagnostic run...")
    price_data = await de.fetch_all_market_data(TRADING_PAIRS)

    # Inspect cex exchange symbols availability
    for name, ex in de.cex_exchanges.items():
        try:
            symbols = getattr(ex, "symbols", None)
            report["exchanges"][name] = {
                "has_symbols": bool(symbols),
                "symbols_sample": list(symbols)[:10] if symbols else []
            }
            LOG.info("Exchange %s has_symbols=%s sample_len=%d", name, bool(symbols), len(report["exchanges"][name]["symbols_sample"]))
        except Exception as e:
            report["exchanges"][name] = {"error": str(e)}
            LOG.warning("Error inspecting exchange %s: %s", name, e)

    tokens = price_data.get("tokens", [])
    LOG.info("Tokens for diagnostics: %s", tokens)

    # Helper: attempt get token info like strategy.get_token_price_info
    def token_price_lookup(exchange_data, token):
        if not isinstance(exchange_data, dict):
            return None
        if token in exchange_data:
            return exchange_data[token]
        for pair, info in exchange_data.items():
            if isinstance(pair, str) and '/' in pair:
                base = pair.split('/')[0]
                if base == token:
                    return info
        return None

    # Iterate and compute direct profits for cex<->dex combos
    for token in tokens:
        for cex in strategy.cex_exchanges:
            for dex in strategy.dex_protocols:
                cex_data = price_data.get('cex', {}).get(cex, {})
                dex_data = price_data.get('dex', {}).get(dex, {})

                cex_price_info = token_price_lookup(cex_data, token)
                dex_price_info = token_price_lookup(dex_data, token)

                # Compute both directions if data available
                pairs_to_check = [
                    ('cex_to_dex', cex_price_info, dex_price_info, cex, dex),
                    ('dex_to_cex', dex_price_info, cex_price_info, dex, cex)
                ]

                for direction, buy_info, sell_info, buy_ex, sell_ex in pairs_to_check:
                    if not buy_info or not sell_info:
                        continue
                    try:
                        result = await strategy.calculate_arbitrage_profit(
                            token, buy_ex, sell_ex, buy_info, sell_info, direction
                        )
                    except Exception as e:
                        LOG.exception("Error calculating profit for %s %s->%s: %s", token, buy_ex, sell_ex, e)
                        result = {"error": str(e)}

                    profit_pct = result.get("profit_pct")
                    # collect anomalies
                    if isinstance(profit_pct, (int, float)):
                        if abs(profit_pct) >= ABSOLUTE_PROFIT_PCT_THRESHOLD or abs(profit_pct) >= PROFIT_PCT_THRESHOLD:
                            anomaly = {
                                "token": token,
                                "direction": direction,
                                "buy_exchange": buy_ex,
                                "sell_exchange": sell_ex,
                                "profit_pct": profit_pct,
                                "profit_usd": result.get("profit_usd"),
                                "buy_price_info": buy_info,
                                "sell_price_info": sell_info,
                                "diagnostic_note": "profit_pct exceeded thresholds"
                            }
                            report["anomalies"].append(anomaly)
                            LOG.info("ANOMALY: %s %s->%s profit_pct=%.4f", token, buy_ex, sell_ex, profit_pct)

    # Also scan edges added by strategy add_cex_to_dex_edges/add_dex_to_cex_edges by building a temporary graph
    try:
        import networkx as nx
        G = nx.DiGraph()
        # create nodes for combinations
        for token in tokens:
            for cex in strategy.cex_exchanges:
                G.add_node(f"{token}@{cex}")
            for dex in strategy.dex_protocols:
                G.add_node(f"{token}@{dex}")
        # add edges and capture edges with suspicious computed profit_pct via logs above; here we re-run add_strategy_edges but intercept INFO logs by checking weight/rate
        await strategy.add_strategy_edges(G, price_data)
        edges_info = []
        for u, v, data in G.edges(data=True):
            edges_info.append({
                "edge": f"{u}->{v}",
                "weight": data.get("weight"),
                "rate": data.get("rate"),
                "ai_confidence": data.get("ai_confidence"),
                "total_fees": data.get("total_fees"),
                "gas_cost": data.get("gas_cost")
            })
        report["graph_edges_sample"] = edges_info[:200]
    except Exception as e:
        LOG.warning("Could not build graph edges during diagnostics: %s", e)
        report["graph_error"] = str(e)

    # Write report
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOG.info("Diagnostic report written to %s (anomalies=%d)", OUTPUT_PATH, len(report.get("anomalies", [])))
    print(f"DIAGNOSTIC_OUTPUT={OUTPUT_PATH} ANOMALIES={len(report.get('anomalies', []))}")


if __name__ == "__main__":
    asyncio.run(run_diagnostics())