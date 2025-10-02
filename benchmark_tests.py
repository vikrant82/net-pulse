#!/usr/bin/env python3
"""
Test Performance Benchmark for Net-Pulse

This script benchmarks test execution times for different test categories
and configurations to track performance improvements.

Usage:
    python benchmark_tests.py
    python benchmark_tests.py --runs 5
    python benchmark_tests.py --categories fast,integration
"""

import subprocess
import time
import statistics
from typing import Dict, List
import argparse
import json
from datetime import datetime


class TestBenchmark:
    """Benchmark test execution performance."""

    def __init__(self):
        self.results = {}

    def run_benchmark(self, category: str, runs: int = 3) -> Dict:
        """Run benchmark for a specific test category."""

        print(f"\n🔍 Benchmarking {category} tests ({runs} runs)...")

        times = []

        for i in range(runs):
            print(f"  Run {i+1}/{runs}...", end=" ", flush=True)

            start_time = time.time()

            if category == "fast":
                cmd = ["python", "run_fast_tests.py", "--no-parallel"]
            elif category == "all":
                cmd = ["python", "-m", "pytest", "tests/", "--tb=no", "-q"]
            elif category == "integration":
                cmd = ["python", "-m", "pytest", "tests/", "-m", "integration", "--tb=no", "-q"]
            elif category == "slow":
                cmd = ["python", "-m", "pytest", "tests/", "-m", "slow", "--tb=no", "-q"]
            else:
                cmd = ["python", "-m", "pytest", "tests/", "-m", category, "--tb=no", "-q"]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                end_time = time.time()
                execution_time = end_time - start_time

                if result.returncode == 0:
                    times.append(execution_time)
                    print(f"✅ {execution_time".2f"}s")
                else:
                    print(f"❌ Failed (exit code: {result.returncode})")
                    if result.stderr:
                        print(f"     Error: {result.stderr.strip()[-100:]}")

            except subprocess.TimeoutExpired:
                print("❌ Timeout (>5min)")
                end_time = time.time()
                execution_time = end_time - start_time
                times.append(execution_time)
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0

            result = {
                'category': category,
                'runs': len(times),
                'avg_time': avg_time,
                'min_time': min_time,
                'max_time': max_time,
                'std_dev': std_dev,
                'times': times,
                'timestamp': datetime.now().isoformat()
            }

            self.results[category] = result

            print("
📊 Results:"            print(f"   Average: {avg_time".2f"}s")
            print(f"   Min: {min_time".2f"}s")
            print(f"   Max: {max_time".2f"}s")
            print(f"   Std Dev: {std_dev:".2f"s")

            return result
        else:
            print("❌ No successful runs")
            return None

    def run_all_benchmarks(self, categories: List[str], runs: int = 3):
        """Run benchmarks for all specified categories."""

        print("🚀 Starting Test Performance Benchmarks"        print(f"Categories: {', '.join(categories)}")
        print(f"Runs per category: {runs}")
        print("-" * 50)

        for category in categories:
            self.run_benchmark(category, runs)
            time.sleep(1)  # Brief pause between categories

    def save_results(self, filename: str = None):
        """Save benchmark results to file."""

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_benchmark_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to {filename}")

    def print_summary(self):
        """Print a summary of all benchmark results."""

        print("\n📋 BENCHMARK SUMMARY")
        print("-" * 50)

        if not self.results:
            print("No results to display")
            return

        # Sort by average time
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1]['avg_time']
        )

        for category, result in sorted_results:
            avg_time = result['avg_time']
            runs = result['runs']

            if avg_time < 60:
                time_str = f"{avg_time".2f"}s"
            else:
                time_str = f"{avg_time/60".2f"}m"

            print(f"{category"15"} | {time_str"8"} | {runs} runs")

        if len(sorted_results) > 1:
            fastest = sorted_results[0]
            slowest = sorted_results[-1]

            print("
🏆 Performance Insights:"            print(f"   Fastest: {fastest[0]} ({fastest[1]['avg_time']".2f"}s)")
            print(f"   Slowest: {slowest[0]} ({slowest[1]['avg_time']".2f"}s)")

            ratio = slowest[1]['avg_time'] / fastest[1]['avg_time']
            print(f"   Speed ratio: {ratio".1f"}x")

    def compare_with_baseline(self, baseline_file: str):
        """Compare current results with a baseline file."""

        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)

            print("
📈 COMPARISON WITH BASELINE"            print("-" * 50)

            for category in self.results:
                if category in baseline:
                    current = self.results[category]['avg_time']
                    base = baseline[category]['avg_time']

                    if current < base:
                        improvement = ((base - current) / base) * 100
                        print(f"{category"15"} | {improvement"+6.1f"}% faster")
                    elif current > base:
                        degradation = ((current - base) / base) * 100
                        print(f"{category"15"} | {degradation"+6.1f"}% slower")
                    else:
                        print(f"{category"15"} | No change")
                else:
                    print(f"{category"15"} | New benchmark")

        except FileNotFoundError:
            print(f"❌ Baseline file not found: {baseline_file}")
        except Exception as e:
            print(f"❌ Error comparing with baseline: {e}")


def main():
    """Main benchmark function."""

    parser = argparse.ArgumentParser(description="Benchmark test performance")
    parser.add_argument("--runs", "-r", type=int, default=3,
                       help="Number of runs per category (default: 3)")
    parser.add_argument("--categories", "-c",
                       default="fast,integration,api,unit",
                       help="Comma-separated list of categories to benchmark")
    parser.add_argument("--baseline", "-b",
                       help="Baseline file to compare against")
    parser.add_argument("--output", "-o",
                       help="Output file for results")

    args = parser.parse_args()

    categories = [cat.strip() for cat in args.categories.split(",")]

    benchmark = TestBenchmark()
    benchmark.run_all_benchmarks(categories, args.runs)
    benchmark.print_summary()

    if args.baseline:
        benchmark.compare_with_baseline(args.baseline)

    if args.output:
        benchmark.save_results(args.output)
    else:
        benchmark.save_results()


if __name__ == "__main__":
    main()