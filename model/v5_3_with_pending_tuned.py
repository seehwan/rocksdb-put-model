#!/usr/bin/env python3
"""
V5.3 Enhanced with Tuned Pending Adjustment
검증 결과: Pending은 High pressure 시에만 추가 이점

전략:
- Low Pending: No bonus (avoid over-prediction)
- High Pending: Moderate penalty (2-4%)
- Focus on preventing high-end errors
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.v5_3_wa_ra_enhanced import V5_3Enhanced


@dataclass
class TunedResult:
    predicted_s_max: float
    phase: str
    base_wa_ra: float
    pending_adj: float
    combined: float
    accuracy: float
    details: Dict


class V5_3TunedPending:
    """
    Tuned Pending Adjustment Strategy
    
    Key Findings from validation:
    1. Pending bonus causes over-prediction
    2. Only penalty on high pending is effective
    3. Keep WA/RA as primary adjustment
    """
    
    def __init__(self):
        self.model_version = "v5.3_tuned_pending"
        self.v5_3_enhanced = V5_3Enhanced()
        
        # Tuned: Only penalty, no bonus
        self.pending_params = {
            'initial': {
                'threshold_medium': 3_000_000_000,    # 3GB
                'threshold_high': 6_000_000_000,     # 6GB
                'medium_penalty': 0.98,               # 2% penalty
                'high_penalty': 0.95                  # 5% penalty
            },
            'middle': {
                'threshold_medium': 5_000_000_000,    
                'threshold_high': 10_000_000_000,
                'medium_penalty': 0.98,
                'high_penalty': 0.95
            },
            'final': {
                'threshold_medium': 8_000_000_000,
                'threshold_high': 15_000_000_000,
                'medium_penalty': 0.97,               # 3% penalty
                'high_penalty': 0.94                 # 6% penalty
            }
        }
    
    def predict_s_max(self,
                     device_write_bw: float,
                     phase: str,
                     context: Optional[Dict] = None) -> TunedResult:
        """Tuned prediction with pending adjustment"""
        
        if context is None:
            context = {}
        
        # 1. WA/RA prediction
        wa_ra_result = self.v5_3_enhanced.predict_s_max(
            device_write_bw, phase, context
        )
        base_pred = wa_ra_result.predicted_s_max
        wa_ra_adj = wa_ra_result.combined_adjustment
        
        # 2. Pending adjustment (penalty only)
        pending = context.get('pending_compaction_bytes', 0)
        pending_adj = self._calculate_pending_adjustment(phase, pending)
        
        # 3. Final prediction
        final_pred = base_pred * pending_adj
        
        details = {
            'base': base_pred,
            'wa': context.get('wa', 2.5),
            'ra': context.get('ra', 0.8),
            'pending': pending,
            'wa_ra_adj': wa_ra_adj,
            'pending_adj': pending_adj,
            'combined_adj': wa_ra_adj * pending_adj
        }
        
        return TunedResult(
            predicted_s_max=final_pred,
            phase=phase,
            base_wa_ra=base_pred,
            pending_adj=pending_adj,
            combined=wa_ra_adj * pending_adj,
            accuracy=0.0,
            details=details
        )
    
    def _calculate_pending_adjustment(self, phase: str, pending: float) -> float:
        """Calculate pending adjustment (penalty only)"""
        
        params = self.pending_params[phase]
        
        if pending > params['threshold_high']:
            return params['high_penalty']
        elif pending > params['threshold_medium']:
            return params['medium_penalty']
        else:
            return 1.0  # No adjustment


def main():
    """Tuned pending validation"""
    print("=" * 80)
    print("🎯 V5.3 Tuned Pending (Penalty Only)")
    print("=" * 80)
    
    model = V5_3TunedPending()
    
    test_cases = [
        {'name': 'Initial - Optimal WA/RA, No Pending', 'device_bw': 4116.6, 'phase': 'initial',
         'context': {'wa': 1.2, 'ra': 0.1, 'cv': 0.538, 'pending_compaction_bytes': 500_000_000}, 'actual': 138769},
        {'name': 'Initial - High WA/RA, No Pending', 'device_bw': 4116.6, 'phase': 'initial',
         'context': {'wa': 2.0, 'ra': 0.5, 'cv': 0.538, 'pending_compaction_bytes': 1_000_000_000}, 'actual': 138769},
        {'name': 'Initial - High WA/RA, High Pending', 'device_bw': 4116.6, 'phase': 'initial',
         'context': {'wa': 2.0, 'ra': 0.5, 'cv': 0.538, 'pending_compaction_bytes': 10_000_000_000}, 'actual': 138769},
        {'name': 'Final - Optimal, No Pending', 'device_bw': 1074.8, 'phase': 'final',
         'context': {'wa': 3.5, 'ra': 0.8, 'cv': 0.041, 'lsm_depth': 7, 'pending_compaction_bytes': 1_000_000_000}, 'actual': 109678},
        {'name': 'Final - Optimal, High Pending', 'device_bw': 1074.8, 'phase': 'final',
         'context': {'wa': 3.5, 'ra': 0.8, 'cv': 0.041, 'lsm_depth': 7, 'pending_compaction_bytes': 20_000_000_000}, 'actual': 109678},
        {'name': 'Final - High WA, High Pending', 'device_bw': 1074.8, 'phase': 'final',
         'context': {'wa': 5.0, 'ra': 1.2, 'cv': 0.041, 'lsm_depth': 7, 'pending_compaction_bytes': 20_000_000_000}, 'actual': 109678}
    ]
    
    print("\n" + "=" * 80)
    print("📊 Results")
    print("=" * 80)
    
    results = []
    
    print(f"\n{'Scenario':<40} {'Accuracy':<10} {'Pending Adj':<12} {'Combined':<10}")
    print("-" * 80)
    
    for test in test_cases:
        result = model.predict_s_max(
            test['device_bw'], test['phase'], test['context']
        )
        
        actual = test['actual']
        accuracy = (1 - abs(result.predicted_s_max - actual) / actual) * 100
        
        results.append({
            'name': test['name'],
            'accuracy': accuracy,
            'pending_adj': result.pending_adj,
            'combined': result.combined
        })
        
        print(f"{test['name']:<40} {accuracy:>7.1f}%     {result.pending_adj:>8.3f}x    {result.combined:>8.3f}x")
    
    avg = np.mean([r['accuracy'] for r in results])
    print(f"\n{'Average:':<40} {avg:>7.1f}%")
    
    print("\n" + "=" * 80)
    print("📈 Comparison Summary")
    print("=" * 80)
    print(f"  V5.3 Original:     84.5%")
    print(f"  V5.3 WA/RA only:  87.4%")
    print(f"  V5.3 + Pending:   {avg:.1f}%")
    
    if avg > 87.4:
        print(f"\n  ✅ Pending adds +{avg-87.4:.1f}% improvement!")
    else:
        print(f"\n  ⚠️  Pending shows {avg-87.4:.1f}% (may not be worth complexity)")
    
    print("\n" + "=" * 80)
    print("✅ Tuned Pending Validation Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

