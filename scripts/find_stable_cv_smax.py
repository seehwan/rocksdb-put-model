#!/usr/bin/env python3
"""
Find S_max where CV stays low (stable performance)
"""

import pandas as pd
import numpy as np
import json
from scipy import stats

def analyze_cv_stability():
    """Analyze how CV changes with different rate limits"""
    
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    initial_end = 9.81
    middle_end = 42.0
    
    initial_df = df[df['time_hours'] < initial_end]
    middle_df = df[(df['time_hours'] >= initial_end) & (df['time_hours'] < middle_end)]
    final_df = df[df['time_hours'] >= middle_end]
    
    print("=" * 80)
    print("Finding S_max for Low CV (Stable Performance)")
    print("=" * 80)
    
    phases = [
        ('Initial', initial_df),
        ('Middle', middle_df),
        ('Final', final_df)
    ]
    
    results = {}
    
    for phase_name, phase_df in phases:
        qps = phase_df['interval_qps'].values
        
        # Strategy 1: Find rate where CV would be < 0.1 (stable)
        # This would require filtering out spikes
        
        # Strategy 2: Use percentiles to find "typical" stable range
        p25 = np.percentile(qps, 25)
        p50 = np.percentile(qps, 50)  # median
        p75 = np.percentile(qps, 75)
        
        # Strategy 3: Mode-based (most common value range)
        # Bin the data and find the modal range
        hist, bin_edges = np.histogram(qps, bins=100)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        modal_bin_idx = np.argmax(hist)
        modal_range = (bin_edges[modal_bin_idx], bin_edges[modal_bin_idx+1])
        
        # Strategy 4: Trimmed mean (remove outliers)
        trimmed_mean = stats.trim_mean(qps, proportiontocut=0.1)
        
        # Strategy 5: IQR-based range (stable middle)
        q1 = np.percentile(qps, 25)
        q3 = np.percentile(qps, 75)
        iqr = q3 - q1
        stable_max = q3  # Upper bound of stable range
        
        # Strategy 6: CV of values below median (stable portion)
        below_median = qps[qps <= p50]
        cv_below_median = np.std(below_median) / np.mean(below_median) if len(below_median) > 0 and np.mean(below_median) > 0 else 0
        
        # Strategy 7: P90 of stable range (where CV < 0.2)
        # Define stable as values within ±1 std of mean
        mean_qps = np.mean(qps)
        std_qps = np.std(qps)
        stable_values = qps[(qps >= mean_qps - std_qps) & (qps <= mean_qps + std_qps)]
        p90_stable = np.percentile(stable_values, 90) if len(stable_values) > 0 else mean_qps
        
        results[phase_name] = {
            'mean': np.mean(qps),
            'median': p50,
            'p25': p25,
            'p75': p75,
            'modal_range': modal_range,
            'trimmed_mean': trimmed_mean,
            'stable_max_iqr': stable_max,
            'p90_stable': p90_stable,
            'cv_below_median': cv_below_median,
            'full_cv': np.std(qps) / np.mean(qps),
            'stddev': np.std(qps)
        }
        
        print(f"\n{phase_name} Phase:")
        print(f"  Current CV: {results[phase_name]['full_cv']:.3f} (unstable)")
        print(f"  CV when below median: {cv_below_median:.3f} {'(stable)' if cv_below_median < 0.1 else '(still unstable)'}")
        
        print(f"\n  Candidate S_max values:")
        print(f"    Median (P50): {p50:.0f} QPS")
        print(f"    Trimmed Mean: {trimmed_mean:.0f} QPS")
        print(f"    Modal Range: {modal_range[0]:.0f} - {modal_range[1]:.0f} QPS")
        print(f"    IQR Stable: {stable_max:.0f} QPS")
        print(f"    P90 of Stable: {p90_stable:.0f} QPS")
        
        # Recommend the lowest value with stable CV
        if cv_below_median < 0.1:
            recommended = max(p50, trimmed_mean, modal_range[0])
            print(f"\n  ✅ Recommended S_max: {recommended:.0f} QPS (CV < 0.1)")
        else:
            # If even below median is unstable, use much more conservative
            recommended = p25
            print(f"\n  ⚠️  Even below median is unstable. Use conservative: {recommended:.0f} QPS")
    
    # Save results
    with open('stable_cv_smax_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    
    for phase_name in ['Initial', 'Middle', 'Final']:
        r = results[phase_name]
        if r['cv_below_median'] < 0.1:
            print(f"{phase_name}: Use S_max = {max(r['median'], r['trimmed_mean'], r['modal_range'][0]):.0f} QPS")
        else:
            print(f"{phase_name}: System is fundamentally unstable even at low rates")
    
    return results

if __name__ == '__main__':
    results = analyze_cv_stability()


