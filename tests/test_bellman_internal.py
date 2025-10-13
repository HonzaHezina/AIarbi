import math
import pytest

from core.graph_builder import GraphBuilder
from core.bellman_ford_detector import BellmanFordDetector

@pytest.fixture
def simple_profitable_cycle_graph():
    """
    Build a simple 3-node graph with a known profitable cycle.
    Nodes include exchange suffixes so classifier picks up dex/cex types.
    """
    gb = GraphBuilder(ai_model=None)
    G = gb.build_unified_graph({
        # Minimal price_data used only for node creation - edges will be added manually
        'tokens': ['A', 'B', 'C'],
        'cex': {
            'binance': {'A/B': {'bid': 0.0, 'ask': 0.0}},
            'kraken': {'C/A': {'bid': 0.0, 'ask': 0.0}}
        },
        'dex': {
            'uniswap_v3': {'B/C': {'bid': 0.0, 'ask': 0.0}}
        }
    })

    # Create a cycle A@binance -> B@uniswap_v3 -> C@kraken -> A@binance
    n1 = "A@binance"
    n2 = "B@uniswap_v3"
    n3 = "C@kraken"

    # Choose rates so product > 1 (5% profit overall)
    total_profit_factor = 1.05
    r = total_profit_factor ** (1/3)

    # Add edges with weight = -log(rate)
    G.add_edge(n1, n2, weight=-math.log(r), rate=r, pair="A/B", exchange="mixed")
    G.add_edge(n2, n3, weight=-math.log(r), rate=r, pair="B/C", exchange="mixed")
    G.add_edge(n3, n1, weight=-math.log(r), rate=r, pair="C/A", exchange="mixed")

    return G

def test_detect_all_cycles_finds_profitable_cycle(simple_profitable_cycle_graph):
    detector = BellmanFordDetector(ai_model=None)
    cycles = detector.detect_all_cycles(simple_profitable_cycle_graph)

    assert isinstance(cycles, list)
    assert len(cycles) > 0, "Expected detector to find at least one profitable cycle"

    cycle = cycles[0]
    assert 'path' in cycle and isinstance(cycle['path'], list)
    assert cycle.get('profit_estimate', 0) > 0.1, "Expected profit_estimate > 0.1% for our synthetic cycle"

def test_extract_cycle_and_classification(simple_profitable_cycle_graph):
    detector = BellmanFordDetector(ai_model=None)
    G = simple_profitable_cycle_graph

    # Build predecessor map that points into a cycle: n1<-n3<-n2<-n1
    predecessors = {node: None for node in G.nodes()}
    # pick the three cycle nodes explicitly
    n1 = "A@binance"
    n2 = "B@uniswap_v3"
    n3 = "C@kraken"
    predecessors[n2] = n1
    predecessors[n3] = n2
    predecessors[n1] = n3

    cycle = detector.extract_cycle(G, predecessors, n1)
    assert cycle is not None, "extract_cycle should return a cycle dict for the provided predecessors"
    assert cycle['cycle_length'] == 3
    assert 'strategy_type' in cycle
    # Because we used both dex and cex names, classifier should label it 'dex_cex'
    assert cycle['strategy_type'] == 'dex_cex'

def test_is_valid_cycle_filters_low_profit():
    detector = BellmanFordDetector(ai_model=None)

    # Construct a low-profit cycle dict (profit_estimate below 0.1)
    cycle = {
        'path': ['A@binance', 'B@uniswap_v3', 'A@binance'],
        'profit_estimate': 0.05,
        'cycle_length': 2,
        'exchanges_involved': ['binance', 'uniswap_v3'],
        'strategy_type': 'dex_cex'
    }

    assert detector.is_valid_cycle(cycle) is False

def test_is_valid_cycle_filters_too_long():
    detector = BellmanFordDetector(ai_model=None)

    # Construct a cycle with excessive length
    long_path = [f"T{i}@ex{i}" for i in range(10)]
    cycle = {
        'path': long_path + [long_path[0]],
        'profit_estimate': 10.0,  # big profit would normally be valid
        'cycle_length': len(long_path),
        'exchanges_involved': ['ex0', 'ex1', 'ex2'],
        'strategy_type': 'cross_exchange'
    }

    # Ensure max_cycle_length is less than our cycle_length for the detector
    detector.max_cycle_length = 6
    assert detector.is_valid_cycle(cycle) is False