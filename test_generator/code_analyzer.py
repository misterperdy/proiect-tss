"""Code analyzer: Extract control flow information from Python source code using AST."""

import ast
import inspect
from typing import Dict, List, Set, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class ControlFlowElement:
    """Represents a control flow element (if, while, for)."""
    element_type: str  # 'if', 'while', 'for', 'ifexp', 'boolop'
    line_num: int
    col_offset: int
    condition: str = ""  # textual representation of condition if available
    depth: int = 0  # nesting depth
    parent_type: str = ""  # type of parent control structure
    true_summary: str = ""  # summary of operations in TRUE branch
    false_summary: str = ""  # summary of operations in FALSE branch


@dataclass
class MethodAnalysis:
    """Analysis of a single method's control flow."""
    method_name: str
    line_start: int
    line_end: int
    is_public: bool  # True if method doesn't start with _
    parameters: List[str] = field(default_factory=list)
    if_statements: List[ControlFlowElement] = field(default_factory=list)
    while_loops: List[ControlFlowElement] = field(default_factory=list)
    for_loops: List[ControlFlowElement] = field(default_factory=list)
    all_control_flow: List[ControlFlowElement] = field(default_factory=list)
    
    @property
    def total_branches(self) -> int:
        """Total number of control flow elements."""
        return len(self.all_control_flow)
    
    @property
    def complexity(self) -> int:
        """Cyclomatic complexity estimate (1 + number of decision points)."""
        return 1 + len([e for e in self.all_control_flow if e.element_type in ['if', 'while', 'for']])


@dataclass
class ClassAnalysis:
    """Complete analysis of a class."""
    class_name: str
    methods: Dict[str, MethodAnalysis] = field(default_factory=dict)
    source_lines: List[str] = field(default_factory=list)
    
    @property
    def public_methods(self) -> List[MethodAnalysis]:
        """Return only public methods."""
        return [m for m in self.methods.values() if m.is_public]
    
    @property
    def private_methods(self) -> List[MethodAnalysis]:
        """Return only private methods."""
        return [m for m in self.methods.values() if not m.is_public]
    
    @property
    def total_if_statements(self) -> int:
        """Count all if statements across all methods."""
        return sum(len(m.if_statements) for m in self.methods.values())
    
    @property
    def total_while_loops(self) -> int:
        """Count all while loops across all methods."""
        return sum(len(m.while_loops) for m in self.methods.values())
    
    @property
    def total_for_loops(self) -> int:
        """Count all for loops across all methods."""
        return sum(len(m.for_loops) for m in self.methods.values())
    
    @property
    def total_branches(self) -> int:
        """Count all control flow elements."""
        return sum(m.total_branches for m in self.methods.values())


class ControlFlowVisitor(ast.NodeVisitor):
    """AST visitor to extract control flow elements from a method."""
    
    def __init__(self, method_name: str, source_lines: List[str]):
        self.method_name = method_name
        self.source_lines = source_lines
        self.if_statements: List[ControlFlowElement] = []
        self.while_loops: List[ControlFlowElement] = []
        self.for_loops: List[ControlFlowElement] = []
        self.all_control_flow: List[ControlFlowElement] = []
        self.depth = 0
        self.current_parent = ""
    
    def visit_If(self, node: ast.If) -> None:
        """Visit if statements."""
        condition_str = self._get_node_source(node.test)
        true_summary = self._summarize_body(node.body)
        false_summary = self._summarize_body(node.orelse) if node.orelse else "pass"
        
        element = ControlFlowElement(
            element_type='if',
            line_num=node.lineno,
            col_offset=node.col_offset,
            condition=condition_str,
            depth=self.depth,
            parent_type=self.current_parent,
            true_summary=true_summary,
            false_summary=false_summary
        )
        self.if_statements.append(element)
        self.all_control_flow.append(element)
        
        # Visit nested control flow in if/else bodies
        old_parent = self.current_parent
        self.current_parent = 'if'
        self.depth += 1
        for child in node.body:
            self.visit(child)
        self.depth -= 1
        for child in node.orelse:
            self.visit(child)
        self.current_parent = old_parent
    
    def visit_While(self, node: ast.While) -> None:
        """Visit while loops."""
        condition_str = self._get_node_source(node.test)
        element = ControlFlowElement(
            element_type='while',
            line_num=node.lineno,
            col_offset=node.col_offset,
            condition=condition_str,
            depth=self.depth,
            parent_type=self.current_parent
        )
        self.while_loops.append(element)
        self.all_control_flow.append(element)
        
        old_parent = self.current_parent
        self.current_parent = 'while'
        self.depth += 1
        for child in node.body:
            self.visit(child)
        self.depth -= 1
        for child in node.orelse:
            self.visit(child)
        self.current_parent = old_parent
    
    def visit_For(self, node: ast.For) -> None:
        """Visit for loops."""
        condition_str = self._get_node_source(node.iter)
        element = ControlFlowElement(
            element_type='for',
            line_num=node.lineno,
            col_offset=node.col_offset,
            condition=condition_str,
            depth=self.depth,
            parent_type=self.current_parent
        )
        self.for_loops.append(element)
        self.all_control_flow.append(element)
        
        old_parent = self.current_parent
        self.current_parent = 'for'
        self.depth += 1
        for child in node.body:
            self.visit(child)
        self.depth -= 1
        for child in node.orelse:
            self.visit(child)
        self.current_parent = old_parent
    
    def _get_node_source(self, node: ast.expr) -> str:
        """Extract source code from AST node."""
        try:
            if hasattr(node, 'lineno'):
                line_num = node.lineno - 1  # 0-indexed
                if 0 <= line_num < len(self.source_lines):
                    # For simple cases, return the line content
                    line = self.source_lines[line_num].strip()
                    # Truncate very long lines
                    if len(line) > 60:
                        return line[:57] + "..."
                    return line
        except (IndexError, AttributeError):
            pass
        
        # Fallback: try to unparse the AST node (Python 3.9+)
        try:
            return ast.unparse(node)[:60]
        except AttributeError:
            return ast.dump(node)[:60]
    
    def _summarize_body(self, body: List[ast.stmt]) -> str:
        """Extract a summary of key operations from a code block."""
        if not body:
            return "pass"
        
        summaries = []
        for stmt in body[:3]:  # Look at first 3 statements
            if isinstance(stmt, ast.Return):
                if stmt.value:
                    if isinstance(stmt.value, ast.Constant):
                        summaries.append(f"return {stmt.value.value}")
                    elif isinstance(stmt.value, ast.Name):
                        summaries.append(f"return {stmt.value.id}")
                    else:
                        summaries.append("return ...")
                else:
                    summaries.append("return")
            elif isinstance(stmt, ast.Assign):
                # Get the target and value
                if stmt.targets:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        if isinstance(stmt.value, ast.Constant):
                            summaries.append(f"{target.id} = {stmt.value.value}")
                        elif isinstance(stmt.value, ast.Name):
                            summaries.append(f"{target.id} = {stmt.value.id}")
                        elif isinstance(stmt.value, ast.Subscript):
                            summaries.append(f"{target.id} = [...]")
                        else:
                            summaries.append(f"{target.id} = ...")
            elif isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Name):
                        summaries.append(f"{stmt.value.func.id}(...)")
                    elif isinstance(stmt.value.func, ast.Attribute):
                        summaries.append(f".{stmt.value.func.attr}(...)")
            elif isinstance(stmt, ast.If):
                summaries.append("nested if ...")
        
        if not summaries:
            return "..."
        
        return "; ".join(summaries[:2])  # Show first 2 operations


class CodeAnalyzer:
    """Analyze Python source code to extract control flow information."""
    
    def __init__(self, source_path: str):
        """Initialize analyzer with source file path."""
        self.source_path = source_path
        with open(source_path, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
        self.source_lines = self.source_code.split('\n')
        self.tree = ast.parse(self.source_code)
    
    def analyze(self) -> ClassAnalysis:
        """Analyze the source code and return complete class analysis."""
        # Find the main class definition
        class_def = self._find_class_def()
        if not class_def:
            raise ValueError(f"No class definition found in {self.source_path}")
        
        class_analysis = ClassAnalysis(
            class_name=class_def.name,
            source_lines=self.source_lines
        )
        
        # Analyze each method
        for node in class_def.body:
            if isinstance(node, ast.FunctionDef):
                method_analysis = self._analyze_method(node, class_def)
                class_analysis.methods[node.name] = method_analysis
        
        return class_analysis
    
    def _find_class_def(self) -> ast.ClassDef | None:
        """Find the first class definition in the AST."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                return node
        return None
    
    def _analyze_method(self, func_node: ast.FunctionDef, class_node: ast.ClassDef) -> MethodAnalysis:
        """Analyze a single method's control flow."""
        method_name = func_node.name
        is_public = not method_name.startswith('_')
        
        # Extract parameters
        parameters = [arg.arg for arg in func_node.args.args if arg.arg != 'self']
        
        # Find line range
        line_start = func_node.lineno
        line_end = func_node.end_lineno or line_start
        
        # Extract control flow elements
        visitor = ControlFlowVisitor(method_name, self.source_lines)
        visitor.visit(func_node)
        
        method_analysis = MethodAnalysis(
            method_name=method_name,
            line_start=line_start,
            line_end=line_end,
            is_public=is_public,
            parameters=parameters,
            if_statements=visitor.if_statements,
            while_loops=visitor.while_loops,
            for_loops=visitor.for_loops,
            all_control_flow=visitor.all_control_flow
        )
        
        return method_analysis
    
    def get_critical_methods(self, threshold: int = 1) -> List[MethodAnalysis]:
        """Get methods with significant control flow (at least `threshold` branches)."""
        analysis = self.analyze()
        return [m for m in analysis.methods.values() if m.total_branches >= threshold]


def analyze_code(source_path: str) -> ClassAnalysis:
    """Main entry point: analyze code and return class analysis."""
    analyzer = CodeAnalyzer(source_path)
    return analyzer.analyze()


if __name__ == '__main__':
    # Example usage
    import sys
    if len(sys.argv) > 1:
        analysis = analyze_code(sys.argv[1])
        print(f"Class: {analysis.class_name}")
        print(f"Methods: {len(analysis.methods)}")
        print(f"Total if statements: {analysis.total_if_statements}")
        print(f"Total while loops: {analysis.total_while_loops}")
        print(f"Total for loops: {analysis.total_for_loops}")
        print(f"Total branches: {analysis.total_branches}")
        print("\nMethods:")
        for name, method in sorted(analysis.methods.items()):
            print(f"  {name}: {method.total_branches} branches (complexity: {method.complexity})")
