"""
Generate sample Java codebase data for testing the code dependency graph framework
"""

import random
from codegraphs import (
    CodeDependencyGraph, JavaFileNode, DependencyStatement, DependencyLink, 
    DependencyType, Language
)


def generate_sample_java_codebase():
    """Generate a sample Java codebase with 10 files and various dependencies"""
    
    # Create the main graph
    graph = CodeDependencyGraph("SampleJavaCodebase")
    graph.metadata = {
        "description": "Sample Java codebase for testing dependency analysis",
        "generated": True,
        "language": "java"
    }
    
    # Define the Java files with their packages
    files_info = [
        ("A.java", "com.example.core", ["User", "UserService"]),
        ("B.java", "com.example.core", ["Product", "ProductManager"]),
        ("C.java", "com.example.model", ["Order", "OrderItem"]),
        ("D.java", "com.example.model", ["Customer", "Address"]),
        ("E.java", "com.example.service", ["AuthenticationService"]),
        ("F.java", "com.example.service", ["PaymentService", "PaymentProcessor"]),
        ("G.java", "com.example.util", ["StringUtils", "DateUtils"]),
        ("H.java", "com.example.util", ["ValidationUtils"]),
        ("I.java", "com.example.controller", ["UserController"]),
        ("J.java", "com.example.controller", ["ProductController"])
    ]
    
    # Create file nodes
    nodes = {}
    for filename, package, classes in files_info:
        file_path = f"src/main/java/{package.replace('.', '/')}/{filename}"
        node = JavaFileNode(file_path, filename, package)
        
        # Add classes to the node
        for class_name in classes:
            access_modifier = "public" if random.random() > 0.3 else "package-private"
            node.add_class(class_name, access_modifier)
        
        nodes[filename] = node
        graph.add_node(node)
    
    # Define intrinsic dependencies (within the same codebase)
    intrinsic_dependencies = [
        ("A.java", "G.java", ["StringUtils"]),  # A depends on G
        ("A.java", "H.java", ["ValidationUtils"]),  # A depends on H
        ("B.java", "G.java", ["DateUtils"]),  # B depends on G
        ("C.java", "A.java", ["User"]),  # C depends on A
        ("C.java", "B.java", ["Product"]),  # C depends on B
        ("C.java", "D.java", ["Customer"]),  # C depends on D
        ("E.java", "A.java", ["User", "UserService"]),  # E depends on A
        ("E.java", "H.java", ["ValidationUtils"]),  # E depends on H
        ("F.java", "C.java", ["Order"]),  # F depends on C
        ("F.java", "D.java", ["Customer"]),  # F depends on D
        ("I.java", "A.java", ["User", "UserService"]),  # I depends on A
        ("I.java", "E.java", ["AuthenticationService"]),  # I depends on E
        ("J.java", "B.java", ["Product", "ProductManager"]),  # J depends on B
        ("J.java", "F.java", ["PaymentService"]),  # J depends on F
        ("D.java", "G.java", ["StringUtils"]),  # D depends on G
    ]
    
    # Add intrinsic dependency links
    for source_file, target_file, imported_classes in intrinsic_dependencies:
        source_node = nodes[source_file]
        target_node = nodes[target_file]
        
        # Create dependency statements
        statements = []
        for class_name in imported_classes:
            full_class_name = f"{target_node.container_name}.{class_name}"
            stmt = DependencyStatement(
                target=full_class_name,
                statement_type="import",
                line_number=random.randint(1, 10)
            )
            statements.append(stmt)
            source_node.add_dependency(stmt)
        
        # Create dependency link
        link = DependencyLink(
            source_node_id=source_node.unique_id,
            target_node_id=target_node.unique_id,
            dependency_type=DependencyType.INTRINSIC_IMPORT,
            dependency_statements=statements,
            weight=len(imported_classes)
        )
        
        graph.add_link(link)
    
    # Define external dependencies (external libraries)
    external_libraries = [
        "java.util.List",
        "java.util.Map",
        "java.util.ArrayList",
        "java.util.HashMap",
        "java.time.LocalDateTime",
        "java.math.BigDecimal",
        "org.springframework.stereotype.Service",
        "org.springframework.web.bind.annotation.RestController",
        "org.springframework.web.bind.annotation.GetMapping",
        "com.fasterxml.jackson.annotation.JsonProperty",
        "javax.validation.constraints.NotNull",
        "lombok.Data",
        "lombok.AllArgsConstructor"
    ]
    
    # Add external dependencies randomly
    for filename, node in nodes.items():
        # Each file gets 2-5 external dependencies
        num_external_deps = random.randint(2, 5)
        selected_externals = random.sample(external_libraries, num_external_deps)
        
        for external_dep in selected_externals:
            stmt = DependencyStatement(
                target=external_dep,
                statement_type="import",
                line_number=random.randint(1, 15)
            )
            node.add_dependency(stmt)
    
    return graph


def add_some_circular_dependencies(graph: CodeDependencyGraph):
    """Add a few circular dependencies to make the graph more interesting"""
    
    # Get some nodes for creating cycles
    node_ids = list(graph.nodes.keys())
    
    if len(node_ids) >= 3:
        # Create a small cycle: G -> H -> G (utility classes depending on each other)
        g_node_id = next((nid for nid in node_ids if "G.java" in nid), None)
        h_node_id = next((nid for nid in node_ids if "H.java" in nid), None)
        
        if g_node_id and h_node_id:
            # G depends on H (already exists), now add H depends on G
            h_node = graph.nodes[h_node_id]
            g_node = graph.nodes[g_node_id]
            
            stmt = DependencyStatement(
                target=f"{g_node.container_name}.StringUtils",
                statement_type="import",
                line_number=8
            )
            h_node.add_dependency(stmt)
            
            link = DependencyLink(
                source_node_id=h_node_id,
                target_node_id=g_node_id,
                dependency_type=DependencyType.INTRINSIC_IMPORT,
                dependency_statements=[stmt],
                weight=1.0
            )
            
            graph.add_link(link)


def main():
    """Generate sample data and save to JSON"""
    print("Generating sample Java codebase...")
    
    # Generate the sample codebase
    graph = generate_sample_java_codebase()
    
    # Add some circular dependencies for testing
    add_some_circular_dependencies(graph)
    
    # Print some statistics
    metrics = graph.calculate_metrics()
    print(f"\nGenerated codebase statistics:")
    print(f"- Number of files: {metrics['num_nodes']}")
    print(f"- Number of dependencies: {metrics['num_edges']}")
    print(f"- Graph density: {metrics['density']:.3f}")
    print(f"- Is DAG (no cycles): {metrics['is_dag']}")
    print(f"- Number of cycles: {metrics['cycles']}")
    
    # Detect and print cycles
    cycles = graph.detect_cycles()
    if cycles:
        print(f"\nDetected cycles:")
        for i, cycle in enumerate(cycles, 1):
            cycle_files = [graph.nodes[node_id].file_name for node_id in cycle]
            print(f"  Cycle {i}: {' -> '.join(cycle_files)} -> {cycle_files[0]}")
    
    # Save to JSON
    output_file = "sample_java_codebase.json"
    graph.save_to_json(output_file)
    print(f"\nSample codebase saved to: {output_file}")
    
    # Test loading the graph back
    print("\nTesting graph loading from JSON...")
    loaded_graph = CodeDependencyGraph.load_from_json(output_file)
    loaded_metrics = loaded_graph.calculate_metrics()
    print(f"Loaded graph has {loaded_metrics['num_nodes']} nodes and {loaded_metrics['num_edges']} edges")
    
    print("\nSample data generation complete!")


if __name__ == "__main__":
    main()
