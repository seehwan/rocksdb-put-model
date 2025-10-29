#!/usr/bin/env python3
"""
Calculate STABLE S_max values
- Safe rate for RocksDB to operate without exceeding capacity
- Accounts for volatility and variation
"""

import pandas as pd
import numpy as np
import json

def load_model_params():
    """Load model parameters"""
    with open('model/v5_3_optimized_parameters.json', 'r') as f:
        data = json.load(f)
    
    params = {}
    for phase in ['initial', 'middle', 'final']:
        params[phase] = {
            'U': data['optimized_parameters'][phase]['U'],
            'C': data['optimized_parameters'][phase]['C']
        }
    
    return params

def calculate_stable_smax(phase_df, phase_name):
    """
    Calculate STABLE S_max based on:
    1. Percentile-based: P95 or P99 of actual QPS
    2. Mean minus X sigma: Mean - 2*StdDev for safety
    3. CV-adjusted: Mean / (1 + CV) to account for volatility
    """
    qps = phase_df['interval_qps'].values
    
    mean_qps = np.mean(qps)
    std_qps = np.std(qps)
    cv = std_qps / mean_qps if mean_qps > 0 else 0
    
    # Method 1: P95 - 95% of the time, QPS stays below this
    p95_qps = np.percentile(qps, 95)
    
    # Method 2: Mean - 2*StdDev (covers ~95% of normal distribution)
    safe_mean = mean_qps - 2 * std_qps
    
    # Method 3: CV-adjusted (recommended)
    # If CV is high, reduce the safe rate
    # stable_smax = mean / (1 + CV)
    stable_smax_cv = mean_qps / (1 + cv)
    
    # Method 4: Conservative (P99)
    p99_qps = np.percentile(qps, 99)
    
    results = {
        'phase': phase_name,
        'mean_qps': mean_qps,
        'std_qps': std_qps,
        'cv': cv,
        'smax_p95': max(0, p95_qps),
        'smax_p99': max(0, p99_qps),
        'smax_mean_minus_2std': max(0, safe_mean),
        'smax_cv_adjusted': max(0, stable_smax_cv),
        'recommended_smax': max(0, p95_qps)  # Use P95 as recommended
    }
    
    return results

def main():
    print("=" * 80)
    print("STABLE S_max Calculation")
    print("Safe put rate for RocksDB to operate without exceeding capacity")
    print("=" * 80)
    
    # Load experimental data
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    # Phase boundaries
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
    
    all_results = {}
    
    for phase_name, phase_df in phases:
        result = calculate_stable_smax(phase_df, phase_name)
        all_results[phase_name] = result
        
        print(f"\n{phase_name} Phase:")
        print(f"  Mean QPS: {result['mean_qps']:.0f}")
        print(f"  Std Dev: {result['std_qps']:.0f}")
        print(f"  CV: {result['cv']:.3f}")
        print(f"\n  Safe S_max options:")
        print(f"    P95 method (recommended): {result['smax_p95']:.0f} QPS")
        print(f"    P99 method: {result['smax_p99']:.0f} QPS")
        print(f"    Mean - 2*Std: {result['smax_mean_minus_2std']:.0f} QPS")
        print(f"    CV-adjusted: {result['smax_cv_adjusted']:.0f} QPS")
        print(f"\n  ✅ Recommended S_max: {result['recommended_smax']:.0f} QPS")
    
    # Save results
    with open('stable_smax_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("Summary and Recommendations:")
    print("=" * 80)
    print("\nTo ensure RocksDB operates stably:")
    print(f"  - Initial Phase (0-9.81h): Max {all_results['Initial']['recommended_smax']:.0f} QPS")
    print(f"  - Middle Phase (9.81-42.0h): Max {all_results['Middle']['recommended_smax']:.0f} QPS")
    print(f"  - Final Phase (42.0h+): Max {all_results['Final']['recommended_smax']:.0f} QPS")
    print("\nNote: These are P95 values - 95% of the time QPS stays below this rate")
    
    return all_results

if __name__ == '__main__':
    results = main()


