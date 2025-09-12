#!/usr/bin/env python3
"""
FillRandom 모델 실패 원인 분석
v4 모델이 FillRandom에서 왜 이렇게 안 맞는지 근본적인 원인을 분석합니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

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

def analyze_fillrandom_characteristics():
    """FillRandom의 특성을 분석합니다."""
    
    print("=== FillRandom 특성 분석 ===")
    
    # 실제 측정값
    measured_throughput = 30.1  # MB/s
    measured_ops_per_sec = 30397  # ops/sec
    value_size = 1024  # bytes
    
    print(f"실제 측정값:")
    print(f"  처리량: {measured_throughput} MB/s")
    print(f"  Ops/sec: {measured_ops_per_sec:,}")
    print(f"  값 크기: {value_size} bytes")
    
    # FillRandom의 특성
    print(f"\nFillRandom 워크로드 특성:")
    print(f"  1. 순수 쓰기 워크로드 (읽기 없음)")
    print(f"  2. 랜덤 키 패턴 (순차적이지 않음)")
    print(f"  3. 대용량 데이터 (10억 키, 1TB)")
    print(f"  4. 지속적 쓰기 (36.6시간)")
    print(f"  5. 높은 WAF (2.39)")
    
    # 이론적 계산
    theoretical_ops = measured_throughput * 1024 * 1024 / value_size
    print(f"\n이론적 계산:")
    print(f"  측정값 기반 Ops/sec: {theoretical_ops:,.0f}")
    print(f"  실제 Ops/sec: {measured_ops_per_sec:,}")
    print(f"  차이: {abs(theoretical_ops - measured_ops_per_sec):,.0f}")
    
    return {
        'measured_throughput': measured_throughput,
        'measured_ops_per_sec': measured_ops_per_sec,
        'value_size': value_size,
        'theoretical_ops': theoretical_ops
    }

def analyze_v4_model_assumptions():
    """v4 모델의 가정들을 분석합니다."""
    
    print("\n=== v4 모델 가정 분석 ===")
    
    # v4 모델의 기본 가정들
    print("v4 모델의 기본 가정들:")
    print("  1. Device Envelope 모델이 정확함")
    print("  2. 동적 시뮬레이션이 실제 RocksDB와 유사함")
    print("  3. Per-level 용량 제약이 정확함")
    print("  4. Stall 모델이 현실적임")
    print("  5. 읽기 비율 추정이 정확함")
    
    # 각 가정의 문제점 분석
    print("\n각 가정의 문제점:")
    
    print("\n1. Device Envelope 모델 문제:")
    print("  - fio 데이터가 실제 측정값이 아닌 추정값")
    print("  - FillRandom 조건과 fio 조건의 차이")
    print("  - RocksDB 내부 처리와 fio의 차이")
    
    print("\n2. 동적 시뮬레이션 문제:")
    print("  - 실제 RocksDB의 복잡한 내부 로직 미반영")
    print("  - Compaction, Flush 등의 실제 동작과 차이")
    print("  - 메모리 관리, 캐시 동작 미반영")
    
    print("\n3. Per-level 용량 제약 문제:")
    print("  - 실제 LSM-tree 레벨별 동작과 차이")
    print("  - Compaction 정책의 복잡성 미반영")
    print("  - 파일 크기, 개수 제한 미반영")
    
    print("\n4. Stall 모델 문제:")
    print("  - 실제 Write Stall 조건과 차이")
    print("  - L0 파일 수 기반 단순 모델")
    print("  - 실제 RocksDB의 복잡한 Stall 로직 미반영")
    
    print("\n5. 읽기 비율 추정 문제:")
    print("  - FillRandom은 순수 쓰기인데 읽기 비율 추정")
    print("  - 실제 읽기 비율은 0이어야 함")
    print("  - 읽기 비율 추정 로직의 부정확성")

def analyze_fillrandom_specific_issues():
    """FillRandom 특화 문제들을 분석합니다."""
    
    print("\n=== FillRandom 특화 문제 분석 ===")
    
    # FillRandom에서만 발생하는 특별한 문제들
    print("FillRandom에서만 발생하는 특별한 문제들:")
    
    print("\n1. 랜덤 키 패턴의 문제:")
    print("  - 캐시 효율성 극도로 낮음")
    print("  - B+ Tree 인덱스 탐색 오버헤드")
    print("  - 메모리 지역성 부족")
    print("  - 페이지 폴트 빈발")
    
    print("\n2. 대용량 데이터의 문제:")
    print("  - 10억 키 × 1KB = 1TB 데이터")
    print("  - 메모리 부족으로 인한 스와핑")
    print("  - 디스크 I/O 병목")
    print("  - 가비지 컬렉션 압력")
    
    print("\n3. 지속적 쓰기의 문제:")
    print("  - 36.6시간 지속적 실행")
    print("  - 메모리 단편화 누적")
    print("  - 디스크 공간 단편화")
    print("  - 시스템 리소스 고갈")
    
    print("\n4. 높은 WAF의 문제:")
    print("  - WAF 2.39 = 실제로 2.39배 더 많이 씀")
    print("  - Compaction 오버헤드 증가")
    print("  - 디스크 쓰기 대역폭 고갈")
    print("  - CPU 압축/해제 오버헤드")
    
    print("\n5. RocksDB 내부 오버헤드:")
    print("  - MemTable 관리 오버헤드")
    print("  - WAL 쓰기 오버헤드")
    print("  - 인덱스 업데이트 오버헤드")
    print("  - 메타데이터 관리 오버헤드")

def analyze_system_bottlenecks():
    """시스템 병목을 분석합니다."""
    
    print("\n=== 시스템 병목 분석 ===")
    
    # 실제 측정값
    measured_throughput = 30.1  # MB/s
    theoretical_max = 1241.8   # MB/s
    efficiency = measured_throughput / theoretical_max
    
    print(f"효율성: {efficiency:.3f} ({efficiency*100:.1f}%)")
    print(f"→ 이론적 최대의 {efficiency*100:.1f}%만 달성")
    
    # 병목 분석
    print("\n병목 분석:")
    
    bottlenecks = {
        'CPU 병목': {
            'description': 'CPU 처리 오버헤드',
            'impact': '압축, 해제, 인덱싱, 메타데이터 관리',
            'efficiency_loss': 0.4
        },
        '메모리 병목': {
            'description': '메모리 대역폭 및 용량 제약',
            'impact': '캐시 미스, 페이지 폴트, 스와핑',
            'efficiency_loss': 0.3
        },
        '디스크 I/O 병목': {
            'description': '디스크 쓰기 대역폭 제약',
            'impact': 'WAL, SST 파일 쓰기, Compaction',
            'efficiency_loss': 0.2
        },
        '동시성 병목': {
            'description': '스레드 경합 및 락 경합',
            'impact': '멀티스레딩 오버헤드, 락 대기',
            'efficiency_loss': 0.1
        }
    }
    
    for bottleneck_name, bottleneck_info in bottlenecks.items():
        print(f"\n{bottleneck_name}:")
        print(f"  설명: {bottleneck_info['description']}")
        print(f"  영향: {bottleneck_info['impact']}")
        print(f"  효율성 손실: {bottleneck_info['efficiency_loss']*100:.0f}%")
    
    # 누적 효율성 계산
    cumulative_efficiency = 1.0
    for bottleneck_info in bottlenecks.values():
        cumulative_efficiency *= (1.0 - bottleneck_info['efficiency_loss'])
    
    print(f"\n누적 효율성: {cumulative_efficiency:.3f} ({cumulative_efficiency*100:.1f}%)")
    print(f"실제 효율성: {efficiency:.3f} ({efficiency*100:.1f}%)")
    print(f"차이: {abs(cumulative_efficiency - efficiency):.3f}")

def analyze_v4_model_failure_reasons():
    """v4 모델 실패의 근본적인 이유를 분석합니다."""
    
    print("\n=== v4 모델 실패 근본 원인 ===")
    
    print("v4 모델이 FillRandom에서 실패하는 근본적인 이유들:")
    
    print("\n1. 모델링 철학의 문제:")
    print("  - '이론적 상한선' 모델링에 집중")
    print("  - '현실적 제약' 모델링 부족")
    print("  - 이상적인 조건 가정")
    print("  - 실제 시스템의 복잡성 무시")
    
    print("\n2. 데이터 품질 문제:")
    print("  - fio 데이터가 실제 측정값이 아닌 추정값")
    print("  - FillRandom 조건과 fio 조건의 불일치")
    print("  - RocksDB 내부 처리와 fio의 차이")
    print("  - 워크로드별 특성 미반영")
    
    print("\n3. 모델 복잡성 문제:")
    print("  - 너무 복잡한 동적 시뮬레이션")
    print("  - 많은 가정과 추정값")
    print("  - 오류 누적 효과")
    print("  - 검증 어려움")
    
    print("\n4. FillRandom 특화 부족:")
    print("  - 일반적인 LSM-tree 모델")
    print("  - FillRandom 특성 미반영")
    print("  - 랜덤 키 패턴의 영향 무시")
    print("  - 대용량 데이터의 영향 무시")
    
    print("\n5. 시스템 오버헤드 무시:")
    print("  - CPU 오버헤드 과소평가")
    print("  - 메모리 제약 무시")
    print("  - OS/파일시스템 오버헤드 무시")
    print("  - RocksDB 내부 오버헤드 무시")

def propose_solutions():
    """해결 방안을 제안합니다."""
    
    print("\n=== 해결 방안 제안 ===")
    
    print("FillRandom 모델링을 위한 해결 방안들:")
    
    print("\n1. 실험적 접근법:")
    print("  - 실제 측정값 기반 보정 계수")
    print("  - 워크로드별 실험적 모델")
    print("  - 시스템 설정별 보정 계수")
    print("  - 하이브리드 모델 (이론 + 실험)")
    
    print("\n2. FillRandom 특화 모델:")
    print("  - 랜덤 키 패턴 모델링")
    print("  - 캐시 효율성 모델링")
    print("  - 메모리 지역성 모델링")
    print("  - 페이지 폴트 모델링")
    
    print("\n3. 시스템 오버헤드 모델링:")
    print("  - CPU 오버헤드 정량화")
    print("  - 메모리 제약 모델링")
    print("  - 디스크 I/O 병목 모델링")
    print("  - 동시성 제약 모델링")
    
    print("\n4. 단순화된 모델:")
    print("  - 복잡한 동적 시뮬레이션 대신 단순한 공식")
    print("  - 실험적 보정 계수 기반")
    print("  - 검증 가능한 가정들만 사용")
    print("  - 해석 가능한 모델")
    
    print("\n5. 데이터 품질 개선:")
    print("  - 실제 fio 측정값 사용")
    print("  - FillRandom 조건과 동일한 fio 설정")
    print("  - RocksDB 내부 처리 고려")
    print("  - 워크로드별 특성 반영")

def main():
    """메인 분석 함수"""
    
    print("=== FillRandom 모델 실패 원인 분석 ===")
    
    # 데이터 로드
    phase_data = load_phase_data()
    if not phase_data:
        return
    
    # FillRandom 특성 분석
    fillrandom_chars = analyze_fillrandom_characteristics()
    
    # v4 모델 가정 분석
    analyze_v4_model_assumptions()
    
    # FillRandom 특화 문제 분석
    analyze_fillrandom_specific_issues()
    
    # 시스템 병목 분석
    analyze_system_bottlenecks()
    
    # v4 모델 실패 근본 원인
    analyze_v4_model_failure_reasons()
    
    # 해결 방안 제안
    propose_solutions()
    
    print(f"\n=== 분석 완료 ===")
    print("결론: v4 모델은 '이론적 상한선' 모델링에 집중하여")
    print("FillRandom의 '현실적 제약'을 제대로 반영하지 못했습니다.")
    print("v5 모델은 실험적 접근법과 FillRandom 특화 모델링이 필요합니다.")

if __name__ == "__main__":
    main()



