#!/usr/bin/env python3
"""
Fast Test Runner for Net-Pulse

This script runs only the fast unit tests, excluding slow integration tests
and performance tests. Ideal for development and CI environments where quick
feedback is needed.

Usage:
    python run_fast_tests.py
    python run_fast_tests.py --verbose
    python run_fast_tests.py --parallel
"""

import subprocess
import sys
import argparse


def run_fast_tests(verbose=False, parallel=True):
    """Run fast tests only (excluding slow and integration tests)."""

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add parallel execution if requested
    if parallel:
        cmd.append("-n")
        cmd.append("auto")

    # Add markers to exclude slow and integration tests
    cmd.append("-m")
    cmd.append("not slow and not integration")

    # Add other useful options
    cmd.extend([
        "--tb=short",
        "--durations=10",
        "--maxfail=5"
    ])

    if verbose:
        cmd.append("-v")
        cmd.append("--capture=no")

    # Add test paths
    cmd.append("tests/")

    print("Running fast tests with command:")
    print(" ".join(cmd))
    print("-" * 50)

    try:
        result = subprocess.run(cmd, cwd=".")

        if result.returncode == 0:
            print("-" * 50)
            print("✅ All fast tests passed!")
            return True
        else:
            print("-" * 50)
            print("❌ Some fast tests failed!")
            return False

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def run_specific_test_category(category, verbose=False):
    """Run tests for a specific category."""

    cmd = ["python", "-m", "pytest", "-m", category, "--tb=short"]

    if verbose:
        cmd.append("-v")

    cmd.append("tests/")

    print(f"Running {category} tests...")
    result = subprocess.run(cmd, cwd=".")

    return result.returncode == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run fast tests for Net-Pulse")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--parallel", "-p", action="store_true", default=True, help="Enable parallel execution")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel execution")
    parser.add_argument("--category", "-c", choices=["fast", "unit", "api", "integration", "slow"],
                       help="Run specific test category")

    args = parser.parse_args()

    if args.no_parallel:
        args.parallel = False

    if args.category:
        success = run_specific_test_category(args.category, args.verbose)
    else:
        success = run_fast_tests(args.verbose, args.parallel)

    sys.exit(0 if success else 1)