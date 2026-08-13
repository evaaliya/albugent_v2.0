import networkx as nx
from typing import Dict, List, Tuple

def build_and_analyze_graph(nodes: List[str], edges: List[Tuple[str, str]]) -> Dict[str, float]:
    """
    Строит глобальный направленный граф lineage-связей 
    и вычисляет Betweenness Centrality для каждого узла.
    """
    G = nx.DiGraph()
    
    for node in nodes:
        G.add_node(node)
        
    for src, dst in edges:
        G.add_edge(src, dst)

    if G.number_of_nodes() <= 1:
        return {node: 0.0 for node in nodes}

    centrality_map = nx.betweenness_centrality(G)
    return {node: round(score, 3) for node, score in centrality_map.items()}