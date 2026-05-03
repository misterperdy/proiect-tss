#!/usr/bin/env python3
"""CLI entry point for structural test generator.

Usage:
    python generate_tests.py                                 # Generate once
    python generate_tests.py --num-tests 10                  # Specify test count
    python generate_tests.py --watch                         # Watch mode
    python generate_tests.py --output tests/my_tests.py      # Custom output path
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Add parent directory to path so we can import test_generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_generator.generator import generate_tests as run_generation


def setup_argparse():
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description='Generate structural tests and control flow graphs for Python code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate tests once
  python generate_tests.py

  # Generate 10 specific tests
  python generate_tests.py --num-tests 10

  # Watch for changes and regenerate automatically
  python generate_tests.py --watch

  # Custom output paths
  python generate_tests.py --output tests/custom_tests.py --graphs docs/graphs/

  # Quiet mode (minimal output)
  python generate_tests.py -q
        """,
    )
    
    parser.add_argument(
        'source',
        nargs='?',
        default='Quoridor_Class.py',
        help='Path to source Python file to analyze (default: Quoridor_Class.py)',
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default='tests/test_structural_quoridor.py',
        help='Output path for generated test file (default: tests/test_structural_quoridor.py)',
    )
    
    parser.add_argument(
        '--graphs',
        '-g',
        default='tests/control_flow_graphs',
        help='Output directory for control flow graphs (default: tests/control_flow_graphs)',
    )
    
    parser.add_argument(
        '--num-tests',
        '-n',
        type=int,
        default=None,
        help='Number of tests to generate (default: auto-calculated based on branches)',
    )
    
    parser.add_argument(
        '--watch',
        '-w',
        action='store_true',
        help='Watch source file for changes and regenerate automatically',
    )
    
    parser.add_argument(
        '--no-validate',
        action='store_true',
        help='Skip pytest validation after generation',
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress status messages',
    )
    
    return parser


def run_once(args):
    """Run generation once."""
    if not os.path.exists(args.source):
        print(f"[!] Source file not found: {args.source}", file=sys.stderr)
        return False
    
    try:
        test_code, graphs = run_generation(
            args.source,
            output_test_path=args.output,
            output_graph_dir=args.graphs,
            num_tests=args.num_tests,
            validate=not args.no_validate,
            verbose=not args.quiet,
        )
        return True
    except Exception as e:
        print(f"[!] Generation failed: {e}", file=sys.stderr)
        return False


def run_watch_mode(args):
    """Run generation in watch mode (continuous monitoring)."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("[!] Watch mode requires 'watchdog' package. Install with: pip install watchdog")
        return False
    
    class SourceFileHandler(FileSystemEventHandler):
        """Handle file system events."""
        
        def __init__(self, source_path, handler_args):
            self.source_path = os.path.abspath(source_path)
            self.handler_args = handler_args
            self.last_run = 0
            self.debounce_delay = 1  # Seconds
        
        def on_modified(self, event):
            """Handle file modification."""
            if event.is_directory:
                return
            
            if os.path.abspath(event.src_path) == self.source_path:
                # Debounce: don't regenerate too frequently
                now = time.time()
                if now - self.last_run < self.debounce_delay:
                    return
                
                self.last_run = now
                
                if not args.quiet:
                    print(f"\n[*] Detected change in {os.path.basename(self.source_path)}")
                    print(f"[*] Regenerating tests...")
                
                run_once(self.handler_args)
    
    if not os.path.exists(args.source):
        print(f"[!] Source file not found: {args.source}", file=sys.stderr)
        return False
    
    if not args.quiet:
        print(f"[*] Watch mode enabled")
        print(f"[*] Monitoring {args.source} for changes...")
        print(f"[*] Press Ctrl+C to exit")
        print(f"")
    
    # Initial generation
    if not run_once(args):
        return False
    
    # Start watching
    observer = Observer()
    source_dir = os.path.dirname(os.path.abspath(args.source))
    event_handler = SourceFileHandler(args.source, args)
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if not args.quiet:
            print(f"\n[*] Watch mode stopped")
        observer.join()
        return True


def main():
    """Main entry point."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Validate source file exists
    if not os.path.exists(args.source):
        print(f"[!] Source file not found: {args.source}", file=sys.stderr)
        sys.exit(1)
    
    # Run appropriate mode
    if args.watch:
        success = run_watch_mode(args)
    else:
        success = run_once(args)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
