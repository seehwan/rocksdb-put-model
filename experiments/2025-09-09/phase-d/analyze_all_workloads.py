#!/usr/bin/env python3
"""
모든 워크로드 데이터 분석
기존 워크로드들(fillrandom, fillseq, overwrite, readrandomwriterandom, mixgraph)의 데이터를 체계적으로 분석합니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import re
from datetime import datetime

def extract_workload_data(workload_name, log_file_path):
    """특정 워크로드의 데이터를 추출합니다."""
    
    print(f"\n=== {workload_name.upper()} 데이터 추출 ===")
    
    if not log_file_path.exists():
        print(f"❌ {workload_name} 로그 파일을 찾을 수 없습니다: {log_file_path}")
        return None
    
    with open(log_file_path, 'r') as f:
        content = f.read()
    
    # 기본 성능 데이터 추출
    basic_performance = {}
    
    # 워크로드 결과 라인 찾기
    workload_match = re.search(rf'{workload_name}\s+:\s+([\d.]+)\s+micros/op\s+(\d+)\s+ops/sec\s+([\d.]+)\s+seconds\s+(\d+)\s+operations;\s+([\d.]+)\s+MB/s', content)
    if workload_match:
        basic_performance = {
            'micros_per_op': float(workload_match.group(1)),
            'ops_per_sec': int(workload_match.group(2)),
            'total_seconds': float(workload_match.group(3)),
            'total_operations': int(workload_match.group(4)),
            'throughput_mb_s': float(workload_match.group(5))
        }
    else:
        print(f"⚠️ {workload_name} 기본 성능 데이터를 찾을 수 없습니다.")
        return None
    
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
    
    print(f"상세 통계 데이터 (일부):")
    key_stats = ['write_stall_count', 'write_stall_sum', 'sst_read_count', 'sst_write_count', 'flush_count', 'compaction_write_count']
    for key in key_stats:
        if key in detailed_stats:
            print(f"  {key}: {detailed_stats[key]:,}")
    
    return {
        'workload_name': workload_name,
        'basic_performance': basic_performance,
        'detailed_stats': detailed_stats
    }

def analyze_workload_bottlenecks(workload_data):
    """워크로드별 병목을 분석합니다."""
    
    workload_name = workload_data['workload_name']
    basic = workload_data['basic_performance']
    stats = workload_data['detailed_stats']
    
    print(f"\n=== {workload_name.upper()} 병목 분석 ===")
    
    # 실제 성능 지표
    actual_throughput = basic['throughput_mb_s']
    total_time = basic['total_seconds']
    
    print(f"실제 성능 지표:")
    print(f"  처리량: {actual_throughput} MB/s")
    print(f"  총 시간: {total_time:.2f} 초")
    print(f"  총 연산: {basic['total_operations']:,}")
    
    # 병목 분석
    bottlenecks = {}
    
    # 1. Write Stall 분석
    stall_count = stats['write_stall_count']
    stall_sum_micros = stats['write_stall_sum']
    stall_ratio = (stall_sum_micros / 1000000) / total_time if total_time > 0 else 0
    
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
    compaction_ratio = total_compaction_time / total_time if total_time > 0 else 0
    
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
    cache_miss_ratio = cache_miss / total_cache_access if total_cache_access > 0 else 0
    
    bottlenecks['cache_miss'] = {
        'miss_count': cache_miss,
        'hit_count': cache_hit,
        'total_access': total_cache_access,
        'miss_ratio': cache_miss_ratio,
        'impact': '캐시 미스로 인한 성능 저하'
    }
    
    # 4. Flush 분석
    flush_count = stats['flush_count']
    flush_sum_micros = stats['flush_sum']
    flush_ratio = (flush_sum_micros / 1000000) / total_time if total_time > 0 else 0
    avg_flush_time = flush_sum_micros / flush_count if flush_count > 0 else 0
    
    bottlenecks['flush'] = {
        'count': flush_count,
        'time_micros': flush_sum_micros,
        'time_seconds': flush_sum_micros / 1000000,
        'ratio': flush_ratio,
        'avg_time_micros': avg_flush_time,
        'impact': 'MemTable Flush 오버헤드'
    }
    
    print(f"병목 분석 결과:")
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

def compare_workloads(all_workload_data):
    """워크로드들을 비교 분석합니다."""
    
    print(f"\n=== 워크로드 비교 분석 ===")
    
    comparison_data = {}
    
    for workload_data in all_workload_data:
        if workload_data is None:
            continue
            
        workload_name = workload_data['workload_name']
        basic = workload_data['basic_performance']
        
        comparison_data[workload_name] = {
            'throughput_mb_s': basic['throughput_mb_s'],
            'ops_per_sec': basic['ops_per_sec'],
            'micros_per_op': basic['micros_per_op'],
            'total_seconds': basic['total_seconds'],
            'total_operations': basic['total_operations']
        }
    
    # 비교 테이블 생성
    print(f"\n워크로드별 성능 비교:")
    print(f"{'워크로드':<20} {'처리량(MB/s)':<15} {'ops/sec':<15} {'micros/op':<15} {'총시간(초)':<15}")
    print("-" * 80)
    
    for workload_name, data in comparison_data.items():
        print(f"{workload_name:<20} {data['throughput_mb_s']:<15.1f} {data['ops_per_sec']:<15,} {data['micros_per_op']:<15.2f} {data['total_seconds']:<15.2f}")
    
    # 성능 순위
    print(f"\n처리량 순위:")
    sorted_workloads = sorted(comparison_data.items(), key=lambda x: x[1]['throughput_mb_s'], reverse=True)
    for i, (workload_name, data) in enumerate(sorted_workloads, 1):
        print(f"  {i}. {workload_name}: {data['throughput_mb_s']:.1f} MB/s")
    
    return comparison_data

def identify_core_variables(all_workload_data):
    """핵심 변수들을 식별합니다."""
    
    print(f"\n=== 핵심 변수 식별 ===")
    
    core_variables = {
        'performance_metrics': {
            'throughput_mb_s': '처리량 (MB/s)',
            'ops_per_sec': '초당 연산 수',
            'micros_per_op': '연산당 마이크로초',
            'total_seconds': '총 실행 시간'
        },
        'bottleneck_metrics': {
            'write_stall_ratio': 'Write Stall 비율',
            'compaction_io_ratio': 'Compaction I/O 비율',
            'cache_miss_ratio': 'Cache Miss 비율',
            'flush_ratio': 'Flush 비율'
        },
        'workload_characteristics': {
            'workload_type': '워크로드 유형',
            'access_pattern': '접근 패턴',
            'write_ratio': '쓰기 비율',
            'read_ratio': '읽기 비율'
        }
    }
    
    print("핵심 변수들:")
    for category, variables in core_variables.items():
        print(f"\n{category.upper()}:")
        for var_name, var_description in variables.items():
            print(f"  - {var_name}: {var_description}")
    
    # 워크로드별 특성 분석
    workload_characteristics = {}
    
    for workload_data in all_workload_data:
        if workload_data is None:
            continue
            
        workload_name = workload_data['workload_name']
        
        # 워크로드 특성 정의
        if 'fillrandom' in workload_name:
            characteristics = {
                'type': 'write_heavy',
                'access_pattern': 'random',
                'write_ratio': 1.0,
                'read_ratio': 0.0,
                'description': '랜덤 키로 순차 쓰기'
            }
        elif 'fillseq' in workload_name:
            characteristics = {
                'type': 'write_heavy',
                'access_pattern': 'sequential',
                'write_ratio': 1.0,
                'read_ratio': 0.0,
                'description': '순차 키로 순차 쓰기'
            }
        elif 'overwrite' in workload_name:
            characteristics = {
                'type': 'write_heavy',
                'access_pattern': 'random',
                'write_ratio': 1.0,
                'read_ratio': 0.0,
                'description': '기존 키 덮어쓰기'
            }
        elif 'readrandomwriterandom' in workload_name:
            characteristics = {
                'type': 'mixed',
                'access_pattern': 'random',
                'write_ratio': 0.5,
                'read_ratio': 0.5,
                'description': '랜덤 읽기/쓰기 혼합'
            }
        elif 'mixgraph' in workload_name:
            characteristics = {
                'type': 'mixed',
                'access_pattern': 'mixed',
                'write_ratio': 0.7,
                'read_ratio': 0.3,
                'description': '복합 워크로드'
            }
        else:
            characteristics = {
                'type': 'unknown',
                'access_pattern': 'unknown',
                'write_ratio': 0.0,
                'read_ratio': 0.0,
                'description': '알 수 없는 워크로드'
            }
        
        workload_characteristics[workload_name] = characteristics
    
    print(f"\n워크로드별 특성:")
    for workload_name, characteristics in workload_characteristics.items():
        print(f"\n{workload_name.upper()}:")
        for key, value in characteristics.items():
            print(f"  {key}: {value}")
    
    return {
        'core_variables': core_variables,
        'workload_characteristics': workload_characteristics
    }

def main():
    """메인 함수"""
    
    print("=== 모든 워크로드 데이터 분석 ===")
    
    # 워크로드 파일 경로 정의
    workload_files = {
        'fillrandom': Path("../phase-b/phase_b_final_results/fillrandom_results.txt"),
        'fillseq': Path("../phase-b/phase_b_final_results/fillseq_results.txt"),
        'overwrite': Path("../phase-b/phase_b_final_results/overwrite_results.txt"),
        'readrandomwriterandom': Path("../phase-b/phase_b_final_results/readrandomwriterandom_results.txt"),
        'mixgraph': Path("../phase-b/phase_b_final_results/mixgraph_results.txt")
    }
    
    # 각 워크로드 데이터 추출
    all_workload_data = []
    for workload_name, log_file_path in workload_files.items():
        workload_data = extract_workload_data(workload_name, log_file_path)
        if workload_data:
            all_workload_data.append(workload_data)
    
    if not all_workload_data:
        print("❌ 분석할 워크로드 데이터가 없습니다.")
        return
    
    # 각 워크로드별 병목 분석
    all_bottlenecks = {}
    for workload_data in all_workload_data:
        bottlenecks = analyze_workload_bottlenecks(workload_data)
        all_bottlenecks[workload_data['workload_name']] = bottlenecks
    
    # 워크로드 비교 분석
    comparison_data = compare_workloads(all_workload_data)
    
    # 핵심 변수 식별
    core_variables = identify_core_variables(all_workload_data)
    
    # 결과 저장
    analysis_results = {
        'timestamp': datetime.now().isoformat(),
        'workload_data': all_workload_data,
        'bottlenecks': all_bottlenecks,
        'comparison': comparison_data,
        'core_variables': core_variables
    }
    
    # JSON 파일로 저장
    output_file = "all_workloads_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    print(f"\n=== 분석 완료 ===")
    print(f"분석 결과가 {output_file}에 저장되었습니다.")
    print(f"총 {len(all_workload_data)}개 워크로드가 분석되었습니다.")

if __name__ == "__main__":
    main()



