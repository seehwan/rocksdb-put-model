#!/usr/bin/env python3
"""
Analyze RocksDB stability based on QPS variations
"""

import pandas as pd
import numpy as np

def analyze_stability():
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    # Phase boundaries
    initial_end = 9.81
    middle_end = 42.0
    
    initial_df = df[df['time_hours'] < initial_end]
    middle_df = df[(df['time_hours'] >= initial_end) & (df['time_hours'] < middle_end)]
    final_df = df[df['time_hours'] >= middle_end]
    
    print("=" * 80)
    print("RocksDB Stability Analysis")
    print("=" * 80)
    
    phases = [
        ('Initial', initial_df),
        ('Middle', middle_df),
        ('Final', final_df)
    ]
    
    for phase_name, phase_df in phases:
        qps = phase_df['interval_qps'].values
        
        mean_qps = np.mean(qps)
        std_qps = np.std(qps)
        cv = std_qps / mean_qps if mean_qps > 0 else 0
        min_qps = np.min(qps)
        max_qps = np.max(qps)
        
        # What % of the time is QPS within ±20% of mean?
        within_20pct = np.sum(np.abs(qps - mean_qps) / mean_qps <= 0.2) / len(qps) * 100
        
        # What % of the time is QPS within ±50% of mean?
        within_50pct = np.sum(np.abs(qps - mean_qps) / mean_qps <= 0.5) / len(qps) * 100
        
        print(f"\n{phase_name} Phase:")
        print(f"  Mean QPS: {mean_qps:.0f}")
        print(f"  Std Dev: {std_qps:.0f}")
        print(f"  CV: {cv:.3f}")
        print(f"  Min QPS: {min_qps:.0f} ({min_qps/mean_qps*100:.1f}% of mean)")
        print(f"  Max QPS: {max_qps:.0f} ({max_qps/mean_qps*100:.1f}% of mean)")
        print(f"  Range: {min_qps:.0f} - {max_qps:.0f} ({(max_qps/min_qps):.1f}x variation)")
        print(f"  Within ±20%%: {within_20pct:.1f}% of time")
        print(f"  Within ±50%%: {within_50pct:.1f}% of time")
    
    print("\n" + "=" * 80)
    print("Interpretation:")
    print("=" * 80)
    print("- CV (Coefficient of Variation): Lower is better (< 0.1 = stable, > 0.5 = unstable)")
    print("- QPS variation: RocksDB is NOT stable if CV is high")
    print("- The model predicts MEAN QPS, not stability")

if __name__ == '__main__':
    analyze_stability()


