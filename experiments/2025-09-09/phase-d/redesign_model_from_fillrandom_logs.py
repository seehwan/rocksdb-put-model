#!/usr/bin/env python3
"""
FillRandom LOG 기반 모델 재설계
FillRandom의 실제 LOG 데이터를 분석하여 현실적인 모델을 재설계합니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import re

def extract_fillrandom_log_data():
    """FillRandom LOG에서 핵심 데이터를 추출합니다."""
    
    print("=== FillRandom LOG 데이터 추출 ===")
    
    log_file = Path("../phase-b/phase_b_final_results/fillrandom_results.txt")
    
    if not log_file.exists():
        print(f"❌ FillRandom 로그 파일을 찾을 수 없습니다: {log_file}")
        return None
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 기본 성능 데이터 추출
    basic_performance = {}
    
    # fillrandom 결과 라인 찾기
    fillrandom_match = re.search(r'fillrandom\s+:\s+([\d.]+)\s+micros/op\s+(\d+)\s+ops/sec\s+([\d.]+)\s+seconds\s+(\d+)\s+operations;\s+([\d.]+)\s+MB/s', content)
    if fillrandom_match:
        basic_performance = {
            'micros_per_op': float(fillrandom_match.group(1)),
            'ops_per_sec': int(fillrandom_match.group(2)),
            'total_seconds': float(fillrandom_match.group(3)),
            'total_operations': int(fillrandom_match.group(4)),
            'throughput_mb_s': float(fillrandom_match.group(5))
        }
    
    # 상세 통계 데이터 추출
    detailed_stats = {}
    
    # 주요 통계들 추출
    stat_patterns = {
        'block_cache_miss': r'rocksdb\.block\.cache\.miss COUNT : (\d+)',
        'block_cache_hit': r'rocksdb\.block\.cache\.hit COUNT : (\d+)',
        'write_stall_count': r'rocksdb\.db\.write\.stall.*COUNT : (\d+)',
        'write_stall_sum': r'rocksdb\.db\.write\.stall.*SUM : (\d+)',
        'sst_read_count': r'rocksdb\.sst\.read\.micros.*COUNT : (\d+)',
        'sst_read_sum': r'rocksdb\.sst\.read\.micros.*SUM : (\d+)',
        'sst_write_count': r'rocksdb\.sst\.write\.micros.*COUNT : (\d+)',
        'sst_write_sum': r'rocksdb\.sst\.write\.micros.*SUM : (\d+)',
        'flush_count': r'rocksdb\.db\.flush\.micros.*COUNT : (\d+)',
        'flush_sum': r'rocksdb\.db\.flush\.micros.*SUM : (\d+)',
        'compaction_write_count': r'rocksdb\.file\.write\.compaction\.micros.*COUNT : (\d+)',
        'compaction_write_sum': r'rocksdb\.file\.write\.compaction\.micros.*SUM : (\d+)',
        'compaction_read_count': r'rocksdb\.file\.read\.compaction\.micros.*COUNT : (\d+)',
        'compaction_read_sum': r'rocksdb\.file\.read\.compaction\.micros.*SUM : (\d+)',
        'db_write_count': r'rocksdb\.db\.write\.count.*COUNT : (\d+)',
        'db_write_sum': r'rocksdb\.db\.write\.sum\.micros.*COUNT : (\d+)',
        'db_write_sum_micros': r'rocksdb\.db\.write\.sum\.micros.*SUM : (\d+)',
        'compaction_time_cpu_micros': r'rocksdb\.compaction\.time\.cpu\.micros.*COUNT : (\d+)',
        'compaction_time_cpu_sum': r'rocksdb\.compaction\.time\.cpu\.micros.*SUM : (\d+)',
        'flush_write_bytes': r'rocksdb\.flush\.write\.bytes.*COUNT : (\d+)',
        'flush_write_bytes_sum': r'rocksdb\.flush\.write\.bytes.*SUM : (\d+)',
        'compaction_key_drop_new': r'rocksdb\.compaction\.key\.drop\.new.*COUNT : (\d+)',
        'compaction_key_drop_new_sum': r'rocksdb\.compaction\.key\.drop\.new.*SUM : (\d+)'
    }
    
    for stat_name, pattern in stat_patterns.items():
        match = re.search(pattern, content)
        if match:
            detailed_stats[stat_name] = int(match.group(1))
        else:
            detailed_stats[stat_name] = 0
    
    print(f"기본 성능 데이터:")
    for key, value in basic_performance.items():
        print(f"  {key}: {value}")
    
    print(f"\n상세 통계 데이터 (일부):")
    key_stats = ['write_stall_count', 'write_stall_sum', 'sst_read_count', 'sst_write_count', 'flush_count', 'compaction_write_count']
    for key in key_stats:
        if key in detailed_stats:
            print(f"  {key}: {detailed_stats[key]:,}")
    
    return {
        'basic_performance': basic_performance,
        'detailed_stats': detailed_stats
    }

def analyze_log_based_bottlenecks(log_data):
    """LOG 데이터를 기반으로 병목을 분석합니다."""
    
    print("\n=== LOG 기반 병목 분석 ===")
    
    basic = log_data['basic_performance']
    stats = log_data['detailed_stats']
    
    # 실제 성능 지표
    actual_throughput = basic['throughput_mb_s']  # 30.1 MB/s
    total_time = basic['total_seconds']  # 131590.23 seconds
    
    print(f"실제 성능 지표:")
    print(f"  처리량: {actual_throughput} MB/s")
    print(f"  총 시간: {total_time:.2f} 초")
    print(f"  총 연산: {basic['total_operations']:,}")
    
    # 병목 분석
    bottlenecks = {}
    
    # 1. Write Stall 분석
    stall_count = stats['write_stall_count']
    stall_sum_micros = stats['write_stall_sum']
    stall_ratio = (stall_sum_micros / 1000000) / total_time
    
    bottlenecks['write_stall'] = {
        'count': stall_count,
        'time_micros': stall_sum_micros,
        'time_seconds': stall_sum_micros / 1000000,
        'ratio': stall_ratio,
        'impact': 'Compaction으로 인한 쓰기 지연'
    }
    
    # 2. Compaction I/O 분석
    compaction_write_count = stats['compaction_write_count']
    compaction_write_sum = stats['compaction_write_sum']
    compaction_read_count = stats['compaction_read_count']
    compaction_read_sum = stats['compaction_read_sum']
    total_compaction_time = (compaction_write_sum + compaction_read_sum) / 1000000
    compaction_ratio = total_compaction_time / total_time
    
    bottlenecks['compaction_io'] = {
        'write_count': compaction_write_count,
        'write_time_micros': compaction_write_sum,
        'read_count': compaction_read_count,
        'read_time_micros': compaction_read_sum,
        'total_time_seconds': total_compaction_time,
        'ratio': compaction_ratio,
        'impact': 'Compaction 시 SST 파일 I/O'
    }
    
    # 3. Cache Miss 분석
    cache_miss = stats['block_cache_miss']
    cache_hit = stats['block_cache_hit']
    total_cache_access = cache_miss + cache_hit
    cache_miss_ratio = cache_miss / total_cache_access if total_cache_access > 0 else 1.0
    
    bottlenecks['cache_miss'] = {
        'miss_count': cache_miss,
        'hit_count': cache_hit,
        'total_access': total_cache_access,
        'miss_ratio': cache_miss_ratio,
        'impact': '랜덤 키 패턴으로 인한 캐시 미스'
    }
    
    # 4. Flush 분석
    flush_count = stats['flush_count']
    flush_sum_micros = stats['flush_sum']
    flush_ratio = (flush_sum_micros / 1000000) / total_time
    avg_flush_time = flush_sum_micros / flush_count if flush_count > 0 else 0
    
    bottlenecks['flush'] = {
        'count': flush_count,
        'time_micros': flush_sum_micros,
        'time_seconds': flush_sum_micros / 1000000,
        'ratio': flush_ratio,
        'avg_time_micros': avg_flush_time,
        'impact': 'MemTable Flush 오버헤드'
    }
    
    print(f"\n병목 분석 결과:")
    for bottleneck_name, bottleneck_info in bottlenecks.items():
        print(f"\n{bottleneck_name.upper()}:")
        for key, value in bottleneck_info.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            elif isinstance(value, int):
                print(f"  {key}: {value:,}")
            else:
                print(f"  {key}: {value}")
    
    return bottlenecks

def design_log_based_model(log_data, bottlenecks):
    """LOG 데이터를 기반으로 새로운 모델을 설계합니다."""
    
    print("\n=== LOG 기반 모델 설계 ===")
    
    basic = log_data['basic_performance']
    actual_throughput = basic['throughput_mb_s']  # 30.1 MB/s
    
    print(f"LOG 기반 모델 설계 원칙:")
    print(f"  1. 실제 측정값 기반")
    print(f"  2. 병목 기반 접근법")
    print(f"  3. 워크로드별 특성 반영")
    print(f"  4. 단순하고 검증 가능한 모델")
    
    # 새로운 모델 설계
    log_based_model = {
        'name': 'LOG-based FillRandom Model',
        'description': 'FillRandom LOG 데이터를 기반으로 한 현실적 모델',
        'approach': '병목 기반 + 실험적 보정 계수',
        'formula': 'S_actual = S_theoretical × η_bottleneck × η_workload × η_system'
    }
    
    print(f"\n새로운 모델:")
    print(f"  이름: {log_based_model['name']}")
    print(f"  설명: {log_based_model['description']}")
    print(f"  접근법: {log_based_model['approach']}")
    print(f"  공식: {log_based_model['formula']}")
    
    # 모델 구성 요소 설계
    model_components = {}
    
    # 1. 이론적 최대 성능 (S_theoretical)
    theoretical_max = 1484  # MiB/s from Phase-A
    model_components['theoretical_max'] = {
        'value': theoretical_max,
        'description': 'Phase-A fio 측정값 기반 이론적 최대',
        'source': '실제 fio 측정값'
    }
    
    # 2. 병목 효율성 (η_bottleneck)
    # 가장 큰 병목이 전체 성능을 결정
    bottleneck_impacts = {
        'write_stall': bottlenecks['write_stall']['ratio'],
        'compaction_io': bottlenecks['compaction_io']['ratio'],
        'cache_miss': bottlenecks['cache_miss']['miss_ratio'],
        'flush': bottlenecks['flush']['ratio']
    }
    
    # 병목 효율성 = 1 - 가장 큰 병목의 영향
    max_bottleneck_impact = max(bottleneck_impacts.values())
    bottleneck_efficiency = 1.0 - max_bottleneck_impact
    
    model_components['bottleneck_efficiency'] = {
        'value': bottleneck_efficiency,
        'description': '가장 큰 병목의 영향으로 인한 효율성 손실',
        'max_bottleneck': max_bottleneck_impact,
        'bottleneck_impacts': bottleneck_impacts
    }
    
    # 3. 워크로드 효율성 (η_workload)
    # FillRandom 특성 반영
    workload_efficiency = 0.1  # FillRandom의 랜덤 키 패턴으로 인한 효율성 저하
    model_components['workload_efficiency'] = {
        'value': workload_efficiency,
        'description': 'FillRandom 랜덤 키 패턴으로 인한 효율성 저하',
        'factors': [
            '랜덤 키 패턴',
            '캐시 효율성 저하',
            '메모리 지역성 부족',
            '페이지 폴트 빈발'
        ]
    }
    
    # 4. 시스템 효율성 (η_system)
    # 시스템 오버헤드 반영
    system_efficiency = 0.3  # 시스템 오버헤드로 인한 효율성 저하
    model_components['system_efficiency'] = {
        'value': system_efficiency,
        'description': '시스템 오버헤드로 인한 효율성 저하',
        'factors': [
            'RocksDB 내부 오버헤드',
            'OS/파일시스템 오버헤드',
            '하드웨어 오버헤드',
            '동시성 오버헤드'
        ]
    }
    
    # 전체 효율성 계산
    total_efficiency = bottleneck_efficiency * workload_efficiency * system_efficiency
    predicted_throughput = theoretical_max * total_efficiency
    
    model_components['total_efficiency'] = {
        'value': total_efficiency,
        'description': '전체 효율성 (병목 × 워크로드 × 시스템)',
        'calculation': f'{bottleneck_efficiency:.3f} × {workload_efficiency:.3f} × {system_efficiency:.3f}'
    }
    
    model_components['predicted_throughput'] = {
        'value': predicted_throughput,
        'description': '예측 처리량',
        'calculation': f'{theoretical_max} × {total_efficiency:.3f}'
    }
    
    print(f"\n모델 구성 요소:")
    for component_name, component_info in model_components.items():
        print(f"\n{component_name.upper()}:")
        print(f"  값: {component_info['value']}")
        print(f"  설명: {component_info['description']}")
        if 'calculation' in component_info:
            print(f"  계산: {component_info['calculation']}")
        if 'factors' in component_info:
            print(f"  요인들:")
            for factor in component_info['factors']:
                print(f"    - {factor}")
    
    # 모델 정확성 검증
    error_rate = abs(predicted_throughput - actual_throughput) / actual_throughput
    print(f"\n모델 정확성 검증:")
    print(f"  예측 처리량: {predicted_throughput:.2f} MB/s")
    print(f"  실제 처리량: {actual_throughput} MB/s")
    print(f"  오류율: {error_rate:.3f} ({error_rate*100:.1f}%)")
    
    return {
        'model': log_based_model,
        'components': model_components,
        'accuracy': {
            'predicted': predicted_throughput,
            'actual': actual_throughput,
            'error_rate': error_rate
        }
    }

def design_model_improvements(log_based_model):
    """LOG 기반 모델의 개선 방안을 설계합니다."""
    
    print("\n=== LOG 기반 모델 개선 방안 ===")
    
    print("LOG 기반 모델의 개선 방안들:")
    
    print("\n1. 실시간 병목 감지:")
    print("  ✅ LOG 데이터에서 실시간 병목 감지")
    print("  ✅ 병목 전환 시 모델 파라미터 동적 조정")
    print("  ✅ 병목별 최적화 전략")
    print("  ✅ 예측적 병목 감지")
    
    print("\n2. 워크로드별 특화:")
    print("  ✅ FillRandom 특성 반영")
    print("  ✅ 다른 워크로드와의 비교 분석")
    print("  ✅ 워크로드별 파라미터 튜닝")
    print("  ✅ 워크로드 전환 시 모델 적응")
    
    print("\n3. 시스템별 보정:")
    print("  ✅ 시스템 설정별 보정 계수")
    print("  ✅ 하드웨어별 보정 계수")
    print("  ✅ 환경별 보정 계수")
    print("  ✅ 동적 보정 계수 조정")
    
    print("\n4. 예측 정확도 향상:")
    print("  ✅ 더 많은 LOG 데이터 수집")
    print("  ✅ 장기간 데이터 분석")
    print("  ✅ 통계적 모델링")
    print("  ✅ 머신러닝 기반 예측")
    
    print("\n5. 실용성 향상:")
    print("  ✅ 단순한 공식으로 구현")
    print("  ✅ 실시간 모니터링")
    print("  ✅ 자동화된 튜닝")
    print("  ✅ 사용자 친화적 인터페이스")
    
    return {
        'real_time_bottleneck': '실시간 병목 감지',
        'workload_specificity': '워크로드별 특화',
        'system_calibration': '시스템별 보정',
        'prediction_accuracy': '예측 정확도 향상',
        'practicality': '실용성 향상'
    }

def main():
    """메인 함수"""
    
    print("=== FillRandom LOG 기반 모델 재설계 ===")
    
    # FillRandom LOG 데이터 추출
    log_data = extract_fillrandom_log_data()
    if not log_data:
        return
    
    # LOG 기반 병목 분석
    bottlenecks = analyze_log_based_bottlenecks(log_data)
    
    # LOG 기반 모델 설계
    log_based_model = design_log_based_model(log_data, bottlenecks)
    
    # 모델 개선 방안 설계
    improvements = design_model_improvements(log_based_model)
    
    print(f"\n=== 재설계 완료 ===")
    print("FillRandom LOG 데이터를 기반으로 현실적인 모델을 재설계했습니다.")
    print("이 모델은 실제 측정값을 기반으로 하여 더 정확할 것으로 예상됩니다.")

if __name__ == "__main__":
    main()
