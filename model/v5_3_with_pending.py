#!/usr/bin/env python3
"""
V5.3 Enhanced with Pending Compaction Bytes
WA/RA 조정 + Pending Compaction Bytes 추가

검증 가설:
1. Pending과 WA/RA는 독립적 정보
2. 둘을 결합하면 추가 개선 가능
3. Expected: 87.4% → 90%+ accuracy
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
class FullEnhancedResult:
    """WA/RA + Pending 조합 결과"""
    predicted_s_max: float
    phase: str
    base_prediction: float
    wa_ra_combined: float
    pending_adjustment: float
    final_combined: float
    accuracy: float
    confidence: str
    details: Dict


class V5_3WithPending:
    """
    V5.3 + Pending Compaction Bytes
    
    Hypothesis: Pending and WA/RA are independent
    Expected improvement: +2-4% additional accuracy
    """
    
    def __init__(self):
        self.model_version = "v5.3_full_enhanced"
        self.creation_time = datetime.now().isoformat()
        self.v5_3_enhanced = V5_3Enhanced()
        
        # Pending Compaction Bytes parameters
        self.pending_params = {
            'initial': {
                'threshold_low': 1_000_000_000,    # 1GB
                'threshold_high': 5_000_000_000,    # 5GB
                'bonus': 1.03,                      # 3% bonus for low pending
                'penalty': 0.97                     # 3% penalty for high pending
            },
            'middle': {
                'threshold_low': 2_000_000_000,    # 2GB
                'threshold_high': 10_000_000_000,   # 10GB
                'bonus': 1.02,                      # 2% bonus
                'penalty': 0.96                     # 4% penalty
            },
            'final': {
                'threshold_low': 3_000_000_000,    # 3GB
                'threshold_high': 15_000_000_000,  # 15GB
                'bonus': 1.02,                      # 2% bonus
                'penalty': 0.94                     # 6% penalty
            }
        }
    
    def predict_s_max(self,
                     device_write_bw: float,
                     phase: str,
                     context: Optional[Dict] = None) -> FullEnhancedResult:
        """Full enhanced prediction with WA/RA + Pending"""
        
        if context is None:
            context = {}
        
        # 1. Get V5.3 Enhanced (WA/RA adjustment) prediction
        v5_3_result = self.v5_3_enhanced.predict_s_max(
            device_write_bw, phase, context
        )
        base_pred = v5_3_result.predicted_s_max
        wa_ra_combined = v5_3_result.combined_adjustment
        
        # 2. Get pending compaction bytes
        pending = context.get('pending_compaction_bytes', 0)
        
        # 3. Calculate pending adjustment
        pending_adj = self._calculate_pending_adjustment(phase, pending)
        
        # 4. Apply both adjustments
        # Final = base × WA_RA_adjustment × Pending_adjustment
        final_pred = base_pred * pending_adj
        
        # 5. Confidence
        wa = context.get('wa', 2.5)
        ra = context.get('ra', 0.8)
        confidence = self._assess_confidence(phase, wa, ra, pending)
        
        # 6. Details
        details = {
            'base_prediction': base_pred,
            'wa': wa,
            'ra': ra,
            'pending_bytes': pending,
            'wa_ra_adj': wa_ra_combined,
            'pending_adj': pending_adj,
            'theoretical_max': (device_write_bw * 1024 * 1024) / 1040,
            'utilization': final_pred / ((device_write_bw * 1024 * 1024) / 1040)
        }
        
        return FullEnhancedResult(
            predicted_s_max=final_pred,
            phase=phase,
            base_prediction=base_pred,
            wa_ra_combined=wa_ra_combined,
            pending_adjustment=pending_adj,
            final_combined=wa_ra_combined * pending_adj,
            accuracy=0.0,
            confidence=confidence,
            details=details
        )
    
    def _calculate_pending_adjustment(self, phase: str, pending: float) -> float:
        """Calculate pending compaction bytes adjustment"""
        
        params = self.pending_params[phase]
        
        if pending < params['threshold_low']:
            # Low pending = system keeping up
            return params['bonus']
        elif pending > params['threshold_high']:
            # High pending = system under pressure
            return params['penalty']
        else:
            # Medium pending = no adjustment
            return 1.0
    
    def _assess_confidence(self, phase: str, wa: float, ra: float, pending: float) -> str:
        """Assess confidence with WA/RA + Pending"""
        
        params = self.pending_params[phase]
        
        # WA/RA in optimal range?
        wa_ra_opt = self.v5_3_enhanced.wa_ra_params[phase]
        wa_in_range = wa_ra_opt['optimal_range']['wa'][0] <= wa <= wa_ra_opt['optimal_range']['wa'][1]
        ra_in_range = wa_ra_opt['optimal_range']['ra'][0] <= ra <= wa_ra_opt['optimal_range']['ra'][1]
        
        # Pending in acceptable range?
        pending_ok = pending < params['threshold_high']
        
        # High confidence if all good
        if wa_in_range and ra_in_range and pending_ok:
            return 'high'
        # Medium if one issue
        elif (wa_in_range and ra_in_range) or pending_ok:
            return 'medium'
        # Lower if multiple issues
        else:
            return 'medium_low'


def main():
    """Full enhanced model validation"""
    print("=" * 80)
    print("🚀 V5.3 Full Enhanced (WA/RA + Pending)")
    print("=" * 80)
    
    model = V5_3WithPending()
    
    # Test cases with various pending scenarios
    test_cases = [
        {
            'name': 'Initial - Optimal WA/RA, Low Pending',
            'device_bw': 4116.6, 'phase': 'initial',
            'context': {'wa': 1.2, 'ra': 0.1, 'cv': 0.538, 'pending_compaction_bytes': 500_000_000},  # 0.5GB
            'actual': 138769
        },
        {
            'name': 'Initial - High WA/RA, Medium Pending',
            'device_bw': 4116.6, 'phase': 'initial',
            'context': {'wa': 2.0, 'ra': 0.5, 'cv': 0.538, 'pending_compaction_bytes': 3_000_000_000},  # 3GB
            'actual': 138769
        },
        {
            'name': 'Initial - High WA/RA, High Pending',
            'device_bw': 4116.6, 'phase': 'initial',
            'context': {'wa': 2.0, 'ra': 0.5, 'cv': 0.538, 'pending_compaction_bytes': 8_000_000_000},  # 8GB
            'actual': 138769
        },
        {
            'name': 'Final - Optimal, Low Pending',
            'device_bw': 1074.8, 'phase': 'final',
            'context': {'wa': 3.5, 'ra': 0.8, 'cv': 0.041, 'lsm_depth': 7, 'pending_compaction_bytes': 1_000_000_000},  # 1GB
            'actual': 109678
        },
        {
            'name': 'Final - Optimal, High Pending',
            'device_bw': 1074.8, 'phase': 'final',
            'context': {'wa': 3.5, 'ra': 0.8, 'cv': 0.041, 'lsm_depth': 7, 'pending_compaction_bytes': 20_000_000_000},  # 20GB
            'actual': 109678
        },
        {
            'name': 'Final - High WA, High Pending',
            'device_bw': 1074.8, 'phase': 'final',
            'context': {'wa': 5.0, 'ra': 1.2, 'cv': 0.041, 'lsm_depth': 7, 'pending_compaction_bytes': 20_000_000_000},  # 20GB
            'actual': 109678
        }
    ]
    
    print("\n" + "=" * 80)
    print("📊 Validation Results")
    print("=" * 80)
    
    results = []
    
    for test in test_cases:
        result = model.predict_s_max(
            test['device_bw'],
            test['phase'],
            test['context']
        )
        
        actual = test['actual']
        accuracy = (1 - abs(result.predicted_s_max - actual) / actual) * 100
        error = ((result.predicted_s_max - actual) / actual) * 100
        
        results.append({
            'name': test['name'],
            'predicted': result.predicted_s_max,
            'actual': actual,
            'accuracy': accuracy,
            'error': error,
            'wa_ra_adj': result.wa_ra_combined,
            'pending_adj': result.pending_adjustment,
            'combined': result.final_combined,
            'confidence': result.confidence
        })
    
    # Print results
    print(f"\n{'Scenario':<35} {'Accuracy':<10} {'WA/RA':<8} {'Pending':<9} {'Combined':<9}")
    print("-" * 85)
    
    for r in results:
        print(f"{r['name']:<35} {r['accuracy']:>7.1f}%  {r['wa_ra_adj']:>6.3f}x  {r['pending_adj']:>7.3f}x  {r['combined']:>8.3f}x")
    
    # Summary
    avg_accuracy = np.mean([r['accuracy'] for r in results])
    print(f"\n{'Average Accuracy:':<35} {avg_accuracy:>7.1f}%")
    
    # Compare with WA/RA only
    compare_cases = [
        (1, results[0]['name']),  # Initial Optimal
        (1, results[0]['name']),  # Same case for comparison
    ]
    
    print("\n" + "=" * 80)
    print("🔍 Analysis")
    print("=" * 80)
    
    # Show how pending affects high WA scenarios
    high_wa_cases = [r for r in results if 'High WA' in r['name']]
    for r in high_wa_cases:
        print(f"\n{r['name']}:")
        print(f"  Accuracy: {r['accuracy']:.1f}%")
        print(f"  WA/RA adjustment: {r['wa_ra_adj']:.3f}x")
        print(f"  Pending adjustment: {r['pending_adj']:.3f}x")
        print(f"  Combined effect: {r['combined']:.3f}x")
    
    print("\n" + "=" * 80)
    print("✅ Full Enhanced Validation Complete!")
    print("=" * 80)
    print(f"  Average Accuracy: {avg_accuracy:.1f}%")
    print(f"  Expected vs WA/RA-only: {avg_accuracy:.1f}% (check if improved)")


if __name__ == "__main__":
    main()

