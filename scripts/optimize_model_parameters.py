#!/usr/bin/env python3
"""
새로운 Phase 경계(9.81h, 42.00h)에 맞게 모델 파라미터 최적화
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

def optimize_parameters_for_boundary(df, phase_name, device_bw_mb_s=1484.0, record_size=1040):
    """특정 phase에 대해 최적의 U와 C를 찾기"""
    
    phase_df = df
    actual_qps = phase_df['interval_qps'].mean()
    
    # 그리드 서치로 최적화
    best_error = 1e10
    best_U = 0.03
    best_C = 1.0
    
    # U 범위: 0.001 ~ 0.2, C 범위: 0.1 ~ 5.0
    for U in np.arange(0.001, 0.2, 0.001):
        for C in np.arange(0.1, 5.0, 0.1):
            predicted_qps = (device_bw_mb_s * 1024 * 1024) / record_size * U * C
            error = abs(predicted_qps - actual_qps) / actual_qps
            
            if error < best_error:
                best_error = error
                best_U = U
                best_C = C
    
    predicted_qps = (device_bw_mb_s * 1024 * 1024) / record_size * best_U * best_C
    accuracy = 100 * (1 - best_error)
    
    return {
        'U': best_U,
        'C': best_C,
        'predicted_qps': predicted_qps,
        'actual_qps': actual_qps,
        'accuracy': accuracy
    }

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 새로운 Phase 경계에 맞게 모델 파라미터 최적화")
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
    
    # Device bandwidth (from phase-a)
    device_write_bw = 1484.0  # MB/s
    record_size = 1040  # bytes
    
    # Phase별로 최적화
    optimized_params = {}
    
    for phase_name in ['initial', 'middle', 'final']:
        print(f"\n{'='*80}")
        print(f"📊 {phase_name.upper()} Phase 최적화")
        print(f"{'='*80}")
        
        phase_df = df[df['phase_new'] == phase_name]
        
        print(f"  실제 평균 QPS: {phase_df['interval_qps'].mean():.0f} ops/sec")
        print(f"  표준편차: {phase_df['interval_qps'].std():.0f} ops/sec")
        print(f"  CV: {phase_df['interval_qps'].std() / phase_df['interval_qps'].mean():.3f}")
        
        result = optimize_parameters_for_boundary(
            phase_df, 
            phase_name,
            device_write_bw,
            record_size
        )
        
        if result:
            optimized_params[phase_name] = result
            
            print(f"\n  ✅ 최적화 결과:")
            print(f"     U = {result['U']:.4f}")
            print(f"     C = {result['C']:.4f}")
            print(f"     예측 QPS: {result['predicted_qps']:.0f}")
            print(f"     실제 QPS: {result['actual_qps']:.0f}")
            print(f"     정확도: {result['accuracy']:.1f}%")
    
    # 전체 정확도 계산
    if 'initial' in optimized_params and 'middle' in optimized_params and 'final' in optimized_params:
        overall_accuracy = np.mean([
            optimized_params['initial']['accuracy'],
            optimized_params['middle']['accuracy'],
            optimized_params['final']['accuracy']
        ])
        
        print(f"\n{'='*80}")
        print(f"📊 전체 모델 정확도: {overall_accuracy:.1f}%")
        print(f"{'='*80}")
        
        print(f"\n✅ 최종 파라미터:")
        print(f"  Initial: U={optimized_params['initial']['U']:.4f}, C={optimized_params['initial']['C']:.4f}")
        print(f"  Middle:  U={optimized_params['middle']['U']:.4f}, C={optimized_params['middle']['C']:.4f}")
        print(f"  Final:   U={optimized_params['final']['U']:.4f}, C={optimized_params['final']['C']:.4f}")
    
    # 결과 저장
    results = {
        'phase_boundaries': {
            'initial_to_middle': boundary_1,
            'middle_to_final': boundary_2
        },
        'optimized_parameters': optimized_params,
        'device_bandwidth': {
            'write_mb_s': device_write_bw
        },
        'record_size_bytes': record_size
    }
    
    output_file = Path('model/v5_3_optimized_parameters.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ 최적화된 파라미터 저장: {output_file}")
    print(f"✅ 완료!")

if __name__ == "__main__":
    main()

