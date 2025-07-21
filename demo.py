"""
Example usage of the Code Migration Graphs framework
"""

from codegraphs import (
    CodeDependencyGraph, JavaFileNode, PythonFileNode, CSharpFileNode,
    DependencyStatement, DependencyLink, DependencyType, Language
)


def demo_basic_usage():
    """Demonstrate basic usage of the framework"""
    print("=== Code Migration Graphs Demo ===\n")
    
    # Create a new graph
    graph = CodeDependencyGraph("DemoProject")
    
    # Create some Java files
    print("Creating Java files...")
    user_service = JavaFileNode("src/main/java/UserService.java", "UserService.java", "com.demo.service")
    user_service.add_class("UserService", "public")
    user_service.add_class("UserValidator", "package-private")
    
    user_model = JavaFileNode("src/main/java/User.java", "User.java", "com.demo.model")
    user_model.add_class("User", "public")
    
    # Create a Python file
    print("Creating Python file...")
    utils = PythonFileNode("src/utils.py", "utils.py", "demo.utils")
    utils.add_function("validate_email")
    utils.add_function("hash_password")
    utils.add_class("ValidationError")
    
    # Create a C# file
    print("Creating C# file...")
    controller = CSharpFileNode("Controllers/UserController.cs", "UserController.cs", "Demo.Controllers")
    controller.add_class("UserController", "public")
    
    # Add nodes to graph
    graph.add_node(user_service)
    graph.add_node(user_model)
    graph.add_node(utils)
    graph.add_node(controller)
    
    print(f"Added {len(graph.nodes)} nodes to the graph")
    
    # Create dependencies
    print("\nCreating dependencies...")
    
    # UserService depends on User model
    dep1 = DependencyStatement("com.demo.model.User", "import", line_number=5)
    user_service.add_dependency(dep1)
    
    link1 = DependencyLink(
        source_node_id=user_service.unique_id,
        target_node_id=user_model.unique_id,
        dependency_type=DependencyType.INTRINSIC_IMPORT,
        dependency_statements=[dep1],
        weight=1.0
    )
    graph.add_link(link1)
    
    # Add external dependencies
    external_deps = [
        DependencyStatement("java.util.List", "import"),
        DependencyStatement("org.springframework.stereotype.Service", "import"),
        DependencyStatement("javax.validation.constraints.NotNull", "import")
    ]
    
    for dep in external_deps:
        user_service.add_dependency(dep)
    
    print(f"Added {len(graph.links)} dependency links")
    
    # Calculate metrics
    print("\n=== Graph Analysis ===")
    metrics = graph.calculate_metrics()
    
    print(f"Number of files: {metrics['num_nodes']}")
    print(f"Number of dependencies: {metrics['num_edges']}")
    print(f"Graph density: {metrics['density']:.3f}")
    print(f"Is DAG (no cycles): {metrics['is_dag']}")
    print(f"Connected components: {metrics['num_weakly_connected_components']}")
    
    # Show file details
    print("\n=== File Details ===")
    for node_id, node in graph.nodes.items():
        print(f"\n{node.file_name} ({node.language.value})")
        print(f"  Package/Module: {node.container_name}")
        print(f"  Exports: {list(node.exports)}")
        print(f"  Dependencies: {len(node.dependency_statements)}")
        
        # Show language-specific info
        lang_info = node.get_language_specific_info()
        for key, value in lang_info.items():
            if value:
                print(f"  {key.title()}: {value}")
    
    # Demonstrate filtering
    print("\n=== Language Filtering ===")
    java_graph = graph.filter_by_language(Language.JAVA)
    python_graph = graph.filter_by_language(Language.PYTHON)
    csharp_graph = graph.filter_by_language(Language.CSHARP)
    
    print(f"Java files: {len(java_graph.nodes)}")
    print(f"Python files: {len(python_graph.nodes)}")
    print(f"C# files: {len(csharp_graph.nodes)}")
    
    # Save to JSON
    print("\n=== Saving Graph ===")
    graph.save_to_json("demo_graph.json")
    print("Saved graph to: demo_graph.json")
    
    # Test loading
    loaded_graph = CodeDependencyGraph.load_from_json("demo_graph.json")
    loaded_metrics = loaded_graph.calculate_metrics()
    print(f"Loaded graph verification: {loaded_metrics['num_nodes']} nodes, {loaded_metrics['num_edges']} edges")
    
    print("\n=== Demo Complete! ===")
    return graph


def demo_dependency_analysis():
    """Demonstrate dependency analysis features"""
    print("\n=== Dependency Analysis Demo ===")
    
    # Load the sample Java codebase
    try:
        graph = CodeDependencyGraph.load_from_json("sample_java_codebase.json")
        print(f"Loaded sample codebase: {graph.name}")
        
        # Find all dependencies for a specific file
        sample_node_id = list(graph.nodes.keys())[0]
        sample_node = graph.nodes[sample_node_id]
        
        print(f"\nAnalyzing dependencies for: {sample_node.file_name}")
        
        dependencies = graph.get_dependencies(sample_node_id)
        dependents = graph.get_dependents(sample_node_id)
        
        print(f"  Depends on {len(dependencies)} files:")
        for dep_id in dependencies:
            dep_node = graph.nodes[dep_id]
            print(f"    - {dep_node.file_name}")
        
        print(f"  {len(dependents)} files depend on it:")
        for dep_id in dependents:
            dep_node = graph.nodes[dep_id]
            print(f"    - {dep_node.file_name}")
        
        # Check for cycles
        print(f"\n=== Cycle Detection ===")
        cycles = graph.detect_cycles()
        if cycles:
            print(f"Found {len(cycles)} cycles:")
            for i, cycle in enumerate(cycles, 1):
                cycle_files = [graph.nodes[node_id].file_name for node_id in cycle]
                print(f"  Cycle {i}: {' -> '.join(cycle_files)} -> {cycle_files[0]}")
        else:
            print("No cycles detected - this is a DAG (Directed Acyclic Graph)")
        
        # Package analysis
        print(f"\n=== Package Analysis ===")
        packages = {}
        for node in graph.nodes.values():
            pkg = node.container_name or "default"
            packages[pkg] = packages.get(pkg, 0) + 1
        
        for package, count in sorted(packages.items()):
            print(f"  {package}: {count} files")
        
    except FileNotFoundError:
        print("Sample codebase not found. Run generate_sample_data.py first.")


if __name__ == "__main__":
    # Run the demos
    demo_graph = demo_basic_usage()
    demo_dependency_analysis()
