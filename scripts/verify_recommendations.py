#!/usr/bin/env python3
"""
Verify the statistical basis for recommendations
"""

import pandas as pd
import numpy as np

def verify_recommendations():
    """Verify why 70K QPS, 42% etc are recommended"""
    
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    initial_df = df[df['time_hours'] < 9.81]
    
    qps = initial_df['interval_qps'].values
    mean_qps = np.mean(qps)
    p25 = np.percentile(qps, 25)
    p10 = np.percentile(qps, 10)
    
    print("=" * 80)
    print("Statistical Basis Verification")
    print("=" * 80)
    
    print(f"\nInitial Phase Statistics:")
    print(f"  Mean QPS: {mean_qps:.0f}")
    print(f"  P25: {p25:.0f}")
    print(f"  P10: {p10:.0f}")
    print(f"  Recommended: 70K QPS (P25-ish)")
    
    print(f"\nQuestion: Why 70K? Let's verify...")
    
    # Check 1: What % of values are <= 70K?
    pct_below_70k = np.sum(qps <= 70000) / len(qps) * 100
    print(f"\n1. Percentile of 70K QPS:")
    print(f"   {pct_below_70k:.1f}% of actual QPS values are <= 70K")
    print(f"   This means we observed this rate or lower {pct_below_70k:.1f}% of the time")
    
    # Check 2: What are actual percentiles?
    p20 = np.percentile(qps, 20)
    p30 = np.percentile(qps, 30)
    
    print(f"\n2. Actual Percentiles:")
    print(f"   P10: {p10:.0f}")
    print(f"   P20: {p20:.0f}")
    print(f"   P25: {p25:.0f}")
    print(f"   P30: {p30:.0f}")
    
    # Check if 70K matches any percentile
    if abs(p25 - 70000) < 1000:
        print(f"   → 70K ≈ P25")
    elif abs(p20 - 70000) < 1000:
        print(f"   → 70K ≈ P20")
    elif abs(p30 - 70000) < 1000:
        print(f"   → 70K ≈ P30")
    else:
        print(f"   → 70K is between P20 ({p20:.0f}) and P30 ({p30:.0f})")
    
    # Check 3: What's the basis for "42%"?
    ratio = p25 / mean_qps * 100
    print(f"\n3. Why '42%'?")
    print(f"   P25 / Mean = {p25:.0f} / {mean_qps:.0f} = {ratio:.1f}%")
    print(f"   This is where 75% of values are below this level")
    
    # Check 4: Does this actually prevent stalls?
    print(f"\n4. Does 70K prevent stalls?")
    print(f"   We CANNOT prove this from the data alone!")
    print(f"   Reason: Lower QPS might occur during stalls (cause and effect unclear)")
    print(f"   Just because QPS was low doesn't mean it's safe")
    
    # Check 5: What we're really saying
    print(f"\n5. What we're REALLY saying:")
    print(f"   'During the experiment, 75% of time QPS was ≤ {p25:.0f}'")
    print(f"   'If we limit to this rate, we won't exceed what we observed 75% of time'")
    print(f"   'But we can't prove it prevents stalls - correlation not causation'")
    
    # Check 6: The real question
    print(f"\n6. The REAL question:")
    print(f"   Did low QPS occur BECAUSE of stalls?")
    print(f"   Or did low QPS prevent stalls?")
    print(f"   Answer: We DON'T KNOW from this data alone")
    
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("""
The numbers (70K, 42%, etc.) are based on:
1. Statistical percentiles (P25, P30, etc.)
2. Observation that lower QPS values occur
3. ASSUMPTION that lower QPS = fewer stalls

BUT:
- Correlation ≠ Causation
- Low QPS might be RESULT of stalls
- We need more direct analysis of LOG files
- Actual verification requires controlled experiments
""")
    
    return {
        'mean': mean_qps,
        'p25': p25,
        'p10': p10,
        'pct_below_70k': pct_below_70k,
        'ratio': ratio
    }

if __name__ == '__main__':
    results = verify_recommendations()


