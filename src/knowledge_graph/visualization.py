"""Visualization utilities for knowledge graphs."""
import networkx as nx
import json
import re
import os
from pyvis.network import Network

# HTML template for visualization is now stored in a separate file
def _load_html_template():
    """Load the HTML template from the template file."""
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'graph_template.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load template file: {e}")
        return '<div id="mynetwork" class="card-body"></div>'  # Fallback to basic template

def visualize_knowledge_graph(triples, output_file="knowledge_graph.html", edge_smooth=None, config=None):
    """
    从主谓宾三元组创建并可视化知识图谱。
    
    Args:
        triples: 包含'subject'、'predicate'和'object'键的字典列表
        output_file: 保存可视化结果的HTML文件
        edge_smooth: 边平滑设置（覆盖配置）：
                    false, "dynamic", "continuous", "discrete", "diagonalCross", 
                    "straightCross", "horizontal", "vertical", "curvedCW", "curvedCCW", "cubicBezier"
        config: 配置字典（可选）
        
    Returns:
        包含图谱统计信息的字典
    """
    # Determine edge smoothing from config if not explicitly provided
    if edge_smooth is None and config is not None:
        edge_smooth = config.get("visualization", {}).get("edge_smooth", False)
    elif edge_smooth is None:
        edge_smooth = False
    
    if not triples:
        print("Warning: No triples provided for visualization")
        return {"nodes": 0, "edges": 0, "communities": 0}
        
    print(f"Processing {len(triples)} triples for visualization")
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Dictionary to store node groups for community visualization
    node_communities = {}
    
    # Set of all unique nodes
    all_nodes = set()
    
    # Track inferred vs. original relationships
    inferred_edges = set()
    
    # Add all subjects and objects as nodes
    for triple in triples:
        subject = triple["subject"]
        obj = triple["object"]
        all_nodes.add(subject)
        all_nodes.add(obj)
        
        # Mark inferred relationships
        if triple.get("inferred", False):
            inferred_edges.add((subject, obj))
    
    print(f"Found {len(all_nodes)} unique nodes")
    print(f"Found {len(inferred_edges)} inferred relationships")
    
    # Create an undirected graph for community detection and centrality measures
    G_undirected = nx.Graph()
    
    for triple in triples:
        G_undirected.add_edge(triple["subject"], triple["object"])
    
    # Calculate centrality metrics
    centrality_metrics = _calculate_centrality_metrics(G_undirected, all_nodes)
    betweenness = centrality_metrics["betweenness"]
    degree = centrality_metrics["degree"]
    eigenvector = centrality_metrics["eigenvector"]
    
    # Calculate communities
    node_communities, community_count = _detect_communities(G_undirected, all_nodes)
    
    # Define colors for communities - these are standard colorblind-friendly colors
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf']
    
    # Calculate node sizes based on centrality metrics
    node_sizes = _calculate_node_sizes(all_nodes, betweenness, degree, eigenvector)
    
    # Add nodes to the graph with community colors and sizes
    for node in all_nodes:
        community = node_communities[node]
        G.add_node(
            node, 
            color=colors[community % len(colors)],  # Ensure we don't go out of bounds
            label=node,  # Explicit label
            title=f"{node} - Connections: {degree.get(node, 0)}",  # Simple tooltip without HTML tags
            size=node_sizes[node]
        )
    
    # Add edges with predicates as labels
    for triple in triples:
        subject = triple["subject"]
        obj = triple["object"]
        
        # Determine if this is an inferred relationship
        is_inferred = triple.get("inferred", False)
        
        G.add_edge(
            subject, 
            obj, 
            title=triple["predicate"],
            label=triple["predicate"],
            arrows="to",   # Add arrow direction
            width=1,       # Edge width
            dashes=is_inferred,  # Use dashed lines for inferred relationships
            color="#555555" if is_inferred else None  # Lighter color for inferred relationships
        )
    
    # Create a PyVis network with explicit configuration
    net = Network(
        height="100%", 
        width="100%", 
        directed=True,
        notebook=False,
        cdn_resources='in_line',  # Include resources in-line to ensure independence
        bgcolor="#ffffff",
        font_color=True,
        select_menu=False,
        filter_menu=False
    )
    
    # Dump some debug info
    print(f"Nodes in NetworkX graph: {G.number_of_nodes()}")
    print(f"Edges in NetworkX graph: {G.number_of_edges()}")
    
    # Add nodes and edges from NetworkX graph - do this explicitly for better control
    _add_nodes_and_edges_to_network(net, G)
    
    # Set visualization options
    options = _get_visualization_options(len(all_nodes), len(triples))
    
    # Set all options in one go with proper JSON
    net.set_options(json.dumps(options))
    
    
    # Save the network as HTML and modify with custom template
    _save_and_modify_html(net, output_file, community_count, all_nodes, triples)
    
    # Return statistics
    original_edges = len(triples) - len(inferred_edges)
    stats = {
        "nodes": len(all_nodes),
        "edges": len(triples),
        "original_edges": original_edges,
        "inferred_edges": len(inferred_edges),
        "communities": len(set(node_communities.values()))
    }
    print(f"Graph Statistics: {json.dumps(stats, indent=2)}")
    return stats

def _calculate_centrality_metrics(G_undirected, all_nodes):
    """Calculate centrality metrics for the graph nodes."""
    # Betweenness centrality - nodes that bridge communities are more important
    betweenness = nx.betweenness_centrality(G_undirected)
    
    # Degree centrality - nodes with more connections are more important
    degree = dict(G_undirected.degree())
    
    # Eigenvector centrality - nodes connected to high-value nodes are more important
    try:
        eigenvector = nx.eigenvector_centrality(G_undirected, max_iter=1000)
    except:
        # If eigenvector calculation fails (can happen with certain graph structures)
        eigenvector = {node: 0.5 for node in all_nodes}
    
    return {
        "betweenness": betweenness,
        "degree": degree,
        "eigenvector": eigenvector
    }

def _detect_communities(G_undirected, all_nodes):
    """Detect communities in the graph."""
    try:
        # Attempt to detect communities using Louvain method
        import community as community_louvain
        partition = community_louvain.best_partition(G_undirected)
        community_count = len(set(partition.values()))
        print(f"Detected {community_count} communities using Louvain method")
        return partition, community_count
    except:
        # Fallback: assign community IDs based on degree for simplicity
        node_communities = {}
        for node in all_nodes:
            node_degree = G_undirected.degree(node) if node in G_undirected else 0
            # Ensure we have at least 0 as a community ID
            community_id = max(0, node_degree) % 8  # Using modulo 8 to limit number of colors
            node_communities[node] = community_id
        community_count = len(set(node_communities.values()))
        print(f"Using degree-based communities ({community_count} communities)")
        return node_communities, community_count

def _calculate_node_sizes(all_nodes, betweenness, degree, eigenvector):
    """Calculate node sizes based on centrality metrics."""
    # Find max values for normalization
    max_betweenness = max(betweenness.values()) if betweenness else 1
    max_degree = max(degree.values()) if degree else 1
    max_eigenvector = max(eigenvector.values()) if eigenvector else 1
    
    node_sizes = {}
    for node in all_nodes:
        # Normalize and combine metrics with weights
        degree_norm = degree.get(node, 1) / max_degree
        betweenness_norm = betweenness.get(node, 0) / max_betweenness if max_betweenness > 0 else 0
        eigenvector_norm = eigenvector.get(node, 0) / max_eigenvector if max_eigenvector > 0 else 0
        
        # Calculate a weighted importance score (adjust weights as needed)
        importance = 0.5 * degree_norm + 0.3 * betweenness_norm + 0.2 * eigenvector_norm
        
        # Scale node size - ensure minimum size and reasonable maximum
        node_sizes[node] = 10 + (20 * importance)  # Size range from 10 to 30
    
    return node_sizes

def _add_nodes_and_edges_to_network(net, G):
    """Add nodes and edges from NetworkX graph to PyVis network."""
    # Add nodes with all their attributes
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        net.add_node(
            node_id, 
            color=node_data.get('color', '#4daf4a'),
            label=str(node_id),  # Ensure label is a string
            title=str(node_data.get('title', node_id)),  # Ensure title is a string
            shape="dot",
            size=node_data.get('size', 10),
            font={'color': '#000000'}  # Explicitly set font color to black
        )
    
    # Add edges with all their attributes
    for edge in G.edges(data=True):
        source, target, data = edge
        
        # Support for dashed lines for inferred relationships
        edge_options = {
            'title': data.get('title', ''),
            'label': data.get('label', ''),
            'arrows': "to"
        }
        
        # Add dashes if specified
        if data.get('dashes', False):
            edge_options['dashes'] = True
        
        # Add color if specified
        if data.get('color'):
            edge_options['color'] = data.get('color')
        
        net.add_edge(source, target, **edge_options)

def _get_visualization_options(nodes_count, edges_count):
    """
    Get visualization options for the network graph.
    
    Args:
        nodes_count (int): Number of nodes in the network
        edges_count (int): Number of edges in the network
        
    Returns:
        dict: Network visualization options
    """
    # Get adaptive physics settings based on network size
    physics_settings = _get_adaptive_physics_settings(nodes_count, edges_count)
    
    return {
        "physics": physics_settings,
        "edges": {
            "color": {"inherit": True},
            "font": {"size": 11},
            "smooth": False,  # Straight lines for better performance
            "width": 1.5,  # Slightly thicker default edges
            "selectionWidth": 2  # Width when selected
        },
        "nodes": {
            "font": {
                "size": 14,
                "face": "Tahoma"
            },
            "scaling": {
                "min": 10,
                "max": 50
            },
            "shape": "dot",  # Consistent shape
            "margin": 10,  # Add some margin around node labels
            "tooltipDelay": 200,
            "borderWidth": 2,
            "borderWidthSelected": 3
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
            "tooltipDelay": 200,
            "zoomView": True,
            "dragView": True
        },
        "layout": {
            "improvedLayout": True,
            "hierarchical": {
                "enabled": False,  # We'll use force-directed by default
                "sortMethod": "directed"  # But keep this ready for hierarchical option
            }
        }
    }

def _save_and_modify_html(net, output_file, community_count, all_nodes, triples):
    """Save the network as HTML and modify with custom template."""
    # Instead of letting PyVis write to a file, we'll access its HTML directly
    # and write it ourselves with explicit UTF-8 encoding
    
    # Generate the HTML content
    # This happens internally in PyVis without writing to a file
    net.generate_html()
    
    # Get the HTML from PyVis's internal html attribute
    html = net.html
    
    # Add our custom controls by replacing the div with our template
    html = html.replace('<div id="mynetwork" class="card-body"></div>', _load_html_template())
    
    # Fix the duplicate title issue
    # Remove the default PyVis header
    html = re.sub(r'<center>\s*<h1>.*?</h1>\s*</center>', '', html)
    
    # Replace the other h1 with our enhanced title
    html = html.replace('<h1></h1>', f'<h1>Knowledge Graph - {len(all_nodes)} Nodes, {len(triples)} Relationships, {community_count} Communities</h1>')
    
    # Write the HTML directly to the output file with explicit UTF-8 encoding
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Knowledge graph visualization saved to {output_file}")

def sample_data_visualization(output_file="sample_knowledge_graph.html", edge_smooth=None, config=None):
    """
    Generate a visualization using sample data to test the functionality.
    
    Args:
        output_file: Path to save the sample graph HTML
        edge_smooth: Edge smoothing setting (overrides config): 
                    false, "dynamic", "continuous", "discrete", "diagonalCross", 
                    "straightCross", "horizontal", "vertical", "curvedCW", "curvedCCW", "cubicBezier"
        config: Configuration dictionary (optional)
    """
    # Sample data representing knowledge graph triples
    sample_triples = [
        {"subject": "Industrial Revolution", "predicate": "began in", "object": "Great Britain"},
        {"subject": "Industrial Revolution", "predicate": "characterized by", "object": "machine manufacturing"},
        {"subject": "Industrial Revolution", "predicate": "led to", "object": "urbanization"},
        {"subject": "Industrial Revolution", "predicate": "led to", "object": "rise of capitalism"},
        {"subject": "Industrial Revolution", "predicate": "led to", "object": "new labor movements"},
        {"subject": "Industrial Revolution", "predicate": "fueled by", "object": "technological innovations"},
        {"subject": "James Watt", "predicate": "developed", "object": "steam engine"},
        {"subject": "James Watt", "predicate": "born in", "object": "Scottland"},
        {"subject": "Scottland", "predicate": "a country in", "object": "Europe"},
        {"subject": "steam engine", "predicate": "revolutionized", "object": "transportation"},
        {"subject": "steam engine", "predicate": "revolutionized", "object": "manufacturing processes"},
        {"subject": "steam engine", "predicate": "spread to", "object": "Europe"},
        {"subject": "steam engine", "predicate": "lead to", "object": "Industrial Revolution"},
        {"subject": "steam engine", "predicate": "spread to", "object": "North America"},
        {"subject": "technological innovations", "predicate": "led to", "object": "Digital Computers"},
        {"subject": "Digital Computers", "predicate": "enabled", "object": "Artificial Intelligence"},
        {"subject": "Artificial Intelligence", "predicate": "will replace", "object": "Humanity"},
        {"subject": "Artificial Intelligence", "predicate": "led to", "object": "LLMs"},
        {"subject": "Robert McDermott", "predicate": "likes", "object": "LLMs"},
        {"subject": "Robert McDermott", "predicate": "owns", "object": "Digital Computers"},
        {"subject": "Robert McDermott", "predicate": "lives in", "object": "North America"}
    ]
    
    # Determine edge smoothing from config if not explicitly provided
    if edge_smooth is None and config is not None:
        edge_smooth = config.get("visualization", {}).get("edge_smooth", False)
    elif edge_smooth is None:
        edge_smooth = False
    
    # Generate the visualization
    print(f"Generating sample visualization with {len(sample_triples)} triples")
    
    # Display edge smoothing type
    if edge_smooth is False:
        edge_style = "Straight (no smoothing)"
    elif isinstance(edge_smooth, str):
        edge_style = edge_smooth
    else:
        edge_style = "continuous (default curved)"
    
    print(f"Edge style: {edge_style}")
    stats = visualize_knowledge_graph(sample_triples, output_file, edge_smooth=edge_smooth, config=config)
    
    print("\nSample Knowledge Graph Statistics:")
    print(f"Nodes: {stats['nodes']}")
    print(f"Edges: {stats['edges']}")
    print(f"Communities: {stats['communities']}")
    
    print(f"\nVisualization saved to {output_file}")
    print(f"To view, open: file://{os.path.abspath(output_file)}") 

if __name__ == "__main__":
    # Run sample visualization when this module is run directly
    from src.knowledge_graph.config import load_config
    
    # Try to load config, fall back to defaults if not found
    config = load_config()
    if config is None:
        config = {"visualization": {"edge_smooth": False}}
        print("No config.toml found, using default settings")
    
    # Create sample visualizations with different edge types
    examples = [
        ("sample_knowledge_graph_straight.html", False, "Straight edges (no smoothing)"),
        ("sample_knowledge_graph_curvedCW.html", "curvedCW", "Curved clockwise"),
        ("sample_knowledge_graph_curvedCCW.html", "curvedCCW", "Curved counter-clockwise"),
        ("sample_knowledge_graph_dynamic.html", "dynamic", "Dynamic edges"),
        ("sample_knowledge_graph_cubicBezier.html", "cubicBezier", "Cubic Bezier curves"),
    ]
    
    # Create example visualizations
    for filename, edge_type, description in examples:
        print(f"\nCreating visualization with {description}...")
        config_example = {"visualization": {"edge_smooth": edge_type}}
        sample_data_visualization(filename, config=config_example)
    
    # Create visualization using config.toml settings
    print("\nCreating visualization using configuration from config.toml...")
    sample_data_visualization("sample_knowledge_graph_config.html", config=config)
    
    # Determine edge style from config for output message
    config_edge_type = config.get("visualization", {}).get("edge_smooth", False)
    if config_edge_type is False:
        config_description = "straight edges (no smoothing)"
    else:
        config_description = f"edge style '{config_edge_type}'"
    
    print(f"\nCreated sample visualizations:")
    for filename, _, description in examples:
        print(f"- {filename}: {description}")
    print(f"- sample_knowledge_graph_config.html: Using {config_description} from config.toml")
    print("\nTo view these visualizations, open the HTML files in your browser.")

def _process_triples(triples, G):
    """处理三元组并添加到图中"""
    # 用于存储节点颜色的字典
    node_colors = {}
    edge_colors = {}
    
    for triple in triples:
        subj = triple['subject']
        pred = triple['predicate']
        obj = triple['object']
        
        # 如果是新节点，随机分配颜色
        for node in [subj, obj]:
            if node not in node_colors:
                # 使用预定义的柔和色彩
                colors = ['#7FDBFF', '#B10DC9', '#39CCCC', '#01FF70', '#FF4136', '#F012BE', 
                         '#3D9970', '#AAAAAA', '#FFB6C1', '#20B2AA']
                node_colors[node] = colors[len(node_colors) % len(colors)]
        
        # 添加节点和边
        G.add_node(subj, color=node_colors[subj], title=f"实体: {subj}")
        G.add_node(obj, color=node_colors[obj], title=f"实体: {obj}")
        
        # 确定边的样式
        edge_style = 'solid'  # 默认样式
        if 'inferred' in triple and triple['inferred']:
            edge_style = 'dashed'
        
        # 添加边，使用谓词作为标签
        G.add_edge(subj, obj, title=pred, label=pred, style=edge_style)

def _apply_community_colors(G):
    """应用社区检测和颜色"""
    try:
        import community
        
        # 使用 Louvain 方法进行社区检测
        communities = community.best_partition(G.to_undirected())
        
        # 为每个社区分配不同的颜色
        community_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
                          '#D4A5A5', '#9B59B6', '#3498DB', '#E67E22', '#2ECC71']
        
        # 更新节点颜色
        for node in G.nodes():
            community_id = communities[node]
            color = community_colors[community_id % len(community_colors)]
            G.nodes[node]['color'] = color
            
    except ImportError:
        print("Note: community detection package not found. Using default colors.")

def _get_adaptive_physics_settings(nodes_count, edges_count):
    """
    Returns optimized physics settings based on network size.
    
    Args:
        nodes_count (int): Number of nodes in the network
        edges_count (int): Number of edges in the network
        
    Returns:
        dict: Physics configuration options
    """
    # Base settings for small networks
    settings = {
        "enabled": True,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
            "gravitationalConstant": -50,
            "centralGravity": 0.01,
            "springLength": 100,
            "springConstant": 0.08,
        },
        "stabilization": {
            "enabled": True,
            "iterations": 200
        }
    }
    
    # Adjust settings for larger networks
    if nodes_count > 100:
        settings["forceAtlas2Based"].update({
            "gravitationalConstant": -80,
            "centralGravity": 0.02,
            "springLength": 150,
            "springConstant": 0.05
        })
        settings["stabilization"]["iterations"] = 300
        
    if nodes_count > 200:
        settings["solver"] = "barnesHut"
        settings["barnesHut"] = {
            "gravitationalConstant": -8000,
            "centralGravity": 0.3,
            "springLength": 250,
            "springConstant": 0.04,
            "damping": 0.09
        }
        settings["stabilization"]["iterations"] = 500
    
    if edges_count / max(nodes_count, 1) > 5:  # Dense networks
        if settings["solver"] == "forceAtlas2Based":
            settings["forceAtlas2Based"]["springLength"] *= 1.5
        else:
            settings["barnesHut"]["springLength"] *= 1.5
    
    return settings