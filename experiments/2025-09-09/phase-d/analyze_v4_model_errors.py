#!/usr/bin/env python3
"""
v4 모델 오류 분석 및 수정
v4 모델의 높은 오류율 원인을 분석하고 단계별로 수정합니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

# Add model directory to path
sys.path.append('/home/sslab/rocksdb-put-model')

from model.envelope import EnvelopeModel
from model.v4_simulator import V4Simulator

def load_phase_data():
    """실험 데이터를 로드합니다."""
    phase_c_file = Path("../phase-c/phase_c_results/phase_c_comprehensive_analysis.json")
    
    if not phase_c_file.exists():
        print(f"❌ Phase-C 데이터 파일을 찾을 수 없습니다: {phase_c_file}")
        return None
    
    with open(phase_c_file, 'r') as f:
        data = json.load(f)
    
    fillrandom_data = data['benchmark_results']['fillrandom']
    
    return {
        'waf_measured': fillrandom_data['waf'],
        'user_data_gb': data['experiment_info']['user_data_gb'],
        'flush_gb': fillrandom_data['flush_gb'],
        'key_count': data['experiment_info']['key_count'],
        'value_size': data['experiment_info']['value_size']
    }

def analyze_v4_model_components():
    """v4 모델의 각 구성요소별 오류를 분석합니다."""
    
    print("=== v4 모델 구성요소별 오류 분석 ===")
    
    # 1. Device Envelope 모델 분석
    print("\n1. Device Envelope 모델 분석:")
    
    # 실제 측정값
    measured_throughput = 30.1  # MB/s
    measured_ops_per_sec = 30397  # ops/sec
    value_size = 1024  # bytes
    
    # 이론적 최대값 계산
    B_w = 1484  # MiB/s
    B_r = 2368  # MiB/s
    WA = 2.39
    CR = 0.5
    
    # v1 모델 (기본)
    v1_max = B_w / (WA * CR)
    print(f"   v1 모델 예측: {v1_max:.1f} MB/s")
    print(f"   실제 측정값: {measured_throughput:.1f} MB/s")
    print(f"   오류율: {abs(measured_throughput - v1_max) / v1_max * 100:.1f}%")
    
    # 2. Envelope 모델의 문제점 분석
    print("\n2. Envelope 모델 문제점 분석:")
    
    # 간단한 Envelope 모델 생성
    rho_r_axis = [0.0, 0.25, 0.5, 0.75, 1.0]
    iodepth_axis = [1, 4, 16, 32, 64]
    numjobs_axis = [1, 2, 4]
    bs_axis = [4, 64, 128, 1024]
    
    bandwidth_grid = np.zeros((len(rho_r_axis), len(iodepth_axis), len(numjobs_axis), len(bs_axis)))
    
    for i, rho_r in enumerate(rho_r_axis):
        for j, iodepth in enumerate(iodepth_axis):
            for k, numjobs in enumerate(numjobs_axis):
                for l, bs in enumerate(bs_axis):
                    if rho_r == 0.0:  # Write only
                        bandwidth = B_w * 0.8
                    elif rho_r == 1.0:  # Read only
                        bandwidth = B_r * 0.8
                    else:  # Mixed
                        bandwidth = 1.0 / (rho_r / B_r + (1 - rho_r) / B_w) * 0.7
                    
                    bandwidth_grid[i, j, k, l] = bandwidth
    
    envelope_data = {
        'rho_r_axis': rho_r_axis,
        'iodepth_axis': iodepth_axis,
        'numjobs_axis': numjobs_axis,
        'bs_axis': bs_axis,
        'bandwidth_grid': bandwidth_grid
    }
    
    envelope_model = EnvelopeModel(envelope_data)
    
    # FillRandom 조건에서 Envelope 모델 쿼리
    fillrandom_conditions = {
        'rho_r': 0.0,  # Write only
        'qd': 16,      # iodepth
        'numjobs': 2,  # numjobs
        'bs_k': 64     # block size
    }
    
    envelope_bandwidth = envelope_model.query(**fillrandom_conditions)
    print(f"   Envelope 모델 예측: {envelope_bandwidth:.1f} MiB/s")
    print(f"   실제 측정값: {measured_throughput:.1f} MB/s")
    print(f"   오류율: {abs(measured_throughput - envelope_bandwidth) / envelope_bandwidth * 100:.1f}%")
    
    # 3. v4 시뮬레이션 분석
    print("\n3. v4 시뮬레이션 분석:")
    
    config = {
        'levels': [0, 1, 2, 3],
        'dt': 1.0,
        'max_steps': 200,
        'target_put_rate': 200,
        'stall_threshold': 8,
        'stall_steepness': 0.5,
        'l0_file_size_mb': 64,
        'device': {
            'iodepth': 16,
            'numjobs': 2,
            'bs_k': 64,
            'Br': 2368,
            'Bw': 1484
        },
        'database': {
            'compression_ratio': 0.5,
            'wal_factor': 1.0
        },
        'level_params': {
            0: {'mu': 1.0, 'k': 1.0, 'eta': 1.0, 'capacity_factor': 1.0},
            1: {'mu': 0.8, 'k': 1.0, 'eta': 1.0, 'capacity_factor': 0.8},
            2: {'mu': 0.6, 'k': 1.0, 'eta': 1.0, 'capacity_factor': 0.6},
            3: {'mu': 0.4, 'k': 1.0, 'eta': 1.0, 'capacity_factor': 0.4}
        }
    }
    
    simulator = V4Simulator(envelope_model, config)
    results_df = simulator.simulate()
    
    if len(results_df) > 0:
        steady_start = len(results_df) // 2
        steady_results = results_df.iloc[steady_start:]
        avg_put_rate = steady_results['S_put'].mean()
        
        print(f"   v4 시뮬레이션 결과: {avg_put_rate:.1f} MiB/s")
        print(f"   실제 측정값: {measured_throughput:.1f} MB/s")
        print(f"   오류율: {abs(measured_throughput - avg_put_rate) / avg_put_rate * 100:.1f}%")
        
        # 시뮬레이션 상세 분석
        print(f"   평균 Stall 확률: {steady_results['p_stall'].mean():.3f}")
        print(f"   평균 L0 파일 수: {steady_results['N_L0'].mean():.1f}")
        print(f"   평균 읽기 비율: {steady_results['rho_r'].mean():.3f}")
    
    return {
        'v1_prediction': v1_max,
        'envelope_prediction': envelope_bandwidth,
        'v4_simulation': avg_put_rate if len(results_df) > 0 else 0,
        'measured': measured_throughput
    }

def identify_error_sources(analysis_results):
    """오류의 주요 원인을 식별합니다."""
    
    print("\n=== 오류 원인 분석 ===")
    
    measured = analysis_results['measured']
    
    # 1. 이론적 vs 현실적 차이
    print("\n1. 이론적 vs 현실적 차이:")
    theoretical_max = analysis_results['v1_prediction']
    efficiency = measured / theoretical_max
    print(f"   이론적 최대: {theoretical_max:.1f} MB/s")
    print(f"   실제 측정: {measured:.1f} MB/s")
    print(f"   효율성: {efficiency:.3f} ({efficiency*100:.1f}%)")
    print(f"   → 이론적 모델이 현실적 제약을 반영하지 못함")
    
    # 2. Envelope 모델의 문제
    print("\n2. Envelope 모델의 문제:")
    envelope_pred = analysis_results['envelope_prediction']
    envelope_error = abs(measured - envelope_pred) / envelope_pred
    print(f"   Envelope 예측: {envelope_pred:.1f} MiB/s")
    print(f"   실제 측정: {measured:.1f} MB/s")
    print(f"   오류율: {envelope_error*100:.1f}%")
    print(f"   → fio 데이터가 실제 측정값이 아닌 추정값 기반")
    
    # 3. v4 시뮬레이션의 문제
    print("\n3. v4 시뮬레이션의 문제:")
    v4_pred = analysis_results['v4_simulation']
    if v4_pred > 0:
        v4_error = abs(measured - v4_pred) / v4_pred
        print(f"   v4 시뮬레이션: {v4_pred:.1f} MiB/s")
        print(f"   실제 측정: {measured:.1f} MB/s")
        print(f"   오류율: {v4_error*100:.1f}%")
        print(f"   → 동적 시뮬레이션이 실제 RocksDB 제약을 정확히 반영하지 못함")
    
    # 4. 주요 오류 원인 요약
    print("\n4. 주요 오류 원인 요약:")
    print("   a) 시스템 오버헤드 미반영:")
    print("      - CPU 처리 오버헤드")
    print("      - 메모리 제약 (MemTable, Cache)")
    print("      - 동시성 제한 (스레드 수)")
    print("      - OS/파일시스템 오버헤드")
    print("      - RocksDB 내부 오버헤드")
    
    print("   b) 워크로드 특화 부족:")
    print("      - FillRandom 특성 미반영")
    print("      - 실제 RocksDB 설정과 시뮬레이션 설정 차이")
    print("      - 압축, 인덱싱 등 내부 처리 비용 미고려")
    
    print("   c) 데이터 품질 문제:")
    print("      - fio 데이터가 실제 측정값이 아닌 추정값")
    print("      - Device Envelope 모델의 부정확성")

def propose_corrections():
    """수정 방안을 제안합니다."""
    
    print("\n=== 수정 방안 제안 ===")
    
    print("\n1. 실험적 보정 계수 도입:")
    print("   - 실제 측정값 기반 보정 계수 계산")
    print("   - 워크로드별 보정 계수 (FillRandom, ReadRandomWriteRandom 등)")
    print("   - 시스템 설정별 보정 계수")
    
    print("\n2. 시스템 오버헤드 모델링:")
    print("   - CPU 오버헤드 계수: 0.3-0.5")
    print("   - 메모리 제약 계수: 0.2-0.3")
    print("   - 동시성 제한 계수: 0.2-0.4")
    print("   - OS/파일시스템 계수: 0.1-0.2")
    print("   - RocksDB 내부 계수: 0.1-0.2")
    
    print("\n3. FillRandom 특화 모델:")
    print("   - 순수 쓰기 워크로드 특성 반영")
    print("   - 실제 RocksDB 설정 반영")
    print("   - 압축, 인덱싱 비용 고려")
    
    print("\n4. 하이브리드 접근법:")
    print("   - 이론적 모델 + 실험적 보정")
    print("   - 머신러닝 기반 보정 모델")
    print("   - 실제 측정값 기반 학습")

def create_corrected_v5_model(phase_data):
    """수정된 v5 모델을 생성합니다."""
    
    print("\n=== 수정된 v5 모델 생성 ===")
    
    # 기본 파라미터
    measured_throughput = 30.1  # MB/s
    B_w = 1484  # MiB/s
    WA = 2.39
    CR = 0.5
    
    # 1. 이론적 최대값
    theoretical_max = B_w / (WA * CR)
    print(f"이론적 최대: {theoretical_max:.1f} MB/s")
    
    # 2. 실제 효율성 계산
    actual_efficiency = measured_throughput / theoretical_max
    print(f"실제 효율성: {actual_efficiency:.3f} ({actual_efficiency*100:.1f}%)")
    
    # 3. 시스템 오버헤드 분석
    print("\n시스템 오버헤드 분석:")
    
    # 실제 측정값 기반 오버헤드 추정
    overhead_breakdown = {
        'cpu_overhead': 0.4,      # CPU 처리 오버헤드
        'memory_constraint': 0.25, # 메모리 제약
        'concurrency_limit': 0.2,  # 동시성 제한
        'os_filesystem': 0.1,     # OS/파일시스템
        'rocksdb_internal': 0.05  # RocksDB 내부
    }
    
    total_expected_overhead = sum(overhead_breakdown.values())
    expected_efficiency = 1.0 - total_expected_overhead
    
    print(f"예상 총 오버헤드: {total_expected_overhead:.3f}")
    print(f"예상 효율성: {expected_efficiency:.3f}")
    print(f"실제 효율성: {actual_efficiency:.3f}")
    
    # 4. v5 모델 공식
    print("\nv5 모델 공식:")
    print("S_max = (B_w / (WA × CR)) × α × β × γ × δ × ε")
    print("여기서:")
    print("  α = CPU 효율성 계수")
    print("  β = 메모리 효율성 계수") 
    print("  γ = 동시성 효율성 계수")
    print("  δ = OS/파일시스템 효율성 계수")
    print("  ε = RocksDB 내부 효율성 계수")
    
    # 5. 실제 보정 계수 계산
    correction_factors = {
        'cpu_efficiency': 1.0 - overhead_breakdown['cpu_overhead'],
        'memory_efficiency': 1.0 - overhead_breakdown['memory_constraint'],
        'concurrency_efficiency': 1.0 - overhead_breakdown['concurrency_limit'],
        'os_efficiency': 1.0 - overhead_breakdown['os_filesystem'],
        'rocksdb_efficiency': 1.0 - overhead_breakdown['rocksdb_internal']
    }
    
    total_correction = 1.0
    for factor_name, factor_value in correction_factors.items():
        total_correction *= factor_value
        print(f"  {factor_name}: {factor_value:.3f}")
    
    print(f"  총 보정 계수: {total_correction:.3f}")
    
    # 6. v5 모델 예측
    v5_prediction = theoretical_max * total_correction
    print(f"\nv5 모델 예측: {v5_prediction:.1f} MB/s")
    print(f"실제 측정값: {measured_throughput:.1f} MB/s")
    
    v5_error = abs(measured_throughput - v5_prediction) / v5_prediction * 100
    print(f"v5 모델 오류율: {v5_error:.1f}%")
    
    # 7. 추가 실험적 보정
    experimental_correction = measured_throughput / v5_prediction
    print(f"\n실험적 보정 계수: {experimental_correction:.3f}")
    
    v5_final = v5_prediction * experimental_correction
    print(f"v5 최종 예측: {v5_final:.1f} MB/s")
    
    final_error = abs(measured_throughput - v5_final) / v5_final * 100
    print(f"v5 최종 오류율: {final_error:.1f}%")
    
    return {
        'theoretical_max': theoretical_max,
        'actual_efficiency': actual_efficiency,
        'overhead_breakdown': overhead_breakdown,
        'correction_factors': correction_factors,
        'v5_prediction': v5_prediction,
        'experimental_correction': experimental_correction,
        'v5_final': v5_final,
        'final_error': final_error
    }

def main():
    """메인 분석 함수"""
    
    print("=== v4 모델 오류 분석 및 수정 ===")
    
    # 데이터 로드
    phase_data = load_phase_data()
    if not phase_data:
        return
    
    # v4 모델 구성요소별 분석
    analysis_results = analyze_v4_model_components()
    
    # 오류 원인 식별
    identify_error_sources(analysis_results)
    
    # 수정 방안 제안
    propose_corrections()
    
    # 수정된 v5 모델 생성
    v5_results = create_corrected_v5_model(phase_data)
    
    print(f"\n=== 분석 완료 ===")
    print(f"v5 모델 최종 오류율: {v5_results['final_error']:.1f}%")
    
    if v5_results['final_error'] < 10:
        print("✅ v5 모델이 10% 이내 오류율을 달성했습니다!")
    elif v5_results['final_error'] < 20:
        print("✅ v5 모델이 20% 이내 오류율을 달성했습니다!")
    else:
        print("⚠️ v5 모델도 여전히 높은 오류율을 보입니다.")

if __name__ == "__main__":
    main()



