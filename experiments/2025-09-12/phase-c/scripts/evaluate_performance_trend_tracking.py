#!/usr/bin/env python3
"""
성능 변화량(트렌드) 추적 능력 평가
QPS 평균값이 아닌 성능 변화 패턴을 얼마나 잘 따라가는지 분석
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from scipy.stats import pearsonr
from sklearn.metrics import mean_squared_error, mean_absolute_error

class PerformanceTrendTracker:
    """성능 변화량 추적 평가기"""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 실제 성능 변화 데이터 (Phase-B)
        self.actual_performance_trend = self._load_actual_performance_trend()
        
        # 모델별 예측 트렌드
        self.model_trend_predictions = self._load_model_trend_predictions()
        
    def _load_actual_performance_trend(self):
        """실제 성능 변화 트렌드 데이터 로드"""
        print("📊 실제 성능 변화 트렌드 데이터 로드 중...")
        
        # Phase-B 실제 성능 변화 패턴
        actual_trend = {
            'phase_transitions': {
                'initial_to_middle': {
                    'start_qps': 138769,  # Initial phase 평균
                    'end_qps': 114472,    # Middle phase 평균
                    'change_amount': -24297,  # 절대 변화량
                    'change_percent': -17.5,  # 상대 변화율
                    'trend_direction': 'decreasing',
                    'change_magnitude': 'moderate'
                },
                'middle_to_final': {
                    'start_qps': 114472,  # Middle phase 평균
                    'end_qps': 109678,    # Final phase 평균
                    'change_amount': -4794,   # 절대 변화량
                    'change_percent': -4.2,   # 상대 변화율
                    'trend_direction': 'decreasing',
                    'change_magnitude': 'small'
                },
                'overall': {
                    'start_qps': 138769,  # Initial phase
                    'end_qps': 109678,    # Final phase
                    'change_amount': -29091,  # 전체 변화량
                    'change_percent': -21.0,  # 전체 변화율
                    'trend_direction': 'decreasing',
                    'change_magnitude': 'moderate'
                }
            },
            'detailed_characteristics': {
                'initial_phase': {
                    'avg_qps': 138769,
                    'write_rate': 65.97,  # MB/s
                    'volatility': 'high',  # CV: 0.538
                    'trend_slope': -1.39,  # 급격한 감소
                    'stability_score': 0.2
                },
                'middle_phase': {
                    'avg_qps': 114472,
                    'write_rate': 16.95,  # MB/s
                    'volatility': 'medium',  # CV: 0.272
                    'trend_slope': -0.001,  # 완만한 감소
                    'stability_score': 0.5
                },
                'final_phase': {
                    'avg_qps': 109678,
                    'write_rate': 12.76,  # MB/s
                    'volatility': 'low',   # CV: 0.041
                    'trend_slope': -0.000077,  # 거의 수평
                    'stability_score': 0.8
                }
            },
            'performance_evolution_pattern': {
                'pattern_type': 'exponential_decay',
                'initial_burst': True,
                'stabilization_trend': True,
                'final_plateau': True,
                'overall_trend': 'decreasing_with_stabilization'
            }
        }
        
        print("✅ 실제 성능 변화 트렌드 데이터 로드 완료")
        return actual_trend
    
    def _load_model_trend_predictions(self):
        """모델별 트렌드 예측 데이터 로드"""
        print("📊 모델별 트렌드 예측 데이터 로드 중...")
        
        model_predictions = {
            'v4_model': {
                'predicted_trend': {
                    'initial_phase': 185000,
                    'middle_phase': 125000,
                    'final_phase': 95000
                },
                'trend_characteristics': {
                    'initial_to_middle': {
                        'change_amount': -60000,  # 185000 - 125000
                        'change_percent': -32.4,
                        'predicted_direction': 'decreasing',
                        'predicted_magnitude': 'large'
                    },
                    'middle_to_final': {
                        'change_amount': -30000,  # 125000 - 95000
                        'change_percent': -24.0,
                        'predicted_direction': 'decreasing',
                        'predicted_magnitude': 'moderate'
                    },
                    'overall': {
                        'change_amount': -90000,  # 185000 - 95000
                        'change_percent': -48.6,
                        'predicted_direction': 'decreasing',
                        'predicted_magnitude': 'large'
                    }
                },
                'model_type': 'Device Envelope',
                'trend_modeling_capability': 'basic'
            },
            'v4_1_temporal': {
                'predicted_trend': {
                    'initial_phase': 95000,
                    'middle_phase': 118000,
                    'final_phase': 142000
                },
                'trend_characteristics': {
                    'initial_to_middle': {
                        'change_amount': 23000,   # 118000 - 95000
                        'change_percent': 24.2,
                        'predicted_direction': 'increasing',
                        'predicted_magnitude': 'moderate'
                    },
                    'middle_to_final': {
                        'change_amount': 24000,   # 142000 - 118000
                        'change_percent': 20.3,
                        'predicted_direction': 'increasing',
                        'predicted_magnitude': 'moderate'
                    },
                    'overall': {
                        'change_amount': 47000,   # 142000 - 95000
                        'change_percent': 49.5,
                        'predicted_direction': 'increasing',
                        'predicted_magnitude': 'large'
                    }
                },
                'model_type': 'Temporal Enhanced',
                'trend_modeling_capability': 'advanced'
            },
            'v4_2_enhanced': {
                'predicted_trend': {
                    'initial_phase': 33132,
                    'middle_phase': 119002,
                    'final_phase': 250598
                },
                'trend_characteristics': {
                    'initial_to_middle': {
                        'change_amount': 85870,   # 119002 - 33132
                        'change_percent': 259.1,
                        'predicted_direction': 'increasing',
                        'predicted_magnitude': 'very_large'
                    },
                    'middle_to_final': {
                        'change_amount': 131596,  # 250598 - 119002
                        'change_percent': 110.6,
                        'predicted_direction': 'increasing',
                        'predicted_magnitude': 'very_large'
                    },
                    'overall': {
                        'change_amount': 217466,  # 250598 - 33132
                        'change_percent': 656.2,
                        'predicted_direction': 'increasing',
                        'predicted_magnitude': 'extreme'
                    }
                },
                'model_type': 'Level-wise Temporal Enhanced',
                'trend_modeling_capability': 'sophisticated'
            }
        }
        
        print("✅ 모델별 트렌드 예측 데이터 로드 완료")
        return model_predictions
    
    def evaluate_trend_tracking_accuracy(self):
        """트렌드 추적 정확도 평가"""
        print("📊 트렌드 추적 정확도 평가 중...")
        
        actual_trend = self.actual_performance_trend['phase_transitions']
        evaluation_results = {}
        
        for model_name, model_data in self.model_trend_predictions.items():
            model_trend = model_data['trend_characteristics']
            
            # 1. 방향성 정확도 (Direction Accuracy)
            direction_scores = {}
            for transition in ['initial_to_middle', 'middle_to_final', 'overall']:
                actual_direction = actual_trend[transition]['trend_direction']
                predicted_direction = model_trend[transition]['predicted_direction']
                
                direction_correct = (actual_direction == predicted_direction)
                direction_scores[transition] = {
                    'actual_direction': actual_direction,
                    'predicted_direction': predicted_direction,
                    'correct': direction_correct,
                    'score': 1.0 if direction_correct else 0.0
                }
            
            direction_accuracy = np.mean([score['score'] for score in direction_scores.values()])
            
            # 2. 변화량 정확도 (Magnitude Accuracy)
            magnitude_scores = {}
            for transition in ['initial_to_middle', 'middle_to_final', 'overall']:
                actual_change_percent = actual_trend[transition]['change_percent']
                predicted_change_percent = model_trend[transition]['change_percent']
                
                # 절댓값 기준 오차율 계산
                magnitude_error = abs(abs(predicted_change_percent) - abs(actual_change_percent)) / abs(actual_change_percent) * 100
                magnitude_accuracy = max(0, (100 - magnitude_error) / 100)
                
                magnitude_scores[transition] = {
                    'actual_change_percent': actual_change_percent,
                    'predicted_change_percent': predicted_change_percent,
                    'magnitude_error': magnitude_error,
                    'magnitude_accuracy': magnitude_accuracy
                }
            
            avg_magnitude_accuracy = np.mean([score['magnitude_accuracy'] for score in magnitude_scores.values()])
            
            # 3. 트렌드 패턴 일치도 (Pattern Consistency)
            actual_values = [138769, 114472, 109678]  # Initial, Middle, Final
            predicted_values = [
                model_data['predicted_trend']['initial_phase'],
                model_data['predicted_trend']['middle_phase'],
                model_data['predicted_trend']['final_phase']
            ]
            
            # 피어슨 상관계수로 패턴 일치도 측정
            correlation, p_value = pearsonr(actual_values, predicted_values)
            pattern_consistency = max(0, correlation)  # 음수면 0으로 처리
            
            # 4. 전체 트렌드 점수 계산
            trend_tracking_score = (
                direction_accuracy * 0.4 +      # 방향성 40%
                avg_magnitude_accuracy * 0.4 +  # 변화량 40%
                pattern_consistency * 0.2       # 패턴 일치도 20%
            )
            
            # 5. 트렌드 추적 등급
            if trend_tracking_score >= 0.8:
                trend_grade = "Excellent"
            elif trend_tracking_score >= 0.6:
                trend_grade = "Good"
            elif trend_tracking_score >= 0.4:
                trend_grade = "Fair"
            elif trend_tracking_score >= 0.2:
                trend_grade = "Poor"
            else:
                trend_grade = "Very Poor"
            
            evaluation_results[model_name] = {
                'direction_accuracy': direction_accuracy,
                'magnitude_accuracy': avg_magnitude_accuracy,
                'pattern_consistency': pattern_consistency,
                'trend_tracking_score': trend_tracking_score,
                'trend_grade': trend_grade,
                'direction_scores': direction_scores,
                'magnitude_scores': magnitude_scores,
                'correlation_coefficient': correlation,
                'p_value': p_value,
                'predicted_values': predicted_values,
                'actual_values': actual_values
            }
        
        return evaluation_results
    
    def analyze_trend_modeling_capabilities(self, evaluation_results):
        """트렌드 모델링 능력 분석"""
        print("📊 트렌드 모델링 능력 분석 중...")
        
        analysis_results = {
            'best_trend_tracker': None,
            'direction_accuracy_ranking': [],
            'magnitude_accuracy_ranking': [],
            'pattern_consistency_ranking': [],
            'model_trend_insights': {}
        }
        
        # 각 카테고리별 순위
        direction_ranking = sorted(evaluation_results.items(), key=lambda x: x[1]['direction_accuracy'], reverse=True)
        magnitude_ranking = sorted(evaluation_results.items(), key=lambda x: x[1]['magnitude_accuracy'], reverse=True)
        pattern_ranking = sorted(evaluation_results.items(), key=lambda x: x[1]['pattern_consistency'], reverse=True)
        overall_ranking = sorted(evaluation_results.items(), key=lambda x: x[1]['trend_tracking_score'], reverse=True)
        
        analysis_results['direction_accuracy_ranking'] = direction_ranking
        analysis_results['magnitude_accuracy_ranking'] = magnitude_ranking
        analysis_results['pattern_consistency_ranking'] = pattern_ranking
        analysis_results['best_trend_tracker'] = overall_ranking[0]
        
        # 모델별 트렌드 인사이트
        for model_name, results in evaluation_results.items():
            insights = []
            
            # 방향성 분석
            if results['direction_accuracy'] == 1.0:
                insights.append("모든 구간에서 트렌드 방향 정확히 예측")
            elif results['direction_accuracy'] >= 0.67:
                insights.append("대부분 구간에서 트렌드 방향 정확")
            else:
                insights.append("트렌드 방향 예측에 어려움")
            
            # 변화량 분석
            if results['magnitude_accuracy'] >= 0.8:
                insights.append("변화량 크기 정확히 예측")
            elif results['magnitude_accuracy'] >= 0.5:
                insights.append("변화량 크기 어느 정도 예측")
            else:
                insights.append("변화량 크기 예측 부정확")
            
            # 패턴 일치도 분석
            if results['pattern_consistency'] >= 0.8:
                insights.append("실제 성능 패턴과 높은 일치도")
            elif results['pattern_consistency'] >= 0.5:
                insights.append("실제 성능 패턴과 중간 일치도")
            elif results['pattern_consistency'] >= 0:
                insights.append("실제 성능 패턴과 낮은 일치도")
            else:
                insights.append("실제 성능 패턴과 반대 경향")
            
            # 특별한 특성 분석
            predicted_trend = self.model_trend_predictions[model_name]['trend_characteristics']['overall']['predicted_direction']
            actual_trend = self.actual_performance_trend['phase_transitions']['overall']['trend_direction']
            
            if predicted_trend != actual_trend:
                if predicted_trend == 'increasing' and actual_trend == 'decreasing':
                    insights.append("실제 성능 감소를 증가로 잘못 예측 (치명적 오류)")
                elif predicted_trend == 'decreasing' and actual_trend == 'increasing':
                    insights.append("실제 성능 증가를 감소로 잘못 예측")
            
            analysis_results['model_trend_insights'][model_name] = insights
        
        return analysis_results
    
    def create_trend_visualization(self, evaluation_results, analysis_results, output_dir):
        """트렌드 추적 시각화 생성"""
        print("📊 트렌드 추적 시각화 생성 중...")
        
        # Liberation Serif 폰트 설정
        plt.rcParams['font.family'] = 'Liberation Serif'
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Performance Trend Tracking Analysis: v4, v4.1, v4.2 Models', fontsize=16, fontweight='bold')
        
        phases = ['Initial', 'Middle', 'Final']
        models = ['v4_model', 'v4_1_temporal', 'v4_2_enhanced']
        model_labels = ['v4', 'v4.1', 'v4.2']
        colors = ['blue', 'green', 'red']
        
        # 1. 실제 vs 예측 트렌드 비교
        ax1 = axes[0, 0]
        actual_values = [138769, 114472, 109678]
        
        ax1.plot(phases, actual_values, marker='o', linewidth=3, color='black', label='Actual', markersize=8)
        
        for i, model in enumerate(models):
            predicted_values = evaluation_results[model]['predicted_values']
            ax1.plot(phases, predicted_values, marker='s', linewidth=2, 
                    color=colors[i], label=f'{model_labels[i]} Predicted', alpha=0.8)
        
        ax1.set_xlabel('Phase')
        ax1.set_ylabel('Throughput (ops/sec)')
        ax1.set_title('Actual vs Predicted Performance Trends')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 트렌드 추적 점수
        ax2 = axes[0, 1]
        trend_scores = [evaluation_results[model]['trend_tracking_score'] for model in models]
        
        bars = ax2.bar(model_labels, trend_scores, color=['lightblue', 'lightgreen', 'lightcoral'], alpha=0.8)
        
        for bar, score in zip(bars, trend_scores):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax2.set_ylabel('Trend Tracking Score')
        ax2.set_title('Overall Trend Tracking Performance')
        ax2.set_ylim(0, 1.0)
        ax2.grid(True, alpha=0.3)
        
        # 3. 방향성 정확도
        ax3 = axes[0, 2]
        direction_accuracies = [evaluation_results[model]['direction_accuracy'] for model in models]
        
        bars = ax3.bar(model_labels, direction_accuracies, color=colors, alpha=0.7)
        
        for bar, acc in zip(bars, direction_accuracies):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{acc:.1%}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax3.set_ylabel('Direction Accuracy')
        ax3.set_title('Trend Direction Prediction Accuracy')
        ax3.set_ylim(0, 1.1)
        ax3.grid(True, alpha=0.3)
        
        # 4. 변화량 정확도
        ax4 = axes[1, 0]
        magnitude_accuracies = [evaluation_results[model]['magnitude_accuracy'] for model in models]
        
        bars = ax4.bar(model_labels, magnitude_accuracies, color=colors, alpha=0.7)
        
        for bar, acc in zip(bars, magnitude_accuracies):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{acc:.1%}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax4.set_ylabel('Magnitude Accuracy')
        ax4.set_title('Change Magnitude Prediction Accuracy')
        ax4.set_ylim(0, 1.1)
        ax4.grid(True, alpha=0.3)
        
        # 5. 패턴 일치도
        ax5 = axes[1, 1]
        pattern_consistencies = [evaluation_results[model]['pattern_consistency'] for model in models]
        
        bars = ax5.bar(model_labels, pattern_consistencies, color=colors, alpha=0.7)
        
        for bar, consistency in zip(bars, pattern_consistencies):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{consistency:.3f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax5.set_ylabel('Pattern Consistency (Correlation)')
        ax5.set_title('Performance Pattern Consistency')
        ax5.set_ylim(-1.0, 1.0)
        ax5.grid(True, alpha=0.3)
        ax5.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        
        # 6. 변화량 비교 (절댓값)
        ax6 = axes[1, 2]
        
        # 실제 변화량
        actual_changes = [-24297, -4794]  # Initial->Middle, Middle->Final
        
        # 예측 변화량
        v4_changes = [-60000, -30000]
        v41_changes = [23000, 24000]
        v42_changes = [85870, 131596]
        
        x = np.arange(2)
        width = 0.2
        
        ax6.bar(x - width*1.5, actual_changes, width, label='Actual', color='black', alpha=0.8)
        ax6.bar(x - width/2, v4_changes, width, label='v4', color=colors[0], alpha=0.7)
        ax6.bar(x + width/2, v41_changes, width, label='v4.1', color=colors[1], alpha=0.7)
        ax6.bar(x + width*1.5, v42_changes, width, label='v4.2', color=colors[2], alpha=0.7)
        
        ax6.set_xlabel('Transition')
        ax6.set_ylabel('Change Amount (ops/sec)')
        ax6.set_title('Performance Change Amount Comparison')
        ax6.set_xticks(x)
        ax6.set_xticklabels(['Initial→Middle', 'Middle→Final'])
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        ax6.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        
        # 저장
        output_file = os.path.join(output_dir, 'performance_trend_tracking_analysis.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 트렌드 추적 시각화 저장 완료: {output_file}")
    
    def save_trend_analysis_results(self, evaluation_results, analysis_results, output_dir):
        """트렌드 분석 결과 저장"""
        print("💾 트렌드 분석 결과 저장 중...")
        
        comprehensive_report = {
            'analysis_metadata': {
                'analysis_date': datetime.now().isoformat(),
                'analysis_type': 'Performance Trend Tracking Evaluation',
                'focus': 'Trend prediction accuracy vs average QPS accuracy',
                'models_analyzed': list(self.model_trend_predictions.keys())
            },
            'actual_performance_trend': self.actual_performance_trend,
            'model_trend_predictions': self.model_trend_predictions,
            'trend_tracking_evaluation': evaluation_results,
            'trend_modeling_analysis': analysis_results,
            'key_findings': self._generate_key_findings(evaluation_results, analysis_results)
        }
        
        # JSON 결과 저장
        json_file = os.path.join(output_dir, "performance_trend_tracking_analysis.json")
        with open(json_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        # 마크다운 리포트 생성
        report_file = os.path.join(output_dir, "performance_trend_tracking_analysis.md")
        self._generate_trend_markdown_report(comprehensive_report, report_file)
        
        print(f"✅ 트렌드 분석 결과 저장 완료:")
        print(f"   - JSON: {json_file}")
        print(f"   - Report: {report_file}")
    
    def _generate_key_findings(self, evaluation_results, analysis_results):
        """주요 발견사항 생성"""
        findings = {
            'best_trend_tracker': analysis_results['best_trend_tracker'][0],
            'best_trend_score': analysis_results['best_trend_tracker'][1]['trend_tracking_score'],
            'direction_prediction_analysis': {},
            'magnitude_prediction_analysis': {},
            'critical_insights': []
        }
        
        # 방향성 예측 분석
        for model_name, results in evaluation_results.items():
            direction_acc = results['direction_accuracy']
            findings['direction_prediction_analysis'][model_name] = {
                'accuracy': direction_acc,
                'correct_predictions': int(direction_acc * 3),  # 3개 구간 중
                'status': 'excellent' if direction_acc == 1.0 else 'good' if direction_acc >= 0.67 else 'poor'
            }
        
        # 변화량 예측 분석
        for model_name, results in evaluation_results.items():
            magnitude_acc = results['magnitude_accuracy']
            findings['magnitude_prediction_analysis'][model_name] = {
                'accuracy': magnitude_acc,
                'status': 'excellent' if magnitude_acc >= 0.8 else 'good' if magnitude_acc >= 0.5 else 'poor'
            }
        
        # 중요한 인사이트
        findings['critical_insights'] = [
            "QPS 평균값 정확도와 트렌드 추적 능력은 다른 능력임",
            "실제 성능은 감소 추세이지만 일부 모델은 증가로 예측",
            "트렌드 방향 예측이 변화량 크기 예측보다 중요함",
            "모든 모델이 실제 성능 변화 패턴을 완전히 포착하지 못함"
        ]
        
        return findings
    
    def _generate_trend_markdown_report(self, comprehensive_report, report_file):
        """트렌드 분석 마크다운 리포트 생성"""
        with open(report_file, 'w') as f:
            f.write("# Performance Trend Tracking Analysis\n\n")
            f.write("## 🎯 Analysis Focus\n\n")
            f.write("이 분석은 **QPS 평균값 정확도**가 아닌 **성능 변화 패턴(트렌드) 추적 능력**을 평가합니다.\n\n")
            
            # 실제 성능 트렌드
            f.write("## 📊 Actual Performance Trend\n\n")
            actual_trend = comprehensive_report['actual_performance_trend']['phase_transitions']
            
            f.write("### Performance Evolution Pattern\n")
            f.write("```\n")
            f.write(f"Initial Phase: 138,769 ops/sec\n")
            f.write(f"    ↓ {actual_trend['initial_to_middle']['change_percent']:.1f}% ({actual_trend['initial_to_middle']['change_amount']:,} ops/sec)\n")
            f.write(f"Middle Phase: 114,472 ops/sec\n")
            f.write(f"    ↓ {actual_trend['middle_to_final']['change_percent']:.1f}% ({actual_trend['middle_to_final']['change_amount']:,} ops/sec)\n")
            f.write(f"Final Phase: 109,678 ops/sec\n")
            f.write("```\n\n")
            
            f.write(f"**Overall Trend**: {actual_trend['overall']['trend_direction']} ({actual_trend['overall']['change_percent']:.1f}%)\n\n")
            
            # 모델별 트렌드 예측
            f.write("## 🔍 Model Trend Predictions\n\n")
            
            for model_name, model_data in comprehensive_report['model_trend_predictions'].items():
                model_display = model_name.replace('_', '.').replace('v4.2.enhanced', 'v4.2')
                f.write(f"### {model_display.upper()}\n")
                
                trend = model_data['predicted_trend']
                f.write("```\n")
                f.write(f"Initial Phase: {trend['initial_phase']:,} ops/sec\n")
                
                initial_to_middle = model_data['trend_characteristics']['initial_to_middle']
                f.write(f"    {'↑' if initial_to_middle['predicted_direction'] == 'increasing' else '↓'} {abs(initial_to_middle['change_percent']):.1f}% ({initial_to_middle['change_amount']:+,} ops/sec)\n")
                
                f.write(f"Middle Phase: {trend['middle_phase']:,} ops/sec\n")
                
                middle_to_final = model_data['trend_characteristics']['middle_to_final']
                f.write(f"    {'↑' if middle_to_final['predicted_direction'] == 'increasing' else '↓'} {abs(middle_to_final['change_percent']):.1f}% ({middle_to_final['change_amount']:+,} ops/sec)\n")
                
                f.write(f"Final Phase: {trend['final_phase']:,} ops/sec\n")
                f.write("```\n")
                
                overall_trend = model_data['trend_characteristics']['overall']
                f.write(f"**Predicted Overall Trend**: {overall_trend['predicted_direction']} ({overall_trend['change_percent']:+.1f}%)\n\n")
            
            # 트렌드 추적 평가 결과
            f.write("## 📈 Trend Tracking Evaluation Results\n\n")
            
            f.write("| Model | Trend Score | Direction Accuracy | Magnitude Accuracy | Pattern Consistency | Grade |\n")
            f.write("|-------|-------------|--------------------|--------------------|--------------------|---------|\n")
            
            for model_name, results in comprehensive_report['trend_tracking_evaluation'].items():
                model_display = model_name.replace('_', '.').replace('v4.2.enhanced', 'v4.2')
                f.write(f"| {model_display} | "
                       f"{results['trend_tracking_score']:.3f} | "
                       f"{results['direction_accuracy']:.1%} | "
                       f"{results['magnitude_accuracy']:.1%} | "
                       f"{results['pattern_consistency']:.3f} | "
                       f"{results['trend_grade']} |\n")
            
            f.write("\n")
            
            # 주요 발견사항
            findings = comprehensive_report['key_findings']
            f.write("## 💡 Key Findings\n\n")
            f.write(f"**최고 트렌드 추적 모델**: {findings['best_trend_tracker']} (Score: {findings['best_trend_score']:.3f})\n\n")
            
            f.write("### Critical Insights\n")
            for insight in findings['critical_insights']:
                f.write(f"- {insight}\n")
            f.write("\n")
            
            # 모델별 상세 분석
            f.write("## 🔬 Detailed Model Analysis\n\n")
            
            for model_name, insights in comprehensive_report['trend_modeling_analysis']['model_trend_insights'].items():
                model_display = model_name.replace('_', '.').replace('v4.2.enhanced', 'v4.2')
                f.write(f"### {model_display.upper()}\n")
                for insight in insights:
                    f.write(f"- {insight}\n")
                f.write("\n")
            
            # 결론
            f.write("## 🎯 Conclusion\n\n")
            f.write("**성능 변화 패턴 추적**은 **QPS 평균값 예측**과는 다른 능력입니다. ")
            f.write("실제 RocksDB 성능은 시간에 따라 감소하는 패턴을 보이지만, ")
            f.write("일부 모델들은 이를 증가 패턴으로 잘못 예측하고 있습니다.\n\n")
            
            f.write("트렌드 추적 능력이 우수한 모델을 개발하기 위해서는 ")
            f.write("**방향성 예측**과 **변화량 크기 예측**을 모두 고려해야 합니다.\n")

def main():
    """메인 실행 함수"""
    print("🚀 Performance Trend Tracking Analysis 시작")
    print("=" * 70)
    
    # 트렌드 추적 분석기 생성
    tracker = PerformanceTrendTracker()
    
    # 트렌드 추적 정확도 평가
    evaluation_results = tracker.evaluate_trend_tracking_accuracy()
    
    # 트렌드 모델링 능력 분석
    analysis_results = tracker.analyze_trend_modeling_capabilities(evaluation_results)
    
    # 시각화 생성
    tracker.create_trend_visualization(evaluation_results, analysis_results, tracker.results_dir)
    
    # 결과 저장
    tracker.save_trend_analysis_results(evaluation_results, analysis_results, tracker.results_dir)
    
    # 결과 요약 출력
    print("\n" + "=" * 70)
    print("📊 Performance Trend Tracking Analysis Summary")
    print("=" * 70)
    
    best_tracker = analysis_results['best_trend_tracker']
    print(f"Best Trend Tracker: {best_tracker[0]} (Score: {best_tracker[1]['trend_tracking_score']:.3f})")
    print()
    
    print("Model Trend Tracking Scores:")
    for model_name, results in evaluation_results.items():
        model_display = model_name.replace('_', '.').replace('v4.2.enhanced', 'v4.2')
        print(f"  {model_display.upper()}: {results['trend_tracking_score']:.3f} ({results['trend_grade']})")
    print()
    
    print("Direction Prediction Accuracy:")
    for model_name, results in evaluation_results.items():
        model_display = model_name.replace('_', '.').replace('v4.2.enhanced', 'v4.2')
        print(f"  {model_display.upper()}: {results['direction_accuracy']:.1%}")
    print()
    
    print("Critical Finding:")
    print("  실제 성능은 감소 추세이지만 일부 모델은 증가로 예측")
    print("  QPS 평균값 정확도 ≠ 트렌드 추적 능력")
    
    print("\n✅ Performance Trend Tracking Analysis 완료!")
    print("=" * 70)

if __name__ == "__main__":
    main()
