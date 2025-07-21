"""
Visualize code dependency graphs using Plotly
"""

import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import math
from typing import Dict, List, Tuple, Any
from codegraphs import CodeDependencyGraph, DependencyType


class GraphVisualizer:
    """Visualize code dependency graphs using Plotly"""
    
    def __init__(self, graph: CodeDependencyGraph):
        self.graph = graph
        self.nx_graph = graph.graph
        self.node_colors = self._assign_node_colors()
        self.edge_colors = self._assign_edge_colors()
    
    def _assign_node_colors(self) -> Dict[str, str]:
        """Assign colors based on package/namespace"""
        colors = {}
        unique_containers = set()
        
        for node_id, node in self.graph.nodes.items():
            container = node.container_name or "default"
            unique_containers.add(container)
        
        # Generate color palette
        color_palette = px.colors.qualitative.Set3
        container_colors = {}
        for i, container in enumerate(sorted(unique_containers)):
            container_colors[container] = color_palette[i % len(color_palette)]
        
        for node_id, node in self.graph.nodes.items():
            container = node.container_name or "default"
            colors[node_id] = container_colors[container]
        
        return colors
    
    def _assign_edge_colors(self) -> Dict[str, str]:
        """Assign colors based on dependency type"""
        type_colors = {
            DependencyType.INTRINSIC_IMPORT: "#2E86AB",
            DependencyType.EXTRINSIC_IMPORT: "#A23B72",
            DependencyType.IMPLICIT_IMPORT: "#F18F01", 
            DependencyType.INHERITANCE: "#C73E1D",
            DependencyType.COMPOSITION: "#592E83",
            DependencyType.INTERFACE_IMPLEMENTATION: "#048A81"
        }
        
        colors = {}
        for edge_id, link in self.graph.links.items():
            colors[edge_id] = type_colors.get(link.dependency_type, "#666666")
        
        return colors
    
    def create_network_layout(self, layout_type: str = "spring") -> Dict[str, Tuple[float, float]]:
        """Create node positions using NetworkX layouts"""
        if layout_type == "spring":
            pos = nx.spring_layout(self.nx_graph, k=2, iterations=50)
        elif layout_type == "circular":
            pos = nx.circular_layout(self.nx_graph)
        elif layout_type == "kamada_kawai":
            pos = nx.kamada_kawai_layout(self.nx_graph)
        elif layout_type == "planar":
            try:
                pos = nx.planar_layout(self.nx_graph)
            except:
                pos = nx.spring_layout(self.nx_graph)
        else:
            pos = nx.spring_layout(self.nx_graph)
        
        return pos
    
    def visualize_network(self, layout_type: str = "spring", 
                         show_labels: bool = True,
                         show_external_deps: bool = False,
                         title: str = None) -> go.Figure:
        """Create an interactive network visualization"""
        
        # Filter graph if needed
        if not show_external_deps:
            # Create a subgraph with only intrinsic dependencies
            filtered_graph = self.graph.filter_by_dependency_type(DependencyType.INTRINSIC_IMPORT)
            nx_graph = filtered_graph.graph
            nodes = filtered_graph.nodes
            links = filtered_graph.links
        else:
            nx_graph = self.nx_graph
            nodes = self.graph.nodes
            links = self.graph.links
        
        # Get layout positions
        pos = self.create_network_layout(layout_type) if nx_graph.number_of_nodes() > 0 else {}
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_colors_list = []
        node_sizes = []
        hover_text = []
        
        for node_id in nx_graph.nodes():
            if node_id in pos:
                x, y = pos[node_id]
                node_x.append(x)
                node_y.append(y)
                
                node = nodes[node_id]
                node_text.append(node.file_name)
                node_colors_list.append(self.node_colors.get(node_id, "#999999"))
                
                # Node size based on number of dependencies
                num_deps = len(list(nx_graph.successors(node_id)))
                node_sizes.append(max(20, min(60, 20 + num_deps * 5)))
                
                # Hover information
                hover_info = f"""
                <b>{node.file_name}</b><br>
                Package: {node.container_name or 'None'}<br>
                Language: {node.language.value}<br>
                Dependencies: {num_deps}<br>
                Dependents: {len(list(nx_graph.predecessors(node_id)))}<br>
                Exports: {len(node.exports)}
                """
                hover_text.append(hover_info)
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in nx_graph.edges():
            if edge[0] in pos and edge[1] in pos:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                
                # Edge information
                edge_id = f"{edge[0]}->{edge[1]}"
                if edge_id in links:
                    link = links[edge_id]
                    source_file = nodes[edge[0]].file_name
                    target_file = nodes[edge[1]].file_name
                    edge_info.append(f"{source_file} → {target_file}")
        
        # Create the figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines',
            name='Dependencies'
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text' if show_labels else 'markers',
            marker=dict(
                size=node_sizes,
                color=node_colors_list,
                line=dict(width=1, color='white'),
                opacity=0.8
            ),
            text=node_text if show_labels else None,
            textposition="middle center" if show_labels else None,
            textfont=dict(size=10, color='black'),
            hovertext=hover_text,
            hoverinfo='text',
            name='Files'
        ))
        
        # Update layout
        fig.update_layout(
            title=dict(text=title or f"Code Dependency Graph: {self.graph.name}", font=dict(size=16)),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text=f"Nodes: {len(node_x)} | Edges: {len(edge_info)} | Layout: {layout_type}",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='#666666', size=12)
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        return fig
    
    def create_metrics_dashboard(self) -> go.Figure:
        """Create a dashboard with various graph metrics"""
        
        metrics = self.graph.calculate_metrics()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Graph Overview', 'Dependency Distribution', 
                          'Package Distribution', 'Cycle Analysis'),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Graph overview metrics
        overview_data = [
            ['Nodes', metrics['num_nodes']],
            ['Edges', metrics['num_edges']], 
            ['Density', round(metrics['density'], 3)],
            ['Components', metrics['num_weakly_connected_components']]
        ]
        
        fig.add_trace(
            go.Bar(x=[item[0] for item in overview_data], 
                   y=[item[1] for item in overview_data],
                   marker_color='lightblue',
                   name='Metrics'),
            row=1, col=1
        )
        
        # Dependency type distribution
        dep_counts = {}
        for link in self.graph.links.values():
            dep_type = link.dependency_type.value.replace('_', ' ').title()
            dep_counts[dep_type] = dep_counts.get(dep_type, 0) + 1
        
        if dep_counts:
            fig.add_trace(
                go.Pie(labels=list(dep_counts.keys()), 
                       values=list(dep_counts.values()),
                       name="Dependencies"),
                row=1, col=2
            )
        
        # Package/namespace distribution
        package_counts = {}
        for node in self.graph.nodes.values():
            package = node.container_name or 'default'
            package_counts[package] = package_counts.get(package, 0) + 1
        
        fig.add_trace(
            go.Bar(x=list(package_counts.keys()), 
                   y=list(package_counts.values()),
                   marker_color='lightgreen',
                   name='Packages'),
            row=2, col=1
        )
        
        # Cycle analysis
        cycles = self.graph.detect_cycles()
        cycle_lengths = [len(cycle) for cycle in cycles]
        if cycle_lengths:
            from collections import Counter
            length_counts = Counter(cycle_lengths)
            fig.add_trace(
                go.Bar(x=list(length_counts.keys()), 
                       y=list(length_counts.values()),
                       marker_color='lightcoral',
                       name='Cycle Lengths'),
                row=2, col=2
            )
        else:
            fig.add_trace(
                go.Bar(x=['No Cycles'], y=[0],
                       marker_color='lightgray',
                       name='No Cycles'),
                row=2, col=2
            )
        
        fig.update_layout(
            title_text=f"Dependency Analysis Dashboard: {self.graph.name}",
            showlegend=False,
            height=700
        )
        
        return fig
    
    def save_visualization(self, filename: str, fig: go.Figure, 
                          format: str = "html") -> None:
        """Save visualization to file"""
        if format.lower() == "html":
            fig.write_html(filename)
        elif format.lower() == "png":
            fig.write_image(filename)
        elif format.lower() == "pdf":
            fig.write_image(filename)
        elif format.lower() == "svg":
            fig.write_image(filename)
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    """Load sample data and create visualizations"""
    print("Loading sample Java codebase...")
    
    # Load the graph from JSON
    try:
        graph = CodeDependencyGraph.load_from_json("sample_java_codebase.json")
        print(f"Loaded graph: {graph.name}")
        
        # Create visualizer
        visualizer = GraphVisualizer(graph)
        
        # Create network visualization
        print("Creating network visualization...")
        network_fig = visualizer.visualize_network(
            layout_type="spring",
            show_labels=True,
            show_external_deps=False,
            title="Java Codebase Dependency Network"
        )
        
        # Save network visualization
        visualizer.save_visualization("dependency_network.html", network_fig)
        print("Saved: dependency_network.html")
        
        # Create metrics dashboard
        print("Creating metrics dashboard...")
        metrics_fig = visualizer.create_metrics_dashboard()
        
        # Save metrics dashboard
        visualizer.save_visualization("metrics_dashboard.html", metrics_fig)
        print("Saved: metrics_dashboard.html")
        
        # Create different layouts
        layouts = ["circular", "kamada_kawai", "planar"]
        for layout in layouts:
            print(f"Creating {layout} layout...")
            fig = visualizer.visualize_network(
                layout_type=layout,
                show_labels=True,
                title=f"Dependency Network - {layout.title()} Layout"
            )
            filename = f"dependency_network_{layout}.html"
            visualizer.save_visualization(filename, fig)
            print(f"Saved: {filename}")
        
        print("\nVisualization complete! Open the HTML files in your browser to view the graphs.")
        
        # Print some statistics
        metrics = graph.calculate_metrics()
        print(f"\nGraph Statistics:")
        print(f"- Files: {metrics['num_nodes']}")
        print(f"- Dependencies: {metrics['num_edges']}")
        print(f"- Density: {metrics['density']:.3f}")
        print(f"- Has cycles: {not metrics['is_dag']}")
        print(f"- Cycle count: {metrics['cycles']}")
        
    except FileNotFoundError:
        print("Error: sample_java_codebase.json not found.")
        print("Please run generate_sample_data.py first to create the sample data.")
    except Exception as e:
        print(f"Error loading or visualizing graph: {e}")


if __name__ == "__main__":
    main()
