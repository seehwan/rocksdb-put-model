#!/usr/bin/env python3
"""
Phase-B 실험 결과를 이용한 v4.2 모델 평가
실제 측정 데이터와 모델 예측값의 객관적 비교 분석
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class V4_2PhaseBEvaluator:
    """Phase-B 실험 결과 기반 v4.2 모델 평가기"""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Phase-B 실제 측정 데이터
        self.phase_b_actual_data = self._load_phase_b_actual_data()
        
        # v4.2 모델 예측 데이터
        self.v4_2_predictions = self._load_v4_2_predictions()
        
    def _load_phase_b_actual_data(self):
        """Phase-B 실제 측정 데이터 로드"""
        print("📊 Phase-B 실제 측정 데이터 로드 중...")
        
        # 실제 Phase-B 성능 데이터 (성능 기반 구간 분할 결과)
        phase_b_data = {
            'initial_phase': {
                'duration_hours': 0.14,
                'sample_count': 52,
                'avg_qps': 138769,  # 실제 측정된 평균 QPS
                'performance_stats': {
                    'avg_write_rate': 65.97,  # MB/s
                    'max_write_rate': 280.18,
                    'min_write_rate': 46.74,
                    'std_write_rate': 35.49,
                    'cv': 0.538  # 변동계수
                },
                'characteristics': {
                    'stability': 'low',
                    'trend': 'decreasing',
                    'performance_level': 'high',
                    'change_intensity': 'low'
                }
            },
            'middle_phase': {
                'duration_hours': 31.79,
                'sample_count': 11443,
                'avg_qps': 114472,  # 실제 측정된 평균 QPS
                'performance_stats': {
                    'avg_write_rate': 16.95,  # MB/s
                    'max_write_rate': 47.05,
                    'min_write_rate': 13.84,
                    'std_write_rate': 4.61,
                    'cv': 0.272  # 변동계수
                },
                'characteristics': {
                    'stability': 'medium',
                    'trend': 'stable',
                    'performance_level': 'medium',
                    'change_intensity': 'low'
                }
            },
            'final_phase': {
                'duration_hours': 64.68,
                'sample_count': 23280,
                'avg_qps': 109678,  # 실제 측정된 평균 QPS
                'performance_stats': {
                    'avg_write_rate': 12.76,  # MB/s
                    'max_write_rate': 13.84,
                    'min_write_rate': 12.76,
                    'std_write_rate': 0.0,
                    'cv': 0.0  # 변동계수 (안정화)
                },
                'characteristics': {
                    'stability': 'high',
                    'trend': 'stable',
                    'performance_level': 'low',
                    'change_intensity': 'none'
                }
            }
        }
        
        print("✅ Phase-B 실제 측정 데이터 로드 완료")
        return phase_b_data
    
    def _load_v4_2_predictions(self):
        """v4.2 모델 예측 데이터 로드"""
        print("📊 v4.2 모델 예측 데이터 로드 중...")
        
        # v4.2 Enhanced 모델 예측값
        v4_2_predictions = {
            'initial_phase': {
                'predicted_s_max': 33132,  # ops/sec
                'level_wise_analysis': {
                    'L0': {'wa': 1.0, 'ra': 0.0, 'io_impact': 0.10},
                    'L1': {'wa': 1.1, 'ra': 0.1, 'io_impact': 0.20},
                    'L2': {'wa': 1.3, 'ra': 0.2, 'io_impact': 0.30},
                    'L3': {'wa': 1.5, 'ra': 0.3, 'io_impact': 0.20},
                    'L4': {'wa': 2.0, 'ra': 0.5, 'io_impact': 0.10},
                    'L5': {'wa': 2.5, 'ra': 0.8, 'io_impact': 0.05},
                    'L6': {'wa': 3.0, 'ra': 1.0, 'io_impact': 0.05}
                },
                'performance_factors': {
                    'performance_factor': 0.3,
                    'stability_factor': 0.2,
                    'io_contention': 0.6,
                    'avg_wa': 1.3,
                    'avg_ra': 0.2
                }
            },
            'middle_phase': {
                'predicted_s_max': 119002,  # ops/sec
                'level_wise_analysis': {
                    'L0': {'wa': 1.0, 'ra': 0.0, 'io_impact': 0.10},
                    'L1': {'wa': 1.2, 'ra': 0.2, 'io_impact': 0.20},
                    'L2': {'wa': 2.5, 'ra': 0.8, 'io_impact': 0.40},
                    'L3': {'wa': 3.5, 'ra': 1.2, 'io_impact': 0.20},
                    'L4': {'wa': 4.0, 'ra': 1.5, 'io_impact': 0.10},
                    'L5': {'wa': 4.5, 'ra': 1.8, 'io_impact': 0.05},
                    'L6': {'wa': 5.0, 'ra': 2.0, 'io_impact': 0.05}
                },
                'performance_factors': {
                    'performance_factor': 0.6,
                    'stability_factor': 0.5,
                    'io_contention': 0.8,
                    'avg_wa': 2.4,
                    'avg_ra': 0.8
                }
            },
            'final_phase': {
                'predicted_s_max': 250598,  # ops/sec
                'level_wise_analysis': {
                    'L0': {'wa': 1.0, 'ra': 0.0, 'io_impact': 0.10},
                    'L1': {'wa': 1.3, 'ra': 0.3, 'io_impact': 0.20},
                    'L2': {'wa': 3.0, 'ra': 1.0, 'io_impact': 0.40},
                    'L3': {'wa': 4.0, 'ra': 1.5, 'io_impact': 0.20},
                    'L4': {'wa': 5.0, 'ra': 2.0, 'io_impact': 0.10},
                    'L5': {'wa': 5.5, 'ra': 2.2, 'io_impact': 0.05},
                    'L6': {'wa': 6.0, 'ra': 2.5, 'io_impact': 0.05}
                },
                'performance_factors': {
                    'performance_factor': 0.9,
                    'stability_factor': 0.8,
                    'io_contention': 0.9,
                    'avg_wa': 3.2,
                    'avg_ra': 1.1
                }
            }
        }
        
        print("✅ v4.2 모델 예측 데이터 로드 완료")
        return v4_2_predictions
    
    def evaluate_model_accuracy(self):
        """모델 정확도 평가"""
        print("📊 v4.2 모델 정확도 평가 중...")
        
        evaluation_results = {}
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            actual_data = self.phase_b_actual_data[phase_name]
            predicted_data = self.v4_2_predictions[phase_name]
            
            actual_qps = actual_data['avg_qps']
            predicted_s_max = predicted_data['predicted_s_max']
            
            # 정확도 계산
            accuracy = (1 - abs(predicted_s_max - actual_qps) / actual_qps) * 100
            
            # 오차율 계산
            error_rate = abs(predicted_s_max - actual_qps) / actual_qps * 100
            
            # 방향성 분석 (과대/과소 예측)
            if predicted_s_max > actual_qps:
                prediction_direction = "over_prediction"
                direction_percent = ((predicted_s_max - actual_qps) / actual_qps) * 100
            else:
                prediction_direction = "under_prediction"
                direction_percent = ((actual_qps - predicted_s_max) / actual_qps) * 100
            
            evaluation_results[phase_name] = {
                'actual_qps': actual_qps,
                'predicted_s_max': predicted_s_max,
                'accuracy_percent': accuracy,
                'error_rate_percent': error_rate,
                'prediction_direction': prediction_direction,
                'direction_percent': direction_percent,
                'performance_factors': predicted_data['performance_factors']
            }
        
        return evaluation_results
    
    def analyze_prediction_patterns(self, evaluation_results):
        """예측 패턴 분석"""
        print("📊 예측 패턴 분석 중...")
        
        pattern_analysis = {}
        
        # 시기별 정확도 트렌드
        accuracies = [evaluation_results[phase]['accuracy_percent'] for phase in evaluation_results.keys()]
        phases = list(evaluation_results.keys())
        
        # 정확도 변화 패턴
        accuracy_trend = 'increasing' if accuracies[1] > accuracies[0] and accuracies[2] > accuracies[1] else 'variable'
        
        # 예측 방향성 분석
        over_predictions = sum(1 for result in evaluation_results.values() if result['prediction_direction'] == 'over_prediction')
        under_predictions = sum(1 for result in evaluation_results.values() if result['prediction_direction'] == 'under_prediction')
        
        # 평균 정확도
        avg_accuracy = np.mean(accuracies)
        
        # 표준 편차
        accuracy_std = np.std(accuracies)
        
        pattern_analysis = {
            'accuracy_trend': accuracy_trend,
            'over_predictions': over_predictions,
            'under_predictions': under_predictions,
            'average_accuracy': avg_accuracy,
            'accuracy_std': accuracy_std,
            'accuracy_consistency': 'high' if accuracy_std < 20 else 'medium' if accuracy_std < 50 else 'low',
            'prediction_bias': 'over_prediction' if over_predictions > under_predictions else 'under_prediction' if under_predictions > over_predictions else 'balanced'
        }
        
        return pattern_analysis
    
    def evaluate_model_strengths_weaknesses(self, evaluation_results):
        """모델 강점과 약점 평가"""
        print("📊 모델 강점과 약점 평가 중...")
        
        strengths = []
        weaknesses = []
        
        # 정확도 기반 평가
        accuracies = [result['accuracy_percent'] for result in evaluation_results.values()]
        
        if any(acc > 90 for acc in accuracies):
            strengths.append("일부 시기에서 높은 정확도 달성 (90% 이상)")
        
        if any(acc < 50 for acc in accuracies):
            weaknesses.append("일부 시기에서 낮은 정확도 (50% 미만)")
        
        # 예측 방향성 분석
        over_predictions = sum(1 for result in evaluation_results.values() if result['prediction_direction'] == 'over_prediction')
        under_predictions = sum(1 for result in evaluation_results.values() if result['prediction_direction'] == 'under_prediction')
        
        if over_predictions > under_predictions:
            weaknesses.append("과대 예측 경향 (실제보다 높게 예측)")
        elif under_predictions > over_predictions:
            weaknesses.append("과소 예측 경향 (실제보다 낮게 예측)")
        else:
            strengths.append("균형잡힌 예측 방향성")
        
        # 시기별 성능 분석
        phase_performances = [(phase, result['accuracy_percent']) for phase, result in evaluation_results.items()]
        best_phase = max(phase_performances, key=lambda x: x[1])
        worst_phase = min(phase_performances, key=lambda x: x[1])
        
        strengths.append(f"{best_phase[0]}에서 최고 성능 ({best_phase[1]:.1f}% 정확도)")
        weaknesses.append(f"{worst_phase[0]}에서 개선 필요 ({worst_phase[1]:.1f}% 정확도)")
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def generate_evaluation_report(self, evaluation_results, pattern_analysis, strengths_weaknesses):
        """평가 리포트 생성"""
        print("📊 평가 리포트 생성 중...")
        
        report = {
            'evaluation_metadata': {
                'evaluation_date': datetime.now().isoformat(),
                'evaluator': 'Phase-B Experimental Results',
                'model_version': 'v4.2_enhanced_level_wise_temporal',
                'evaluation_scope': 'Phase-B experimental data comparison'
            },
            'phase_by_phase_evaluation': evaluation_results,
            'pattern_analysis': pattern_analysis,
            'strengths_weaknesses': strengths_weaknesses,
            'overall_assessment': self._generate_overall_assessment(evaluation_results, pattern_analysis)
        }
        
        return report
    
    def _generate_overall_assessment(self, evaluation_results, pattern_analysis):
        """전체 평가 생성"""
        avg_accuracy = pattern_analysis['average_accuracy']
        
        if avg_accuracy > 80:
            assessment_level = "Excellent"
            assessment_description = "모델이 매우 높은 정확도를 보이며 실용적으로 활용 가능"
        elif avg_accuracy > 60:
            assessment_level = "Good"
            assessment_description = "모델이 양호한 정확도를 보이며 일부 개선 후 활용 가능"
        elif avg_accuracy > 40:
            assessment_level = "Fair"
            assessment_description = "모델이 보통 수준의 정확도를 보이며 상당한 개선 필요"
        else:
            assessment_level = "Poor"
            assessment_description = "모델의 정확도가 낮으며 대폭적인 개선 필요"
        
        return {
            'assessment_level': assessment_level,
            'assessment_description': assessment_description,
            'average_accuracy': avg_accuracy,
            'recommendation': self._generate_recommendation(avg_accuracy, pattern_analysis)
        }
    
    def _generate_recommendation(self, avg_accuracy, pattern_analysis):
        """개선 권장사항 생성"""
        recommendations = []
        
        if avg_accuracy < 70:
            recommendations.append("모델 파라미터 재조정 필요")
        
        if pattern_analysis['prediction_bias'] == 'over_prediction':
            recommendations.append("과대 예측 경향 보정 필요")
        elif pattern_analysis['prediction_bias'] == 'under_prediction':
            recommendations.append("과소 예측 경향 보정 필요")
        
        if pattern_analysis['accuracy_consistency'] == 'low':
            recommendations.append("시기별 정확도 일관성 개선 필요")
        
        if not recommendations:
            recommendations.append("모델이 양호한 성능을 보이며 현재 상태 유지 권장")
        
        return recommendations
    
    def create_visualization(self, evaluation_results, output_dir):
        """시각화 생성"""
        print("📊 평가 결과 시각화 생성 중...")
        
        # Liberation Serif 폰트 설정
        plt.rcParams['font.family'] = 'Liberation Serif'
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('V4.2 Model Evaluation with Phase-B Results', fontsize=16, fontweight='bold')
        
        # 1. 실제 vs 예측값 비교
        ax1 = axes[0, 0]
        phases = list(evaluation_results.keys())
        actual_values = [evaluation_results[phase]['actual_qps'] for phase in phases]
        predicted_values = [evaluation_results[phase]['predicted_s_max'] for phase in phases]
        
        x = np.arange(len(phases))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, actual_values, width, label='Actual QPS', alpha=0.8, color='skyblue')
        bars2 = ax1.bar(x + width/2, predicted_values, width, label='Predicted S_max', alpha=0.8, color='lightcoral')
        
        ax1.set_xlabel('Phase')
        ax1.set_ylabel('Throughput (ops/sec)')
        ax1.set_title('Actual vs Predicted Throughput')
        ax1.set_xticks(x)
        ax1.set_xticklabels([p.replace('_', ' ').title() for p in phases])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 값 표시
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{height:,.0f}', ha='center', va='bottom', fontsize=9)
        for bar in bars2:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{height:,.0f}', ha='center', va='bottom', fontsize=9)
        
        # 2. 정확도 막대 그래프
        ax2 = axes[0, 1]
        accuracies = [evaluation_results[phase]['accuracy_percent'] for phase in phases]
        colors = ['green' if acc > 70 else 'orange' if acc > 40 else 'red' for acc in accuracies]
        
        bars = ax2.bar([p.replace('_', ' ').title() for p in phases], accuracies, color=colors, alpha=0.7)
        ax2.set_ylabel('Accuracy (%)')
        ax2.set_title('Model Accuracy by Phase')
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)
        
        # 정확도 값 표시
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 3. 오차율 분석
        ax3 = axes[1, 0]
        error_rates = [evaluation_results[phase]['error_rate_percent'] for phase in phases]
        direction_colors = ['red' if evaluation_results[phase]['prediction_direction'] == 'over_prediction' else 'blue' for phase in phases]
        
        bars = ax3.bar([p.replace('_', ' ').title() for p in phases], error_rates, color=direction_colors, alpha=0.7)
        ax3.set_ylabel('Error Rate (%)')
        ax3.set_title('Prediction Error Rate by Phase')
        ax3.grid(True, alpha=0.3)
        
        # 오차율 값 표시
        for bar, err in zip(bars, error_rates):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                    f'{err:.1f}%', ha='center', va='bottom', fontsize=10)
        
        # 4. 성능 인자 분석
        ax4 = axes[1, 1]
        performance_factors = ['Performance', 'Stability', 'IO Contention']
        
        # 각 시기별 성능 인자 데이터
        initial_factors = [
            evaluation_results['initial_phase']['performance_factors']['performance_factor'],
            evaluation_results['initial_phase']['performance_factors']['stability_factor'],
            evaluation_results['initial_phase']['performance_factors']['io_contention']
        ]
        
        middle_factors = [
            evaluation_results['middle_phase']['performance_factors']['performance_factor'],
            evaluation_results['middle_phase']['performance_factors']['stability_factor'],
            evaluation_results['middle_phase']['performance_factors']['io_contention']
        ]
        
        final_factors = [
            evaluation_results['final_phase']['performance_factors']['performance_factor'],
            evaluation_results['final_phase']['performance_factors']['stability_factor'],
            evaluation_results['final_phase']['performance_factors']['io_contention']
        ]
        
        x = np.arange(len(performance_factors))
        width = 0.25
        
        ax4.bar(x - width, initial_factors, width, label='Initial', alpha=0.8, color='lightblue')
        ax4.bar(x, middle_factors, width, label='Middle', alpha=0.8, color='lightgreen')
        ax4.bar(x + width, final_factors, width, label='Final', alpha=0.8, color='lightcoral')
        
        ax4.set_xlabel('Performance Factors')
        ax4.set_ylabel('Factor Value')
        ax4.set_title('Performance Factors by Phase')
        ax4.set_xticks(x)
        ax4.set_xticklabels(performance_factors)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        output_file = os.path.join(output_dir, 'v4_2_phase_b_evaluation.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 시각화 저장 완료: {output_file}")
    
    def save_evaluation_results(self, evaluation_report, output_dir):
        """평가 결과 저장"""
        print("💾 평가 결과 저장 중...")
        
        # JSON 결과 저장
        json_file = os.path.join(output_dir, "v4_2_phase_b_evaluation_results.json")
        with open(json_file, 'w') as f:
            json.dump(evaluation_report, f, indent=2)
        
        # 마크다운 리포트 생성
        report_file = os.path.join(output_dir, "v4_2_phase_b_evaluation_report.md")
        self._generate_markdown_report(evaluation_report, report_file)
        
        print(f"✅ 평가 결과 저장 완료:")
        print(f"   - JSON: {json_file}")
        print(f"   - Report: {report_file}")
    
    def _generate_markdown_report(self, evaluation_report, report_file):
        """마크다운 리포트 생성"""
        with open(report_file, 'w') as f:
            f.write("# V4.2 Model Evaluation with Phase-B Results\n\n")
            f.write(f"**평가 일시**: {evaluation_report['evaluation_metadata']['evaluation_date']}\n")
            f.write(f"**모델 버전**: {evaluation_report['evaluation_metadata']['model_version']}\n\n")
            
            # 전체 평가
            overall = evaluation_report['overall_assessment']
            f.write("## Overall Assessment\n\n")
            f.write(f"**평가 등급**: {overall['assessment_level']}\n")
            f.write(f"**평가 설명**: {overall['assessment_description']}\n")
            f.write(f"**평균 정확도**: {overall['average_accuracy']:.1f}%\n\n")
            
            # 시기별 평가
            f.write("## Phase-by-Phase Evaluation\n\n")
            f.write("| Phase | Actual QPS | Predicted S_max | Accuracy | Error Rate | Direction |\n")
            f.write("|-------|------------|-----------------|----------|------------|----------|\n")
            
            for phase, result in evaluation_report['phase_by_phase_evaluation'].items():
                f.write(f"| {phase.replace('_', ' ').title()} | "
                       f"{result['actual_qps']:,.0f} | "
                       f"{result['predicted_s_max']:,.0f} | "
                       f"{result['accuracy_percent']:.1f}% | "
                       f"{result['error_rate_percent']:.1f}% | "
                       f"{result['prediction_direction']} |\n")
            
            f.write("\n")
            
            # 패턴 분석
            pattern = evaluation_report['pattern_analysis']
            f.write("## Pattern Analysis\n\n")
            f.write(f"- **정확도 트렌드**: {pattern['accuracy_trend']}\n")
            f.write(f"- **과대 예측**: {pattern['over_predictions']}개 시기\n")
            f.write(f"- **과소 예측**: {pattern['under_predictions']}개 시기\n")
            f.write(f"- **평균 정확도**: {pattern['average_accuracy']:.1f}%\n")
            f.write(f"- **정확도 표준편차**: {pattern['accuracy_std']:.1f}%\n")
            f.write(f"- **정확도 일관성**: {pattern['accuracy_consistency']}\n")
            f.write(f"- **예측 편향**: {pattern['prediction_bias']}\n\n")
            
            # 강점과 약점
            sw = evaluation_report['strengths_weaknesses']
            f.write("## Strengths and Weaknesses\n\n")
            f.write("### Strengths\n")
            for strength in sw['strengths']:
                f.write(f"- {strength}\n")
            f.write("\n### Weaknesses\n")
            for weakness in sw['weaknesses']:
                f.write(f"- {weakness}\n")
            f.write("\n")
            
            # 권장사항
            f.write("## Recommendations\n\n")
            for recommendation in overall['recommendation']:
                f.write(f"- {recommendation}\n")
            f.write("\n")

def main():
    """메인 실행 함수"""
    print("🚀 V4.2 Model Evaluation with Phase-B Results 시작")
    print("=" * 60)
    
    # 평가기 생성
    evaluator = V4_2PhaseBEvaluator()
    
    # 모델 정확도 평가
    evaluation_results = evaluator.evaluate_model_accuracy()
    
    # 예측 패턴 분석
    pattern_analysis = evaluator.analyze_prediction_patterns(evaluation_results)
    
    # 강점과 약점 평가
    strengths_weaknesses = evaluator.evaluate_model_strengths_weaknesses(evaluation_results)
    
    # 평가 리포트 생성
    evaluation_report = evaluator.generate_evaluation_report(evaluation_results, pattern_analysis, strengths_weaknesses)
    
    # 시각화 생성
    evaluator.create_visualization(evaluation_results, evaluator.results_dir)
    
    # 결과 저장
    evaluator.save_evaluation_results(evaluation_report, evaluator.results_dir)
    
    # 결과 요약 출력
    print("\n" + "=" * 60)
    print("📊 V4.2 Model Evaluation Summary")
    print("=" * 60)
    
    overall = evaluation_report['overall_assessment']
    print(f"Overall Assessment: {overall['assessment_level']}")
    print(f"Average Accuracy: {overall['average_accuracy']:.1f}%")
    print()
    
    for phase, result in evaluation_results.items():
        print(f"{phase.replace('_', ' ').title()}:")
        print(f"  - Actual QPS: {result['actual_qps']:,.0f}")
        print(f"  - Predicted S_max: {result['predicted_s_max']:,.0f}")
        print(f"  - Accuracy: {result['accuracy_percent']:.1f}%")
        print(f"  - Error Rate: {result['error_rate_percent']:.1f}%")
        print(f"  - Direction: {result['prediction_direction']}")
        print()
    
    print("✅ V4.2 Model Evaluation 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
