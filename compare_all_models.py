#!/usr/bin/env python3
"""
Compare Original V5.3 vs Enhanced V5.3 (WA/RA adjustment)

Test all phases with optimal and non-optimal WA/RA scenarios
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.v5_3_initial_phase_optimized import V5_3InitialPhaseOptimized
from model.v5_3_wa_ra_enhanced import V5_3Enhanced
import numpy as np


def main():
    print("=" * 80)
    print("🔬 V5.3 Original vs Enhanced Comparison")
    print("=" * 80)
    
    original_model = V5_3InitialPhaseOptimized()
    enhanced_model = V5_3Enhanced()
    
    test_cases = [
        {
            'name': 'Initial - Optimal WA/RA',
            'device_bw': 4116.6, 'phase': 'initial',
            'context': {'wa': 1.2, 'ra': 0.1, 'cv': 0.538},
            'actual': 138769
        },
        {
            'name': 'Initial - High WA/RA',
            'device_bw': 4116.6, 'phase': 'initial',
            'context': {'wa': 2.0, 'ra': 0.5, 'cv': 0.538},
            'actual': 138769
        },
        {
            'name': 'Middle - Optimal',
            'device_bw': 2595.7, 'phase': 'middle',
            'context': {'wa': 2.5, 'ra': 0.8, 'cv': 0.272},
            'actual': 114472
        },
        {
            'name': 'Final - Optimal',
            'device_bw': 1074.8, 'phase': 'final',
            'context': {'wa': 3.5, 'ra': 0.8, 'cv': 0.041, 'lsm_depth': 7},
            'actual': 109678
        },
        {
            'name': 'Final - High WA',
            'device_bw': 1074.8, 'phase': 'final',
            'context': {'wa': 5.0, 'ra': 1.2, 'cv': 0.041, 'lsm_depth': 7},
            'actual': 109678
        }
    ]
    
    print(f"\n{'Test Case':<30} {'Original':<15} {'Enhanced':<15} {'Improvement':<15}")
    print("-" * 80)
    
    results = []
    
    for test in test_cases:
        # Original
        orig_result = original_model.predict_s_max(
            test['device_bw'], test['phase'], test['context']
        )
        orig_acc = (1 - abs(orig_result.predicted_s_max - test['actual']) / test['actual']) * 100
        
        # Enhanced
        enh_result = enhanced_model.predict_s_max(
            test['device_bw'], test['phase'], test['context']
        )
        enh_acc = (1 - abs(enh_result.predicted_s_max - test['actual']) / test['actual']) * 100
        
        improvement = enh_acc - orig_acc
        
        results.append({
            'name': test['name'],
            'original': orig_acc,
            'enhanced': enh_acc,
            'improvement': improvement
        })
        
        print(f"{test['name']:<30} {orig_acc:>7.1f}%     {enh_acc:>7.1f}%     {improvement:>+7.1f}%")
    
    # Summary
    orig_avg = np.mean([r['original'] for r in results])
    enh_avg = np.mean([r['enhanced'] for r in results])
    avg_improvement = enh_avg - orig_avg
    
    print("-" * 80)
    print(f"{'Average':<30} {orig_avg:>7.1f}%     {enh_avg:>7.1f}%     {avg_improvement:>+7.1f}%")
    
    print("\n" + "=" * 80)
    print("📊 Summary")
    print("=" * 80)
    print(f"  Original V5.3 Average: {orig_avg:.1f}%")
    print(f"  Enhanced V5.3 Average: {enh_avg:.1f}%")
    print(f"  Overall Improvement: {avg_improvement:+.1f}%")
    
    # Best improvements
    improvements = [(r['name'], r['improvement']) for r in results]
    improvements.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n  Top 3 Improvements:")
    for i, (name, imp) in enumerate(improvements[:3], 1):
        print(f"    {i}. {name}: {imp:+.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ Comparison Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

