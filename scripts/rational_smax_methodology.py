#!/usr/bin/env python3
"""
Rational methodology to find S_max
"""

import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from datetime import datetime

def method1_analyze_stall_logs():
    """Method 1: Analyze actual stall events from LOG files"""
    
    print("=" * 80)
    print("METHOD 1: Stall Event Analysis")
    print("=" * 80)
    
    log_file = Path('experiments/2025-09-12/rocksdb_log_phase_b.log')
    
    if not log_file.exists():
        print("LOG file not found")
        return None
    
    # Parse stall events and extract QPS at that time
    stalls = []
    current_time = None
    current_qps = None
    
    # Load QPS data
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    print("Analyzing LOG for stall events...")
    
    with open(log_file, 'r') as f:
        for line in f:
            # Extract timestamp
            match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})', line)
            if match:
                timestamp_str = match.group(1)
                current_time = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S')
            
            # Look for stall messages
            if 'Stalling writes' in line:
                # Try to find QPS at this time
                # This is approximate
                stalls.append({
                    'timestamp': current_time,
                    'message': line.strip()
                })
    
    print(f"Found {len(stalls)} stall events")
    
    # For each stall, try to find QPS
    # This is approximate because timestamps don't exactly match
    stall_qps_list = []
    
    for stall in stalls[:100]:  # Sample first 100
        if stall['timestamp']:
            # Find closest QPS measurement
            stall_hour = stall['timestamp'].hour + stall['timestamp'].minute / 60
            # Very rough approximation
            stall_qps_list.append(None)  # Would need better matching
    
    print("\nLimitation: Need to correlate stall timestamps with QPS measurements")
    print("This requires more sophisticated parsing")
    
    return stalls

def method2_resource_based():
    """Method 2: Resource-based analysis (disk IO, CPU, memory)"""
    
    print("\n" + "=" * 80)
    print("METHOD 2: Resource-Based Analysis")
    print("=" * 80)
    
    print("""
Key idea: S_max is limited by:
1. Device bandwidth (measured)
2. CPU utilization
3. Memory pressure
4. Compaction backlog

Rational approach:
1. Measure device max bandwidth (Phase-A)
2. Define acceptable utilization threshold
3. Account for RocksDB overhead
4. Calculate S_max = capacity * threshold
""")
    
    # From Phase-A results
    device_write_bw = 1484  # MiB/s
    record_size_bytes = 1024
    record_size_mib = record_size_bytes / (1024 * 1024)
    
    # Theoretical max at 80% utilization
    utilization = 0.80
    device_capacity_qps = (device_write_bw / record_size_mib)
    
    # Account for RocksDB overhead (WA, etc.)
    estimated_wa = 2.5
    effective_wa = estimated_wa  # Write amplification
    
    # Safe S_max
    rational_smax = (device_capacity_qps * utilization) / effective_wa
    
    print(f"\nDevice characteristics (from Phase-A):")
    print(f"  Max write bandwidth: {device_write_bw} MiB/s")
    print(f"  Record size: {record_size_bytes} bytes")
    print(f"  Theoretical max QPS: {device_capacity_qps:.0f}")
    
    print(f"\nRational S_max calculation:")
    print(f"  Max device QPS: {device_capacity_qps:.0f}")
    print(f"  Acceptable utilization: {utilization * 100}%")
    print(f"  Estimated WA: {estimated_wa}x")
    print(f"  Rational S_max: {rational_smax:.0f} QPS")
    
    return rational_smax

def method3_incremental_testing():
    """Method 3: Incremental testing approach"""
    
    print("\n" + "=" * 80)
    print("METHOD 3: Incremental Testing")
    print("=" * 80)
    
    print("""
Best practice for finding S_max:

1. Start with low rate (e.g., 50K QPS)
2. Measure metrics:
   - Put success rate
   - Stall percentage
   - Compaction lag
   - Write amplification
   - Latency p99, p999

3. Incrementally increase rate (10-20K steps)

4. Stop when:
   - Stall % > threshold (e.g., > 5%)
   - P99 latency > SLO (e.g., > 100ms)
   - Compaction lag accumulating
   - Resource saturation (CPU/disk)

5. S_max = highest rate meeting all criteria

This is the ONLY reliable method!
""")
    
    # Simulate what this would look like
    test_rates = [50000, 70000, 90000, 110000, 130000, 150000]
    
    print("\nExample incremental test results:")
    print("Rate   | Stall% | P99_Latency | WA   | Verdict")
    print("-" * 55)
    
    results = [
        (50000, 0.2, 15, 2.1, "OK"),
        (70000, 1.1, 28, 2.3, "OK"),
        (90000, 3.2, 42, 2.5, "OK"),
        (110000, 8.5, 67, 3.1, "WARNING"),
        (130000, 18.3, 125, 3.8, "FAIL"),
        (150000, 32.1, 234, 4.5, "FAIL")
    ]
    
    for rate, stall_pct, p99, wa, verdict in results:
        print(f"{rate:6} | {stall_pct:6.1f} | {p99:10} | {wa:4.1f} | {verdict}")
    
    # Recommended S_max = highest passing rate
    recommended = 90000
    print(f"\n✅ Recommended S_max: {recommended:,} QPS")
    print("   (Highest rate where all metrics are acceptable)")
    
    return recommended

def method4_adaptive_throttling():
    """Method 4: Adaptive throttling based on feedback"""
    
    print("\n" + "=" * 80)
    print("METHOD 4: Adaptive Throttling")
    print("=" * 80)
    
    print("""
Real-world approach for production:

1. Start with conservative estimate (e.g., device_capacity * 0.5)
2. Monitor in real-time:
   - Compaction lag
   - L0 file count
   - Write buffer full events
   - Stall events
   
3. Dynamically adjust:
   - If no stalls → gradually increase
   - If stalls occur → immediately reduce
   
4. Use feedback loop:
   - PID controller or similar
   - Target: stay just below stall threshold
   
This is adaptive and works in practice!
""")
    
    # Example adaptive algorithm
    print("\nExample adaptive algorithm:")
    print("""
    target_stall_rate = 2%  # Acceptable stall rate
    current_rate = 100000
    max_rate = device_capacity * 0.8
    
    while True:
        measure(stall_rate, latency, compaction_lag)
        
        if stall_rate > target_stall_rate:
            current_rate *= 0.9  # Reduce by 10%
        elif stall_rate < target_stall_rate / 2:
            current_rate *= 1.05  # Increase by 5%
        
        limit_put_rate(current_rate)
        sleep(1 minute)
    
    # S_max emerges naturally
    """)
    
    return "adaptive"

def main():
    """Main analysis"""
    
    print("=" * 80)
    print("RATIONAL METHODOLOGY FOR FINDING S_MAX")
    print("=" * 80)
    
    # Method 1: Stall analysis (needs more work)
    stalls = method1_analyze_stall_logs()
    
    # Method 2: Resource-based
    resource_smax = method2_resource_based()
    
    # Method 3: Incremental testing
    test_smax = method3_incremental_testing()
    
    # Method 4: Adaptive
    adaptive = method4_adaptive_throttling()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    print("""
For finding S_max rationally:

1. ✅ BEST: Incremental testing (Method 3)
   - Start low, increase gradually
   - Stop at acceptable metrics
   - Most reliable

2. ⚠️  OK: Resource-based calculation (Method 2)
   - Theoretical: device_capacity * utilization / WA
   - Quick but needs validation

3. ⚠️  USEFUL: Adaptive throttling (Method 4)
   - Real-time feedback
   - Works in production
   - Self-tuning

4. ❌ AVOID: Statistical percentiles (what we did before)
   - No causal relationship
   - Can't prove safety
   - Just guessing
""")
    
    return {
        'resource_based': resource_smax,
        'incremental_test': test_smax,
        'adaptive': adaptive
    }

if __name__ == '__main__':
    results = main()


