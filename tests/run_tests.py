#!/usr/bin/env python
"""
Universal test runner for Google Workspace MCP.

This script can discover and run tests across all domain modules (gcalendar, gmail, gdrive, etc.)
with flexible options for running specific domains, files, or test cases.
"""

import sys
import os
import unittest
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
from datetime import datetime


class DomainTestRunner:
    """Test runner that can handle tests across multiple domains."""
    
    def __init__(self, verbosity: int = 2, quiet: bool = False):
        self.verbosity = 0 if quiet else verbosity
        self.project_root = Path(__file__).parent.parent
        # Add project root to Python path for imports
        if str(self.project_root) not in sys.path:
            sys.path.insert(0, str(self.project_root))
        self.domains = self._discover_domains()
        self.results = {}
        
    def _discover_domains(self) -> List[str]:
        """Discover all domain directories that start with 'g' and have tests."""
        domains = []
        for path in self.project_root.iterdir():
            if (path.is_dir() and 
                path.name.startswith('g') and 
                len(path.name) > 1 and 
                path.name[1:].isalpha() and
                (path / 'tests').exists()):
                domains.append(path.name)
        return sorted(domains)
    
    def list_domains_and_tests(self) -> None:
        """List all available domains and their test files."""
        print("=" * 70)
        print("Available Test Domains and Files")
        print("=" * 70)
        print()
        
        total_files = 0
        for domain in self.domains:
            test_files = self._get_test_files(domain)
            if test_files:
                print(f"{domain}:")
                for test_file in test_files:
                    print(f"  - {test_file}")
                print()
                total_files += len(test_files)
        
        print(f"Total: {len(self.domains)} domains, {total_files} test files")
    
    def _get_test_files(self, domain: str) -> List[str]:
        """Get all test files for a specific domain."""
        test_dir = self.project_root / domain / 'tests'
        if not test_dir.exists():
            return []
        
        test_files = []
        for file in test_dir.glob('test_*.py'):
            test_files.append(file.name)
        return sorted(test_files)
    
    def run_all_tests(self) -> bool:
        """Run all tests across all domains."""
        print("=" * 70)
        print("Running All Tests Across All Domains")
        print("=" * 70)
        print()
        
        all_successful = True
        start_time = time.time()
        
        for domain in self.domains:
            domain_successful = self.run_domain_tests(domain, print_header=False)
            all_successful = all_successful and domain_successful
            print()  # Add spacing between domains
        
        # Print overall summary
        self._print_overall_summary(time.time() - start_time)
        
        return all_successful
    
    def run_domain_tests(self, domain: str, print_header: bool = True) -> bool:
        """Run all tests for a specific domain."""
        if domain not in self.domains:
            print(f"Error: Domain '{domain}' not found or has no tests.")
            print(f"Available domains: {', '.join(self.domains)}")
            return False
        
        if print_header:
            print("=" * 70)
            print(f"Running Tests for Domain: {domain}")
            print("=" * 70)
            print()
        else:
            print(f"Domain: {domain}")
            print("-" * 50)
        
        # Add domain to Python path
        domain_path = self.project_root / domain
        if str(domain_path) not in sys.path:
            sys.path.insert(0, str(domain_path))
        
        # Discover tests
        loader = unittest.TestLoader()
        test_dir = domain_path / 'tests'
        suite = loader.discover(str(test_dir), pattern='test_*.py', top_level_dir=str(domain_path))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=self.verbosity, stream=sys.stdout)
        result = runner.run(suite)
        
        # Store results
        self.results[domain] = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'successful': result.wasSuccessful()
        }
        
        # Print domain summary
        if self.verbosity > 0:
            self._print_domain_summary(domain, result)
        
        return result.wasSuccessful()
    
    def run_specific_file(self, domain: str, filename: str) -> bool:
        """Run tests from a specific file."""
        if domain not in self.domains:
            print(f"Error: Domain '{domain}' not found.")
            return False
        
        test_path = self.project_root / domain / 'tests' / filename
        if not test_path.exists():
            print(f"Error: Test file '{filename}' not found in {domain}/tests/")
            return False
        
        print("=" * 70)
        print(f"Running Tests from {domain}/{filename}")
        print("=" * 70)
        print()
        
        # Add domain to Python path
        domain_path = self.project_root / domain
        if str(domain_path) not in sys.path:
            sys.path.insert(0, str(domain_path))
        
        # Load tests from specific file
        loader = unittest.TestLoader()
        suite = loader.discover(str(test_path.parent), pattern=filename, top_level_dir=str(domain_path))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=self.verbosity)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    def run_specific_class(self, domain: str, class_name: str) -> bool:
        """Run a specific test class."""
        if domain not in self.domains:
            print(f"Error: Domain '{domain}' not found.")
            return False
        
        print("=" * 70)
        print(f"Running Test Class: {class_name} from {domain}")
        print("=" * 70)
        print()
        
        # Add domain to Python path
        domain_path = self.project_root / domain
        if str(domain_path) not in sys.path:
            sys.path.insert(0, str(domain_path))
        
        # Try to find and load the test class
        test_dir = domain_path / 'tests'
        for test_file in test_dir.glob('test_*.py'):
            module_name = test_file.stem
            try:
                # Import the module
                module = __import__(f'tests.{module_name}', fromlist=[class_name])
                if hasattr(module, class_name):
                    test_class = getattr(module, class_name)
                    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                    runner = unittest.TextTestRunner(verbosity=self.verbosity)
                    result = runner.run(suite)
                    return result.wasSuccessful()
            except (ImportError, AttributeError):
                continue
        
        print(f"Error: Test class '{class_name}' not found in {domain} domain.")
        return False
    
    def _print_domain_summary(self, domain: str, result: unittest.TestResult) -> None:
        """Print summary for a specific domain."""
        print()
        print(f"{domain} Summary:")
        print(f"  Tests run: {result.testsRun}")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Skipped: {len(result.skipped)}")
        
        if result.wasSuccessful():
            print(f"  ✅ All {domain} tests passed!")
        else:
            print(f"  ❌ Some {domain} tests failed!")
    
    def _print_overall_summary(self, elapsed_time: float) -> None:
        """Print overall test summary."""
        print("=" * 70)
        print("Overall Test Summary")
        print("=" * 70)
        print()
        
        total_tests = sum(r['tests_run'] for r in self.results.values())
        total_failures = sum(r['failures'] for r in self.results.values())
        total_errors = sum(r['errors'] for r in self.results.values())
        total_skipped = sum(r['skipped'] for r in self.results.values())
        
        # Per-domain results
        print("Per-Domain Results:")
        for domain, result in self.results.items():
            status = "✅ PASS" if result['successful'] else "❌ FAIL"
            print(f"  {domain}: {status} ({result['tests_run']} tests)")
        
        print()
        print(f"Total Statistics:")
        print(f"  Domains tested: {len(self.results)}")
        print(f"  Total tests run: {total_tests}")
        print(f"  Total failures: {total_failures}")
        print(f"  Total errors: {total_errors}")
        print(f"  Total skipped: {total_skipped}")
        print(f"  Time elapsed: {elapsed_time:.2f}s")
        
        print()
        if all(r['successful'] for r in self.results.values()):
            print("✅ All tests passed across all domains!")
        else:
            print("❌ Some tests failed!")
            failed_domains = [d for d, r in self.results.items() if not r['successful']]
            print(f"Failed domains: {', '.join(failed_domains)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Universal test runner for Google Workspace MCP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                           # Run all tests
  python run_tests.py --domain gcalendar        # Run all calendar tests
  python run_tests.py --domain gmail --file test_gmail_tools.py  # Run specific file
  python run_tests.py --domain gcalendar --class TestGetEventAttendees  # Run specific class
  python run_tests.py --list                    # List all domains and test files
        """
    )
    
    parser.add_argument('--domain', '-d', 
                        help='Run tests for a specific domain (e.g., gcalendar, gmail)')
    parser.add_argument('--file', '-f',
                        help='Run tests from a specific file (requires --domain)')
    parser.add_argument('--class', '-c', dest='test_class',
                        help='Run a specific test class (requires --domain)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all available domains and test files')
    parser.add_argument('--verbose', '-v', action='count', default=2,
                        help='Increase verbosity (can be used multiple times)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Minimal output (overrides --verbose)')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = DomainTestRunner(verbosity=args.verbose, quiet=args.quiet)
    
    # Handle different modes
    if args.list:
        runner.list_domains_and_tests()
        return 0
    
    success = False
    
    if args.file and not args.domain:
        print("Error: --file requires --domain to be specified")
        return 1
    
    if args.test_class and not args.domain:
        print("Error: --class requires --domain to be specified")
        return 1
    
    if args.domain:
        if args.file:
            success = runner.run_specific_file(args.domain, args.file)
        elif args.test_class:
            success = runner.run_specific_class(args.domain, args.test_class)
        else:
            success = runner.run_domain_tests(args.domain)
    else:
        # Run all tests
        success = runner.run_all_tests()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())