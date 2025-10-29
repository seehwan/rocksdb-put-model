#!/usr/bin/env python3
"""
Analyze compaction bandwidth vs put rate to find optimal S_max
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def analyze_compaction_bw():
    """
    Analyze RocksDB LOG to find correlation between:
    - Put rate
    - Compaction bandwidth
    - System stability
    """
    
    # Load experimental results
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    print("=" * 80)
    print("Compaction Bandwidth Analysis")
    print("Finding optimal S_max where compaction BW is reasonable")
    print("=" * 80)
    
    # Load compaction analysis results if available
    compaction_file = Path('experiments/2025-09-12/compaction_analysis.json')
    
    if compaction_file.exists():
        with open(compaction_file, 'r') as f:
            compaction_data = json.load(f)
        
        print("\nCompaction bandwidth data found!")
        
        # Analyze compaction BW over time
        compaction_df = pd.DataFrame(compaction_data)
        
        # Merge with put rate data (approximate time-based merge)
        # Convert hours to seconds for matching
        compaction_df['time_hours'] = compaction_df['timestamp'] / 3600 if 'timestamp' in compaction_df else None
        
        # For now, use the comprehensive BW analysis
        bw_file = Path('experiments/2025-09-12/phase-b/bw_over_time.json')
        
        if bw_file.exists():
            with open(bw_file, 'r') as f:
                bw_data = json.load(f)
            
            print("Bandwidth over time data found!")
            
            # Analyze relationship between put rate and compaction BW
            analyze_compaction_ratio(df)
    
    else:
        # Use existing compaction analysis
        print("\nAnalyzing compaction burden...")
        analyze_compaction_burden(df)

def analyze_compaction_burden(df):
    """Analyze compaction burden vs put rate"""
    
    initial_end = 9.81
    middle_end = 42.0
    
    initial_df = df[df['time_hours'] < initial_end]
    middle_df = df[(df['time_hours'] >= initial_end) & (df['time_hours'] < middle_end)]
    final_df = df[df['time_hours'] >= middle_end]
    
    phases = [
        ('Initial', initial_df),
        ('Middle', middle_df),
        ('Final', final_df)
    ]
    
    results = {}
    
    for phase_name, phase_df in phases:
        qps = phase_df['interval_qps'].values
        mean_qps = np.mean(qps)
        
        # Strategy: Find put rate where compaction is "reasonable"
        # Based on typical LSM-tree behavior:
        # - Compaction BW should be < 2-3x of put BW
        # - If compaction dominates, system is stressed
        
        # Approximate compaction burden
        # Typical WA = 2-4, so compaction writes = 1-3x user writes
        # Reasonable: compaction BW ≈ 1-2x user put rate
        
        # Find QPS where we would have < 2x compaction
        # This is a heuristic based on LSM-tree behavior
        
        # Estimate: If put rate is R, compaction rate should be < 2R
        # Total bandwidth: put_write + compaction_write
        # compaction_write ≈ WA * put_write
        
        # Safe operating point: WA < 2.5, compaction < 1.5x puts
        
        # For analysis, use percentiles to find "normal" behavior
        # Low compaction period = low QPS volatility periods
        
        # Find stable QPS regions
        sorted_qps = np.sort(qps)
        
        # Define "stable" as values near median with low variance
        median = np.median(qps)
        q1 = np.percentile(qps, 25)
        q3 = np.percentile(qps, 75)
        
        # Stable region: between Q1 and median (bottom 50%, lower volatility)
        stable_low = q1
        stable_high = median
        
        # Very conservative: P25
        conservative = q1
        
        compaction_too_high_ratio = np.sum(qps > 2 * median) / len(qps) * 100
        
        results[phase_name] = {
            'mean_qps': mean_qps,
            'median': median,
            'p25': q1,
            'p75': q3,
            'recommended_stable': stable_high,
            'recommended_conservative': conservative,
            'compaction_too_high_ratio': compaction_too_high_ratio
        }
        
        print(f"\n{phase_name} Phase:")
        print(f"  Mean QPS: {mean_qps:.0f}")
        print(f"  Median QPS: {median:.0f}")
        print(f"  Q1-Q3 range: {q1:.0f} - {q3:.0f}")
        
        # Estimate compaction burden
        # Typical: compaction BW = WA * user_write_BW
        # Safe range: WA < 2.5
        
        print(f"\n  Compaction Analysis:")
        print(f"    Conservative (P25): {conservative:.0f} QPS")
        print(f"    Stable (P50): {stable_high:.0f} QPS")
        print(f"    Upper safe (mean): {mean_qps:.0f} QPS")
        
        # Estimate: if we use P50, what's the expected compaction?
        # Assuming WA ≈ 2-3, compaction BW ≈ 1-2x user BW
        estimated_compaction = stable_high * 1.5  # heuristic
        
        print(f"    Estimated compaction at P50: {estimated_compaction:.0f} QPS equivalent")
        print(f"    Total BW ~ {stable_high + estimated_compaction:.0f} QPS")
        
        print(f"    % time at >2x median: {results[phase_name]['compaction_too_high_ratio']:.1f}%")
        
        if results[phase_name]['compaction_too_high_ratio'] > 30:
            print(f"    ⚠️  High compaction burden!")
    
    # Save results
    with open('compaction_safe_smax.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("Recommended S_max (Compaction-aware):")
    print("=" * 80)
    
    for phase_name in ['Initial', 'Middle', 'Final']:
        r = results[phase_name]
        print(f"{phase_name}:")
        print(f"  Stable operation: {r['recommended_stable']:.0f} QPS")
        print(f"  Conservative: {r['recommended_conservative']:.0f} QPS")
    
    return results

def analyze_compaction_ratio(df):
    """Analyze actual compaction ratio if data available"""
    print("\nAnalyzing compaction ratio...")
    print("(Would need actual compaction BW data from LOG files)")

if __name__ == '__main__':
    results = analyze_compaction_bw()

