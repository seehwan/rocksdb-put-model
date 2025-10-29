#!/usr/bin/env python3
"""
V5.3 Enhanced with WA/RA Adjustment
Initial phase 성능 집중 개선 + WA/RA 직접 활용

핵심 개선사항:
1. WA/RA를 utilization factor 계산에 직접 활용
2. Phase-specific WA/RA adjustment
3. Amplification-bounded utilization
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import warnings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.v5_3_initial_phase_optimized import V5_3InitialPhaseOptimized, V5_3PredictionResult


@dataclass
class V5_3WARAResult:
    """WA/RA 조정 포함 예측 결과"""
    predicted_s_max: float
    phase: str
    model_version: str
    timestamp: str
    
    # V5.3 base components
    base_prediction: float
    utilization_factor: float
    calibration_factor: float
    
    # WA/RA adjustment
    wa_adjustment: float
    ra_adjustment: float
    wa_ra_combined: float
    
    # Context bonuses
    context_bonus: float
    
    # Confidence
    confidence: str


class V5_3WithWARA:
    """
    V5.3 with WA/RA Direct Adjustment
    
    핵심 아이디어:
    1. WA/RA를 utilization factor에 직접 반영
    2. Phase-specific amplification ranges
    3. Amplification-bounded adjustment
    """
    
    def __init__(self):
        self.model_version = "v5.3_wa_ra_enhanced"
        self.creation_time = datetime.now().isoformat()
        
        # V5.3 base
        self.v5_3_base = V5_3InitialPhaseOptimized()
        
        # WA/RA adjustment parameters
        self.wa_ra_adjustment = {
            'initial': {
                'nominal_wa': 1.2,
                'nominal_ra': 0.1,
                'optimal_wa_range': (1.0, 1.5),
                'optimal_ra_range': (0.1, 0.3),
                'bonus_threshold': {'wa': 1.5, 'ra': 0.3},
                'penalty_threshold': {'wa': 2.0, 'ra': 0.5},
                'wa_sensitivity': 0.15,  # 15% per unit deviation
                'ra_sensitivity': 0.10   # 10% per unit deviation
            },
            'middle': {
                'nominal_wa': 2.5,
                'nominal_ra': 0.8,
                'optimal_wa_range': (2.0, 3.0),
                'optimal_ra_range': (0.5, 1.0),
                'bonus_threshold': {'wa': 3.0, 'ra': 1.0},
                'penalty_threshold': {'wa': 4.0, 'ra': 1.5},
                'wa_sensitivity': 0.10,
                'ra_sensitivity': 0.08
            },
            'final': {
                'nominal_wa': 3.5,
                'nominal_ra': 0.8,
                'optimal_wa_range': (3.0, 4.0),
                'optimal_ra_range': (0.7, 1.0),
                'bonus_threshold': {'wa': 4.0, 'ra': 1.0},
                'penalty_threshold': {'wa': 5.0, 'ra': 1.5},
                'wa_sensitivity': 0.08,
                'ra_sensitivity': 0.06
            }
        }
    
    def predict_s_max(self,
                     device_write_bw: float,
                     phase: str,
                     context: Optional[Dict] = None) -> V5_3WARAResult:
        """
        WA/RA 조정 포함 예측
        """
        if context is None:
            context = {}
        
        # 1. V5.3 base prediction
        v5_3_result = self.v5_3_base.predict_s_max(device_write_bw, phase, context)
        base_prediction = v5_3_result.predicted_s_max
        
        # 2. WA/RA adjustment
        wa = context.get('wa', self.wa_ra_adjustment[phase]['nominal_wa'])
        ra = context.get('ra', self.wa_ra_adjustment[phase]['nominal_ra'])
        
        wa_adj, ra_adj, wa_ra_combined = self._calculate_wa_ra_adjustment(phase, wa, ra)
        
        # 3. Apply WA/RA adjustment
        # Adjusted prediction = base × WA_factor × RA_factor
        adjusted_prediction = base_prediction * wa_ra_combined
        
        # 4. Confidence assessment
        confidence = self._assess_confidence(phase, wa, ra, context)
        
        # Get utilization and calibration from V5.3
        theoretical_max = (device_write_bw * 1024 * 1024) / 1040
        utilization_factor = adjusted_prediction / theoretical_max
        
        result = V5_3WARAResult(
            predicted_s_max=adjusted_prediction,
            phase=phase,
            model_version=self.model_version,
            timestamp=datetime.now().isoformat(),
            
            base_prediction=base_prediction,
            utilization_factor=utilization_factor,
            calibration_factor=v5_3_result.initial_phase_calibration if hasattr(v5_3_result, 'initial_phase_calibration') else 1.0,
            
            wa_adjustment=wa_adj,
            ra_adjustment=ra_adj,
            wa_ra_combined=wa_ra_combined,
            
            context_bonus=1.0,  # Extract from v5_3_result if needed
            confidence=confidence
        )
        
        return result
    
    def _calculate_wa_ra_adjustment(self, phase: str, wa: float, ra: float) -> Tuple[float, float, float]:
        """
        Calculate WA/RA adjustment factors
        """
        phase_params = self.wa_ra_adjustment[phase]
        
        # WA adjustment
        nominal_wa = phase_params['nominal_wa']
        wa_deviation = wa - nominal_wa
        
        if wa < phase_params['optimal_wa_range'][0]:
            # Low WA (efficient, but may indicate incomplete compaction)
            wa_adjustment = 1.0 + 0.05  # Small bonus
        elif wa > phase_params['optimal_wa_range'][1]:
            # High WA (inefficient)
            wa_adjustment = 1.0 - abs(wa_deviation) * phase_params['wa_sensitivity']
            wa_adjustment = max(0.80, wa_adjustment)  # Cap at 20% penalty
        else:
            # Optimal range
            wa_adjustment = 1.0
        
        # RA adjustment
        nominal_ra = phase_params['nominal_ra']
        ra_deviation = ra - nominal_ra
        
        if ra < phase_params['optimal_ra_range'][0]:
            # Low RA
            ra_adjustment = 1.0
        elif ra > phase_params['optimal_ra_range'][1]:
            # High RA (more compaction reads)
            ra_adjustment = 1.0 - abs(ra_deviation) * phase_params['ra_sensitivity']
            ra_adjustment = max(0.85, ra_adjustment)  # Cap at 15% penalty
        else:
            # Optimal range
            ra_adjustment = 1.0
        
        # Combined effect (multiplicative)
        combined = wa_adjustment * ra_adjustment
        
        return wa_adjustment, ra_adjustment, combined
    
    def _assess_confidence(self, phase: str, wa: float, ra: float, context: Dict) -> str:
        """Assess prediction confidence based on WA/RA"""
        
        phase_params = self.wa_ra_adjustment[phase]
        
        # Check if WA/RA are in expected ranges
        wa_in_range = phase_params['optimal_wa_range'][0] <= wa <= phase_params['optimal_wa_range'][1]
        ra_in_range = phase_params['optimal_ra_range'][0] <= ra <= phase_params['optimal_ra_range'][1]
        
        # High confidence if both in optimal range
        if wa_in_range and ra_in_range:
            return 'high'
        
        # Medium confidence if one out of range
        elif wa_in_range or ra_in_range:
            return 'medium'
        
        # Low confidence if both out of range
        else:
            return 'medium_low'
    
    def get_model_info(self) -> Dict:
        """모델 정보"""
        return {
            'model_name': 'V5.3 with WA/RA Adjustment',
            'version': self.model_version,
            'creation_time': self.creation_time,
            'base_model': 'V5.3 Initial-Phase-Optimized',
            'enhancement': 'WA/RA direct utilization adjustment',
            'key_features': [
                'Phase-specific WA/RA nominal values',
                'Amplification-bounded adjustment',
                'Optimal range recognition',
                'Sensitivity-based penalties'
            ]
        }


def main():
    """WA/RA 조정 포함 모델 테스트"""
    print("=" * 80)
    print("🔬 V5.3 with WA/RA Direct Adjustment")
    print("=" * 80)
    
    # 모델 생성
    model = V5_3WithWARA()
    
    # 모델 정보
    info = model.get_model_info()
    print(f"\n📋 Model: {info['model_name']}")
    print(f"Version: {info['version']}")
    print(f"Base: {info['base_model']}")
    print(f"Enhancement: {info['enhancement']}")
    
    print("\n🎯 Key Features:")
    for feature in info['key_features']:
        print(f"  • {feature}")
    
    # Test cases
    print("\n" + "=" * 80)
    print("🧪 Test Predictions")
    print("=" * 80)
    
    test_cases = [
        {
            'name': 'Initial Phase - Optimal WA/RA',
            'device_write_bw': 4116.6,
            'phase': 'initial',
            'context': {'wa': 1.2, 'ra': 0.1, 'cv': 0.538},
            'actual': 138769
        },
        {
            'name': 'Initial Phase - High WA/RA',
            'device_write_bw': 4116.6,
            'phase': 'initial',
            'context': {'wa': 2.0, 'ra': 0.5, 'cv': 0.538},
            'actual': 138769
        },
        {
            'name': 'Middle Phase - Optimal WA/RA',
            'device_write_bw': 2595.7,
            'phase': 'middle',
            'context': {'wa': 2.5, 'ra': 0.8, 'cv': 0.272},
            'actual': 114472
        },
        {
            'name': 'Final Phase - Optimal WA/RA',
            'device_write_bw': 1074.8,
            'phase': 'final',
            'context': {'wa': 3.5, 'ra': 0.8, 'cv': 0.041, 'lsm_depth': 7},
            'actual': 109678
        },
        {
            'name': 'Final Phase - High WA',
            'device_write_bw': 1074.8,
            'phase': 'final',
            'context': {'wa': 5.0, 'ra': 1.2, 'cv': 0.041, 'lsm_depth': 7},
            'actual': 109678
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'-'*80}")
        print(f"📊 {test_case['name']}")
        print(f"{'-'*80}")
        
        result = model.predict_s_max(
            test_case['device_write_bw'],
            test_case['phase'],
            test_case['context']
        )
        
        actual = test_case.get('actual', None)
        if actual:
            accuracy = (1 - abs(result.predicted_s_max - actual) / actual) * 100
            error = ((result.predicted_s_max - actual) / actual) * 100
            
            print(f"\n  Results:")
            print(f"    Predicted: {result.predicted_s_max:,.0f} ops/sec")
            print(f"    Actual:    {actual:,.0f} ops/sec")
            print(f"    Accuracy:  {accuracy:.1f}%")
            print(f"    Error:     {error:+.1f}%")
        else:
            print(f"\n  Predicted: {result.predicted_s_max:,.0f} ops/sec")
        
        print(f"\n  WA/RA Adjustment:")
        print(f"    WA adjustment:  {result.wa_adjustment:.3f}x")
        print(f"    RA adjustment:  {result.ra_adjustment:.3f}x")
        print(f"    Combined:       {result.wa_ra_combined:.3f}x")
        print(f"\n  Base prediction: {result.base_prediction:,.0f} ops/sec")
        print(f"  Utilization:    {result.utilization_factor:.4f} ({result.utilization_factor*100:.2f}%)")
        print(f"  Confidence:     {result.confidence}")
    
    print("\n" + "=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

