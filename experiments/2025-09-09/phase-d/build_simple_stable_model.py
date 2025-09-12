#!/usr/bin/env python3
"""
단순하고 안정적인 모델 구축
실제 데이터를 기반으로 단순하고 안정적인 모델을 구축합니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from datetime import datetime

def load_workload_analysis():
    """워크로드 분석 결과를 로드합니다."""
    
    print("=== 워크로드 분석 결과 로드 ===")
    
    analysis_file = Path("all_workloads_analysis.json")
    if not analysis_file.exists():
        print(f"❌ 분석 결과 파일을 찾을 수 없습니다: {analysis_file}")
        return None
    
    with open(analysis_file, 'r') as f:
        analysis_data = json.load(f)
    
    print(f"분석 결과 로드 완료:")
    print(f"  타임스탬프: {analysis_data['timestamp']}")
    print(f"  워크로드 수: {len(analysis_data['workload_data'])}")
    
    return analysis_data

def identify_key_patterns(analysis_data):
    """핵심 패턴들을 식별합니다."""
    
    print("\n=== 핵심 패턴 식별 ===")
    
    workload_data = analysis_data['workload_data']
    bottlenecks = analysis_data['bottlenecks']
    
    patterns = {}
    
    for workload in workload_data:
        workload_name = workload['workload_name']
        basic = workload['basic_performance']
        workload_bottlenecks = bottlenecks[workload_name]
        
        print(f"\n{workload_name.upper()} 패턴:")
        
        # 성능 패턴
        performance_pattern = {
            'throughput_mb_s': basic['throughput_mb_s'],
            'ops_per_sec': basic['ops_per_sec'],
            'micros_per_op': basic['micros_per_op'],
            'total_seconds': basic['total_seconds']
        }
        
        # 병목 패턴
        bottleneck_pattern = {
            'write_stall_ratio': workload_bottlenecks['write_stall']['ratio'],
            'compaction_io_ratio': workload_bottlenecks['compaction_io']['ratio'],
            'cache_miss_ratio': workload_bottlenecks['cache_miss']['miss_ratio'],
            'flush_ratio': workload_bottlenecks['flush']['ratio']
        }
        
        # 워크로드 특성
        if 'fillrandom' in workload_name:
            workload_type = 'random_write'
            access_pattern = 'random'
        elif 'overwrite' in workload_name:
            workload_type = 'overwrite'
            access_pattern = 'random'
        else:
            workload_type = 'unknown'
            access_pattern = 'unknown'
        
        patterns[workload_name] = {
            'performance': performance_pattern,
            'bottlenecks': bottleneck_pattern,
            'workload_type': workload_type,
            'access_pattern': access_pattern
        }
        
        print(f"  성능: {performance_pattern['throughput_mb_s']:.1f} MB/s, {performance_pattern['ops_per_sec']:,} ops/sec")
        print(f"  병목: Write Stall {bottleneck_pattern['write_stall_ratio']:.3f}, Compaction I/O {bottleneck_pattern['compaction_io_ratio']:.3f}")
        print(f"  특성: {workload_type}, {access_pattern}")
    
    return patterns

def design_simple_model(patterns):
    """단순한 모델을 설계합니다."""
    
    print("\n=== 단순 모델 설계 ===")
    
    # 모델 설계 원칙
    print("모델 설계 원칙:")
    print("  1. 실제 데이터 기반")
    print("  2. 단순한 선형 관계")
    print("  3. 검증 가능한 가정")
    print("  4. 이해하기 쉬운 공식")
    
    # 핵심 변수 식별
    print("\n핵심 변수 식별:")
    
    # 1. 이론적 최대 성능 (Phase-A fio 결과)
    theoretical_max = 1484  # MiB/s
    print(f"  1. 이론적 최대 성능: {theoretical_max} MiB/s (Phase-A fio 결과)")
    
    # 2. 워크로드별 효율성
    workload_efficiency = {}
    for workload_name, pattern in patterns.items():
        actual_throughput = pattern['performance']['throughput_mb_s']
        efficiency = actual_throughput / theoretical_max
        workload_efficiency[workload_name] = efficiency
        print(f"  2. {workload_name} 효율성: {efficiency:.4f} ({actual_throughput:.1f}/{theoretical_max})")
    
    # 3. 병목별 영향도
    print("\n병목별 영향도 분석:")
    bottleneck_impacts = {}
    
    for workload_name, pattern in patterns.items():
        bottlenecks = pattern['bottlenecks']
        print(f"\n  {workload_name.upper()}:")
        
        # 가장 큰 병목 식별
        max_bottleneck = max(bottlenecks.items(), key=lambda x: x[1])
        bottleneck_impacts[workload_name] = {
            'max_bottleneck': max_bottleneck[0],
            'max_impact': max_bottleneck[1],
            'all_bottlenecks': bottlenecks
        }
        
        print(f"    가장 큰 병목: {max_bottleneck[0]} ({max_bottleneck[1]:.3f})")
        for bottleneck_name, impact in bottlenecks.items():
            print(f"    {bottleneck_name}: {impact:.3f}")
    
    # 4. 단순 모델 공식 설계
    print("\n단순 모델 공식 설계:")
    
    # 모델 1: 워크로드별 고정 효율성
    model_1 = {
        'name': '워크로드별 고정 효율성 모델',
        'formula': 'S_predicted = S_theoretical × η_workload',
        'description': '워크로드별로 고정된 효율성을 사용하는 단순한 모델',
        'parameters': {
            'S_theoretical': theoretical_max,
            'η_workload': workload_efficiency
        }
    }
    
    # 모델 2: 병목 기반 모델
    model_2 = {
        'name': '병목 기반 모델',
        'formula': 'S_predicted = S_theoretical × (1 - max_bottleneck_impact)',
        'description': '가장 큰 병목의 영향을 고려한 모델',
        'parameters': {
            'S_theoretical': theoretical_max,
            'max_bottleneck_impact': {name: data['max_impact'] for name, data in bottleneck_impacts.items()}
        }
    }
    
    # 모델 3: 복합 모델
    model_3 = {
        'name': '복합 모델',
        'formula': 'S_predicted = S_theoretical × η_workload × (1 - max_bottleneck_impact)',
        'description': '워크로드 효율성과 병목을 모두 고려한 모델',
        'parameters': {
            'S_theoretical': theoretical_max,
            'η_workload': workload_efficiency,
            'max_bottleneck_impact': {name: data['max_impact'] for name, data in bottleneck_impacts.items()}
        }
    }
    
    models = [model_1, model_2, model_3]
    
    for i, model in enumerate(models, 1):
        print(f"\n  모델 {i}: {model['name']}")
        print(f"    공식: {model['formula']}")
        print(f"    설명: {model['description']}")
        print(f"    파라미터:")
        for param_name, param_value in model['parameters'].items():
            if isinstance(param_value, dict):
                print(f"      {param_name}:")
                for key, value in param_value.items():
                    print(f"        {key}: {value:.4f}")
            else:
                print(f"      {param_name}: {param_value}")
    
    return {
        'theoretical_max': theoretical_max,
        'workload_efficiency': workload_efficiency,
        'bottleneck_impacts': bottleneck_impacts,
        'models': models
    }

def validate_models(patterns, model_design):
    """모델들을 검증합니다."""
    
    print("\n=== 모델 검증 ===")
    
    models = model_design['models']
    validation_results = {}
    
    for model in models:
        print(f"\n{model['name']} 검증:")
        
        model_results = {}
        
        for workload_name, pattern in patterns.items():
            actual_throughput = pattern['performance']['throughput_mb_s']
            
            # 모델별 예측 계산
            if model['name'] == '워크로드별 고정 효율성 모델':
                predicted_throughput = model_design['theoretical_max'] * model_design['workload_efficiency'][workload_name]
            elif model['name'] == '병목 기반 모델':
                max_impact = model_design['bottleneck_impacts'][workload_name]['max_impact']
                predicted_throughput = model_design['theoretical_max'] * (1 - max_impact)
            elif model['name'] == '복합 모델':
                workload_eff = model_design['workload_efficiency'][workload_name]
                max_impact = model_design['bottleneck_impacts'][workload_name]['max_impact']
                predicted_throughput = model_design['theoretical_max'] * workload_eff * (1 - max_impact)
            else:
                predicted_throughput = 0
            
            # 오류 계산
            error = abs(predicted_throughput - actual_throughput)
            error_rate = error / actual_throughput if actual_throughput > 0 else 0
            
            model_results[workload_name] = {
                'actual': actual_throughput,
                'predicted': predicted_throughput,
                'error': error,
                'error_rate': error_rate
            }
            
            print(f"  {workload_name}:")
            print(f"    실제: {actual_throughput:.1f} MB/s")
            print(f"    예측: {predicted_throughput:.1f} MB/s")
            print(f"    오류: {error:.1f} MB/s ({error_rate:.3f} = {error_rate*100:.1f}%)")
        
        # 전체 모델 성능
        total_error_rate = sum(result['error_rate'] for result in model_results.values()) / len(model_results)
        print(f"  전체 오류율: {total_error_rate:.3f} ({total_error_rate*100:.1f}%)")
        
        validation_results[model['name']] = {
            'results': model_results,
            'total_error_rate': total_error_rate
        }
    
    # 모델 비교
    print(f"\n모델 비교:")
    print(f"{'모델명':<30} {'전체 오류율':<15}")
    print("-" * 45)
    
    sorted_models = sorted(validation_results.items(), key=lambda x: x[1]['total_error_rate'])
    for model_name, results in sorted_models:
        error_rate = results['total_error_rate']
        print(f"{model_name:<30} {error_rate:.3f} ({error_rate*100:.1f}%)")
    
    return validation_results

def recommend_best_model(validation_results):
    """최적 모델을 추천합니다."""
    
    print("\n=== 최적 모델 추천 ===")
    
    # 오류율이 가장 낮은 모델 선택
    best_model = min(validation_results.items(), key=lambda x: x[1]['total_error_rate'])
    best_model_name = best_model[0]
    best_model_results = best_model[1]
    
    print(f"최적 모델: {best_model_name}")
    print(f"전체 오류율: {best_model_results['total_error_rate']:.3f} ({best_model_results['total_error_rate']*100:.1f}%)")
    
    print(f"\n모델 성능 상세:")
    for workload_name, result in best_model_results['results'].items():
        print(f"  {workload_name}:")
        print(f"    실제: {result['actual']:.1f} MB/s")
        print(f"    예측: {result['predicted']:.1f} MB/s")
        print(f"    오류: {result['error']:.1f} MB/s ({result['error_rate']*100:.1f}%)")
    
    # 모델 개선 제안
    print(f"\n모델 개선 제안:")
    if best_model_results['total_error_rate'] > 0.1:  # 10% 이상 오류
        print("  - 오류율이 높습니다. 더 많은 데이터 수집이 필요합니다.")
        print("  - 워크로드별 특성을 더 세밀하게 분석해야 합니다.")
        print("  - 병목 모델링을 개선해야 합니다.")
    else:
        print("  - 모델이 상당히 정확합니다.")
        print("  - 추가 워크로드로 검증을 확장할 수 있습니다.")
    
    return {
        'best_model': best_model_name,
        'best_results': best_model_results,
        'recommendations': '모델 개선 제안'
    }

def main():
    """메인 함수"""
    
    print("=== 단순하고 안정적인 모델 구축 ===")
    
    # 워크로드 분석 결과 로드
    analysis_data = load_workload_analysis()
    if not analysis_data:
        return
    
    # 핵심 패턴 식별
    patterns = identify_key_patterns(analysis_data)
    
    # 단순 모델 설계
    model_design = design_simple_model(patterns)
    
    # 모델 검증
    validation_results = validate_models(patterns, model_design)
    
    # 최적 모델 추천
    recommendation = recommend_best_model(validation_results)
    
    # 결과 저장
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'patterns': patterns,
        'model_design': model_design,
        'validation_results': validation_results,
        'recommendation': recommendation
    }
    
    output_file = "simple_stable_model_results.json"
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"\n=== 모델 구축 완료 ===")
    print(f"결과가 {output_file}에 저장되었습니다.")
    print(f"최적 모델: {recommendation['best_model']}")
    print(f"전체 오류율: {recommendation['best_results']['total_error_rate']*100:.1f}%")

if __name__ == "__main__":
    main()



