#!/usr/bin/env python3
"""
성능 변화 기반 구간 분할을 활용한 v4.2 모델 평가
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

def load_performance_based_segmentation():
    """성능 기반 구간 분할 결과 로드"""
    print("📊 성능 기반 구간 분할 결과 로드 중...")
    
    try:
        with open('performance_based_segmentation_results.json', 'r') as f:
            segmentation_results = json.load(f)
        print("✅ 성능 기반 구간 분할 결과 로드 완료")
        return segmentation_results
    except FileNotFoundError:
        print("❌ 성능 기반 구간 분할 결과 파일을 찾을 수 없습니다.")
        return None

def load_v4_2_model_results():
    """v4.2 모델 결과 로드"""
    print("📊 v4.2 모델 결과 로드 중...")
    
    try:
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

def evaluate_v4_2_with_performance_phases(segmentation_results, model_results):
    """성능 기반 구간을 활용한 v4.2 모델 평가"""
    print("📊 성능 기반 구간을 활용한 v4.2 모델 평가 중...")
    
    if not segmentation_results or not model_results:
        print("❌ 필요한 데이터가 없습니다.")
        return None
    
    # 성능 기반 구간 특성 추출
    performance_phase_characteristics = {}
    for phase_name, phase_data in segmentation_results['segment_analysis'].items():
        performance_phase_characteristics[phase_name] = {
            'avg_performance': phase_data['performance_stats']['avg_write_rate'],
            'stability': phase_data['characteristics']['stability'],
            'performance_level': phase_data['characteristics']['performance_level'],
            'cv': phase_data['performance_stats']['cv'],
            'duration_hours': phase_data['basic_stats']['duration_hours'],
            'trend': phase_data['characteristics']['trend'],
            'change_intensity': phase_data['characteristics']['change_intensity']
        }
    
    # v4.2 모델 예측 결과 추출
    model_predictions = {}
    if 'temporal_predictions' in model_results:
        device_envelope = model_results['temporal_predictions'].get('device_envelope_temporal', {})
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            if phase_name in device_envelope:
                model_predictions[phase_name] = device_envelope[phase_name]
    
    # 모델 평가 수행
    evaluation_results = {}
    
    # 구간 매핑 (성능 기반 구간 → 모델 구간)
    phase_mapping = {
        'initial': 'initial_phase',
        'middle': 'middle_phase', 
        'final': 'final_phase'
    }
    
    for perf_phase, perf_char in performance_phase_characteristics.items():
        model_phase = phase_mapping.get(perf_phase)
        
        if model_phase and model_phase in model_predictions:
            model_pred = model_predictions[model_phase]
            
            # 성능 정확도 평가
            performance_accuracy = evaluate_performance_accuracy(perf_char, model_pred)
            
            # 안정성 매칭 평가
            stability_match = evaluate_stability_match_enhanced(perf_char, model_pred)
            
            # 구간 특성 평가
            phase_characteristics_evaluation = evaluate_phase_characteristics_enhanced(perf_char, model_pred)
            
            # 트렌드 매칭 평가
            trend_match = evaluate_trend_match(perf_char, model_pred)
            
            # 전체 점수 계산
            overall_score = calculate_enhanced_overall_score(
                performance_accuracy, stability_match, 
                phase_characteristics_evaluation, trend_match
            )
            
            evaluation_results[perf_phase] = {
                'performance_characteristics': perf_char,
                'model_predictions': model_pred,
                'performance_accuracy': performance_accuracy,
                'stability_match': stability_match,
                'phase_characteristics_evaluation': phase_characteristics_evaluation,
                'trend_match': trend_match,
                'overall_score': overall_score
            }
    
    return evaluation_results

def evaluate_performance_accuracy(perf_char, model_pred):
    """성능 정확도 평가 (개선된 버전)"""
    actual_performance = perf_char['avg_performance']  # MB/s
    predicted_write_bw = model_pred.get('adjusted_write_bw', 0)  # MB/s
    
    if predicted_write_bw > 0 and actual_performance > 0:
        # 직접 MB/s 단위로 비교
        error_ratio = abs(predicted_write_bw - actual_performance) / actual_performance
        accuracy = max(0, 1 - error_ratio)  # 0~1 사이 값
        return accuracy
    else:
        return 0.0

def evaluate_stability_match_enhanced(perf_char, model_pred):
    """안정성 매칭 평가 (개선된 버전)"""
    # 성능 기반 구간의 실제 안정성
    actual_stability = perf_char['stability']  # 'high', 'medium', 'low'
    actual_cv = perf_char['cv']
    
    # 모델 예측의 안정성 지표들
    model_stability_indicators = []
    
    if 'stability_factor' in model_pred:
        model_stability_indicators.append(model_pred['stability_factor'])
    
    if 'io_contention' in model_pred:
        model_stability_indicators.append(1 - model_pred['io_contention'])
    
    if 'device_degradation' in model_pred:
        # 낮은 degradation = 높은 안정성
        model_stability_indicators.append(1 - model_pred['device_degradation'])
    
    if model_stability_indicators:
        avg_model_stability = np.mean(model_stability_indicators)
        
        # 실제 CV를 기반으로 한 안정성 점수
        if actual_cv < 0.1:
            actual_stability_score = 0.9
        elif actual_cv < 0.3:
            actual_stability_score = 0.6
        else:
            actual_stability_score = 0.3
        
        # 안정성 매칭 점수 계산
        stability_match = 1 - abs(avg_model_stability - actual_stability_score)
        return max(0, min(1, stability_match))
    else:
        return 0.5

def evaluate_phase_characteristics_enhanced(perf_char, model_pred):
    """구간별 특성 평가 (개선된 버전)"""
    characteristics_score = 0
    total_checks = 0
    
    # 성능 수준 매칭
    actual_perf_level = perf_char['performance_level']
    predicted_s_max = model_pred.get('s_max', 0)
    
    # S_max를 MB/s로 변환 (가정: 1KB 레코드)
    predicted_mbps = (predicted_s_max * 1024) / (1024 * 1024)  # ops/sec to MB/s (1KB 레코드)
    
    if predicted_mbps > 50:
        model_perf_level = 'high'
    elif predicted_mbps > 15:
        model_perf_level = 'medium'
    else:
        model_perf_level = 'low'
    
    if actual_perf_level == model_perf_level:
        characteristics_score += 1
    total_checks += 1
    
    # 변동성 매칭
    actual_cv = perf_char['cv']
    model_degradation = model_pred.get('device_degradation', 0)
    
    # degradation이 높을수록 변동성도 높을 것으로 예상
    expected_cv_from_degradation = model_degradation * 0.8
    cv_match = 1 - abs(actual_cv - expected_cv_from_degradation) / max(actual_cv, expected_cv_from_degradation, 0.1)
    characteristics_score += max(0, cv_match)
    total_checks += 1
    
    # 변화 강도 매칭
    actual_change_intensity = perf_char['change_intensity']
    model_workload_impact = model_pred.get('workload_impact', 0)
    
    # workload_impact가 높을수록 변화 강도도 높을 것으로 예상
    if model_workload_impact > 0.6:
        expected_change_intensity = 'high'
    elif model_workload_impact > 0.4:
        expected_change_intensity = 'medium'
    else:
        expected_change_intensity = 'low'
    
    if actual_change_intensity == expected_change_intensity:
        characteristics_score += 1
    total_checks += 1
    
    return characteristics_score / total_checks if total_checks > 0 else 0

def evaluate_trend_match(perf_char, model_pred):
    """트렌드 매칭 평가"""
    actual_trend = perf_char['trend']  # 'increasing', 'stable', 'decreasing'
    
    # 모델에서 트렌드 예측 (degradation 기반)
    device_degradation = model_pred.get('device_degradation', 0)
    
    if device_degradation > 0.5:
        expected_trend = 'decreasing'
    elif device_degradation > 0.1:
        expected_trend = 'stable'
    else:
        expected_trend = 'stable'  # 초기에는 안정적
    
    # 트렌드 매칭 점수
    if actual_trend == expected_trend:
        return 1.0
    elif (actual_trend == 'stable' and expected_trend in ['increasing', 'decreasing']) or \
         (expected_trend == 'stable' and actual_trend in ['increasing', 'decreasing']):
        return 0.5  # 부분 매칭
    else:
        return 0.0

def calculate_enhanced_overall_score(performance_accuracy, stability_match, characteristics_evaluation, trend_match):
    """전체 점수 계산 (개선된 버전)"""
    weights = {
        'performance': 0.4,
        'stability': 0.25,
        'characteristics': 0.25,
        'trend': 0.1
    }
    
    overall_score = (
        performance_accuracy * weights['performance'] +
        stability_match * weights['stability'] +
        characteristics_evaluation * weights['characteristics'] +
        trend_match * weights['trend']
    )
    
    return overall_score

def create_enhanced_evaluation_visualization(evaluation_results):
    """개선된 모델 평가 시각화"""
    print("📊 성능 기반 구간을 활용한 모델 평가 시각화 생성 중...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('V4.2 Model Evaluation with Performance-based Phase Segmentation', fontsize=18, fontweight='bold')
    
    phase_names = list(evaluation_results.keys())
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # 1. 구간별 종합 평가 점수
    overall_scores = [evaluation_results[phase]['overall_score'] for phase in phase_names]
    performance_scores = [evaluation_results[phase]['performance_accuracy'] for phase in phase_names]
    stability_scores = [evaluation_results[phase]['stability_match'] for phase in phase_names]
    characteristics_scores = [evaluation_results[phase]['phase_characteristics_evaluation'] for phase in phase_names]
    trend_scores = [evaluation_results[phase]['trend_match'] for phase in phase_names]
    
    x = np.arange(len(phase_names))
    width = 0.15
    
    bars1 = ax1.bar(x - 2*width, overall_scores, width, label='Overall Score', color='darkblue', alpha=0.8)
    bars2 = ax1.bar(x - width, performance_scores, width, label='Performance', color='skyblue', alpha=0.8)
    bars3 = ax1.bar(x, stability_scores, width, label='Stability', color='lightcoral', alpha=0.8)
    bars4 = ax1.bar(x + width, characteristics_scores, width, label='Characteristics', color='lightgreen', alpha=0.8)
    bars5 = ax1.bar(x + 2*width, trend_scores, width, label='Trend', color='orange', alpha=0.8)
    
    ax1.set_ylabel('Score')
    ax1.set_title('Enhanced Model Evaluation Scores by Phase')
    ax1.set_xticks(x)
    ax1.set_xticklabels([p.title() for p in phase_names])
    ax1.legend()
    ax1.set_ylim(0, 1.2)
    ax1.grid(True, alpha=0.3)
    
    # 2. 실제 vs 예측 성능 비교
    actual_performances = [evaluation_results[phase]['performance_characteristics']['avg_performance'] for phase in phase_names]
    predicted_performances = [evaluation_results[phase]['model_predictions'].get('adjusted_write_bw', 0) for phase in phase_names]
    
    ax2.scatter(actual_performances, predicted_performances, c=colors, s=150, alpha=0.7, edgecolors='black')
    
    # 완벽한 예측선
    min_perf = min(min(actual_performances), min(predicted_performances))
    max_perf = max(max(actual_performances), max(predicted_performances))
    ax2.plot([min_perf, max_perf], [min_perf, max_perf], 'r--', alpha=0.5, label='Perfect Prediction')
    
    # 각 점에 라벨 추가
    for i, phase in enumerate(phase_names):
        ax2.annotate(phase.title(), (actual_performances[i], predicted_performances[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    ax2.set_xlabel('Actual Performance (MB/s)')
    ax2.set_ylabel('Predicted Performance (MB/s)')
    ax2.set_title('Actual vs Predicted Performance (Performance-based Phases)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 구간별 특성 비교 (레이더 차트 스타일)
    metrics = ['Performance', 'Stability', 'Characteristics', 'Trend']
    
    for i, phase in enumerate(phase_names):
        scores = [
            evaluation_results[phase]['performance_accuracy'],
            evaluation_results[phase]['stability_match'],
            evaluation_results[phase]['phase_characteristics_evaluation'],
            evaluation_results[phase]['trend_match']
        ]
        ax3.plot(metrics, scores, 'o-', label=f'{phase.title()} Phase', 
                color=colors[i], linewidth=2, markersize=8)
    
    ax3.set_ylim(0, 1)
    ax3.set_title('Phase-wise Evaluation Metrics')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylabel('Score')
    
    # 4. 평가 요약 및 개선사항
    ax4.text(0.05, 0.95, 'Performance-based Evaluation Summary', fontsize=16, fontweight='bold', transform=ax4.transAxes)
    
    y_pos = 0.85
    avg_overall = np.mean(overall_scores)
    ax4.text(0.05, y_pos, f'Average Overall Score: {avg_overall:.3f}', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.08
    
    for phase_name, results in evaluation_results.items():
        perf_char = results['performance_characteristics']
        
        ax4.text(0.05, y_pos, f'{phase_name.title()} Phase:', fontsize=13, fontweight='bold', transform=ax4.transAxes)
        y_pos -= 0.05
        
        ax4.text(0.05, y_pos, f'  Overall Score: {results["overall_score"]:.3f}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Duration: {perf_char["duration_hours"]:.1f}h, Avg Perf: {perf_char["avg_performance"]:.1f} MB/s', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Stability: {perf_char["stability"]}, Trend: {perf_char["trend"]}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.06
    
    # 개선사항
    y_pos -= 0.02
    ax4.text(0.05, y_pos, 'Key Improvements:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.05
    ax4.text(0.05, y_pos, '• Performance-based segmentation reflects actual behavior', fontsize=10, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '• Variable phase durations based on performance changes', fontsize=10, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '• Enhanced evaluation metrics include trend matching', fontsize=10, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '• Direct MB/s comparison without unit conversion issues', fontsize=10, transform=ax4.transAxes)
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('v4_2_evaluation_with_performance_based_phases.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 성능 기반 구간을 활용한 모델 평가 시각화 완료")

def save_enhanced_evaluation_results(evaluation_results):
    """개선된 평가 결과 저장"""
    print("💾 성능 기반 구간을 활용한 모델 평가 결과 저장 중...")
    
    # JSON 결과 저장
    results = {
        'evaluation_method': 'performance_based_segmentation',
        'model_version': 'v4.2',
        'evaluation_results': evaluation_results,
        'analysis_time': datetime.now().isoformat()
    }
    
    with open('v4_2_evaluation_with_performance_based_phases_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Markdown 보고서 생성
    with open('v4_2_evaluation_with_performance_based_phases_report.md', 'w') as f:
        f.write("# V4.2 Model Evaluation with Performance-based Phase Segmentation\n\n")
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n")
        f.write("This report evaluates the v4.2 model using performance-based phase segmentation.\n")
        f.write("Unlike time-based segmentation, this approach uses actual performance change patterns to define phases.\n\n")
        
        f.write("## Evaluation Method\n")
        f.write("### Performance-based Segmentation Features:\n")
        f.write("1. **Variable Phase Durations**: Based on actual performance transitions\n")
        f.write("2. **Enhanced Metrics**: Performance, stability, characteristics, and trend matching\n")
        f.write("3. **Direct Comparison**: MB/s to MB/s comparison without unit conversion\n")
        f.write("4. **Trend Analysis**: Includes performance trend matching evaluation\n\n")
        
        f.write("## Evaluation Results\n\n")
        
        overall_scores = [results['overall_score'] for results in evaluation_results.values()]
        avg_overall = np.mean(overall_scores)
        f.write(f"**Average Overall Score: {avg_overall:.3f}**\n\n")
        
        for phase_name, results in evaluation_results.items():
            f.write(f"### {phase_name.title()} Phase\n\n")
            
            # 성능 기반 구간 특성
            perf_char = results['performance_characteristics']
            f.write("**Performance-based Phase Characteristics:**\n")
            f.write(f"- Duration: {perf_char['duration_hours']:.1f} hours\n")
            f.write(f"- Average Performance: {perf_char['avg_performance']:.1f} MB/s\n")
            f.write(f"- Stability: {perf_char['stability']} (CV: {perf_char['cv']:.3f})\n")
            f.write(f"- Performance Level: {perf_char['performance_level']}\n")
            f.write(f"- Trend: {perf_char['trend']}\n")
            f.write(f"- Change Intensity: {perf_char['change_intensity']}\n\n")
            
            # 모델 예측
            model_pred = results['model_predictions']
            f.write("**V4.2 Model Predictions:**\n")
            f.write(f"- S_max: {model_pred.get('s_max', 0):.1f} ops/sec\n")
            f.write(f"- Adjusted Write BW: {model_pred.get('adjusted_write_bw', 0):.1f} MB/s\n")
            f.write(f"- Device Degradation: {model_pred.get('device_degradation', 0):.3f}\n")
            f.write(f"- Workload Impact: {model_pred.get('workload_impact', 0):.3f}\n")
            f.write(f"- Stability Factor: {model_pred.get('stability_factor', 0):.3f}\n\n")
            
            # 평가 점수
            f.write("**Evaluation Scores:**\n")
            f.write(f"- Overall Score: {results['overall_score']:.3f}\n")
            f.write(f"- Performance Accuracy: {results['performance_accuracy']:.3f}\n")
            f.write(f"- Stability Match: {results['stability_match']:.3f}\n")
            f.write(f"- Characteristics Evaluation: {results['phase_characteristics_evaluation']:.3f}\n")
            f.write(f"- Trend Match: {results['trend_match']:.3f}\n\n")
            
            f.write("---\n\n")
        
        f.write("## Key Improvements over Time-based Segmentation\n\n")
        f.write("### 1. Meaningful Phase Boundaries\n")
        f.write("- **Initial Phase**: Very short (0.1h) but captures actual rapid change period\n")
        f.write("- **Middle Phase**: Medium duration (31.8h) reflecting stabilization process\n")
        f.write("- **Final Phase**: Long duration (64.7h) representing stable operation\n\n")
        
        f.write("### 2. Enhanced Evaluation Metrics\n")
        f.write("- **Direct Performance Comparison**: MB/s to MB/s without unit conversion issues\n")
        f.write("- **Trend Matching**: Evaluates whether model predictions match actual trends\n")
        f.write("- **Stability Assessment**: Uses actual CV values for precise stability evaluation\n")
        f.write("- **Change Intensity**: Considers the rate and magnitude of performance changes\n\n")
        
        f.write("### 3. Model Insights\n")
        for phase_name, results in evaluation_results.items():
            score = results['overall_score']
            if score >= 0.7:
                rating = "Good"
            elif score >= 0.5:
                rating = "Moderate"
            else:
                rating = "Poor"
            f.write(f"- **{phase_name.title()} Phase**: {rating} match ({score:.3f})\n")
        
        f.write(f"\n## Conclusion\n")
        f.write("Performance-based segmentation provides more meaningful evaluation by:\n")
        f.write("- Reflecting actual system behavior patterns\n")
        f.write("- Using variable phase durations based on performance changes\n")
        f.write("- Enabling direct performance comparisons\n")
        f.write("- Providing comprehensive evaluation metrics\n\n")
        
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    print("✅ 성능 기반 구간을 활용한 모델 평가 결과 저장 완료")

def main():
    """메인 함수"""
    print("🚀 성능 변화 기반 구간을 활용한 v4.2 모델 평가 시작...")
    
    # 데이터 로드
    segmentation_results = load_performance_based_segmentation()
    model_results = load_v4_2_model_results()
    
    if not segmentation_results or not model_results:
        print("❌ 필요한 데이터가 없습니다.")
        return
    
    # 모델 평가 수행
    evaluation_results = evaluate_v4_2_with_performance_phases(segmentation_results, model_results)
    
    if not evaluation_results:
        print("❌ 모델 평가 실패")
        return
    
    # 결과 출력
    print("\n📊 성능 기반 구간을 활용한 v4.2 모델 평가 결과:")
    for phase_name, results in evaluation_results.items():
        perf_char = results['performance_characteristics']
        print(f"\n  {phase_name.title()} Phase:")
        print(f"    지속시간: {perf_char['duration_hours']:.1f} 시간")
        print(f"    실제 성능: {perf_char['avg_performance']:.1f} MB/s")
        print(f"    안정성: {perf_char['stability']} (CV: {perf_char['cv']:.3f})")
        print(f"    트렌드: {perf_char['trend']}")
        print(f"    전체 점수: {results['overall_score']:.3f}")
        print(f"    성능 정확도: {results['performance_accuracy']:.3f}")
        print(f"    안정성 매칭: {results['stability_match']:.3f}")
        print(f"    특성 평가: {results['phase_characteristics_evaluation']:.3f}")
        print(f"    트렌드 매칭: {results['trend_match']:.3f}")
    
    # 전체 평균 점수
    overall_scores = [results['overall_score'] for results in evaluation_results.values()]
    avg_overall = np.mean(overall_scores)
    print(f"\n📊 전체 평균 점수: {avg_overall:.3f}")
    
    # 시각화 생성
    create_enhanced_evaluation_visualization(evaluation_results)
    
    # 결과 저장
    save_enhanced_evaluation_results(evaluation_results)
    
    print("\n✅ 성능 기반 구간을 활용한 v4.2 모델 평가 완료!")
    print("📊 결과 파일: v4_2_evaluation_with_performance_based_phases.png, v4_2_evaluation_with_performance_based_phases_results.json, v4_2_evaluation_with_performance_based_phases_report.md")

if __name__ == "__main__":
    main()







