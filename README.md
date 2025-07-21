# Code Migration Graphs

A comprehensive framework for representing and analyzing code dependencies across different programming languages using NetworkX and Plotly.

## Features

- **Abstract File Node System**: Language-agnostic representation of code files with support for Java, Python, C#, and extensible to other languages
- **Dependency Analysis**: Track imports, using statements, includes, and other dependency types
- **Graph Visualization**: Interactive visualizations using Plotly with multiple layout options
- **Metrics Dashboard**: Comprehensive analysis of code dependencies, cycles, and complexity
- **JSON Export/Import**: Serialize and deserialize dependency graphs for persistence

## Project Structure

### Core Classes

1. **AbstractFileNode**: Base class for representing files in any programming language
   - `JavaFileNode`: Java-specific implementation with package support
   - `PythonFileNode`: Python-specific implementation with module support  
   - `CSharpFileNode`: C#-specific implementation with namespace support

2. **DependencyStatement**: Represents individual dependency statements (import, using, etc.)

3. **DependencyLink**: Represents relationships between files with typing:
   - `INTRINSIC_IMPORT`: Dependencies within the same codebase
   - `EXTRINSIC_IMPORT`: External library dependencies
   - `IMPLICIT_IMPORT`: Implicit dependencies (e.g., same package in Java)
   - `INHERITANCE`: Class inheritance relationships
   - `COMPOSITION`: Object composition relationships
   - `INTERFACE_IMPLEMENTATION`: Interface implementations

4. **CodeDependencyGraph**: Main graph class using NetworkX
   - Cycle detection
   - Dependency path analysis
   - Graph metrics calculation
   - Filtering by language or dependency type

### Utility Scripts

- `generate_sample_data.py`: Creates sample Java codebase with 10 interconnected files
- `visualize_graphs.py`: Creates interactive Plotly visualizations

## Usage

### 1. Generate Sample Data

```bash
python generate_sample_data.py
```

This creates `sample_java_codebase.json` with a simulated Java project containing:
- 10 Java files (A.java through J.java)
- Various packages: `com.example.core`, `com.example.model`, `com.example.service`, etc.
- Intrinsic dependencies between files
- External library dependencies

### 2. Create Visualizations

```bash
python visualize_graphs.py
```

This generates several HTML files:
- `dependency_network.html`: Main dependency network visualization
- `metrics_dashboard.html`: Comprehensive metrics and analysis dashboard
- `dependency_network_circular.html`: Circular layout
- Additional layout variations

### 3. Programmatic Usage

```python
from codegraphs import CodeDependencyGraph, JavaFileNode, DependencyStatement, DependencyLink, DependencyType

# Create a new graph
graph = CodeDependencyGraph("MyProject")

# Create file nodes
file_a = JavaFileNode("src/main/java/A.java", "A.java", "com.example")
file_b = JavaFileNode("src/main/java/B.java", "B.java", "com.example")

# Add classes
file_a.add_class("ClassA", "public")
file_b.add_class("ClassB", "public")

# Add to graph
graph.add_node(file_a)
graph.add_node(file_b)

# Create dependency
dep_stmt = DependencyStatement("com.example.ClassB", "import")
file_a.add_dependency(dep_stmt)

link = DependencyLink(
    source_node_id=file_a.unique_id,
    target_node_id=file_b.unique_id,
    dependency_type=DependencyType.INTRINSIC_IMPORT,
    dependency_statements=[dep_stmt]
)

graph.add_link(link)

# Analyze
metrics = graph.calculate_metrics()
cycles = graph.detect_cycles()

# Save/Load
graph.save_to_json("my_graph.json")
loaded_graph = CodeDependencyGraph.load_from_json("my_graph.json")
```

## Sample Output

The generated sample data includes:

**Files**: 10 Java files across multiple packages
**Dependencies**: 16 intrinsic dependencies plus external library imports
**Packages**: 
- `com.example.core` (User management)
- `com.example.model` (Data models)
- `com.example.service` (Business logic)
- `com.example.util` (Utilities)
- `com.example.controller` (Web controllers)

**Metrics**:
- Graph density: ~0.178
- Detects circular dependencies
- Strongly connected components analysis
- Package-level dependency distribution

## Extending the Framework

### Adding New Languages

```python
class GoFileNode(AbstractFileNode):
    def __init__(self, file_path: str, file_name: str, package_name: str = None):
        super().__init__(file_path, file_name, Language.GO, package_name)
        self.functions = set()
        self.structs = set()
    
    def get_language_specific_info(self) -> Dict[str, Any]:
        return {
            "package_name": self.container_name,
            "functions": list(self.functions),
            "structs": list(self.structs)
        }
```

### Custom Dependency Types

```python
class CustomDependencyType(Enum):
    DATABASE_DEPENDENCY = "database_dependency"
    CONFIG_DEPENDENCY = "config_dependency"
    RESOURCE_DEPENDENCY = "resource_dependency"
```

## Dependencies

- `networkx`: Graph data structures and algorithms
- `plotly`: Interactive visualizations
- `json`: Data serialization
- `typing`: Type hints
- `dataclasses`: Data structures
- `pathlib`: File path handling

## Visualization Features

- **Interactive Network Graphs**: Hover information, zoom, pan
- **Multiple Layouts**: Spring, circular, Kamada-Kawai, planar
- **Color Coding**: Packages/namespaces and dependency types
- **Metrics Dashboard**: Graph statistics, dependency distribution, cycle analysis
- **Filtering Options**: By language, dependency type, package

Open the generated HTML files in your browser to explore the interactive visualizations!
