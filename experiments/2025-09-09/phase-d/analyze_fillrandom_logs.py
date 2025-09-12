#!/usr/bin/env python3
"""
FillRandom 로그 상세 분석
실제 병목을 정확히 파악하기 위해 로그를 자세히 분석합니다.
"""

import re
import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from collections import defaultdict

def parse_fillrandom_log():
    """FillRandom 로그를 파싱합니다."""
    
    log_file = Path("../phase-b/phase_b_final_results/fillrandom_results.txt")
    
    if not log_file.exists():
        print(f"❌ FillRandom 로그 파일을 찾을 수 없습니다: {log_file}")
        return None
    
    print("=== FillRandom 로그 파싱 ===")
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 기본 정보 추출
    basic_info = {}
    
    # fillrandom 결과 라인 찾기
    fillrandom_match = re.search(r'fillrandom\s+:\s+([\d.]+)\s+micros/op\s+(\d+)\s+ops/sec\s+([\d.]+)\s+seconds\s+(\d+)\s+operations;\s+([\d.]+)\s+MB/s', content)
    if fillrandom_match:
        basic_info = {
            'micros_per_op': float(fillrandom_match.group(1)),
            'ops_per_sec': int(fillrandom_match.group(2)),
            'total_seconds': float(fillrandom_match.group(3)),
            'total_operations': int(fillrandom_match.group(4)),
            'throughput_mb_s': float(fillrandom_match.group(5))
        }
    
    # 통계 정보 추출
    stats = {}
    
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
            stats[stat_name] = int(match.group(1))
        else:
            stats[stat_name] = 0
    
    # 추가 통계들 (SUM 값들) - 이미 위에서 처리됨
    
    return {
        'basic_info': basic_info,
        'stats': stats
    }

def analyze_write_stalls(log_data):
    """Write Stall을 분석합니다."""
    
    print("\n=== Write Stall 분석 ===")
    
    stats = log_data['stats']
    basic_info = log_data['basic_info']
    
    write_stall_count = stats['write_stall_count']
    write_stall_sum = stats['write_stall_sum']
    total_seconds = basic_info['total_seconds']
    
    print(f"Write Stall 통계:")
    print(f"  총 발생 횟수: {write_stall_count:,}")
    print(f"  총 Stall 시간: {write_stall_sum:,} 마이크로초")
    print(f"  총 Stall 시간: {write_stall_sum / 1000000:.2f} 초")
    print(f"  총 실험 시간: {total_seconds:.2f} 초")
    
    # Stall 비율 계산
    stall_ratio = (write_stall_sum / 1000000) / total_seconds
    print(f"  Stall 비율: {stall_ratio:.3f} ({stall_ratio*100:.1f}%)")
    
    # 평균 Stall 시간
    if write_stall_count > 0:
        avg_stall_time = write_stall_sum / write_stall_count
        print(f"  평균 Stall 시간: {avg_stall_time:.2f} 마이크로초")
    
    # Stall이 성능에 미치는 영향
    print(f"\nStall이 성능에 미치는 영향:")
    print(f"  Stall 없을 때 예상 처리량: {basic_info['throughput_mb_s'] / (1 - stall_ratio):.2f} MB/s")
    print(f"  Stall로 인한 성능 저하: {stall_ratio*100:.1f}%")
    
    return {
        'stall_count': write_stall_count,
        'stall_sum_micros': write_stall_sum,
        'stall_ratio': stall_ratio,
        'avg_stall_time': avg_stall_time if write_stall_count > 0 else 0
    }

def analyze_compaction_performance(log_data):
    """Compaction 성능을 분석합니다."""
    
    print("\n=== Compaction 성능 분석 ===")
    
    stats = log_data['stats']
    basic_info = log_data['basic_info']
    
    # Compaction 관련 통계
    compaction_write_count = stats['compaction_write_count']
    compaction_write_sum = stats['compaction_write_sum']
    compaction_read_count = stats['compaction_read_count']
    compaction_read_sum = stats['compaction_read_sum']
    compaction_time_cpu_count = stats['compaction_time_cpu_micros']
    compaction_time_cpu_sum = stats['compaction_time_cpu_sum']
    
    print(f"Compaction 통계:")
    print(f"  Compaction Write 횟수: {compaction_write_count:,}")
    print(f"  Compaction Write 총 시간: {compaction_write_sum:,} 마이크로초")
    print(f"  Compaction Read 횟수: {compaction_read_count:,}")
    print(f"  Compaction Read 총 시간: {compaction_read_sum:,} 마이크로초")
    print(f"  Compaction CPU 시간: {compaction_time_cpu_sum:,} 마이크로초")
    
    # Compaction 효율성 분석
    total_compaction_time = compaction_write_sum + compaction_read_sum
    total_seconds = basic_info['total_seconds']
    
    print(f"\nCompaction 효율성:")
    print(f"  총 Compaction 시간: {total_compaction_time / 1000000:.2f} 초")
    print(f"  총 실험 시간: {total_seconds:.2f} 초")
    print(f"  Compaction 시간 비율: {(total_compaction_time / 1000000) / total_seconds:.3f} ({(total_compaction_time / 1000000) / total_seconds*100:.1f}%)")
    
    # 평균 Compaction 시간
    if compaction_write_count > 0:
        avg_compaction_write_time = compaction_write_sum / compaction_write_count
        print(f"  평균 Compaction Write 시간: {avg_compaction_write_time:.2f} 마이크로초")
    
    if compaction_read_count > 0:
        avg_compaction_read_time = compaction_read_sum / compaction_read_count
        print(f"  평균 Compaction Read 시간: {avg_compaction_read_time:.2f} 마이크로초")
    
    return {
        'compaction_write_count': compaction_write_count,
        'compaction_write_sum': compaction_write_sum,
        'compaction_read_count': compaction_read_count,
        'compaction_read_sum': compaction_read_sum,
        'compaction_time_cpu_sum': compaction_time_cpu_sum,
        'total_compaction_time': total_compaction_time,
        'compaction_ratio': (total_compaction_time / 1000000) / total_seconds
    }

def analyze_sst_io(log_data):
    """SST I/O를 분석합니다."""
    
    print("\n=== SST I/O 분석 ===")
    
    stats = log_data['stats']
    
    # SST 관련 통계
    sst_read_count = stats['sst_read_count']
    sst_read_sum = stats['sst_read_sum']
    sst_write_count = stats['sst_write_count']
    sst_write_sum = stats['sst_write_sum']
    
    print(f"SST I/O 통계:")
    print(f"  SST Read 횟수: {sst_read_count:,}")
    print(f"  SST Read 총 시간: {sst_read_sum:,} 마이크로초")
    print(f"  SST Write 횟수: {sst_write_count:,}")
    print(f"  SST Write 총 시간: {sst_write_sum:,} 마이크로초")
    
    # 평균 I/O 시간
    if sst_read_count > 0:
        avg_sst_read_time = sst_read_sum / sst_read_count
        print(f"  평균 SST Read 시간: {avg_sst_read_time:.2f} 마이크로초")
    
    if sst_write_count > 0:
        avg_sst_write_time = sst_write_sum / sst_write_count
        print(f"  평균 SST Write 시간: {avg_sst_write_time:.2f} 마이크로초")
    
    # I/O 비율
    total_sst_time = sst_read_sum + sst_write_sum
    print(f"  총 SST I/O 시간: {total_sst_time / 1000000:.2f} 초")
    
    return {
        'sst_read_count': sst_read_count,
        'sst_read_sum': sst_read_sum,
        'sst_write_count': sst_write_count,
        'sst_write_sum': sst_write_sum,
        'total_sst_time': total_sst_time,
        'avg_sst_read_time': avg_sst_read_time if sst_read_count > 0 else 0,
        'avg_sst_write_time': avg_sst_write_time if sst_write_count > 0 else 0
    }

def analyze_flush_performance(log_data):
    """Flush 성능을 분석합니다."""
    
    print("\n=== Flush 성능 분석 ===")
    
    stats = log_data['stats']
    
    # Flush 관련 통계
    flush_count = stats['flush_count']
    flush_sum = stats['flush_sum']
    flush_write_bytes = stats['flush_write_bytes']
    flush_write_bytes_sum = stats['flush_write_bytes_sum']
    
    print(f"Flush 통계:")
    print(f"  Flush 횟수: {flush_count:,}")
    print(f"  Flush 총 시간: {flush_sum:,} 마이크로초")
    print(f"  Flush Write Bytes: {flush_write_bytes:,}")
    print(f"  Flush Write Bytes 총합: {flush_write_bytes_sum:,}")
    
    # 평균 Flush 시간
    if flush_count > 0:
        avg_flush_time = flush_sum / flush_count
        print(f"  평균 Flush 시간: {avg_flush_time:.2f} 마이크로초")
    
    # Flush 처리량
    if flush_sum > 0:
        flush_throughput = (flush_write_bytes_sum / 1024 / 1024) / (flush_sum / 1000000)
        print(f"  Flush 처리량: {flush_throughput:.2f} MB/s")
    
    return {
        'flush_count': flush_count,
        'flush_sum': flush_sum,
        'flush_write_bytes': flush_write_bytes,
        'flush_write_bytes_sum': flush_write_bytes_sum,
        'avg_flush_time': avg_flush_time if flush_count > 0 else 0,
        'flush_throughput': flush_throughput if flush_sum > 0 else 0
    }

def analyze_cache_performance(log_data):
    """캐시 성능을 분석합니다."""
    
    print("\n=== 캐시 성능 분석 ===")
    
    stats = log_data['stats']
    
    # 캐시 관련 통계
    block_cache_miss = stats['block_cache_miss']
    block_cache_hit = stats['block_cache_hit']
    
    print(f"캐시 통계:")
    print(f"  Block Cache Miss: {block_cache_miss:,}")
    print(f"  Block Cache Hit: {block_cache_hit:,}")
    
    # 캐시 히트율
    total_cache_access = block_cache_miss + block_cache_hit
    if total_cache_access > 0:
        cache_hit_ratio = block_cache_hit / total_cache_access
        cache_miss_ratio = block_cache_miss / total_cache_access
        print(f"  캐시 히트율: {cache_hit_ratio:.3f} ({cache_hit_ratio*100:.1f}%)")
        print(f"  캐시 미스율: {cache_miss_ratio:.3f} ({cache_miss_ratio*100:.1f}%)")
    else:
        cache_hit_ratio = 0
        cache_miss_ratio = 0
    
    print(f"\n캐시 성능 분석:")
    print(f"  FillRandom은 순수 쓰기 워크로드")
    print(f"  캐시 미스가 매우 높음: {cache_miss_ratio*100:.1f}%")
    print(f"  → 랜덤 키 패턴으로 인한 캐시 효율성 저하")
    
    return {
        'block_cache_miss': block_cache_miss,
        'block_cache_hit': block_cache_hit,
        'cache_hit_ratio': cache_hit_ratio,
        'cache_miss_ratio': cache_miss_ratio
    }

def analyze_bottleneck_summary(log_data, stall_data, compaction_data, sst_data, flush_data, cache_data):
    """병목 요약 분석을 수행합니다."""
    
    print("\n=== 병목 요약 분석 ===")
    
    basic_info = log_data['basic_info']
    actual_throughput = basic_info['throughput_mb_s']
    
    print(f"실제 처리량: {actual_throughput} MB/s")
    print(f"이론적 최대: 1484 MiB/s (Phase-A 측정값)")
    
    # 각 병목의 영향 분석
    bottlenecks = {
        'Write Stall': {
            'impact': stall_data['stall_ratio'],
            'description': 'Compaction으로 인한 쓰기 지연'
        },
        'Compaction I/O': {
            'impact': compaction_data['compaction_ratio'],
            'description': 'Compaction 시 SST 파일 I/O'
        },
        'Cache Miss': {
            'impact': cache_data['cache_miss_ratio'],
            'description': '랜덤 키 패턴으로 인한 캐시 미스'
        }
    }
    
    print(f"\n병목 분석:")
    for bottleneck_name, bottleneck_info in bottlenecks.items():
        impact = bottleneck_info['impact']
        description = bottleneck_info['description']
        print(f"  {bottleneck_name}: {impact:.3f} ({impact*100:.1f}%) - {description}")
    
    # 주요 병목 식별
    max_impact = max(bottlenecks.values(), key=lambda x: x['impact'])
    max_bottleneck = [name for name, info in bottlenecks.items() if info['impact'] == max_impact['impact']][0]
    
    print(f"\n주요 병목: {max_bottleneck} ({max_impact['impact']*100:.1f}%)")
    
    # 성능 저하 원인 분석
    print(f"\n성능 저하 원인:")
    print(f"  1. Write Stall: {stall_data['stall_ratio']*100:.1f}%")
    print(f"  2. Compaction I/O: {compaction_data['compaction_ratio']*100:.1f}%")
    print(f"  3. Cache Miss: {cache_data['cache_miss_ratio']*100:.1f}%")
    
    # 효율성 계산
    theoretical_max = 1484  # MiB/s
    efficiency = actual_throughput / theoretical_max
    print(f"\n전체 효율성: {efficiency:.3f} ({efficiency*100:.1f}%)")
    
    return {
        'bottlenecks': bottlenecks,
        'max_bottleneck': max_bottleneck,
        'efficiency': efficiency
    }

def main():
    """메인 분석 함수"""
    
    print("=== FillRandom 로그 상세 분석 ===")
    
    # 로그 파싱
    log_data = parse_fillrandom_log()
    if not log_data:
        return
    
    print(f"기본 정보:")
    for key, value in log_data['basic_info'].items():
        print(f"  {key}: {value}")
    
    # 각 성능 요소 분석
    stall_data = analyze_write_stalls(log_data)
    compaction_data = analyze_compaction_performance(log_data)
    sst_data = analyze_sst_io(log_data)
    flush_data = analyze_flush_performance(log_data)
    cache_data = analyze_cache_performance(log_data)
    
    # 병목 요약 분석
    bottleneck_summary = analyze_bottleneck_summary(
        log_data, stall_data, compaction_data, sst_data, flush_data, cache_data
    )
    
    print(f"\n=== 분석 완료 ===")
    print(f"주요 병목: {bottleneck_summary['max_bottleneck']}")
    print(f"전체 효율성: {bottleneck_summary['efficiency']*100:.1f}%")

if __name__ == "__main__":
    main()
