"""Main orchestrator: Coordinate analysis, test generation, and graph generation."""

import os
import subprocess
import sys
from typing import Optional, Tuple
from pathlib import Path

from test_generator.code_analyzer import analyze_code
from test_generator.test_writer import TestWriter
from test_generator.graph_generator import GraphGenerator


class TestGenerator:
    """Main orchestrator for generating tests and control flow graphs."""
    
    def __init__(
        self,
        source_path: str,
        output_test_path: str = "tests/test_structural_quoridor.py",
        output_graph_dir: str = "tests/control_flow_graphs",
        num_tests: Optional[int] = None,
    ):
        """
        Initialize the test generator.
        
        Args:
            source_path: Path to the source Python file to analyze
            output_test_path: Path where generated tests should be written
            output_graph_dir: Directory where control flow graph files should be saved
            num_tests: Number of tests to generate (auto-calculated if None)
        """
        self.source_path = source_path
        self.output_test_path = output_test_path
        self.output_graph_dir = output_graph_dir
        self.num_tests = num_tests
        
        # Results
        self.analysis = None
        self.test_code = None
        self.graph_files = None
    
    def run(self, validate: bool = True, verbose: bool = True) -> Tuple[str, dict]:
        """
        Run the complete generation pipeline.
        
        Args:
            validate: If True, run pytest on generated tests
            verbose: If True, print status messages
        
        Returns:
            Tuple of (test_code, graph_files dict)
        """
        if verbose:
            print(f"[*] Analyzing {self.source_path}...")
        
        # Step 1: Analyze source code
        self.analysis = analyze_code(self.source_path)
        if verbose:
            self._print_analysis_summary()
        
        # Step 2: Generate tests
        if verbose:
            print(f"[*] Generating tests (target: {self.num_tests or 'auto'})...")
        writer = TestWriter(self.analysis, num_tests=self.num_tests)
        self.test_code = writer.generate_test_file()
        # Count tests - look for "def test_" anywhere in the code
        test_count = self.test_code.count('def test_')
        if verbose:
            print(f"    Generated {test_count} test functions")
        
        # Get the methods that have tests
        tested_methods = writer.get_tested_methods()
        
        # Step 3: Generate control flow graphs ONLY for tested methods
        if verbose:
            print(f"[*] Generating control flow graphs for tested methods...")
        graph_gen = GraphGenerator(self.analysis, tested_methods=tested_methods, output_dir=self.output_graph_dir)
        self.graph_files = graph_gen.save_all_graphs()
        if verbose:
            print(f"    Generated {len(self.graph_files)} graph files for {len(tested_methods)} tested methods in {self.output_graph_dir}/")
        
        
        # Step 4: Write test file
        if verbose:
            print(f"[*] Writing test file to {self.output_test_path}...")
        self._write_test_file()
        if verbose:
            print(f"    ✓ Written {os.path.getsize(self.output_test_path)} bytes")
        
        # Step 5: Validate with pytest
        if validate:
            if verbose:
                print(f"[*] Validating with pytest...")
            success = self._run_pytest(verbose=verbose)
            if success and verbose:
                print(f"    ✓ All tests passed!")
            elif not success and verbose:
                print(f"    ⚠ Some tests may have issues (see output above)")
        
        # Print summary
        if verbose:
            self._print_summary()
        
        return self.test_code, self.graph_files
    
    def _print_analysis_summary(self) -> None:
        """Print summary of code analysis."""
        print(f"")
        print(f"  Class: {self.analysis.class_name}")
        print(f"  Methods: {len(self.analysis.methods)} total")
        print(f"    Public: {len(self.analysis.public_methods)}")
        print(f"    Private: {len(self.analysis.private_methods)}")
        print(f"  Control Flow Elements:")
        print(f"    If statements: {self.analysis.total_if_statements}")
        print(f"    While loops: {self.analysis.total_while_loops}")
        print(f"    For loops: {self.analysis.total_for_loops}")
        print(f"    Total: {self.analysis.total_branches}")
        print(f"")
    
    def _write_test_file(self) -> None:
        """Write generated test code to output file."""
        os.makedirs(os.path.dirname(self.output_test_path), exist_ok=True)
        with open(self.output_test_path, 'w', encoding='utf-8') as f:
            f.write(self.test_code)
    
    def _run_pytest(self, verbose: bool = False) -> bool:
        """Run pytest on generated tests to validate them."""
        try:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                self.output_test_path,
                "-v" if verbose else "-q",
                "--tb=short",
            ]
            result = subprocess.run(cmd, capture_output=not verbose, timeout=60)
            return result.returncode == 0
        except Exception as e:
            print(f"    ⚠ Could not run pytest: {e}")
            return False
    
    def _print_summary(self) -> None:
        """Print generation summary."""
        print(f"")
        print(f"[✓] Generation complete!")
        print(f"")
        print(f"  Test file: {self.output_test_path}")
        print(f"  Graph directory: {self.output_graph_dir}/")
        print(f"  Methods with graphs: {len(self.graph_files)}")
        print(f"")


def generate_tests(
    source_path: str,
    output_test_path: str = "tests/test_structural_quoridor.py",
    output_graph_dir: str = "tests/control_flow_graphs",
    num_tests: Optional[int] = None,
    validate: bool = True,
    verbose: bool = True,
) -> Tuple[str, dict]:
    """
    Main entry point: Generate tests and graphs for source code.
    
    Args:
        source_path: Path to source Python file
        output_test_path: Path for output test file
        output_graph_dir: Directory for output graph files
        num_tests: Number of tests to generate (auto if None)
        validate: Run pytest after generation
        verbose: Print status messages
    
    Returns:
        Tuple of (test_code, graph_files_dict)
    """
    generator = TestGenerator(
        source_path,
        output_test_path=output_test_path,
        output_graph_dir=output_graph_dir,
        num_tests=num_tests,
    )
    return generator.run(validate=validate, verbose=verbose)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate structural tests and control flow graphs')
    parser.add_argument('source', help='Path to source Python file')
    parser.add_argument('--output-tests', default='tests/test_structural_quoridor.py',
                       help='Output path for test file (default: tests/test_structural_quoridor.py)')
    parser.add_argument('--output-graphs', default='tests/control_flow_graphs',
                       help='Output directory for graph files (default: tests/control_flow_graphs)')
    parser.add_argument('--num-tests', type=int, default=None,
                       help='Number of tests to generate (default: auto-calculated)')
    parser.add_argument('--no-validate', action='store_true',
                       help='Skip pytest validation')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Suppress status messages')
    
    args = parser.parse_args()
    
    try:
        test_code, graphs = generate_tests(
            args.source,
            output_test_path=args.output_tests,
            output_graph_dir=args.output_graphs,
            num_tests=args.num_tests,
            validate=not args.no_validate,
            verbose=not args.quiet,
        )
        sys.exit(0)
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)
