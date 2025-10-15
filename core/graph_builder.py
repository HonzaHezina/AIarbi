import math
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# networkx is optional for running lightweight tests without installing dependencies.
# Provide a minimal in-process fallback implementation that implements the subset of
# networkx API used by this project. When real networkx is available it will be used.
try:
    import networkx as nx
except Exception:
    logger = logging.getLogger(__name__)

    class _AdjView:
        def __init__(self, graph, u):
            self._graph = graph
            self._u = u

        def __getitem__(self, v):
            return self._graph._edges.get((self._u, v), {})

    class _SimpleDiGraph:
        def __init__(self):
            self._nodes = {}      # node -> attr dict
            self._edges = {}      # (u,v) -> attr dict

        def add_node(self, node, **attrs):
            if node not in self._nodes:
                self._nodes[node] = {}
            self._nodes[node].update(attrs)

        def add_edge(self, u, v, **data):
            # ensure nodes exist
            if u not in self._nodes:
                self._nodes[u] = {}
            if v not in self._nodes:
                self._nodes[v] = {}
            self._edges[(u, v)] = dict(data)

        def nodes(self):
            return list(self._nodes.keys())

        def edges(self, data=False):
            if data:
                return [(u, v, dict(d)) for (u, v), d in self._edges.items()]
            return list(self._edges.keys())

        def number_of_nodes(self):
            return len(self._nodes)

        def number_of_edges(self):
            return len(self._edges)

        def has_edge(self, u, v):
            return (u, v) in self._edges

        def has_node(self, node):
            """Compatibility helper used by strategy code (networkx has has_node)."""
            return node in self._nodes

        def subgraph(self, nodes_list):
            sub = _SimpleDiGraph()
            for n in nodes_list:
                if n in self._nodes:
                    sub.add_node(n, **self._nodes[n])
            for (u, v), d in self._edges.items():
                if u in sub._nodes and v in sub._nodes:
                    sub.add_edge(u, v, **d)
            return sub

        def __getitem__(self, u):
            return _AdjView(self, u)

    def density(graph):
        n = graph.number_of_nodes()
        m = graph.number_of_edges()
        if n <= 1:
            return 0.0
        return m / (n * (n - 1))

    def number_strongly_connected_components(graph):
        # conservative fallback: treat whole graph as one component
        return 1 if graph.number_of_nodes() > 0 else 0

    def number_weakly_connected_components(graph):
        return number_strongly_connected_components(graph)

    class _NXModule:
        DiGraph = _SimpleDiGraph
        density = staticmethod(density)
        number_strongly_connected_components = staticmethod(number_strongly_connected_components)
        number_weakly_connected_components = staticmethod(number_weakly_connected_components)

    nx = _NXModule()

logger = logging.getLogger(__name__)

class GraphBuilder:
    """
    Builds unified graph for Bellman-Ford arbitrage detection
    """

    def __init__(self, ai_model):
        self.ai = ai_model
        self.graph = None

    def build_unified_graph(self, price_data: Dict[str, Any]) -> nx.DiGraph:
        """
        Build a unified graph combining CEX and DEX data
        """
        try:
            logger.info(" Building unified arbitrage graph...")

            if not price_data:
                raise ValueError(" Price data is empty or None")

            # Validate price data
            if not all(pair_data for exchange_data in price_data.get('cex', {}).values() for pair_data in exchange_data.values()):
                raise ValueError(" Price data contains NoneType values")

            # Create directed graph
            G = nx.DiGraph()

            # Add nodes for all tokens on all exchanges/protocols
            self.add_all_nodes(G, price_data)

            # Add basic price edges
            self.add_price_edges(G, price_data)

            logger.info(f" Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

            self.graph = G
            return G

        except Exception as e:
            logger.exception(f" Error building graph: {str(e)}")
            return nx.DiGraph()

    def add_all_nodes(self, graph: nx.DiGraph, price_data: Dict[str, Any]):
        """Add all nodes (token@exchange) to the graph"""

        # Add CEX nodes
        for exchange_name, exchange_data in price_data.get('cex', {}).items():
            for pair, pair_data in exchange_data.items():
                if '/' in pair:
                    base_token, quote_token = pair.split('/')

                    # Add nodes for both tokens
                    base_node = f"{base_token}@{exchange_name}"
                    quote_node = f"{quote_token}@{exchange_name}"

                    graph.add_node(base_node, 
                                 exchange=exchange_name, 
                                 token=base_token,
                                 exchange_type='cex')
                    graph.add_node(quote_node, 
                                 exchange=exchange_name, 
                                 token=quote_token,
                                 exchange_type='cex')

        # Add DEX nodes
        for protocol_name, protocol_data in price_data.get('dex', {}).items():
            for pair, pair_data in protocol_data.items():
                if '/' in pair:
                    base_token, quote_token = pair.split('/')

                    base_node = f"{base_token}@{protocol_name}"
                    quote_node = f"{quote_token}@{protocol_name}"

                    graph.add_node(base_node,
                                 exchange=protocol_name,
                                 token=base_token, 
                                 exchange_type='dex')
                    graph.add_node(quote_node,
                                 exchange=protocol_name,
                                 token=quote_token,
                                 exchange_type='dex')

    def add_price_edges(self, graph: nx.DiGraph, price_data: Dict[str, Any]):
        """Add edges based on trading pairs"""

        # Add CEX trading pair edges
        for exchange_name, exchange_data in price_data.get('cex', {}).items():
            for pair, pair_data in exchange_data.items():
                if '/' in pair and 'bid' in pair_data and 'ask' in pair_data:
                    base_token, quote_token = pair.split('/')

                    base_node = f"{base_token}@{exchange_name}"
                    quote_node = f"{quote_token}@{exchange_name}"

                    # Diagnostic: log the pair data structure and numeric types
                    try:
                        logger.debug(
                            "CEX pair data %s@%s -> pair=%s bid=%s(%s) ask=%s(%s) volume=%s",
                            base_token, exchange_name, pair,
                            pair_data.get('bid'), type(pair_data.get('bid')).__name__,
                            pair_data.get('ask'), type(pair_data.get('ask')).__name__,
                            pair_data.get('volume')
                        )
                    except Exception:
                        logger.debug("CEX pair data available for %s@%s pair=%s", base_token, exchange_name, pair)

                    # Normalize bid/ask and apply explicit CEX fee
                    bid = float(pair_data.get('bid', 0) or 0)
                    ask = float(pair_data.get('ask', 0) or 0)
                    cex_fee = 0.001  # 0.1% CEX fee

                    # Base -> Quote (selling base for quote)
                    if bid > 0:
                        # Validate bid is reasonable (not extreme)
                        if bid > 1e6 or bid < 1e-6:
                            logger.warning(f"Extreme bid price {bid} for pair {pair} on {exchange_name}. Skipping edge.")
                            continue
                        
                        rate = bid
                        try:
                            weight = -math.log(rate * (1 - cex_fee))
                            
                            # Validate weight is not extreme
                            if abs(weight) > 10:
                                logger.warning(f"Extreme weight {weight:.2f} for pair {pair} on {exchange_name}. "
                                             f"bid={bid}, fee={cex_fee}. Skipping edge.")
                                continue
                            
                            logger.debug(
                                "Adding CEX sell edge %s->%s bid=%s computed_weight=%s rate=%s",
                                base_node, quote_node, bid, weight, rate
                            )
                            graph.add_edge(base_node, quote_node,
                                         weight=weight,
                                         rate=rate,
                                         fee=cex_fee,
                                         pair=pair,
                                         exchange=exchange_name,
                                         trade_type='sell')
                        except (ValueError, OverflowError) as e:
                            logger.error(f"Error calculating weight for {pair}: {e}")
                            continue

                    # Quote -> Base (buying base with quote)
                    if ask > 0:
                        # Validate ask is reasonable
                        if ask > 1e6 or ask < 1e-6:
                            logger.warning(f"Extreme ask price {ask} for pair {pair} on {exchange_name}. Skipping edge.")
                            continue
                        
                        # Protect against division by zero; invert ask to get base per quote
                        inv_rate = 1.0 / ask
                        
                        # Validate inverted rate
                        if inv_rate > 1e6 or inv_rate < 1e-6:
                            logger.warning(f"Extreme inverted rate {inv_rate} (1/{ask}) for pair {pair} on {exchange_name}. Skipping edge.")
                            continue
                        
                        try:
                            weight = -math.log(inv_rate * (1 - cex_fee))
                            
                            # Validate weight is not extreme
                            if abs(weight) > 10:
                                logger.warning(f"Extreme weight {weight:.2f} for pair {pair} on {exchange_name}. "
                                             f"ask={ask}, inv_rate={inv_rate}, fee={cex_fee}. Skipping edge.")
                                continue
                            
                            logger.debug(
                                "Adding CEX buy edge %s->%s ask=%s inv_rate=%s computed_weight=%s",
                                quote_node, base_node, ask, inv_rate, weight
                            )
                            graph.add_edge(quote_node, base_node,
                                         weight=weight,
                                         rate=inv_rate,
                                         fee=cex_fee,
                                         pair=pair,
                                         exchange=exchange_name,
                                         trade_type='buy')
                        except (ValueError, OverflowError) as e:
                            logger.error(f"Error calculating weight for {pair}: {e}")
                            continue

        # Add DEX trading pair edges
        for protocol_name, protocol_data in price_data.get('dex', {}).items():
            for pair, pair_data in protocol_data.items():
                if '/' in pair and 'bid' in pair_data and 'ask' in pair_data:
                    base_token, quote_token = pair.split('/')

                    base_node = f"{base_token}@{protocol_name}"
                    quote_node = f"{quote_token}@{protocol_name}"

                    dex_fee = pair_data.get('fee', 0.003)  # Default 0.3%

                    # Diagnostic: log DEX pair data and fee/liquidity fields
                    try:
                        logger.debug(
                            "DEX pair data %s@%s -> pair=%s bid=%s ask=%s fee=%s liquidity=%s",
                            base_token, protocol_name, pair,
                            pair_data.get('bid'), pair_data.get('ask'),
                            dex_fee, pair_data.get('liquidity')
                        )
                    except Exception:
                        logger.debug("DEX pair data available for %s@%s pair=%s", base_token, protocol_name, pair)

                    # Base -> Quote
                    bid = pair_data.get('bid', 0)
                    if bid > 0:
                        # Validate bid is reasonable
                        if bid > 1e6 or bid < 1e-6:
                            logger.warning(f"Extreme DEX bid {bid} for {pair} on {protocol_name}. Skipping.")
                            continue
                        
                        try:
                            weight = -math.log(bid * (1 - dex_fee))
                            
                            # Validate weight
                            if abs(weight) > 10:
                                logger.warning(f"Extreme DEX weight {weight:.2f} for {pair}. Skipping.")
                                continue
                            
                            logger.debug(
                                "Adding DEX sell edge %s->%s bid=%s fee=%s computed_weight=%s rate=%s",
                                base_node, quote_node, bid, dex_fee, weight, bid
                            )
                            graph.add_edge(base_node, quote_node,
                                         weight=weight,
                                         rate=bid,
                                         fee=dex_fee,
                                         pair=pair,
                                         exchange=protocol_name,
                                         trade_type='sell',
                                         liquidity=pair_data.get('liquidity', 0))
                        except (ValueError, OverflowError) as e:
                            logger.error(f"Error calculating DEX weight for {pair}: {e}")
                            continue

                    # Quote -> Base
                    ask = pair_data.get('ask', 0)
                    if ask > 0:
                        # Validate ask is reasonable
                        if ask > 1e6 or ask < 1e-6:
                            logger.warning(f"Extreme DEX ask {ask} for {pair} on {protocol_name}. Skipping.")
                            continue
                        
                        inv_rate = 1 / ask
                        
                        # Validate inverted rate
                        if inv_rate > 1e6 or inv_rate < 1e-6:
                            logger.warning(f"Extreme DEX inv_rate {inv_rate} for {pair}. Skipping.")
                            continue
                        
                        try:
                            weight = -math.log(inv_rate * (1 - dex_fee))
                            
                            # Validate weight
                            if abs(weight) > 10:
                                logger.warning(f"Extreme DEX weight {weight:.2f} for {pair}. Skipping.")
                                continue
                            
                            logger.debug(
                                "Adding DEX buy edge %s->%s ask=%s inv_rate=%s fee=%s computed_weight=%s",
                                quote_node, base_node, ask, inv_rate, dex_fee, weight
                            )
                            graph.add_edge(quote_node, base_node,
                                         weight=weight,
                                         rate=inv_rate,
                                         fee=dex_fee,
                                         pair=pair,
                                         exchange=protocol_name,
                                         trade_type='buy',
                                         liquidity=pair_data.get('liquidity', 0))
                        except (ValueError, OverflowError) as e:
                            logger.error(f"Error calculating DEX weight for {pair}: {e}")
                            continue

    def add_cross_exchange_edges(self, graph: nx.DiGraph, price_data: Dict[str, Any]):
        """Add edges between same tokens on different exchanges"""
        try:
            tokens = price_data.get('tokens', [])

            for token in tokens:
                # Get all nodes for this token
                token_nodes = [node for node in graph.nodes() 
                              if node.startswith(f"{token}@")]

                # Add edges between all pairs of nodes for this token
                for i, node1 in enumerate(token_nodes):
                    for j, node2 in enumerate(token_nodes):
                        if i != j:
                            exchange1 = node1.split('@')[1]
                            exchange2 = node2.split('@')[1]

                            # Calculate transfer cost and time
                            transfer_cost = self.calculate_transfer_cost(token, exchange1, exchange2)

                            if transfer_cost < 0.1:  # Only if transfer cost < 10%
                                weight = -math.log(1 - transfer_cost)

                                graph.add_edge(node1, node2,
                                             weight=weight,
                                             rate=1.0,
                                             fee=transfer_cost,
                                             transfer_type='cross_exchange',
                                             from_exchange=exchange1,
                                             to_exchange=exchange2)

            logger.info(f" Added cross-exchange edges")

        except Exception as e:
            logger.exception(f" Error adding cross-exchange edges: {str(e)}")

    def calculate_transfer_cost(self, token: str, from_exchange: str, to_exchange: str) -> float:
        """Calculate cost of transferring token between exchanges"""

        # Base transfer costs (simplified)
        base_costs = {
            'BTC': 0.0001,    # ~$5
            'ETH': 0.005,     # ~$15  
            'USDT': 1.0,      # $1
            'USDC': 1.0,      # $1
            'BNB': 0.001      # ~$0.30
        }

        base_cost = base_costs.get(token, 0.01)  # Default 1%

        # Exchange-specific adjustments
        dex_protocols = ['uniswap_v3', 'sushiswap']

        if from_exchange in dex_protocols or to_exchange in dex_protocols:
            base_cost *= 2  # Higher cost for DEX transfers

        # Network congestion factor (simplified)
        congestion_factor = 1.5  # Assume medium congestion

        return min(0.1, base_cost * congestion_factor)  # Cap at 10%

    def add_wrapped_token_edges(self, graph: nx.DiGraph):
        """Add edges for wrapped token conversions"""
        try:
            wrapped_pairs = {
                'BTC': 'wBTC',
                'ETH': 'wETH'
            }

            for native, wrapped in wrapped_pairs.items():
                # Find all DEX nodes with these tokens
                native_nodes = [node for node in graph.nodes() 
                              if node.startswith(f"{native}@") and 
                              any(dex in node for dex in ['uniswap', 'sushi'])]

                wrapped_nodes = [node for node in graph.nodes()
                               if node.startswith(f"{wrapped}@") and
                               any(dex in node for dex in ['uniswap', 'sushi'])]

                # Add wrap/unwrap edges
                for native_node in native_nodes:
                    for wrapped_node in wrapped_nodes:
                        if native_node.split('@')[1] == wrapped_node.split('@')[1]:
                            # Same protocol - can wrap/unwrap

                            wrap_fee = 0.001  # Gas fee for wrapping

                            # Native -> Wrapped (wrap)
                            wrap_weight = -math.log(1 - wrap_fee)
                            graph.add_edge(native_node, wrapped_node,
                                         weight=wrap_weight,
                                         rate=1.0,
                                         fee=wrap_fee,
                                         operation='wrap')

                            # Wrapped -> Native (unwrap)
                            unwrap_weight = -math.log(1 - wrap_fee)
                            graph.add_edge(wrapped_node, native_node,
                                         weight=unwrap_weight,
                                         rate=1.0,
                                         fee=wrap_fee,
                                         operation='unwrap')

            logger.info(f" Added wrapped token edges")

        except Exception as e:
            logger.exception(f" Error adding wrapped token edges: {str(e)}")

    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        if not self.graph:
            return {}

        return {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'tokens': len(set(node.split('@')[0] for node in self.graph.nodes())),
            'exchanges': len(set(node.split('@')[1] for node in self.graph.nodes())),
            'strongly_connected_components': nx.number_strongly_connected_components(self.graph),
            'weakly_connected_components': nx.number_weakly_connected_components(self.graph)
        }

    def visualize_subgraph(self, token: str) -> Dict[str, Any]:
        """Get subgraph data for a specific token for visualization"""
        if not self.graph:
            return {}

        # Get all nodes for this token
        token_nodes = [node for node in self.graph.nodes() 
                      if node.startswith(f"{token}@")]

        if not token_nodes:
            return {}

        # Create subgraph
        subgraph = self.graph.subgraph(token_nodes)

        # Prepare data for visualization
        nodes_data = []
        edges_data = []

        for node in subgraph.nodes():
            exchange = node.split('@')[1]
            nodes_data.append({
                'id': node,
                'label': exchange,
                'token': token,
                'exchange': exchange
            })

        for u, v, data in subgraph.edges(data=True):
            edges_data.append({
                'source': u,
                'target': v,
                'weight': data.get('weight', 0),
                'fee': data.get('fee', 0),
                'rate': data.get('rate', 1)
            })

        return {
            'nodes': nodes_data,
            'edges': edges_data,
            'stats': {
                'nodes': len(nodes_data),
                'edges': len(edges_data)
            }
        }
