#!/usr/bin/env python3
"""
Phase-D: v4 모델 완전 검증 (2025-09-08)

이 스크립트는 2025-09-08 실험 데이터를 사용하여 v4 모델을 완전히 검증합니다.
Phase-A의 실제 fio 데이터를 사용하여 Device Envelope 모델을 생성하고,
v4 시뮬레이터를 실행하여 정확한 검증을 수행합니다.
"""

import json
import sys
import os
import numpy as np
from pathlib import Path

# Add model directory to path
sys.path.append('/home/sslab/rocksdb-put-model')

from model.envelope import EnvelopeModel
from model.v4_simulator import V4Simulator
from model.closed_ledger import ClosedLedger
import yaml

def create_real_envelope_model(device_data: dict) -> EnvelopeModel:
    """
    Phase-A의 실제 fio 데이터를 기반으로 Device Envelope 모델을 생성합니다.
    
    Args:
        device_data: Phase-A에서 측정된 장치 데이터
        
    Returns:
        EnvelopeModel 인스턴스
    """
    # Phase-A 결과에서 실제 측정값 추출
    B_w = device_data['write_test']['bandwidth_mib_s']  # 1484 MiB/s
    B_r = device_data['read_test']['bandwidth_mib_s']   # 2368 MiB/s
    B_eff_mixed = device_data['mixed_test']['total_bandwidth_mib_s']  # 2231 MiB/s
    
    # 실제 fio 설정값들
    iodepth = 32
    numjobs = 1
    bs_k = 128  # 128k
    
    # 4D 그리드 생성 (rho_r, iodepth, numjobs, bs_k)
    rho_r_axis = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    iodepth_axis = np.array([1, 4, 16, 32, 64])
    numjobs_axis = np.array([1, 2, 4])
    bs_axis = np.array([4, 64, 128, 1024])  # 4k, 64k, 128k, 1024k
    
    # 실제 측정값을 기반으로 한 4D 대역폭 그리드 생성
    bandwidth_grid = np.zeros((len(rho_r_axis), len(iodepth_axis), len(numjobs_axis), len(bs_axis)))
    
    for i, rho_r in enumerate(rho_r_axis):
        for j, qd in enumerate(iodepth_axis):
            for k, nj in enumerate(numjobs_axis):
                for l, bs in enumerate(bs_axis):
                    # 실제 측정값을 기반으로 한 모델링
                    if rho_r == 0.0:  # 순수 쓰기
                        base_bw = B_w
                    elif rho_r == 1.0:  # 순수 읽기
                        base_bw = B_r
                    else:  # 혼합 I/O
                        # 실제 측정된 50:50 혼합 성능을 기반으로 보간
                        if rho_r == 0.5:
                            base_bw = B_eff_mixed
                        else:
                            # 선형 보간
                            base_bw = B_w + (B_r - B_w) * rho_r
                    
                    # iodepth 영향 (큐 깊이가 깊을수록 성능 향상, 하지만 한계 있음)
                    if qd <= 32:
                        qd_factor = 1.0 + 0.3 * (qd - 1) / 31
                    else:
                        qd_factor = 1.3 + 0.1 * (qd - 32) / 32
                    
                    # numjobs 영향 (병렬 작업이 많을수록 성능 저하)
                    nj_factor = 1.0 - 0.2 * (nj - 1) / 3
                    
                    # bs_k 영향 (블록 크기가 클수록 성능 향상)
                    if bs <= 128:
                        bs_factor = 1.0 + 0.3 * (bs - 4) / 124
                    else:
                        bs_factor = 1.3 + 0.1 * (bs - 128) / 896
                    
                    # 최종 대역폭 계산
                    bandwidth = base_bw * qd_factor * nj_factor * bs_factor
                    
                    # 물리적 제약 적용 (B_w, B_r을 넘지 않도록)
                    max_possible = min(B_r, B_w) if rho_r > 0 and rho_r < 1 else (B_r if rho_r == 1.0 else B_w)
                    bandwidth = min(bandwidth, max_possible)
                    
                    bandwidth_grid[i, j, k, l] = bandwidth
    
    grid_data = {
        'rho_r_axis': rho_r_axis.tolist(),
        'iodepth_axis': iodepth_axis.tolist(),
        'numjobs_axis': numjobs_axis.tolist(),
        'bs_axis': bs_axis.tolist(),
        'bandwidth_grid': bandwidth_grid.tolist(),
        'metadata': {
            'created_by': 'Phase-D v4 full validation',
            'version': '1.0',
            'description': 'Real fio data-based envelope model for v4 validation',
            'source_data': {
                'B_w': B_w,
                'B_r': B_r,
                'B_eff_mixed': B_eff_mixed,
                'test_config': {
                    'iodepth': iodepth,
                    'numjobs': numjobs,
                    'bs_k': bs_k
                }
            }
        }
    }
    
    return EnvelopeModel(grid_data)

def create_v4_config_from_experiment(experiment_data: dict) -> dict:
    """
    실험 데이터를 기반으로 v4 시뮬레이터 설정을 생성합니다.
    
    Args:
        experiment_data: 전체 실험 데이터
        
    Returns:
        v4 시뮬레이터 설정 딕셔너리
    """
    device_data = experiment_data['device_calibration']
    rocksdb_data = experiment_data['phase_b_results']
    phase_c_data = experiment_data['phase_c_results']
    
    # 장치 설정 (Phase-A 결과)
    device_config = {
        'device_read_bandwidth_mib_s': device_data['read_test']['bandwidth_mib_s'],
        'device_write_bandwidth_mib_s': device_data['write_test']['bandwidth_mib_s'],
        'device_qd': 32,  # Phase-A에서 사용된 값
        'device_numjobs': 1,  # Phase-A에서 사용된 값
        'device_bs_k': 128,  # Phase-A에서 사용된 값
    }
    
    # RocksDB 설정 (Phase-B, C 결과)
    rocksdb_config = {
        'levels': ['L0', 'L1', 'L2', 'L3'],
        'level_config': {},
        'global_params': {
            'target_put_rate_mib_s': rocksdb_data['actual_performance']['put_rate_mib_s'],
            'device_read_bandwidth_mib_s': device_data['read_test']['bandwidth_mib_s'],
            'device_write_bandwidth_mib_s': device_data['write_test']['bandwidth_mib_s'],
            'device_qd': 32,
            'device_numjobs': 1,
            'device_bs_k': 128,
            'max_l0_files': 10,
            'l0_stall_threshold': 8,
            'l0_stall_steepness': 2.0,
            'l0_file_size_mib': 64.0,
            'initial_read_ratio': 0.1,  # 휴리스틱
            'total_write_amplification': phase_c_data['total_waf_log'],
            'total_read_amplification': 2.5,  # 휴리스틱
            'concurrency_scaling_factor': 1.0
        }
    }
    
    # Level별 설정 (Phase-C 데이터 기반)
    level_data = phase_c_data['level_wise_waf']
    
    for i, level in enumerate(['L0', 'L1', 'L2', 'L3']):
        wa = level_data[level]['w_amp']
        
        # WA에 따라 파라미터 조정
        if wa > 10:  # L2 같은 높은 WA
            mu_min, mu_max = 0.1, 0.5
            gamma, k0 = 0.5, 0.5
            k_l, eta_l = 0.4, 0.8
            write_share, read_share = 0.4, 0.6
        elif wa > 1:  # L3 같은 중간 WA
            mu_min, mu_max = 0.2, 0.8
            gamma, k0 = 0.6, 0.6
            k_l, eta_l = 0.7, 0.9
            write_share, read_share = 0.3, 0.25
        else:  # L0, L1 같은 낮은 WA
            mu_min, mu_max = 0.5, 1.2
            gamma, k0 = 0.7, 0.7
            k_l, eta_l = 1.0, 1.0
            write_share, read_share = (0.2, 0.05) if level == 'L0' else (0.1, 0.1)
        
        rocksdb_config['level_config'][level] = {
            'write_share': write_share,
            'read_share': read_share,
            'mu_min': mu_min,
            'mu_max': mu_max,
            'gamma': gamma,
            'k0': k0,
            'k_l': k_l,
            'eta_l': eta_l
        }
    
    # 시뮬레이션 설정
    config = {
        'simulation_dt_s': 1.0,
        'simulation_steps': 500,  # 충분한 시뮬레이션
        'rocksdb_params': rocksdb_config
    }
    
    return config

def run_v4_validation(experiment_data: dict) -> dict:
    """
    v4 모델을 완전히 검증합니다.
    
    Args:
        experiment_data: 전체 실험 데이터
        
    Returns:
        검증 결과 딕셔너리
    """
    print("v4 모델 완전 검증 시작...")
    
    # 1. Device Envelope 모델 생성 (실제 fio 데이터 기반)
    print("  - Device Envelope 모델 생성 중...")
    envelope_model = create_real_envelope_model(experiment_data['device_calibration'])
    print(f"    ✓ Envelope 모델 생성 완료")
    
    # 2. v4 시뮬레이터 설정 생성
    print("  - v4 시뮬레이터 설정 생성 중...")
    config = create_v4_config_from_experiment(experiment_data)
    print(f"    ✓ 설정 생성 완료")
    
    # 3. v4 시뮬레이터 생성 및 실행
    print("  - v4 시뮬레이터 실행 중...")
    simulator = V4Simulator(envelope_model, config)
    
    # 시뮬레이션 실행
    results_df = simulator.simulate()
    
    # 결과를 CSV로 저장
    results_df.to_csv("v4_simulation_results.csv", index=False)
    
    # 4. 결과 분석
    print("  - 결과 분석 중...")
    
    # 실제 측정값
    actual_put_rate = experiment_data['phase_b_results']['actual_performance']['put_rate_mib_s']
    
    # 시뮬레이션 결과에서 예측값 추출
    if len(results_df) > 0:
        df = results_df
        
        # Steady-state 평균 계산 (마지막 20% 구간)
        steady_state_df = df.tail(int(len(df) * 0.2))
        predicted_put_rate = steady_state_df['S_put'].mean()
        avg_stall_prob = steady_state_df['p_stall'].mean()
        avg_read_ratio = steady_state_df['rho_r'].mean()
        avg_l0_files = steady_state_df['N_L0'].mean()
        
        # Level별 백로그 분석
        level_backlogs = {}
        for level in ['L0', 'L1', 'L2', 'L3']:
            if f'Q_{level}' in df.columns:
                level_backlogs[level] = steady_state_df[f'Q_{level}'].mean()
        
        # 병목 분석
        bottleneck_level = 'Unknown'
        max_backlog = 0
        for level, backlog in level_backlogs.items():
            if backlog > max_backlog:
                max_backlog = backlog
                bottleneck_level = level
    else:
        # 시뮬레이션 결과가 없는 경우 기본값
        predicted_put_rate = 0
        avg_stall_prob = 0
        avg_read_ratio = 0
        avg_l0_files = 0
        level_backlogs = {}
        bottleneck_level = 'Unknown'
    
    # 5. 오류율 계산
    if predicted_put_rate > 0:
        error_percent = ((predicted_put_rate - actual_put_rate) / actual_put_rate) * 100
        error_abs = abs(error_percent)
    else:
        error_percent = 0
        error_abs = 100
    
    # 검증 상태 판정
    if error_abs <= 10:
        validation_status = "Excellent"
    elif error_abs <= 20:
        validation_status = "Good"
    elif error_abs <= 50:
        validation_status = "Fair"
    else:
        validation_status = "Poor"
    
    return {
        'model': 'v4_full',
        'predicted_smax': predicted_put_rate,
        'actual_put_rate': actual_put_rate,
        'error_percent': error_percent,
        'error_abs': error_abs,
        'validation_status': validation_status,
        'simulation_results': {
            'steps': len(df) if 'df' in locals() else 0,
            'steady_state_metrics': {
                'avg_put_rate': predicted_put_rate,
                'avg_stall_prob': avg_stall_prob,
                'avg_read_ratio': avg_read_ratio,
                'avg_l0_files': avg_l0_files,
                'level_backlogs': level_backlogs
            },
            'bottleneck_level': bottleneck_level,
            'max_backlog': max_backlog
        },
        'envelope_model_info': {
            'grid_shape': envelope_model.bandwidth_grid.shape,
            'total_points': envelope_model.bandwidth_grid.size,
            'metadata': envelope_model.metadata
        },
        'config_used': config
    }

def main():
    """메인 함수"""
    print("Phase-D-3: v4 모델 완전 검증 시작")
    print("=" * 50)
    
    # 실험 데이터 로드
    with open('../experiment_data.json', 'r') as f:
        experiment_data = json.load(f)
    
    # v4 모델 완전 검증
    validation_results = run_v4_validation(experiment_data)
    
    # 결과 출력
    print(f"\n📊 v4 모델 완전 검증 결과")
    print(f"  예측 S_max: {validation_results['predicted_smax']:.1f} MiB/s")
    print(f"  실제 Put Rate: {validation_results['actual_put_rate']:.1f} MiB/s")
    print(f"  오류율: {validation_results['error_percent']:.1f}%")
    print(f"  검증 상태: {validation_results['validation_status']}")
    
    print(f"\n📈 시뮬레이션 결과")
    sim_results = validation_results['simulation_results']
    print(f"  시뮬레이션 단계: {sim_results['steps']}")
    print(f"  Stall 확률: {sim_results['steady_state_metrics']['avg_stall_prob']:.3f}")
    print(f"  Read/Write 비율: {sim_results['steady_state_metrics']['avg_read_ratio']:.3f}")
    print(f"  L0 파일 수: {sim_results['steady_state_metrics']['avg_l0_files']:.1f}")
    print(f"  병목 레벨: {sim_results['bottleneck_level']}")
    print(f"  최대 백로그: {sim_results['max_backlog']:.2f} GiB")
    
    print(f"\n📊 Level별 백로그")
    for level, backlog in sim_results['steady_state_metrics']['level_backlogs'].items():
        print(f"  {level}: {backlog:.2f} GiB")
    
    print(f"\n🔧 사용된 설정")
    config = validation_results['config_used']
    print(f"  대상 Put Rate: {config['rocksdb_params']['global_params']['target_put_rate_mib_s']:.1f} MiB/s")
    print(f"  압축률: {experiment_data['phase_b_results']['compression_analysis']['compression_ratio']:.3f}")
    print(f"  WA: {experiment_data['phase_c_results']['total_waf_log']:.3f}")
    print(f"  장치 대역폭: {config['rocksdb_params']['global_params']['device_write_bandwidth_mib_s']} MiB/s (W), {config['rocksdb_params']['global_params']['device_read_bandwidth_mib_s']} MiB/s (R)")
    
    print(f"\n📊 Envelope 모델 정보")
    env_info = validation_results['envelope_model_info']
    print(f"  그리드 크기: {env_info['grid_shape']}")
    print(f"  총 포인트: {env_info['total_points']}")
    print(f"  소스 데이터: {env_info['metadata']['source_data']}")
    
    # 결과 저장
    with open('phase_d_v4_full_results.json', 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n💾 결과가 phase_d_v4_full_results.json에 저장되었습니다.")
    print(f"💾 시뮬레이션 결과가 v4_simulation_results.csv에 저장되었습니다.")
    
    return validation_results

if __name__ == "__main__":
    main()
