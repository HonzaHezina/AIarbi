import os
import sys
import math
# Ensure project root is on sys.path so local packages are importable when running from tools/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import networkx as nx
import logging
from utils.logging_config import setup_logging
# Initialize logging for this script (ensures HF Spaces / stdout capture)
setup_logging()
logger = logging.getLogger(__name__)

from core.data_engine import DataEngine
from core.graph_builder import GraphBuilder


def main():
    logger.info("Building graph using fallback data for inspection...")
    de = DataEngine()
    # Use default trading pairs if none provided so fallback data is populated
    trading_pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    price_data = de.get_fallback_data(trading_pairs)

    # Inject an artificial profitable gap for diagnostics:
    # Make BTC cheaper on 'kucoin' ask and more expensive on 'binance' bid to create arbitrage
    try:
        # lower ask on kucoin (buy BTC cheaply with USDT)
        if 'kucoin' in price_data['cex'] and 'BTC/USDT' in price_data['cex']['kucoin']:
            price_data['cex']['kucoin']['BTC/USDT']['ask'] *= 0.995  # -0.5% ask

        # raise bid on binance (sell BTC for more USDT)
        if 'binance' in price_data['cex'] and 'BTC/USDT' in price_data['cex']['binance']:
            price_data['cex']['binance']['BTC/USDT']['bid'] *= 1.005  # +0.5% bid
    except Exception:
        logger.debug("Exception while adjusting fallback prices for inspection", exc_info=True)
    
    gb = GraphBuilder(None)
    G = gb.build_unified_graph(price_data)

    logger.info("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    
    logger.info("Enumerating simple cycles (up to length 6)...")
    cycles = list(nx.simple_cycles(G))
    logger.info("Total simple cycles found: %d", len(cycles))

    results = []
    for cycle in cycles:
        if len(cycle) < 2 or len(cycle) > 6:
            continue

        # compute total weight along cycle (closed)
        total_weight = 0.0
        edge_details = []
        for i in range(len(cycle)):
            u = cycle[i]
            v = cycle[(i + 1) % len(cycle)]
            if G.has_edge(u, v):
                data = G[u][v]
                w = data.get('weight', 0.0)
                total_weight += w
                edge_details.append({
                    'edge': f"{u}->{v}",
                    'weight': w,
                    'rate': data.get('rate'),
                    'fee': data.get('fee'),
                })
            else:
                # missing directed edge, skip cycle
                total_weight = None
                break

        if total_weight is None:
            continue

        implied_profit_pct = -total_weight * 100

        # compute round-trip product of rates (pre-fee) and post-fee
        prod_rate = 1.0
        prod_rate_after_fees = 1.0
        for ed in edge_details:
            r = ed.get('rate') or 1.0
            f = ed.get('fee') or 0.0
            try:
                r = float(r)
            except:
                r = 1.0
            prod_rate *= r
            prod_rate_after_fees *= r * (1 - float(f))

        profit_no_fees_pct = (prod_rate - 1) * 100
        profit_after_fees_pct = (prod_rate_after_fees - 1) * 100

        results.append((implied_profit_pct, total_weight, cycle, edge_details, profit_no_fees_pct, profit_after_fees_pct))

    # sort by implied profit descending
    results.sort(key=lambda x: x[0], reverse=True)

    logger.info("Top 20 cycle candidates by implied profit (profit_pct, total_weight, path):")
    for item in results[:20]:
        profit_pct, total_weight, cycle, edges, pf_no_fees, pf_after_fees = item
        logger.info("- implied_profit=%.6f%%, total_weight=%.8f, path=%s", profit_pct, total_weight, cycle)
        logger.info("    roundtrip_no_fees=%.6f%%, roundtrip_after_fees=%.6f%%", pf_no_fees, pf_after_fees)
        for e in edges:
            logger.info("    %s weight=%.8f rate=%s fee=%s", e['edge'], e['weight'], e['rate'], e['fee'])
    
    if not results:
        logger.info("No cycles found within length limits.")
    else:
        best = results[0]
        logger.info("Best implied profit: %.6f%% for path %s", best[0], best[2])
        logger.info("Best roundtrip no-fees: %.6f%%, after-fees: %.6f%%", best[4], best[5])


if __name__ == '__main__':
    main()
