#!/usr/bin/env python3
"""
Robot Puzzle Game - Comprehensive API Test Suite
Professional test runner with detailed reporting and logging
"""

import asyncio
import json
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import importlib.util
import os
from pathlib import Path
from test_base import TestSuite, TestResult

# ANSI color codes for professional output
class Colors:
    # Standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


class TestRunner:
    """Main test runner with professional reporting"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.suites: List[TestSuite] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.verbose = self.config.get('verbose', False)
        self.json_output = self.config.get('json_output', False)
        self.log_file = self.config.get('log_file')
        
    def log(self, message: str, level: str = 'INFO'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        if self.verbose:
            print(log_entry)
            
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')

    def print_header(self):
        """Print professional test suite header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}🧪 ROBOT PUZZLE GAME - COMPREHENSIVE API TEST SUITE{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.CYAN}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.CYAN}Environment: {self.config.get('environment', 'Production')}{Colors.RESET}")
        print(f"{Colors.CYAN}API Base URL: {self.config.get('api_base_url', 'N/A')}{Colors.RESET}")
        print()

    def print_suite_header(self, suite: TestSuite):
        """Print test suite header"""
        print(f"{Colors.BOLD}{Colors.YELLOW}📋 {suite.name}{Colors.RESET}")
        if suite.description:
            print(f"{Colors.DIM}   {suite.description}{Colors.RESET}")
        print(f"{Colors.DIM}   {'─' * 60}{Colors.RESET}")

    def print_test_result(self, test: TestResult):
        """Print individual test result"""
        status_colors = {
            'PASS': Colors.BRIGHT_GREEN,
            'FAIL': Colors.BRIGHT_RED,
            'ERROR': Colors.BRIGHT_RED,
            'SKIP': Colors.BRIGHT_YELLOW
        }
        
        status_icons = {
            'PASS': '✅',
            'FAIL': '❌',
            'ERROR': '💥',
            'SKIP': '⏭️'
        }
        
        color = status_colors.get(test.status, Colors.WHITE)
        icon = status_icons.get(test.status, '❓')
        
        duration_str = f"({test.duration:.3f}s)" if test.duration > 0 else ""
        
        print(f"   {icon} {color}{test.status:<6}{Colors.RESET} {test.name:<50} {Colors.DIM}{duration_str}{Colors.RESET}")
        
        if test.message and self.verbose:
            print(f"      {Colors.DIM}💬 {test.message}{Colors.RESET}")

    def print_suite_summary(self, suite: TestSuite):
        """Print test suite summary"""
        total = suite.total
        passed = suite.passed
        failed = suite.failed
        errors = suite.errors
        skipped = suite.skipped
        
        if total == 0:
            print(f"   {Colors.YELLOW}⚠️  No tests found{Colors.RESET}")
            return
            
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"   {Colors.DIM}{'─' * 60}{Colors.RESET}")
        print(f"   {Colors.BOLD}Summary:{Colors.RESET} {total} tests, {Colors.GREEN}{passed} passed{Colors.RESET}, ", end="")
        
        if failed > 0:
            print(f"{Colors.RED}{failed} failed{Colors.RESET}, ", end="")
        if errors > 0:
            print(f"{Colors.RED}{errors} errors{Colors.RESET}, ", end="")
        if skipped > 0:
            print(f"{Colors.YELLOW}{skipped} skipped{Colors.RESET}, ", end="")
            
        print(f"({success_rate:.1f}% success rate)")
        print(f"   {Colors.DIM}Duration: {suite.duration:.3f}s{Colors.RESET}")
        print()

    def print_detailed_failures(self):
        """Print detailed information about failed tests"""
        all_failures = []
        
        for suite in self.suites:
            for test in suite.tests:
                if test.status in ['FAIL', 'ERROR']:
                    all_failures.append((suite, test))
        
        if not all_failures:
            return
            
        print(f"{Colors.BOLD}{Colors.RED}💥 DETAILED FAILURE REPORT{Colors.RESET}")
        print(f"{Colors.RED}{'='*60}{Colors.RESET}")
        
        for i, (suite, test) in enumerate(all_failures, 1):
            print(f"\n{Colors.BOLD}{i}. {Colors.RED}{test.status}: {suite.name} → {test.name}{Colors.RESET}")
            
            if test.message:
                print(f"   {Colors.BOLD}Message:{Colors.RESET} {test.message}")
                
            if test.details:
                print(f"   {Colors.BOLD}Details:{Colors.RESET}")
                # Indent each line of details
                for line in test.details.split('\n'):
                    if line.strip():
                        print(f"      {Colors.DIM}{line}{Colors.RESET}")
            
            print(f"   {Colors.DIM}Duration: {test.duration:.3f}s{Colors.RESET}")
            print(f"   {Colors.DIM}Timestamp: {test.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

    def print_final_summary(self):
        """Print final test run summary"""
        total_tests = sum(suite.total for suite in self.suites)
        total_passed = sum(suite.passed for suite in self.suites)
        total_failed = sum(suite.failed for suite in self.suites)
        total_errors = sum(suite.errors for suite in self.suites)
        total_skipped = sum(suite.skipped for suite in self.suites)
        
        duration = (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}📊 FINAL SUMMARY{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
        
        print(f"{Colors.BOLD}Test Suites:{Colors.RESET} {len(self.suites)}")
        print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total_tests}")
        print(f"{Colors.BOLD}Duration:{Colors.RESET} {duration:.3f}s")
        print()
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            
            # Overall status
            if total_failed == 0 and total_errors == 0:
                overall_status = f"{Colors.BOLD}{Colors.GREEN}✅ ALL TESTS PASSED{Colors.RESET}"
            else:
                overall_status = f"{Colors.BOLD}{Colors.RED}❌ TESTS FAILED{Colors.RESET}"
            
            print(f"Overall Status: {overall_status}")
            print()
            
            # Detailed breakdown
            print(f"{Colors.GREEN}✅ Passed:{Colors.RESET}  {total_passed:>8} ({(total_passed/total_tests)*100:.1f}%)")
            if total_failed > 0:
                print(f"{Colors.RED}❌ Failed:{Colors.RESET}  {total_failed:>8} ({(total_failed/total_tests)*100:.1f}%)")
            if total_errors > 0:
                print(f"{Colors.RED}💥 Errors:{Colors.RESET}  {total_errors:>8} ({(total_errors/total_tests)*100:.1f}%)")
            if total_skipped > 0:
                print(f"{Colors.YELLOW}⏭️  Skipped:{Colors.RESET} {total_skipped:>8} ({(total_skipped/total_tests)*100:.1f}%)")
            
            print(f"{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}⚠️  No tests were executed{Colors.RESET}")
        
        print(f"\n{Colors.CYAN}Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")

    def export_json_report(self) -> Dict[str, Any]:
        """Export test results as JSON"""
        return {
            'summary': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0,
                'total_suites': len(self.suites),
                'total_tests': sum(suite.total for suite in self.suites),
                'total_passed': sum(suite.passed for suite in self.suites),
                'total_failed': sum(suite.failed for suite in self.suites),
                'total_errors': sum(suite.errors for suite in self.suites),
                'total_skipped': sum(suite.skipped for suite in self.suites),
                'success_rate': (sum(suite.passed for suite in self.suites) / sum(suite.total for suite in self.suites)) * 100 if sum(suite.total for suite in self.suites) > 0 else 0
            },
            'suites': [
                {
                    'name': suite.name,
                    'description': suite.description,
                    'duration': suite.duration,
                    'total': suite.total,
                    'passed': suite.passed,
                    'failed': suite.failed,
                    'errors': suite.errors,
                    'skipped': suite.skipped,
                    'tests': [
                        {
                            'name': test.name,
                            'status': test.status,
                            'duration': test.duration,
                            'message': test.message,
                            'details': test.details,
                            'timestamp': test.timestamp.isoformat()
                        } for test in suite.tests
                    ]
                } for suite in self.suites
            ],
            'config': self.config
        }

    async def discover_and_run_tests(self, test_dir: str = "tests"):
        """Discover and run all test files"""
        self.start_time = datetime.now()
        
        self.print_header()
        
        # Discover test files
        test_files = self.discover_test_files(test_dir)
        
        if not test_files:
            print(f"{Colors.YELLOW}⚠️  No test files found in {test_dir}{Colors.RESET}")
            return
        
        self.log(f"Discovered {len(test_files)} test files")
        
        # Run each test file
        for test_file in test_files:
            try:
                await self.run_test_file(test_file)
            except Exception as e:
                self.log(f"Error running test file {test_file}: {e}", 'ERROR')
                # Create a failed suite for the file
                suite = TestSuite(f"ERROR: {test_file}", "Failed to load test file")
                suite.setup_error = str(e)
                self.suites.append(suite)
        
        self.end_time = datetime.now()
        
        # Print detailed failures
        self.print_detailed_failures()
        
        # Print final summary
        self.print_final_summary()
        
        # Export JSON if requested
        if self.json_output:
            json_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(json_file, 'w') as f:
                json.dump(self.export_json_report(), f, indent=2)
            print(f"\n{Colors.CYAN}📄 JSON report exported to: {json_file}{Colors.RESET}")
        
        # Return exit code
        total_failed = sum(suite.failed + suite.errors for suite in self.suites)
        return 0 if total_failed == 0 else 1

    def discover_test_files(self, test_dir: str) -> List[str]:
        """Discover test files in the test directory"""
        test_files = []
        test_path = Path(test_dir)
        
        # If test_dir doesn't exist, try current directory
        if not test_path.exists():
            test_path = Path('.')
        
        # Look for Python files starting with 'test_'
        for file_path in test_path.glob('test_*.py'):
            if file_path.name not in ['__init__.py', 'test_base.py']:
                test_files.append(str(file_path))
        
        # Sort for consistent ordering
        return sorted(test_files)

    async def run_test_file(self, test_file: str):
        """Run tests from a specific test file"""
        self.log(f"Running tests from {test_file}")
        
        # Skip test_base.py as it's not a test file
        if 'test_base.py' in test_file:
            return
        
        # Import the test module
        spec = importlib.util.spec_from_file_location("test_module", test_file)
        if not spec or not spec.loader:
            raise Exception(f"Could not load test module from {test_file}")
        
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Look for test classes or functions
        if hasattr(test_module, 'TestSuite'):
            # If there's a TestSuite class, instantiate and run it
            test_suite_class = test_module.TestSuite
            test_instance = test_suite_class(self.config)
            suite = await test_instance.run()
            self.suites.append(suite)
            
        elif hasattr(test_module, 'run_tests'):
            # If there's a run_tests function, call it
            suite = await test_module.run_tests(self.config)
            self.suites.append(suite)
        else:
            # Look for functions starting with 'test_'
            test_functions = [getattr(test_module, name) for name in dir(test_module) 
                            if name.startswith('test_') and callable(getattr(test_module, name))]
            
            if test_functions:
                suite_name = Path(test_file).stem
                suite = TestSuite(suite_name, f"Tests from {test_file}")
                suite.start_time = datetime.now()
                
                self.print_suite_header(suite)
                
                for test_func in test_functions:
                    start_time = time.time()
                    try:
                        if asyncio.iscoroutinefunction(test_func):
                            await test_func(self.config)
                        else:
                            test_func(self.config)
                        
                        duration = time.time() - start_time
                        result = TestResult(test_func.__name__, 'PASS', duration)
                        
                    except AssertionError as e:
                        duration = time.time() - start_time
                        result = TestResult(test_func.__name__, 'FAIL', duration, str(e), traceback.format_exc())
                        
                    except Exception as e:
                        duration = time.time() - start_time
                        result = TestResult(test_func.__name__, 'ERROR', duration, str(e), traceback.format_exc())
                    
                    suite.tests.append(result)
                    self.print_test_result(result)
                
                suite.end_time = datetime.now()
                self.print_suite_summary(suite)
                self.suites.append(suite)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Robot Puzzle Game API Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--json', '-j', action='store_true', help='Export JSON report')
    parser.add_argument('--log-file', '-l', help='Log file path')
    parser.add_argument('--api-url', help='API base URL')
    parser.add_argument('--environment', default='Production', help='Test environment')
    parser.add_argument('--test-dir', default='.', help='Test directory path')
    
    args = parser.parse_args()
    
    config = {
        'verbose': args.verbose,
        'json_output': args.json,
        'log_file': args.log_file,
        'api_base_url': args.api_url or 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod',
        'environment': args.environment
    }
    
    runner = TestRunner(config)
    
    try:
        exit_code = asyncio.run(runner.discover_and_run_tests(args.test_dir))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}💥 Fatal error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == '__main__':
    main()