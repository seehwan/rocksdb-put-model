#!/usr/bin/env python3
"""
Verify why the calculated S_max values are stable
"""

import pandas as pd
import numpy as np

def verify_stability():
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    initial_end = 9.81
    middle_end = 42.0
    
    initial_df = df[df['time_hours'] < initial_end]
    middle_df = df[(df['time_hours'] >= initial_end) & (df['time_hours'] < middle_end)]
    final_df = df[df['time_hours'] >= middle_end]
    
    # Recommended values
    recommended = {
        'Initial': 98076,
        'Middle': 82301,
        'Final': 74821
    }
    
    print("=" * 80)
    print("Stability Verification")
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
        recommended_rate = recommended[phase_name]
        
        # Check 1: What % of time does actual QPS exceed recommended rate?
        exceed_count = np.sum(qps > recommended_rate)
        exceed_pct = exceed_count / len(qps) * 100
        
        # Check 2: When it exceeds, by how much?
        exceeded_values = qps[qps > recommended_rate]
        avg_exceedance = np.mean(exceeded_values) / recommended_rate if len(exceeded_values) > 0 else 0
        max_exceedance = np.max(exceeded_values) / recommended_rate if len(exceeded_values) > 0 else 0
        
        # Check 3: What % of time is actual QPS between 50% and 150% of recommended?
        within_range = np.sum((qps >= 0.5 * recommended_rate) & (qps <= 1.5 * recommended_rate))
        within_range_pct = within_range / len(qps) * 100
        
        print(f"\n{phase_name} Phase:")
        print(f"  Recommended S_max: {recommended_rate:.0f} QPS")
        print(f"  Mean actual QPS: {mean_qps:.0f} QPS")
        print(f"  Mean as % of recommended: {mean_qps/recommended_rate*100:.1f}%")
        
        print(f"\n  Verification:")
        print(f"    Time above recommended: {exceed_pct:.1f}%")
        if exceed_pct > 0:
            print(f"    Average exceedance: {avg_exceedance:.1f}x")
            print(f"    Max exceedance: {max_exceedance:.1f}x")
        print(f"    Time within ±50% range: {within_range_pct:.1f}%")
        
        # Check 4: Stability within recommended rate
        below_recommended = qps[qps <= recommended_rate]
        if len(below_recommended) > 0:
            cv_below = np.std(below_recommended) / np.mean(below_recommended) if np.mean(below_recommended) > 0 else 0
            print(f"    CV when below recommended: {cv_below:.3f}")
            print(f"      -> {'Stable' if cv_below < 0.1 else 'Somewhat stable' if cv_below < 0.3 else 'Unstable'}")
    
    print("\n" + "=" * 80)
    print("Critical Analysis:")
    print("=" * 80)
    print("\nThese values are NOT necessarily 'stable' because:")
    print("1. If actual QPS frequently exceeds the recommended rate,")
    print("   RocksDB will still be unstable")
    print("2. The recommended rate is based on statistical safety,")
    print("   not on actual stability guarantees")
    print("\nTrue stability would require:")
    print("- Rate limiting to cap QPS at the recommended rate")
    print("- Or choosing a rate where most QPS values naturally fall below it")
    
if __name__ == '__main__':
    verify_stability()


