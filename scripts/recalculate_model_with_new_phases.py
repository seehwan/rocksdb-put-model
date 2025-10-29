#!/usr/bin/env python3
"""
새로운 Phase 경계(9.81h, 42.00h)로 모델 재계산
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 새로운 Phase 경계로 모델 재계산")
    print("=" * 80)
    
    # 데이터 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    # 새로운 Phase 경계: 9.81h, 42.00h
    boundary_1 = 9.81
    boundary_2 = 42.00
    
    # Phase 구분
    def assign_phase(hour):
        if hour < boundary_1:
            return 'initial'
        elif hour < boundary_2:
            return 'middle'
        else:
            return 'final'
    
    df['phase_new'] = df['time_hours'].apply(assign_phase)
    
    print(f"\n📊 새로운 Phase 분류:")
    print(f"  Initial: 0.00 - {boundary_1:.2f}h")
    print(f"  Middle:  {boundary_1:.2f} - {boundary_2:.2f}h")
    print(f"  Final:   {boundary_2:.2f} - {df['time_hours'].max():.2f}h")
    
    # Phase별 통계
    phase_stats = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_new'] == phase]
        
        # 기본 통계
        qps = phase_df['interval_qps']
        mean_qps = qps.mean()
        std_qps = qps.std()
        cv_integrated = std_qps / mean_qps if mean_qps > 0 else 0
        
        # MB/s 변환 (1040 bytes/record)
        mean_mb_s = mean_qps * 1040 / (1024 * 1024)
        
        phase_stats[phase] = {
            'duration_hours': phase_df['time_hours'].max() - phase_df['time_hours'].min(),
            'sample_count': len(phase_df),
            'avg_write_rate': mean_mb_s,
            'max_write_rate': qps.max() * 1040 / (1024 * 1024),
            'min_write_rate': qps.min() * 1040 / (1024 * 1024),
            'std_write_rate': std_qps * 1040 / (1024 * 1024),
            'cv': cv_integrated,
            'avg_qps': mean_qps,
            'std_qps': std_qps,
            'time_range': (phase_df['time_hours'].min(), phase_df['time_hours'].max())
        }
        
        print(f"\n{phase.upper()} Phase:")
        print(f"  시간: {phase_df['time_hours'].min():.2f} - {phase_df['time_hours'].max():.2f}h")
        print(f"  샘플: {len(phase_df):,}")
        print(f"  평균 QPS: {mean_qps:.0f} ops/sec")
        print(f"  표준편차: {std_qps:.0f} ops/sec")
        print(f"  CV: {cv_integrated:.3f}")
        print(f"  평균 Write Rate: {mean_mb_s:.2f} MiB/s")
    
    # Device bandwidth (from phase-a results)
    device_write_bw = 1484.0  # MB/s
    device_read_bw = 2368.0    # MB/s
    device_mixed_bw = 2231.0   # MB/s
    
    # 모델 파라미터 (기존 값)
    model_params = {
        'initial': {'U': 0.03, 'C': 1.579},
        'middle': {'U': 0.047, 'C': 1.0},
        'final': {'U': 0.095, 'C': 2.065}
    }
    
    # 모델 예측
    record_size = 1040  # bytes
    model_predictions = {}
    
    for phase in ['initial', 'middle', 'final']:
        U = model_params[phase]['U']
        C = model_params[phase]['C']
        
        # 모델 예측
        S_max_predicted = (device_write_bw * 1024 * 1024) / record_size * U * C
        
        # 실제 QPS
        S_max_actual = phase_stats[phase]['avg_qps']
        
        # 정확도 계산
        accuracy = 100 * (1 - abs(S_max_predicted - S_max_actual) / S_max_actual)
        
        model_predictions[phase] = {
            'predicted_qps': S_max_predicted,
            'actual_qps': S_max_actual,
            'accuracy': accuracy
        }
        
        print(f"\n{phase.upper()} Model Prediction:")
        print(f"  Device Write BW: {device_write_bw} MB/s")
        print(f"  U = {U:.3f}, C = {C:.3f}")
        print(f"  Predicted QPS: {S_max_predicted:.0f}")
        print(f"  Actual QPS: {S_max_actual:.0f}")
        print(f"  Accuracy: {accuracy:.1f}%")
    
    # 전체 정확도
    overall_accuracy = np.mean([model_predictions[p]['accuracy'] for p in ['initial', 'middle', 'final']])
    print(f"\n📊 Overall Model Accuracy: {overall_accuracy:.1f}%")
    
    # 결과 저장
    results = {
        'phase_boundaries': {
            'initial_to_middle': boundary_1,
            'middle_to_final': boundary_2
        },
        'phase_stats': phase_stats,
        'model_predictions': model_predictions,
        'overall_accuracy': overall_accuracy,
        'device_bandwidth': {
            'write_mb_s': device_write_bw,
            'read_mb_s': device_read_bw,
            'mixed_mb_s': device_mixed_bw
        }
    }
    
    output_file = Path('experiments/2025-09-12/phase-b/phase_b_new_boundaries_results.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ 결과 저장: {output_file}")
    
    # 기존 결과와 비교
    print(f"\n📊 기존 경계 vs 새로운 경계 비교:")
    print(f"\n기존 경계 (33% split):")
    print(f"  Initial: 0-32.2h, CV=0.356")
    print(f"  Middle:  32.2-64.4h, CV=0.027")
    print(f"  Final:   64.4-96.6h, CV=0.013")
    
    print(f"\n새로운 경계 (CV-based):")
    print(f"  Initial: 0-9.81h, CV={phase_stats['initial']['cv']:.3f}")
    print(f"  Middle:  9.81-42.00h, CV={phase_stats['middle']['cv']:.3f}")
    print(f"  Final:   42.00-96.61h, CV={phase_stats['final']['cv']:.3f}")
    
    print(f"\n✅ 완료!")

if __name__ == "__main__":
    main()

