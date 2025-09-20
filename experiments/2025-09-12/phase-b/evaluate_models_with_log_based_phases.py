#!/usr/bin/env python3
"""
LOG 기반 구간 분할을 활용한 모델 평가
LOG 기반 구간 분할 결과를 활용한 v4.2 모델 평가
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def load_log_based_phases():
    """LOG 기반 구간 분할 결과 로드"""
    print("📊 LOG 기반 구간 분할 결과 로드 중...")
    
    try:
        with open('log_based_phases_detailed_results.json', 'r') as f:
            log_results = json.load(f)
        print("✅ LOG 기반 구간 분할 결과 로드 완료")
        return log_results
    except FileNotFoundError:
        print("❌ LOG 기반 구간 분할 결과 파일을 찾을 수 없습니다.")
        return None

def load_v4_2_model_results():
    """v4.2 모델 결과 로드"""
    print("📊 v4.2 모델 결과 로드 중...")
    
    try:
        # Phase-C에서 v4.2 모델 결과 로드
        model_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/results/v4_2_model_results.json'
        if os.path.exists(model_file):
            with open(model_file, 'r') as f:
                model_results = json.load(f)
            print("✅ v4.2 모델 결과 로드 완료")
            return model_results
        else:
            print("❌ v4.2 모델 결과 파일을 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"❌ v4.2 모델 결과 로드 실패: {e}")
        return None

def evaluate_models_with_log_phases(log_phases, model_results):
    """LOG 기반 구간을 활용한 모델 평가"""
    print("📊 LOG 기반 구간을 활용한 모델 평가 중...")
    
    if not log_phases or not model_results:
        print("❌ 필요한 데이터가 없습니다.")
        return None
    
    # LOG 기반 구간 특성 추출
    log_phase_characteristics = {}
    for phase_name, phase_data in log_phases['phase_analysis'].items():
        log_phase_characteristics[phase_name] = {
            'avg_performance': phase_data['performance_stats']['avg_write_rate'],
            'stability': phase_data['phase_characteristics']['stability'],
            'performance_level': phase_data['phase_characteristics']['performance_level'],
            'cv': phase_data['performance_stats']['cv'],
            'duration_hours': phase_data['basic_stats']['duration_hours']
        }
    
    # 모델 예측 결과 추출
    model_predictions = {}
    if 'temporal_predictions' in model_results:
        # v4.2 모델의 device_envelope_temporal에서 예측 결과 추출
        device_envelope = model_results['temporal_predictions'].get('device_envelope_temporal', {})
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            if phase_name in device_envelope:
                model_predictions[phase_name] = device_envelope[phase_name]
    
    # 모델 평가 수행
    evaluation_results = {}
    
    for log_phase, log_char in log_phase_characteristics.items():
        # LOG 기반 구간과 모델 구간 매핑
        model_phase = f"{log_phase}_phase"
        
        if model_phase in model_predictions:
            model_pred = model_predictions[model_phase]
            
            # 모델 예측 성능 추출
            predicted_s_max = model_pred.get('s_max', 0)
            predicted_write_bw = model_pred.get('adjusted_write_bw', 0)
            
            # 실제 LOG 기반 성능
            actual_performance = log_char['avg_performance']
            
            # 성능 비교 (단위 변환 필요)
            # LOG 기반: MB/s, 모델: ops/sec 또는 MB/s
            if predicted_write_bw > 0:
                # 모델 예측을 MB/s로 변환 (가정: 1KB 레코드 크기)
                predicted_mbps = predicted_write_bw
                performance_accuracy = 1 - abs(predicted_mbps - actual_performance) / actual_performance
            else:
                performance_accuracy = 0
            
            # 안정성 비교
            stability_match = evaluate_stability_match(log_char['stability'], model_pred)
            
            # 구간별 특성 평가
            phase_characteristics_evaluation = evaluate_phase_characteristics(log_char, model_pred)
            
            evaluation_results[log_phase] = {
                'log_characteristics': log_char,
                'model_predictions': model_pred,
                'performance_accuracy': performance_accuracy,
                'stability_match': stability_match,
                'phase_characteristics_evaluation': phase_characteristics_evaluation,
                'overall_score': calculate_overall_score(performance_accuracy, stability_match, phase_characteristics_evaluation)
            }
    
    return evaluation_results

def evaluate_stability_match(log_stability, model_pred):
    """안정성 매칭 평가"""
    # 모델에서 안정성 관련 정보 추출
    model_stability_indicators = []
    
    if 'stability_factor' in model_pred:
        model_stability_indicators.append(model_pred['stability_factor'])
    
    if 'io_contention' in model_pred:
        model_stability_indicators.append(1 - model_pred['io_contention'])  # 낮은 contention = 높은 안정성
    
    if model_stability_indicators:
        avg_model_stability = np.mean(model_stability_indicators)
        
        # LOG 기반 안정성을 숫자로 변환
        log_stability_score = {'high': 0.8, 'medium': 0.5, 'low': 0.2}[log_stability]
        
        # 안정성 매칭 점수 계산
        stability_match = 1 - abs(avg_model_stability - log_stability_score)
        return max(0, min(1, stability_match))
    else:
        return 0.5  # 기본값

def evaluate_phase_characteristics(log_char, model_pred):
    """구간별 특성 평가"""
    characteristics_score = 0
    total_checks = 0
    
    # 성능 수준 매칭
    if 'performance_level' in log_char:
        log_perf_level = log_char['performance_level']
        model_perf_level = 'high' if model_pred.get('s_max', 0) > 50000 else 'medium' if model_pred.get('s_max', 0) > 10000 else 'low'
        
        if log_perf_level == model_perf_level:
            characteristics_score += 1
        total_checks += 1
    
    # 변동성 매칭
    if 'cv' in log_char and 'degradation_factor' in model_pred:
        log_cv = log_char['cv']
        model_degradation = model_pred['degradation_factor']
        
        # CV와 degradation factor의 상관관계 평가
        expected_cv_from_degradation = model_degradation * 0.5  # 가정: degradation이 높으면 CV도 높음
        cv_match = 1 - abs(log_cv - expected_cv_from_degradation) / max(log_cv, expected_cv_from_degradation, 0.1)
        characteristics_score += max(0, cv_match)
        total_checks += 1
    
    return characteristics_score / total_checks if total_checks > 0 else 0

def calculate_overall_score(performance_accuracy, stability_match, characteristics_evaluation):
    """전체 점수 계산"""
    weights = {
        'performance': 0.4,
        'stability': 0.3,
        'characteristics': 0.3
    }
    
    overall_score = (
        performance_accuracy * weights['performance'] +
        stability_match * weights['stability'] +
        characteristics_evaluation * weights['characteristics']
    )
    
    return overall_score

def create_model_evaluation_visualization(evaluation_results):
    """모델 평가 시각화 생성"""
    print("📊 LOG 기반 모델 평가 시각화 생성 중...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Model Evaluation with LOG-based Phase Segmentation', fontsize=18, fontweight='bold')
    
    phase_names = list(evaluation_results.keys())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # 1. 구간별 전체 점수
    overall_scores = [evaluation_results[phase]['overall_score'] for phase in phase_names]
    performance_scores = [evaluation_results[phase]['performance_accuracy'] for phase in phase_names]
    stability_scores = [evaluation_results[phase]['stability_match'] for phase in phase_names]
    characteristics_scores = [evaluation_results[phase]['phase_characteristics_evaluation'] for phase in phase_names]
    
    x = np.arange(len(phase_names))
    width = 0.2
    
    bars1 = ax1.bar(x - 1.5*width, overall_scores, width, label='Overall Score', color='darkblue', alpha=0.8)
    bars2 = ax1.bar(x - 0.5*width, performance_scores, width, label='Performance', color='skyblue', alpha=0.8)
    bars3 = ax1.bar(x + 0.5*width, stability_scores, width, label='Stability', color='lightcoral', alpha=0.8)
    bars4 = ax1.bar(x + 1.5*width, characteristics_scores, width, label='Characteristics', color='lightgreen', alpha=0.8)
    
    ax1.set_ylabel('Score')
    ax1.set_title('Model Evaluation Scores by Phase')
    ax1.set_xticks(x)
    ax1.set_xticklabels([p.title() for p in phase_names])
    ax1.legend()
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)
    
    # 2. 성능 정확도 vs 실제 성능
    actual_performances = [evaluation_results[phase]['log_characteristics']['avg_performance'] for phase in phase_names]
    predicted_performances = [evaluation_results[phase]['model_predictions'].get('adjusted_write_bw', 0) for phase in phase_names]
    
    ax2.scatter(actual_performances, predicted_performances, c=colors, s=100, alpha=0.7)
    ax2.plot([min(actual_performances), max(actual_performances)], 
             [min(actual_performances), max(actual_performances)], 
             'r--', alpha=0.5, label='Perfect Match')
    
    ax2.set_xlabel('Actual Performance (MB/s)')
    ax2.set_ylabel('Predicted Performance (MB/s)')
    ax2.set_title('Actual vs Predicted Performance')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 안정성 매칭 분석
    log_stabilities = [evaluation_results[phase]['log_characteristics']['stability'] for phase in phase_names]
    stability_scores = [evaluation_results[phase]['stability_match'] for phase in phase_names]
    
    # 안정성을 숫자로 변환
    stability_mapping = {'high': 3, 'medium': 2, 'low': 1}
    log_stability_numeric = [stability_mapping[stability] for stability in log_stabilities]
    
    ax3.bar(phase_names, log_stability_numeric, alpha=0.5, label='LOG-based Stability', color='lightblue')
    ax3.bar(phase_names, [s * 3 for s in stability_scores], alpha=0.7, label='Model Stability Match', color='lightcoral')
    
    ax3.set_ylabel('Stability Level')
    ax3.set_title('Stability Matching Analysis')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 평가 요약
    ax4.text(0.05, 0.95, 'Model Evaluation Summary', fontsize=16, fontweight='bold', transform=ax4.transAxes)
    
    y_pos = 0.85
    for phase_name, results in evaluation_results.items():
        ax4.text(0.05, y_pos, f'{phase_name.title()} Phase:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        y_pos -= 0.05
        
        ax4.text(0.05, y_pos, f'  Overall Score: {results["overall_score"]:.3f}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Performance Accuracy: {results["performance_accuracy"]:.3f}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Stability Match: {results["stability_match"]:.3f}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Characteristics: {results["phase_characteristics_evaluation"]:.3f}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.06
    
    # 전체 평균 점수
    avg_overall = np.mean(overall_scores)
    ax4.text(0.05, y_pos, f'Average Overall Score: {avg_overall:.3f}', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('model_evaluation_with_log_phases.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ LOG 기반 모델 평가 시각화 완료")

def save_evaluation_results(evaluation_results):
    """평가 결과 저장"""
    print("💾 LOG 기반 모델 평가 결과 저장 중...")
    
    # JSON 결과 저장
    results = {
        'evaluation_results': evaluation_results,
        'analysis_time': datetime.now().isoformat(),
        'analysis_type': 'model_evaluation_with_log_phases'
    }
    
    with open('model_evaluation_with_log_phases_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Markdown 보고서 생성
    with open('model_evaluation_with_log_phases_report.md', 'w') as f:
        f.write("# Model Evaluation with LOG-based Phase Segmentation\n\n")
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n")
        f.write("This report evaluates the v4.2 model using LOG-based phase segmentation results.\n")
        f.write("The evaluation compares model predictions with actual LOG-based performance characteristics.\n\n")
        
        f.write("## Evaluation Results\n\n")
        
        for phase_name, results in evaluation_results.items():
            f.write(f"### {phase_name.title()} Phase\n\n")
            
            # LOG 기반 특성
            log_char = results['log_characteristics']
            f.write("**LOG-based Characteristics:**\n")
            f.write(f"- Average Performance: {log_char['avg_performance']:.1f} MB/s\n")
            f.write(f"- Stability: {log_char['stability']}\n")
            f.write(f"- Performance Level: {log_char['performance_level']}\n")
            f.write(f"- CV: {log_char['cv']:.3f}\n")
            f.write(f"- Duration: {log_char['duration_hours']:.1f} hours\n\n")
            
            # 모델 예측
            model_pred = results['model_predictions']
            f.write("**Model Predictions:**\n")
            f.write(f"- S_max: {model_pred.get('s_max', 0):.1f} ops/sec\n")
            f.write(f"- Adjusted Write BW: {model_pred.get('adjusted_write_bw', 0):.1f} MB/s\n")
            f.write(f"- Degradation Factor: {model_pred.get('degradation_factor', 0):.3f}\n")
            f.write(f"- Stability Factor: {model_pred.get('stability_factor', 0):.3f}\n\n")
            
            # 평가 점수
            f.write("**Evaluation Scores:**\n")
            f.write(f"- Overall Score: {results['overall_score']:.3f}\n")
            f.write(f"- Performance Accuracy: {results['performance_accuracy']:.3f}\n")
            f.write(f"- Stability Match: {results['stability_match']:.3f}\n")
            f.write(f"- Characteristics Evaluation: {results['phase_characteristics_evaluation']:.3f}\n\n")
            
            f.write("---\n\n")
        
        # 전체 평가 요약
        overall_scores = [results['overall_score'] for results in evaluation_results.values()]
        avg_overall = np.mean(overall_scores)
        
        f.write("## Overall Evaluation Summary\n\n")
        f.write(f"**Average Overall Score: {avg_overall:.3f}**\n\n")
        
        f.write("### Score Interpretation:\n")
        f.write("- **0.8-1.0**: Excellent match\n")
        f.write("- **0.6-0.8**: Good match\n")
        f.write("- **0.4-0.6**: Moderate match\n")
        f.write("- **0.0-0.4**: Poor match\n\n")
        
        f.write("### Key Findings:\n")
        for phase_name, results in evaluation_results.items():
            score = results['overall_score']
            if score >= 0.8:
                rating = "Excellent"
            elif score >= 0.6:
                rating = "Good"
            elif score >= 0.4:
                rating = "Moderate"
            else:
                rating = "Poor"
            
            f.write(f"- **{phase_name.title()} Phase**: {rating} ({score:.3f})\n")
        
        f.write(f"\n## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    print("✅ LOG 기반 모델 평가 결과 저장 완료")

def main():
    """메인 함수"""
    print("🚀 LOG 기반 구간을 활용한 모델 평가 시작...")
    
    # 데이터 로드
    log_phases = load_log_based_phases()
    model_results = load_v4_2_model_results()
    
    if not log_phases or not model_results:
        print("❌ 필요한 데이터가 없습니다.")
        return
    
    # 모델 평가 수행
    evaluation_results = evaluate_models_with_log_phases(log_phases, model_results)
    
    if not evaluation_results:
        print("❌ 모델 평가 실패")
        return
    
    # 결과 출력
    print("\n📊 LOG 기반 모델 평가 결과:")
    for phase_name, results in evaluation_results.items():
        print(f"\n  {phase_name.title()} Phase:")
        print(f"    전체 점수: {results['overall_score']:.3f}")
        print(f"    성능 정확도: {results['performance_accuracy']:.3f}")
        print(f"    안정성 매칭: {results['stability_match']:.3f}")
        print(f"    특성 평가: {results['phase_characteristics_evaluation']:.3f}")
    
    # 전체 평균 점수
    overall_scores = [results['overall_score'] for results in evaluation_results.values()]
    avg_overall = np.mean(overall_scores)
    print(f"\n📊 전체 평균 점수: {avg_overall:.3f}")
    
    # 시각화 생성
    create_model_evaluation_visualization(evaluation_results)
    
    # 결과 저장
    save_evaluation_results(evaluation_results)
    
    print("\n✅ LOG 기반 모델 평가 완료!")
    print("📊 결과 파일: model_evaluation_with_log_phases.png, model_evaluation_with_log_phases_results.json, model_evaluation_with_log_phases_report.md")

if __name__ == "__main__":
    main()
