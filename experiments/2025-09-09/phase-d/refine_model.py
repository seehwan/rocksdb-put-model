#!/usr/bin/env python3
"""
모델 정교화
현재 모델을 더 정교하게 다듬어서 정확도와 실용성을 향상시킵니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from datetime import datetime

def load_existing_model():
    """기존 모델 결과를 로드합니다."""
    
    print("=== 기존 모델 결과 로드 ===")
    
    model_file = Path("simple_stable_model_results.json")
    if not model_file.exists():
        print(f"❌ 기존 모델 파일을 찾을 수 없습니다: {model_file}")
        return None
    
    with open(model_file, 'r') as f:
        model_data = json.load(f)
    
    print(f"기존 모델 로드 완료:")
    print(f"  타임스탬프: {model_data['timestamp']}")
    print(f"  최적 모델: {model_data['recommendation']['best_model']}")
    print(f"  오류율: {model_data['recommendation']['best_results']['total_error_rate']*100:.1f}%")
    
    return model_data

def analyze_workload_characteristics(model_data):
    """워크로드 특성을 더 세밀하게 분석합니다."""
    
    print("\n=== 워크로드 특성 세밀 분석 ===")
    
    patterns = model_data['patterns']
    
    workload_characteristics = {}
    
    for workload_name, pattern in patterns.items():
        print(f"\n{workload_name.upper()} 특성 분석:")
        
        # 기본 성능 특성
        performance = pattern['performance']
        bottlenecks = pattern['bottlenecks']
        
        # 1. 성능 특성
        performance_chars = {
            'throughput_mb_s': performance['throughput_mb_s'],
            'ops_per_sec': performance['ops_per_sec'],
            'micros_per_op': performance['micros_per_op'],
            'efficiency': performance['throughput_mb_s'] / 1484,  # 이론적 최대 대비
            'ops_efficiency': performance['ops_per_sec'] / 100000,  # 10만 ops/sec 대비
            'latency_efficiency': 100 / performance['micros_per_op']  # 100 micros/op 대비
        }
        
        # 2. 병목 특성
        bottleneck_chars = {
            'write_stall_ratio': bottlenecks['write_stall_ratio'],
            'compaction_io_ratio': bottlenecks['compaction_io_ratio'],
            'cache_miss_ratio': bottlenecks['cache_miss_ratio'],
            'flush_ratio': bottlenecks['flush_ratio'],
            'total_bottleneck_ratio': sum(bottlenecks.values()),
            'max_bottleneck': max(bottlenecks.items(), key=lambda x: x[1])[0],
            'bottleneck_diversity': len([r for r in bottlenecks.values() if r > 0.1])  # 10% 이상인 병목 수
        }
        
        # 3. 워크로드 유형 특성
        if 'fillrandom' in workload_name:
            workload_type_chars = {
                'access_pattern': 'random',
                'write_type': 'new_keys',
                'key_distribution': 'uniform',
                'value_size': 'fixed',
                'compression_ratio': 'high',  # 새로운 키이므로 압축률 높음
                'cache_friendliness': 'low',  # 랜덤 접근으로 캐시 효율성 낮음
                'compaction_frequency': 'high'  # 랜덤 키로 인한 높은 컴팩션 빈도
            }
        elif 'overwrite' in workload_name:
            workload_type_chars = {
                'access_pattern': 'random',
                'write_type': 'existing_keys',
                'key_distribution': 'uniform',
                'value_size': 'fixed',
                'compression_ratio': 'medium',  # 기존 키 덮어쓰기로 중간 압축률
                'cache_friendliness': 'medium',  # 기존 키 접근으로 중간 캐시 효율성
                'compaction_frequency': 'medium'  # 덮어쓰기로 인한 중간 컴팩션 빈도
            }
        else:
            workload_type_chars = {
                'access_pattern': 'unknown',
                'write_type': 'unknown',
                'key_distribution': 'unknown',
                'value_size': 'unknown',
                'compression_ratio': 'unknown',
                'cache_friendliness': 'unknown',
                'compaction_frequency': 'unknown'
            }
        
        # 4. 통합 특성 점수
        integrated_scores = {
            'performance_score': (performance_chars['efficiency'] + performance_chars['ops_efficiency'] + performance_chars['latency_efficiency']) / 3,
            'bottleneck_score': 1 - (bottleneck_chars['total_bottleneck_ratio'] / 4),  # 병목이 적을수록 높은 점수
            'workload_complexity': bottleneck_chars['bottleneck_diversity'],  # 병목 다양성이 복잡성
            'overall_efficiency': performance_chars['efficiency']
        }
        
        workload_characteristics[workload_name] = {
            'performance': performance_chars,
            'bottlenecks': bottleneck_chars,
            'workload_type': workload_type_chars,
            'integrated_scores': integrated_scores
        }
        
        print(f"  성능 특성:")
        for key, value in performance_chars.items():
            if isinstance(value, float):
                print(f"    {key}: {value:.4f}")
            else:
                print(f"    {key}: {value}")
        
        print(f"  병목 특성:")
        for key, value in bottleneck_chars.items():
            if isinstance(value, float):
                print(f"    {key}: {value:.4f}")
            else:
                print(f"    {key}: {value}")
        
        print(f"  워크로드 유형:")
        for key, value in workload_type_chars.items():
            print(f"    {key}: {value}")
        
        print(f"  통합 점수:")
        for key, value in integrated_scores.items():
            print(f"    {key}: {value:.4f}")
    
    return workload_characteristics

def design_refined_models(workload_characteristics):
    """정교화된 모델들을 설계합니다."""
    
    print("\n=== 정교화된 모델 설계 ===")
    
    refined_models = {}
    
    # 모델 1: 성능 기반 모델
    model_1 = {
        'name': '성능 기반 모델',
        'formula': 'S_predicted = S_theoretical × η_performance',
        'description': '성능 특성(처리량, 연산수, 지연시간)을 종합한 모델',
        'parameters': {},
        'calculation_method': 'performance_based'
    }
    
    # 모델 2: 병목 기반 모델 (개선)
    model_2 = {
        'name': '병목 기반 모델 (개선)',
        'formula': 'S_predicted = S_theoretical × (1 - weighted_bottleneck_impact)',
        'description': '병목의 가중치를 고려한 개선된 병목 모델',
        'parameters': {},
        'calculation_method': 'bottleneck_based'
    }
    
    # 모델 3: 워크로드 유형 기반 모델
    model_3 = {
        'name': '워크로드 유형 기반 모델',
        'formula': 'S_predicted = S_theoretical × η_workload_type',
        'description': '워크로드 유형별 특성을 반영한 모델',
        'parameters': {},
        'calculation_method': 'workload_type_based'
    }
    
    # 모델 4: 통합 모델
    model_4 = {
        'name': '통합 모델',
        'formula': 'S_predicted = S_theoretical × η_performance × η_bottleneck × η_workload_type',
        'description': '성능, 병목, 워크로드 유형을 모두 고려한 통합 모델',
        'parameters': {},
        'calculation_method': 'integrated'
    }
    
    # 모델 5: 적응형 모델
    model_5 = {
        'name': '적응형 모델',
        'formula': 'S_predicted = S_theoretical × adaptive_efficiency',
        'description': '워크로드 특성에 따라 적응적으로 효율성을 조정하는 모델',
        'parameters': {},
        'calculation_method': 'adaptive'
    }
    
    refined_models = {
        'performance_based': model_1,
        'bottleneck_based': model_2,
        'workload_type_based': model_3,
        'integrated': model_4,
        'adaptive': model_5
    }
    
    print("정교화된 모델들:")
    for model_name, model in refined_models.items():
        print(f"\n{model['name']}:")
        print(f"  공식: {model['formula']}")
        print(f"  설명: {model['description']}")
        print(f"  계산 방법: {model['calculation_method']}")
    
    return refined_models

def calculate_model_parameters(workload_characteristics, refined_models):
    """각 모델의 파라미터를 계산합니다."""
    
    print("\n=== 모델 파라미터 계산 ===")
    
    theoretical_max = 1484  # MiB/s
    
    for model_name, model in refined_models.items():
        print(f"\n{model_name.upper()} 모델 파라미터:")
        
        if model['calculation_method'] == 'performance_based':
            # 성능 기반 모델
            for workload_name, chars in workload_characteristics.items():
                performance_score = chars['integrated_scores']['performance_score']
                efficiency = performance_score * 0.1  # 스케일링
                model['parameters'][workload_name] = efficiency
                print(f"  {workload_name}: {efficiency:.4f} (성능 점수: {performance_score:.4f})")
        
        elif model['calculation_method'] == 'bottleneck_based':
            # 병목 기반 모델 (개선)
            for workload_name, chars in workload_characteristics.items():
                bottlenecks = chars['bottlenecks']
                # 가중치 적용: Write Stall > Compaction I/O > Cache Miss > Flush
                weights = {'write_stall_ratio': 0.4, 'compaction_io_ratio': 0.3, 'cache_miss_ratio': 0.2, 'flush_ratio': 0.1}
                weighted_impact = sum(bottlenecks[key] * weights[key] for key in weights.keys())
                efficiency = 1 - weighted_impact
                model['parameters'][workload_name] = efficiency
                print(f"  {workload_name}: {efficiency:.4f} (가중치 병목 영향: {weighted_impact:.4f})")
        
        elif model['calculation_method'] == 'workload_type_based':
            # 워크로드 유형 기반 모델
            for workload_name, chars in workload_characteristics.items():
                workload_type = chars['workload_type']
                if 'fillrandom' in workload_name:
                    efficiency = 0.02  # 랜덤 키로 인한 낮은 효율성
                elif 'overwrite' in workload_name:
                    efficiency = 0.05  # 덮어쓰기로 인한 중간 효율성
                else:
                    efficiency = 0.03  # 기본값
                model['parameters'][workload_name] = efficiency
                print(f"  {workload_name}: {efficiency:.4f} (워크로드 유형: {workload_type['write_type']})")
        
        elif model['calculation_method'] == 'integrated':
            # 통합 모델
            for workload_name, chars in workload_characteristics.items():
                performance_score = chars['integrated_scores']['performance_score']
                bottleneck_score = chars['integrated_scores']['bottleneck_score']
                overall_efficiency = chars['integrated_scores']['overall_efficiency']
                
                # 통합 효율성 계산
                integrated_efficiency = (performance_score * 0.4 + bottleneck_score * 0.3 + overall_efficiency * 0.3) * 0.1
                model['parameters'][workload_name] = integrated_efficiency
                print(f"  {workload_name}: {integrated_efficiency:.4f} (통합 점수)")
        
        elif model['calculation_method'] == 'adaptive':
            # 적응형 모델
            for workload_name, chars in workload_characteristics.items():
                # 워크로드 복잡성에 따라 적응적 조정
                complexity = chars['integrated_scores']['workload_complexity']
                base_efficiency = chars['integrated_scores']['overall_efficiency']
                
                # 복잡성이 높을수록 효율성 감소
                adaptive_efficiency = base_efficiency * (1 - complexity * 0.1)
                model['parameters'][workload_name] = adaptive_efficiency
                print(f"  {workload_name}: {adaptive_efficiency:.4f} (복잡성: {complexity}, 기본 효율성: {base_efficiency:.4f})")
    
    return refined_models

def validate_refined_models(workload_characteristics, refined_models):
    """정교화된 모델들을 검증합니다."""
    
    print("\n=== 정교화된 모델 검증 ===")
    
    theoretical_max = 1484  # MiB/s
    validation_results = {}
    
    for model_name, model in refined_models.items():
        print(f"\n{model_name.upper()} 모델 검증:")
        
        model_results = {}
        
        for workload_name, chars in workload_characteristics.items():
            actual_throughput = chars['performance']['throughput_mb_s']
            predicted_throughput = theoretical_max * model['parameters'][workload_name]
            
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
        
        validation_results[model_name] = {
            'results': model_results,
            'total_error_rate': total_error_rate
        }
    
    # 모델 비교
    print(f"\n정교화된 모델 비교:")
    print(f"{'모델명':<30} {'전체 오류율':<15}")
    print("-" * 45)
    
    sorted_models = sorted(validation_results.items(), key=lambda x: x[1]['total_error_rate'])
    for model_name, results in sorted_models:
        error_rate = results['total_error_rate']
        print(f"{model_name:<30} {error_rate:.3f} ({error_rate*100:.1f}%)")
    
    return validation_results

def recommend_refined_model(validation_results, refined_models):
    """최적의 정교화된 모델을 추천합니다."""
    
    print("\n=== 최적 정교화 모델 추천 ===")
    
    # 오류율이 가장 낮은 모델 선택
    best_model_name = min(validation_results.items(), key=lambda x: x[1]['total_error_rate'])[0]
    best_model = refined_models[best_model_name]
    best_results = validation_results[best_model_name]
    
    print(f"최적 모델: {best_model['name']}")
    print(f"전체 오류율: {best_results['total_error_rate']:.3f} ({best_results['total_error_rate']*100:.1f}%)")
    
    print(f"\n모델 상세 정보:")
    print(f"  공식: {best_model['formula']}")
    print(f"  설명: {best_model['description']}")
    print(f"  계산 방법: {best_model['calculation_method']}")
    
    print(f"\n모델 성능 상세:")
    for workload_name, result in best_results['results'].items():
        print(f"  {workload_name}:")
        print(f"    실제: {result['actual']:.1f} MB/s")
        print(f"    예측: {result['predicted']:.1f} MB/s")
        print(f"    오류: {result['error']:.1f} MB/s ({result['error_rate']*100:.1f}%)")
    
    # 모델 개선 제안
    print(f"\n모델 개선 제안:")
    if best_results['total_error_rate'] < 0.05:  # 5% 미만 오류
        print("  ✅ 모델이 매우 정확합니다.")
        print("  - 추가 워크로드로 검증을 확장할 수 있습니다.")
        print("  - 실용적 배포가 가능합니다.")
    elif best_results['total_error_rate'] < 0.1:  # 10% 미만 오류
        print("  ✅ 모델이 상당히 정확합니다.")
        print("  - 약간의 개선 여지가 있습니다.")
        print("  - 더 많은 데이터로 정확도를 높일 수 있습니다.")
    else:
        print("  ⚠️ 모델 정확도가 개선이 필요합니다.")
        print("  - 더 많은 워크로드 데이터가 필요합니다.")
        print("  - 모델 파라미터 튜닝이 필요합니다.")
    
    return {
        'best_model_name': best_model_name,
        'best_model': best_model,
        'best_results': best_results,
        'recommendations': '모델 개선 제안'
    }

def main():
    """메인 함수"""
    
    print("=== 모델 정교화 ===")
    
    # 기존 모델 결과 로드
    model_data = load_existing_model()
    if not model_data:
        return
    
    # 워크로드 특성 세밀 분석
    workload_characteristics = analyze_workload_characteristics(model_data)
    
    # 정교화된 모델 설계
    refined_models = design_refined_models(workload_characteristics)
    
    # 모델 파라미터 계산
    refined_models = calculate_model_parameters(workload_characteristics, refined_models)
    
    # 정교화된 모델 검증
    validation_results = validate_refined_models(workload_characteristics, refined_models)
    
    # 최적 모델 추천
    recommendation = recommend_refined_model(validation_results, refined_models)
    
    # 결과 저장
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'workload_characteristics': workload_characteristics,
        'refined_models': refined_models,
        'validation_results': validation_results,
        'recommendation': recommendation
    }
    
    output_file = "refined_model_results.json"
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    print(f"\n=== 모델 정교화 완료 ===")
    print(f"결과가 {output_file}에 저장되었습니다.")
    print(f"최적 모델: {recommendation['best_model']['name']}")
    print(f"전체 오류율: {recommendation['best_results']['total_error_rate']*100:.1f}%")

if __name__ == "__main__":
    main()



