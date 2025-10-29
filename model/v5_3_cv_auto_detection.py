#!/usr/bin/env python3
"""
V5.3 CV-Based Automatic Phase Detection Model
CV 기반 자동 phase 감지 기능 추가

핵심 개선사항:
1. CV로 자동 phase 감지 (CV > 0.30: initial, 0.05-0.30: middle, ≤ 0.05: final)
2. 실험 기간 무관한 adaptive phase detection
3. 시스템 특성에 맞는 자동 구분
4. 실용적이고 간단한 deployment

분석:
- Initial: CV=0.356 (high volatility)
- Middle: CV=0.027 (moderate stability)
- Final: CV=0.013 (stable, mature)
"""

import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.v5_3_initial_phase_optimized import V5_3InitialPhaseOptimized, V5_3PredictionResult


class V5_3CVAutoDetection:
    """
    V5.3 CV-Based Automatic Phase Detection Model
    
    핵심 기능:
    1. CV 기반 자동 phase 감지
    2. 실험 기간 무관한 adaptive detection
    3. 시스템 특성에 맞는 자동 구분
    """
    
    def __init__(self):
        self.model_version = "v5.3_cv_auto_detection"
        self.creation_time = datetime.now().isoformat()
        
        # V5.3 base model
        self.base_model = V5_3InitialPhaseOptimized()
        
        # CV-based phase boundaries (experimental validation)
        self.cv_thresholds = {
            'initial': {'max': 1.0, 'min': 0.30},  # CV > 0.30
            'middle': {'max': 0.30, 'min': 0.015},  # 0.015 < CV <= 0.30
            'final': {'max': 0.015, 'min': 0.0}    # CV <= 0.015
        }
        
        # Time-based boundaries (fallback)
        self.time_boundaries = {
            'initial': {'max': 1.0, 'min': 0.0},    # 0-33%
            'middle': {'max': 0.67, 'min': 0.33},   # 33-67%
            'final': {'max': 0.67, 'min': 0.0}     # 67-100%
        }
    
    def detect_phase_from_cv(self, cv: float) -> str:
        """
        CV 기반 자동 phase 감지
        
        Args:
            cv: Coefficient of variation
        
        Returns:
            phase: 'initial', 'middle', or 'final'
        """
        if cv is None or np.isnan(cv):
            return 'middle'  # default
        
        if cv > 0.30:
            return 'initial'
        elif cv > 0.015:
            return 'middle'
        else:
            return 'final'
    
    def detect_phase_from_time(self, runtime_ratio: float) -> str:
        """
        Time 기반 phase 감지 (fallback)
        
        Args:
            runtime_ratio: 경과 시간 / 전체 시간 (0-1)
        
        Returns:
            phase: 'initial', 'middle', or 'final'
        """
        if runtime_ratio < 0.33:
            return 'initial'
        elif runtime_ratio < 0.67:
            return 'middle'
        else:
            return 'final'
    
    def auto_detect_phase(self, 
                         device_write_bw: float,
                         cv: Optional[float] = None,
                         runtime_ratio: Optional[float] = None,
                         context: Optional[Dict] = None) -> str:
        """
        자동 phase 감지 (CV 우선, time fallback)
        
        Args:
            device_write_bw: Available write bandwidth (MB/s)
            cv: Coefficient of variation (preferred)
            runtime_ratio: Runtime ratio 0-1 (fallback)
            context: Additional context
        
        Returns:
            detected_phase: 'initial', 'middle', or 'final'
        """
        detected_phase = None
        detection_method = None
        
        # Priority 1: CV-based detection (preferred)
        if cv is not None:
            detected_phase = self.detect_phase_from_cv(cv)
            detection_method = 'cv_based'
        # Priority 2: Time-based detection (fallback)
        elif runtime_ratio is not None:
            detected_phase = self.detect_phase_from_time(runtime_ratio)
            detection_method = 'time_based'
        # Priority 3: Bandwidth-based detection
        elif device_write_bw is not None:
            if device_write_bw > 3000:
                detected_phase = 'initial'
            elif device_write_bw > 800:
                detected_phase = 'middle'
            else:
                detected_phase = 'final'
            detection_method = 'bandwidth_based'
        else:
            # Default to middle
            detected_phase = 'middle'
            detection_method = 'default'
        
        return detected_phase
    
    def predict_s_max(self,
                     device_write_bw: float,
                     cv: Optional[float] = None,
                     runtime_ratio: Optional[float] = None,
                     phase: Optional[str] = None,
                     context: Optional[Dict] = None) -> Dict:
        """
        CV 기반 자동 phase 감지 + 예측
        
        Args:
            device_write_bw: Available write bandwidth (MB/s)
            cv: Coefficient of variation (for auto-detection)
            runtime_ratio: Runtime ratio 0-1 (for auto-detection)
            phase: Explicit phase (if provided)
            context: Additional context
        
        Returns:
            result: Prediction result with auto-detected phase
        """
        if context is None:
            context = {}
        
        # Auto-detect phase if not provided
        if phase is None:
            phase = self.auto_detect_phase(
                device_write_bw=device_write_bw,
                cv=cv,
                runtime_ratio=runtime_ratio,
                context=context
            )
            
            # Store detection info in context
            context['auto_detected_phase'] = phase
        
        # Get base model prediction
        result = self.base_model.predict_s_max(
            device_write_bw=device_write_bw,
            phase=phase,
            context=context
        )
        
        return result


def main():
    """CV-based auto-detection 테스트"""
    print("=" * 80)
    print("🔬 V5.3 CV-Based Automatic Phase Detection")
    print("=" * 80)
    
    model = V5_3CVAutoDetection()
    
    # Test cases
    test_cases = [
        {
            'name': 'Initial Phase (CV-based)',
            'device_write_bw': 4116.6,
            'cv': 0.356,
            'phase': None  # auto-detect
        },
        {
            'name': 'Middle Phase (CV-based)',
            'device_write_bw': 2595.7,
            'cv': 0.027,
            'phase': None
        },
        {
            'name': 'Final Phase (CV-based)',
            'device_write_bw': 1074.8,
            'cv': 0.013,
            'phase': None
        },
        {
            'name': 'Time-based fallback',
            'device_write_bw': 1500.0,
            'cv': None,
            'runtime_ratio': 0.5  # middle
        }
    ]
    
    for test in test_cases:
        print(f"\n📊 {test['name']}")
        print(f"  Device BW: {test['device_write_bw']:.1f} MB/s")
        if test.get('cv') is not None:
            print(f"  CV: {test['cv']:.3f}")
        if test.get('runtime_ratio') is not None:
            print(f"  Runtime ratio: {test['runtime_ratio']:.2f}")
        
        result = model.predict_s_max(
            device_write_bw=test['device_write_bw'],
            cv=test.get('cv'),
            runtime_ratio=test.get('runtime_ratio'),
            phase=test.get('phase')
        )
        
        print(f"  → Detected phase: {model.auto_detect_phase(test['device_write_bw'], test.get('cv'), test.get('runtime_ratio'))}")
        print(f"  → Predicted S_max: {result.predicted_s_max:.0f} ops/sec")
    
    print("\n✅ CV-based auto-detection 완료!")


if __name__ == "__main__":
    main()

