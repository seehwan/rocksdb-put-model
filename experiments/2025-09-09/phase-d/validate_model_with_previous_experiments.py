#!/usr/bin/env python3
"""
이전 실험들로 모델 검증
정교화된 모델이 이전 실험들에도 잘 적용되는지 확인합니다.
"""

import json
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from datetime import datetime

def load_previous_experiments():
    """이전 실험들의 데이터를 로드합니다."""
    
    print("=== 이전 실험 데이터 로드 ===")
    
    experiments = {}
    
    # 2025-09-08 실험 데이터
    exp_2025_09_08_file = Path("/home/sslab/rocksdb-put-model/experiments/2025-09-08/phase-b/benchmark_results.json")
    if exp_2025_09_08_file.exists():
        with open(exp_2025_09_08_file, 'r') as f:
            exp_2025_09_08_data = json.load(f)
        
        experiments['2025-09-08'] = {
            'date': '2025-09-08',
            'workload': 'fillrandom',
            'throughput_mb_s': exp_2025_09_08_data['performance_results']['throughput']['put_rate_mb_s'],
            'ops_per_sec': exp_2025_09_08_data['performance_results']['throughput']['operations_per_second'],
            'micros_per_op': exp_2025_09_08_data['performance_results']['throughput']['microseconds_per_operation'],
            'total_seconds': exp_2025_09_08_data['experiment_info']['duration_seconds'],
            'total_operations': exp_2025_09_08_data['performance_results']['throughput']['total_operations'],
            'stall_percentage': exp_2025_09_08_data['stall_analysis']['stall_percentage'],
            'write_amplification': exp_2025_09_08_data['write_amplification']['write_amplification'],
            'compression_ratio': exp_2025_09_08_data['data_volume']['compression_ratio']
        }
        print(f"2025-09-08 실험 로드 완료: {experiments['2025-09-08']['throughput_mb_s']:.1f} MB/s")
    
    # 2025-09-05 실험 데이터
    exp_2025_09_05_file = Path("/home/sslab/rocksdb-put-model/experiments/2025-09-05/experiment_data.json")
    if exp_2025_09_05_file.exists():
        with open(exp_2025_09_05_file, 'r') as f:
            exp_2025_09_05_data = json.load(f)
        
        experiments['2025-09-05'] = {
            'date': '2025-09-05',
            'workload': 'fillrandom',
            'throughput_mb_s': exp_2025_09_05_data['phase_b_results']['actual_performance']['put_rate_mib_s'],
            'ops_per_sec': exp_2025_09_05_data['phase_b_results']['actual_performance']['ops_per_sec'],
            'micros_per_op': exp_2025_09_05_data['phase_b_results']['actual_performance']['micros_per_op'],
            'total_seconds': exp_2025_09_05_data['phase_b_results']['actual_performance']['total_seconds'],
            'total_operations': exp_2025_09_05_data['phase_b_results']['actual_performance']['total_operations'],
            'stall_percentage': exp_2025_09_05_data['phase_b_results']['stall_analysis']['stall_percentage'],
            'write_amplification': exp_2025_09_05_data['phase_b_results']['write_amplification']['write_amplification'],
            'compression_ratio': exp_2025_09_05_data['phase_b_results']['compression_analysis']['compression_ratio']
        }
        print(f"2025-09-05 실험 로드 완료: {experiments['2025-09-05']['throughput_mb_s']:.1f} MB/s")
    
    # 현재 실험 데이터 (2025-09-09)
    current_exp_file = Path("all_workloads_analysis.json")
    if current_exp_file.exists():
        with open(current_exp_file, 'r') as f:
            current_exp_data = json.load(f)
        
        for workload_data in current_exp_data['workload_data']:
            workload_name = workload_data['workload_name']
            basic = workload_data['basic_performance']
            
            experiments[f'2025-09-09-{workload_name}'] = {
                'date': '2025-09-09',
                'workload': workload_name,
                'throughput_mb_s': basic['throughput_mb_s'],
                'ops_per_sec': basic['ops_per_sec'],
                'micros_per_op': basic['micros_per_op'],
                'total_seconds': basic['total_seconds'],
                'total_operations': basic['total_operations'],
                'stall_percentage': 0,  # 현재 실험에서는 stall 비율을 별도로 계산
                'write_amplification': 0,  # 현재 실험에서는 WAF를 별도로 계산
                'compression_ratio': 0  # 현재 실험에서는 압축률을 별도로 계산
            }
            print(f"2025-09-09-{workload_name} 실험 로드 완료: {basic['throughput_mb_s']:.1f} MB/s")
    
    print(f"\n총 {len(experiments)}개 실험 데이터 로드 완료")
    return experiments

def load_refined_model():
    """정교화된 모델을 로드합니다."""
    
    print("\n=== 정교화된 모델 로드 ===")
    
    model_file = Path("refined_model_results.json")
    if not model_file.exists():
        print(f"❌ 정교화된 모델 파일을 찾을 수 없습니다: {model_file}")
        return None
    
    with open(model_file, 'r') as f:
        model_data = json.load(f)
    
    # 최적 모델 정보 추출
    best_model = model_data['recommendation']['best_model']
    refined_models = model_data['refined_models']
    
    # 워크로드 유형 기반 모델 파라미터
    workload_type_model = refined_models['workload_type_based']
    
    print(f"최적 모델: {best_model['name']}")
    print(f"공식: {best_model['formula']}")
    print(f"파라미터:")
    for workload_name, efficiency in workload_type_model['parameters'].items():
        print(f"  {workload_name}: {efficiency:.4f} ({efficiency*100:.2f}%)")
    
    return {
        'model_name': best_model['name'],
        'formula': best_model['formula'],
        'theoretical_max': 1484,  # MiB/s
        'workload_efficiencies': workload_type_model['parameters']
    }

def predict_with_refined_model(experiments, model):
    """정교화된 모델로 이전 실험들을 예측합니다."""
    
    print("\n=== 정교화된 모델로 이전 실험 예측 ===")
    
    predictions = {}
    
    for exp_name, exp_data in experiments.items():
        workload = exp_data['workload']
        actual_throughput = exp_data['throughput_mb_s']
        
        # 워크로드 유형에 따른 효율성 결정
        if 'fillrandom' in workload:
            efficiency = model['workload_efficiencies'].get('fillrandom', 0.0200)
        elif 'overwrite' in workload:
            efficiency = model['workload_efficiencies'].get('overwrite', 0.0500)
        else:
            # 알 수 없는 워크로드의 경우 기본값 사용
            efficiency = 0.0300  # 중간값
        
        # 예측 계산
        predicted_throughput = model['theoretical_max'] * efficiency
        
        # 오류 계산
        error = abs(predicted_throughput - actual_throughput)
        error_rate = error / actual_throughput if actual_throughput > 0 else 0
        
        predictions[exp_name] = {
            'workload': workload,
            'actual': actual_throughput,
            'predicted': predicted_throughput,
            'efficiency_used': efficiency,
            'error': error,
            'error_rate': error_rate,
            'experiment_data': exp_data
        }
        
        print(f"\n{exp_name.upper()}:")
        print(f"  워크로드: {workload}")
        print(f"  실제 처리량: {actual_throughput:.1f} MB/s")
        print(f"  예측 처리량: {predicted_throughput:.1f} MB/s")
        print(f"  사용된 효율성: {efficiency:.4f} ({efficiency*100:.2f}%)")
        print(f"  절대 오류: {error:.1f} MB/s")
        print(f"  상대 오류: {error_rate:.3f} ({error_rate*100:.1f}%)")
    
    return predictions

def analyze_prediction_accuracy(predictions):
    """예측 정확도를 분석합니다."""
    
    print("\n=== 예측 정확도 분석 ===")
    
    # 전체 통계
    total_experiments = len(predictions)
    error_rates = [pred['error_rate'] for pred in predictions.values()]
    
    mean_error_rate = np.mean(error_rates)
    median_error_rate = np.median(error_rates)
    std_error_rate = np.std(error_rates)
    min_error_rate = np.min(error_rates)
    max_error_rate = np.max(error_rates)
    
    print(f"전체 통계:")
    print(f"  실험 수: {total_experiments}")
    print(f"  평균 오류율: {mean_error_rate:.3f} ({mean_error_rate*100:.1f}%)")
    print(f"  중간값 오류율: {median_error_rate:.3f} ({median_error_rate*100:.1f}%)")
    print(f"  표준편차: {std_error_rate:.3f}")
    print(f"  최소 오류율: {min_error_rate:.3f} ({min_error_rate*100:.1f}%)")
    print(f"  최대 오류율: {max_error_rate:.3f} ({max_error_rate*100:.1f}%)")
    
    # 정확도 등급별 분류
    excellent_count = sum(1 for rate in error_rates if rate < 0.05)  # 5% 미만
    good_count = sum(1 for rate in error_rates if 0.05 <= rate < 0.1)  # 5-10%
    fair_count = sum(1 for rate in error_rates if 0.1 <= rate < 0.2)  # 10-20%
    poor_count = sum(1 for rate in error_rates if rate >= 0.2)  # 20% 이상
    
    print(f"\n정확도 등급별 분류:")
    print(f"  우수 (5% 미만): {excellent_count}개 ({excellent_count/total_experiments*100:.1f}%)")
    print(f"  양호 (5-10%): {good_count}개 ({good_count/total_experiments*100:.1f}%)")
    print(f"  보통 (10-20%): {fair_count}개 ({fair_count/total_experiments*100:.1f}%)")
    print(f"  부족 (20% 이상): {poor_count}개 ({poor_count/total_experiments*100:.1f}%)")
    
    # 워크로드별 분석
    print(f"\n워크로드별 분석:")
    workload_stats = {}
    for exp_name, pred in predictions.items():
        workload = pred['workload']
        if workload not in workload_stats:
            workload_stats[workload] = []
        workload_stats[workload].append(pred['error_rate'])
    
    for workload, error_rates in workload_stats.items():
        mean_rate = np.mean(error_rates)
        print(f"  {workload}: 평균 오류율 {mean_rate:.3f} ({mean_rate*100:.1f}%)")
    
    return {
        'total_experiments': total_experiments,
        'mean_error_rate': mean_error_rate,
        'median_error_rate': median_error_rate,
        'std_error_rate': std_error_rate,
        'min_error_rate': min_error_rate,
        'max_error_rate': max_error_rate,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'fair_count': fair_count,
        'poor_count': poor_count,
        'workload_stats': workload_stats
    }

def compare_with_original_model(predictions):
    """원래 모델과 비교합니다."""
    
    print("\n=== 원래 모델과 비교 ===")
    
    # 원래 모델 (v1-v4)의 오류율 (97-98%)
    original_error_rate = 0.975  # 97.5% 평균
    
    # 정교화된 모델의 평균 오류율
    refined_error_rates = [pred['error_rate'] for pred in predictions.values()]
    refined_mean_error_rate = np.mean(refined_error_rates)
    
    print(f"원래 모델 (v1-v4):")
    print(f"  평균 오류율: {original_error_rate:.3f} ({original_error_rate*100:.1f}%)")
    print(f"  문제점: 복잡한 가정, 실제 데이터와 큰 차이")
    
    print(f"\n정교화된 모델:")
    print(f"  평균 오류율: {refined_mean_error_rate:.3f} ({refined_mean_error_rate*100:.1f}%)")
    print(f"  장점: 단순한 공식, 실제 데이터 기반")
    
    improvement = (original_error_rate - refined_mean_error_rate) / original_error_rate
    print(f"\n개선 효과:")
    print(f"  오류율 감소: {improvement:.3f} ({improvement*100:.1f}%)")
    print(f"  정확도 향상: {original_error_rate/refined_mean_error_rate:.1f}배")
    
    return {
        'original_error_rate': original_error_rate,
        'refined_error_rate': refined_mean_error_rate,
        'improvement_ratio': improvement,
        'accuracy_improvement': original_error_rate/refined_mean_error_rate
    }

def generate_validation_report(experiments, predictions, accuracy_stats, comparison_stats):
    """검증 보고서를 생성합니다."""
    
    print("\n=== 검증 보고서 생성 ===")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_validation': {
            'model_name': '워크로드 유형 기반 모델',
            'formula': 'S_predicted = S_theoretical × η_workload_type',
            'theoretical_max': 1484,
            'workload_efficiencies': {
                'fillrandom': 0.0200,
                'overwrite': 0.0500
            }
        },
        'experiments_analyzed': len(experiments),
        'experiments_data': experiments,
        'predictions': predictions,
        'accuracy_statistics': accuracy_stats,
        'comparison_with_original': comparison_stats,
        'conclusions': {
            'model_effectiveness': '매우 효과적' if accuracy_stats['mean_error_rate'] < 0.1 else '효과적' if accuracy_stats['mean_error_rate'] < 0.2 else '개선 필요',
            'generalization_ability': '우수' if accuracy_stats['excellent_count'] + accuracy_stats['good_count'] > len(experiments) * 0.7 else '보통',
            'practical_usability': '실용적' if accuracy_stats['mean_error_rate'] < 0.15 else '제한적'
        }
    }
    
    # 보고서 저장
    report_file = "model_validation_with_previous_experiments.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"검증 보고서가 {report_file}에 저장되었습니다.")
    
    # 결론 출력
    print(f"\n=== 검증 결론 ===")
    print(f"모델 효과성: {report['conclusions']['model_effectiveness']}")
    print(f"일반화 능력: {report['conclusions']['generalization_ability']}")
    print(f"실용성: {report['conclusions']['practical_usability']}")
    
    if accuracy_stats['mean_error_rate'] < 0.1:
        print(f"\n✅ 정교화된 모델이 이전 실험들에도 매우 잘 적용됩니다!")
        print(f"   평균 오류율 {accuracy_stats['mean_error_rate']*100:.1f}%로 높은 정확도를 보입니다.")
    elif accuracy_stats['mean_error_rate'] < 0.2:
        print(f"\n✅ 정교화된 모델이 이전 실험들에도 잘 적용됩니다.")
        print(f"   평균 오류율 {accuracy_stats['mean_error_rate']*100:.1f}%로 실용적인 정확도를 보입니다.")
    else:
        print(f"\n⚠️ 정교화된 모델이 이전 실험들에 적용할 때 개선이 필요합니다.")
        print(f"   평균 오류율 {accuracy_stats['mean_error_rate']*100:.1f}%로 정확도가 부족합니다.")
    
    return report

def main():
    """메인 함수"""
    
    print("=== 이전 실험들로 모델 검증 ===")
    
    # 이전 실험 데이터 로드
    experiments = load_previous_experiments()
    if not experiments:
        print("❌ 이전 실험 데이터를 찾을 수 없습니다.")
        return
    
    # 정교화된 모델 로드
    model = load_refined_model()
    if not model:
        return
    
    # 정교화된 모델로 예측
    predictions = predict_with_refined_model(experiments, model)
    
    # 예측 정확도 분석
    accuracy_stats = analyze_prediction_accuracy(predictions)
    
    # 원래 모델과 비교
    comparison_stats = compare_with_original_model(predictions)
    
    # 검증 보고서 생성
    report = generate_validation_report(experiments, predictions, accuracy_stats, comparison_stats)
    
    print(f"\n=== 검증 완료 ===")
    print(f"총 {len(experiments)}개 실험에 대해 모델 검증이 완료되었습니다.")

if __name__ == "__main__":
    main()



