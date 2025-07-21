"""
Code Migration Graphs - A framework for representing and analyzing code dependencies

This module provides an abstract framework for representing code files and their dependencies
across different programming languages using NetworkX graphs.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set, Optional, Any, Union
from enum import Enum
import networkx as nx
import json
from dataclasses import dataclass, asdict
from pathlib import Path


class DependencyType(Enum):
    """Types of dependencies between files"""
    INTRINSIC_IMPORT = "intrinsic_import"  # Same package/module/namespace
    EXTRINSIC_IMPORT = "extrinsic_import"  # External library/package
    IMPLICIT_IMPORT = "implicit_import"    # Implicit dependencies (e.g., same package in Java)
    INHERITANCE = "inheritance"            # Class inheritance
    COMPOSITION = "composition"            # Object composition
    INTERFACE_IMPLEMENTATION = "interface_implementation"  # Interface implementation


class Language(Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVA = "java"
    CSHARP = "csharp"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    CPP = "cpp"
    GO = "go"


@dataclass
class DependencyStatement:
    """Represents a dependency statement in code (import, using, include, etc.)"""
    target: str                    # What is being imported/used
    statement_type: str           # import, using, include, etc.
    alias: Optional[str] = None   # Alias if any (e.g., "import numpy as np")
    is_wildcard: bool = False     # True for wildcard imports (e.g., "import *")
    line_number: Optional[int] = None  # Line number in source file
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AbstractFileNode(ABC):
    """Abstract base class for representing a file in any programming language"""
    
    def __init__(self, 
                 file_path: str,
                 file_name: str,
                 language: Language,
                 container_name: Optional[str] = None):
        """
        Initialize a file node.
        
        Args:
            file_path: Absolute or relative path to the file
            file_name: Name of the file (e.g., "MyClass.java")
            language: Programming language of the file
            container_name: Package/module/namespace name (e.g., "com.example.models")
        """
        self.file_path = file_path
        self.file_name = file_name
        self.language = language
        self.container_name = container_name
        self.dependency_statements: List[DependencyStatement] = []
        self.exports: Set[str] = set()  # What this file exports/provides
        self.metadata: Dict[str, Any] = {}
    
    @property
    def unique_id(self) -> str:
        """Unique identifier for this file node"""
        return f"{self.language.value}:{self.file_path}"
    
    @property
    def qualified_name(self) -> str:
        """Fully qualified name including container"""
        if self.container_name:
            return f"{self.container_name}.{self.file_name}"
        return self.file_name
    
    def add_dependency(self, dependency: DependencyStatement) -> None:
        """Add a dependency statement to this file"""
        self.dependency_statements.append(dependency)
    
    def add_export(self, export_name: str) -> None:
        """Add an export/public element from this file"""
        self.exports.add(export_name)
    
    @abstractmethod
    def get_language_specific_info(self) -> Dict[str, Any]:
        """Get language-specific information about this file"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "language": self.language.value,
            "container_name": self.container_name,
            "qualified_name": self.qualified_name,
            "dependency_statements": [dep.to_dict() for dep in self.dependency_statements],
            "exports": list(self.exports),
            "metadata": self.metadata,
            "language_specific": self.get_language_specific_info()
        }


class JavaFileNode(AbstractFileNode):
    """Concrete implementation for Java files"""
    
    def __init__(self, file_path: str, file_name: str, package_name: Optional[str] = None):
        super().__init__(file_path, file_name, Language.JAVA, package_name)
        self.class_names: Set[str] = set()
        self.interface_names: Set[str] = set()
        self.access_modifiers: Dict[str, str] = {}
    
    def add_class(self, class_name: str, access_modifier: str = "package-private") -> None:
        """Add a class defined in this file"""
        self.class_names.add(class_name)
        self.access_modifiers[class_name] = access_modifier
        if access_modifier in ["public", "protected"]:
            self.add_export(class_name)
    
    def add_interface(self, interface_name: str, access_modifier: str = "package-private") -> None:
        """Add an interface defined in this file"""
        self.interface_names.add(interface_name)
        self.access_modifiers[interface_name] = access_modifier
        if access_modifier in ["public", "protected"]:
            self.add_export(interface_name)
    
    def get_language_specific_info(self) -> Dict[str, Any]:
        return {
            "package_name": self.container_name,
            "classes": list(self.class_names),
            "interfaces": list(self.interface_names),
            "access_modifiers": self.access_modifiers
        }


class PythonFileNode(AbstractFileNode):
    """Concrete implementation for Python files"""
    
    def __init__(self, file_path: str, file_name: str, module_name: Optional[str] = None):
        super().__init__(file_path, file_name, Language.PYTHON, module_name)
        self.function_names: Set[str] = set()
        self.class_names: Set[str] = set()
        self.variable_names: Set[str] = set()
        self.is_package_init = file_name == "__init__.py"
    
    def add_function(self, function_name: str, is_private: bool = False) -> None:
        """Add a function defined in this file"""
        self.function_names.add(function_name)
        if not is_private and not function_name.startswith('_'):
            self.add_export(function_name)
    
    def add_class(self, class_name: str, is_private: bool = False) -> None:
        """Add a class defined in this file"""
        self.class_names.add(class_name)
        if not is_private and not class_name.startswith('_'):
            self.add_export(class_name)
    
    def get_language_specific_info(self) -> Dict[str, Any]:
        return {
            "module_name": self.container_name,
            "functions": list(self.function_names),
            "classes": list(self.class_names),
            "variables": list(self.variable_names),
            "is_package_init": self.is_package_init
        }


class CSharpFileNode(AbstractFileNode):
    """Concrete implementation for C# files"""
    
    def __init__(self, file_path: str, file_name: str, namespace: Optional[str] = None):
        super().__init__(file_path, file_name, Language.CSHARP, namespace)
        self.class_names: Set[str] = set()
        self.interface_names: Set[str] = set()
        self.struct_names: Set[str] = set()
        self.access_modifiers: Dict[str, str] = {}
    
    def add_class(self, class_name: str, access_modifier: str = "internal") -> None:
        """Add a class defined in this file"""
        self.class_names.add(class_name)
        self.access_modifiers[class_name] = access_modifier
        if access_modifier == "public":
            self.add_export(class_name)
    
    def get_language_specific_info(self) -> Dict[str, Any]:
        return {
            "namespace": self.container_name,
            "classes": list(self.class_names),
            "interfaces": list(self.interface_names),
            "structs": list(self.struct_names),
            "access_modifiers": self.access_modifiers
        }


@dataclass
class DependencyLink:
    """Represents a dependency link between two file nodes"""
    source_node_id: str
    target_node_id: str
    dependency_type: DependencyType
    dependency_statements: List[DependencyStatement]
    weight: float = 1.0  # Strength of dependency
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "dependency_type": self.dependency_type.value,
            "dependency_statements": [stmt.to_dict() for stmt in self.dependency_statements],
            "weight": self.weight,
            "metadata": self.metadata
        }


class CodeDependencyGraph:
    """Graph representation of code dependencies using NetworkX"""
    
    def __init__(self, name: str = "CodeGraph"):
        self.name = name
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, AbstractFileNode] = {}
        self.links: Dict[str, DependencyLink] = {}  # edge_id -> DependencyLink
        self.metadata: Dict[str, Any] = {}
    
    def add_node(self, file_node: AbstractFileNode) -> None:
        """Add a file node to the graph"""
        node_id = file_node.unique_id
        self.nodes[node_id] = file_node
        
        # Add to NetworkX graph with node attributes
        self.graph.add_node(node_id, 
                           file_path=file_node.file_path,
                           file_name=file_node.file_name,
                           language=file_node.language.value,
                           container_name=file_node.container_name,
                           qualified_name=file_node.qualified_name,
                           exports=list(file_node.exports))
    
    def add_link(self, link: DependencyLink) -> None:
        """Add a dependency link between nodes"""
        if link.source_node_id not in self.nodes:
            raise ValueError(f"Source node {link.source_node_id} not found")
        if link.target_node_id not in self.nodes:
            raise ValueError(f"Target node {link.target_node_id} not found")
        
        edge_id = f"{link.source_node_id}->{link.target_node_id}"
        self.links[edge_id] = link
        
        # Add to NetworkX graph with edge attributes
        self.graph.add_edge(link.source_node_id, link.target_node_id,
                           dependency_type=link.dependency_type.value,
                           weight=link.weight,
                           edge_id=edge_id)
    
    def get_dependencies(self, node_id: str) -> List[str]:
        """Get all dependencies (outgoing edges) for a node"""
        return list(self.graph.successors(node_id))
    
    def get_dependents(self, node_id: str) -> List[str]:
        """Get all dependents (incoming edges) for a node"""
        return list(self.graph.predecessors(node_id))
    
    def get_dependency_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find dependency path between two nodes"""
        try:
            return nx.shortest_path(self.graph, source_id, target_id)
        except nx.NetworkXNoPath:
            return None
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies"""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return cycles
        except:
            return []
    
    def get_strongly_connected_components(self) -> List[List[str]]:
        """Get strongly connected components (circular dependency groups)"""
        return list(nx.strongly_connected_components(self.graph))
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate various graph metrics"""
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
            "num_weakly_connected_components": nx.number_weakly_connected_components(self.graph),
            "num_strongly_connected_components": nx.number_strongly_connected_components(self.graph),
            "cycles": len(self.detect_cycles())
        }
    
    def filter_by_language(self, language: Language) -> 'CodeDependencyGraph':
        """Create a subgraph containing only nodes of specified language"""
        filtered_graph = CodeDependencyGraph(f"{self.name}_{language.value}")
        
        for node_id, node in self.nodes.items():
            if node.language == language:
                filtered_graph.add_node(node)
        
        for link in self.links.values():
            if (link.source_node_id in filtered_graph.nodes and 
                link.target_node_id in filtered_graph.nodes):
                filtered_graph.add_link(link)
        
        return filtered_graph
    
    def filter_by_dependency_type(self, dep_type: DependencyType) -> 'CodeDependencyGraph':
        """Create a subgraph containing only specified dependency types"""
        filtered_graph = CodeDependencyGraph(f"{self.name}_{dep_type.value}")
        
        # Add all nodes
        for node in self.nodes.values():
            filtered_graph.add_node(node)
        
        # Add only links of specified type
        for link in self.links.values():
            if link.dependency_type == dep_type:
                filtered_graph.add_link(link)
        
        return filtered_graph
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization"""
        return {
            "name": self.name,
            "metadata": self.metadata,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "links": {edge_id: link.to_dict() for edge_id, link in self.links.items()},
            "metrics": self.calculate_metrics()
        }
    
    def save_to_json(self, file_path: str) -> None:
        """Save graph to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_json(cls, file_path: str) -> 'CodeDependencyGraph':
        """Load graph from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        graph = cls(data["name"])
        graph.metadata = data.get("metadata", {})
        
        # Recreate nodes
        for node_data in data["nodes"].values():
            language = Language(node_data["language"])
            
            # Create appropriate node type based on language
            if language == Language.JAVA:
                node = JavaFileNode(node_data["file_path"], 
                                  node_data["file_name"], 
                                  node_data["container_name"])
            elif language == Language.PYTHON:
                node = PythonFileNode(node_data["file_path"], 
                                    node_data["file_name"], 
                                    node_data["container_name"])
            elif language == Language.CSHARP:
                node = CSharpFileNode(node_data["file_path"], 
                                    node_data["file_name"], 
                                    node_data["container_name"])
            else:
                # Fallback - would need to implement for other languages
                continue
            
            # Restore dependency statements
            for dep_data in node_data["dependency_statements"]:
                dep = DependencyStatement(**dep_data)
                node.add_dependency(dep)
            
            # Restore exports
            for export in node_data["exports"]:
                node.add_export(export)
            
            graph.add_node(node)
        
        # Recreate links
        for link_data in data["links"].values():
            statements = [DependencyStatement(**stmt) for stmt in link_data["dependency_statements"]]
            link = DependencyLink(
                source_node_id=link_data["source_node_id"],
                target_node_id=link_data["target_node_id"],
                dependency_type=DependencyType(link_data["dependency_type"]),
                dependency_statements=statements,
                weight=link_data["weight"],
                metadata=link_data["metadata"]
            )
            graph.add_link(link)
        
        return graph


def create_file_node(file_path: str, file_name: str, language: Language, 
                    container_name: Optional[str] = None) -> AbstractFileNode:
    """Factory function to create appropriate file node based on language"""
    if language == Language.JAVA:
        return JavaFileNode(file_path, file_name, container_name)
    elif language == Language.PYTHON:
        return PythonFileNode(file_path, file_name, container_name)
    elif language == Language.CSHARP:
        return CSharpFileNode(file_path, file_name, container_name)
    else:
        raise NotImplementedError(f"Language {language} not yet implemented")