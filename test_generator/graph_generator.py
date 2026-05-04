"""Graph generator: Create mermaid control flow diagrams for each tested method."""

import os
import shutil
from typing import Dict, List, Set
from test_generator.code_analyzer import ClassAnalysis, MethodAnalysis, ControlFlowElement


class GraphGenerator:
    """Generate per-method mermaid control flow diagrams for tested methods only."""
    
    def __init__(self, class_analysis: ClassAnalysis, tested_methods: Set[str], output_dir: str = "tests/control_flow_graphs"):
        """
        Initialize graph generator.
        
        Args:
            class_analysis: ClassAnalysis object from code analyzer
            tested_methods: Set of method names that have tests
            output_dir: Directory to save generated graph files
        """
        self.class_analysis = class_analysis
        self.tested_methods = tested_methods
        self.output_dir = output_dir
        
        # Clean and recreate output directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_all_graphs(self) -> Dict[str, str]:
        """Generate graphs only for tested methods with control flow."""
        graphs = {}
        
        # Generate graphs only for methods that have tests
        for method_name in self.tested_methods:
            if method_name in self.class_analysis.methods:
                method = self.class_analysis.methods[method_name]
                if method.total_branches > 0:
                    graph = self._generate_method_graph(method)
                    graphs[method_name] = graph
        
        return graphs
    
    def save_all_graphs(self) -> Dict[str, str]:
        """Generate and save all graphs to files. Returns mapping of method names to file paths."""
        graphs = self.generate_all_graphs()
        file_paths = {}
        
        for method_name, graph_content in graphs.items():
            # Sanitize filename
            safe_name = method_name.replace('_', '_').replace(' ', '_')
            filename = f"{safe_name}_flow.md"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(graph_content)
            
            file_paths[method_name] = filepath
        
        # Generate index file
        self._generate_index(file_paths)
        
        return file_paths
    
    def _generate_method_graph(self, method: MethodAnalysis) -> str:
        """Generate mermaid flowchart for a single method."""
        lines = []
        
        # Header
        lines.append(f"# Control Flow: {method.method_name}()")
        lines.append("")
        lines.append(f"**Method:** `{method.method_name}()`")
        lines.append(f"**Lines:** {method.line_start}-{method.line_end}")
        lines.append(f"**Parameters:** {', '.join(method.parameters) if method.parameters else 'self (implicit)'}")
        lines.append(f"**Control Flow Elements:** {method.total_branches}")
        lines.append(f"**Cyclomatic Complexity:** {method.complexity}")
        lines.append("")
        
        # Mermaid diagram
        lines.append("```mermaid")
        lines.append("flowchart TD")
        lines.append("")
        
        # Generate nodes and edges
        node_id = 0
        lines.append(f"  N{node_id}([\"<b>START</b><br/>{method.method_name}()\"])")
        current_node = node_id
        node_id += 1
        
        # Add control flow elements
        for element in sorted(method.all_control_flow, key=lambda e: e.line_num):
            prev_node = current_node
            
            if element.element_type == 'if':
                # If statement: create diamond node
                condition_label = element.condition[:40] + "..." if len(element.condition) > 40 else element.condition
                lines.append(f"  N{node_id}{{\"<b>IF</b><br/>Line {element.line_num}<br/>{condition_label}\"}}")
                lines.append(f"  N{prev_node} --> N{node_id}")
                current_node = node_id
                node_id += 1
                
                # Add true/false branches with operation summaries
                true_label = element.true_summary if element.true_summary else "TRUE"
                true_label = true_label[:35] + "..." if len(true_label) > 35 else true_label
                lines.append(f'  N{node_id}["{true_label}"]')
                lines.append(f"  N{current_node} -->|true| N{node_id}")
                true_node = node_id
                node_id += 1
                
                false_label = element.false_summary if element.false_summary else "FALSE"
                false_label = false_label[:35] + "..." if len(false_label) > 35 else false_label
                lines.append(f'  N{node_id}["{false_label}"]')
                lines.append(f"  N{current_node} -->|false| N{node_id}")
                false_node = node_id
                node_id += 1
                
                # Branches converge
                lines.append(f"  N{node_id}[[\"Converge\"]]")
                lines.append(f"  N{true_node} --> N{node_id}")
                lines.append(f"  N{false_node} --> N{node_id}")
                current_node = node_id
                node_id += 1
                
            elif element.element_type == 'while':
                # While loop: create loop node
                condition_label = element.condition[:40] + "..." if len(element.condition) > 40 else element.condition
                lines.append(f"  N{node_id}{{\"<b>WHILE</b><br/>Line {element.line_num}<br/>{condition_label}\"}}")
                lines.append(f"  N{prev_node} --> N{node_id}")
                loop_node = node_id
                current_node = node_id
                node_id += 1
                
                # Loop body
                lines.append(f'  N{node_id}["Loop<br/>Body"]')
                lines.append(f"  N{loop_node} -->|true| N{node_id}")
                body_node = node_id
                node_id += 1
                
                # Loop back
                lines.append(f'  N{body_node} -."loop back".-> N{loop_node}')
                
                # Exit loop
                lines.append(f"  N{node_id}[[\"Exit Loop\"]]")
                lines.append(f"  N{loop_node} -->|false| N{node_id}")
                current_node = node_id
                node_id += 1
                
            elif element.element_type == 'for':
                # For loop: similar to while
                iter_label = element.condition[:40] + "..." if len(element.condition) > 40 else element.condition
                lines.append(f"  N{node_id}{{\"<b>FOR</b><br/>Line {element.line_num}<br/>iter: {iter_label}\"}}")
                lines.append(f"  N{prev_node} --> N{node_id}")
                loop_node = node_id
                current_node = node_id
                node_id += 1
                
                # Loop iteration
                lines.append(f'  N{node_id}["Iteration"]')
                lines.append(f"  N{loop_node} --> N{node_id}")
                body_node = node_id
                node_id += 1
                
                # Loop back
                lines.append(f'  N{body_node} -."next iteration".-> N{loop_node}')
                
                # Exit loop
                lines.append(f"  N{node_id}[[\"Loop Complete\"]]")
                lines.append(f"  N{loop_node} -->|done| N{node_id}")
                current_node = node_id
                node_id += 1
        
        # End node
        lines.append(f"  N{node_id}([\"<b>END</b><br/>Return\"])")
        lines.append(f"  N{current_node} --> N{node_id}")
        
        lines.append("")
        lines.append("```")
        lines.append("")
        
        # Add legend
        lines.extend(self._generate_legend(method))
        
        return "\n".join(lines)
    
    def _generate_legend(self, method: MethodAnalysis) -> List[str]:
        """Generate legend explaining control flow elements."""
        lines = [
            "## Legend",
            "",
            "| Element | Description |",
            "|---------|-------------|",
            "| Round boxes | Entry/Exit points |",
            "| Diamond | Decision point (if statement) |",
            "| Rectangle | Loop or branch block |",
            "| Double bracket | Convergence/merging point |",
            "| Dotted line | Loop back edge |",
            "",
        ]
        
        # Add summary
        lines.append("## Control Flow Summary")
        lines.append("")
        if method.if_statements:
            lines.append(f"- **If statements:** {len(method.if_statements)}")
            for elem in method.if_statements:
                lines.append(f"  - Line {elem.line_num}: {elem.condition[:60]}")
        
        if method.while_loops:
            lines.append(f"- **While loops:** {len(method.while_loops)}")
            for elem in method.while_loops:
                lines.append(f"  - Line {elem.line_num}: {elem.condition[:60]}")
        
        if method.for_loops:
            lines.append(f"- **For loops:** {len(method.for_loops)}")
            for elem in method.for_loops:
                lines.append(f"  - Line {elem.line_num}: {elem.condition[:60]}")
        
        return lines
    
    def _generate_index(self, file_paths: Dict[str, str]) -> None:
        """Generate index.md listing only tested method graphs."""
        index_path = os.path.join(self.output_dir, "index.md")
        
        lines = [
            f"# Control Flow Graphs - {self.class_analysis.class_name}",
            "",
            f"Control flow diagrams for tested methods in `{self.class_analysis.class_name}` class.",
            "",
            "## Methods with Test Coverage",
            "",
        ]
        
        # Sort methods: public first, then by name
        sorted_methods = sorted(
            [self.class_analysis.methods[name] for name in self.tested_methods if name in self.class_analysis.methods],
            key=lambda m: (m.is_public is False, m.method_name)
        )
        
        for method in sorted_methods:
            if method.method_name in file_paths:
                visibility = "🔓 Public" if method.is_public else "🔒 Private"
                filename = os.path.basename(file_paths[method.method_name])
                lines.append(f"### {method.method_name}() {visibility}")
                lines.append("")
                lines.append(f"- **Branches:** {method.total_branches}")
                lines.append(f"- **Complexity:** {method.complexity}")
                lines.append(f"- **Graph:** [{filename}]({filename})")
                lines.append("")
        
        # Summary statistics
        lines.append("## Overall Statistics")
        lines.append("")
        tested_method_objs = [self.class_analysis.methods[name] for name in self.tested_methods if name in self.class_analysis.methods]
        lines.append(f"- **Total Methods:** {len(self.class_analysis.methods)}")
        lines.append(f"- **Tested Methods:** {len(tested_method_objs)}")
        lines.append(f"- **Test Coverage:** {len(tested_method_objs)}/{len(self.class_analysis.methods)} methods")
        
        if tested_method_objs:
            lines.append(f"- **Total Branches Tested:** {sum(m.total_branches for m in tested_method_objs)}")
            lines.append(f"- **Total If Statements Tested:** {sum(len(m.if_statements) for m in tested_method_objs)}")
            lines.append(f"- **Total While Loops Tested:** {sum(len(m.while_loops) for m in tested_method_objs)}")
            lines.append(f"- **Total For Loops Tested:** {sum(len(m.for_loops) for m in tested_method_objs)}")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))


def generate_graphs(source_path: str, output_dir: str = "tests/control_flow_graphs") -> Dict[str, str]:
    """Main entry point: analyze code and generate control flow graphs."""
    from test_generator.code_analyzer import analyze_code
    
    analysis = analyze_code(source_path)
    generator = GraphGenerator(analysis, output_dir)
    return generator.save_all_graphs()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        source_path = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "tests/control_flow_graphs"
        files = generate_graphs(source_path, output_dir)
        print(f"Generated {len(files)} graph files:")
        for method, filepath in files.items():
            print(f"  - {method}: {filepath}")
