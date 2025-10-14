#!/usr/bin/env python3
"""
Phase-C Analysis with V4.2 FillRandom Enhanced Model (Corrected)
v4.2 FillRandom Enhanced 모델을 사용한 Phase-C 분석 (올바른 로그 위치)
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class Phase_C_V4_2_Analyzer_Corrected:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-B 로그 파일 경로
        self.phase_b_log_path = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/rocksdb_log_phase_b.log'
        
        # v4.2 모델 결과 로드
        self.v4_2_model_results = self._load_v4_2_model_results()
        
        # Phase-C 분석 결과
        self.phase_c_analysis = {}
        
        print("🚀 Phase-C Analysis with V4.2 FillRandom Enhanced Model (Corrected) 시작")
        print("=" * 60)
    
    def _load_v4_2_model_results(self):
        """v4.2 모델 결과 로드"""
        print("📊 v4.2 모델 결과 로드 중...")
        
        v4_2_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/scripts/results/v4_2_fillrandom_enhanced_model_results.json'
        
        if os.path.exists(v4_2_file):
            try:
                with open(v4_2_file, 'r') as f:
                    v4_2_results = json.load(f)
                print("✅ v4.2 모델 결과 로드 완료")
                return v4_2_results
            except Exception as e:
                print(f"⚠️ v4.2 모델 결과 로드 실패: {e}")
                return None
        else:
            print("⚠️ v4.2 모델 결과 파일 없음")
            return None
    
    def _parse_phase_b_log(self):
        """Phase-B 로그 파일 파싱"""
        print("📊 Phase-B 로그 파일 파싱 중...")
        
        if not os.path.exists(self.phase_b_log_path):
            print(f"⚠️ Phase-B 로그 파일 없음: {self.phase_b_log_path}")
            return None
        
        # 로그 파일에서 성능 데이터 추출
        log_data = {
            'qps_data': [],
            'flush_data': [],
            'compaction_data': [],
            'level_io_data': []
        }
        
        try:
            with open(self.phase_b_log_path, 'r') as f:
                for line_num, line in enumerate(f):
                    if line_num % 100000 == 0:
                        print(f"   📊 로그 파싱 진행: {line_num:,} 라인")
                    
                    # QPS 데이터 추출
                    if 'QPS' in line and 'ops/sec' in line:
                        try:
                            # QPS 값 추출 (예: "QPS: 12345 ops/sec")
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'QPS:' and i + 1 < len(parts):
                                    qps_value = float(parts[i + 1])
                                    log_data['qps_data'].append({
                                        'timestamp': line_num,
                                        'qps': qps_value
                                    })
                                    break
                        except (ValueError, IndexError):
                            continue
                    
                    # Flush 데이터 추출
                    if 'flush_started' in line or 'flush_finished' in line:
                        try:
                            # Flush 이벤트 파싱
                            if 'flush_started' in line:
                                log_data['flush_data'].append({
                                    'timestamp': line_num,
                                    'event': 'flush_started',
                                    'line': line.strip()
                                })
                            elif 'flush_finished' in line:
                                log_data['flush_data'].append({
                                    'timestamp': line_num,
                                    'event': 'flush_finished',
                                    'line': line.strip()
                                })
                        except Exception:
                            continue
                    
                    # Compaction 데이터 추출
                    if 'compaction_started' in line or 'compaction_finished' in line:
                        try:
                            # Compaction 이벤트 파싱
                            if 'compaction_started' in line:
                                log_data['compaction_data'].append({
                                    'timestamp': line_num,
                                    'event': 'compaction_started',
                                    'line': line.strip()
                                })
                            elif 'compaction_finished' in line:
                                log_data['compaction_data'].append({
                                    'timestamp': line_num,
                                    'event': 'compaction_finished',
                                    'line': line.strip()
                                })
                        except Exception:
                            continue
                    
                    # Level I/O 데이터 추출
                    if 'Level' in line and ('write' in line.lower() or 'read' in line.lower()):
                        try:
                            log_data['level_io_data'].append({
                                'timestamp': line_num,
                                'line': line.strip()
                            })
                        except Exception:
                            continue
                    
                    # 너무 많은 라인을 처리하지 않도록 제한
                    if line_num > 1000000:  # 100만 라인으로 제한
                        break
                        
        except Exception as e:
            print(f"⚠️ 로그 파일 파싱 실패: {e}")
            return None
        
        print(f"✅ Phase-B 로그 파싱 완료:")
        print(f"   - QPS 데이터: {len(log_data['qps_data'])}개")
        print(f"   - Flush 데이터: {len(log_data['flush_data'])}개")
        print(f"   - Compaction 데이터: {len(log_data['compaction_data'])}개")
        print(f"   - Level I/O 데이터: {len(log_data['level_io_data'])}개")
        
        return log_data
    
    def _extract_phase_b_performance_metrics(self, log_data):
        """Phase-B 로그에서 성능 지표 추출"""
        print("📊 Phase-B 성능 지표 추출 중...")
        
        if not log_data:
            return None
        
        performance_metrics = {
            'qps_analysis': {},
            'flush_analysis': {},
            'compaction_analysis': {},
            'level_io_analysis': {}
        }
        
        # QPS 분석
        if log_data['qps_data']:
            qps_values = [data['qps'] for data in log_data['qps_data']]
            performance_metrics['qps_analysis'] = {
                'avg_qps': np.mean(qps_values),
                'max_qps': np.max(qps_values),
                'min_qps': np.min(qps_values),
                'std_qps': np.std(qps_values),
                'total_samples': len(qps_values)
            }
        
        # Flush 분석
        if log_data['flush_data']:
            flush_started = len([data for data in log_data['flush_data'] if data['event'] == 'flush_started'])
            flush_finished = len([data for data in log_data['flush_data'] if data['event'] == 'flush_finished'])
            performance_metrics['flush_analysis'] = {
                'flush_started_count': flush_started,
                'flush_finished_count': flush_finished,
                'flush_completion_rate': flush_finished / flush_started if flush_started > 0 else 0
            }
        
        # Compaction 분석
        if log_data['compaction_data']:
            compaction_started = len([data for data in log_data['compaction_data'] if data['event'] == 'compaction_started'])
            compaction_finished = len([data for data in log_data['compaction_data'] if data['event'] == 'compaction_finished'])
            performance_metrics['compaction_analysis'] = {
                'compaction_started_count': compaction_started,
                'compaction_finished_count': compaction_finished,
                'compaction_completion_rate': compaction_finished / compaction_started if compaction_started > 0 else 0
            }
        
        # Level I/O 분석
        if log_data['level_io_data']:
            performance_metrics['level_io_analysis'] = {
                'level_io_events': len(log_data['level_io_data']),
                'io_intensity': len(log_data['level_io_data']) / 1000  # 이벤트 밀도
            }
        
        print(f"✅ Phase-B 성능 지표 추출 완료:")
        if performance_metrics['qps_analysis']:
            print(f"   - 평균 QPS: {performance_metrics['qps_analysis']['avg_qps']:.0f}")
            print(f"   - 최대 QPS: {performance_metrics['qps_analysis']['max_qps']:.0f}")
            print(f"   - 최소 QPS: {performance_metrics['qps_analysis']['min_qps']:.0f}")
        
        return performance_metrics
    
    def analyze_phase_c_with_v4_2_corrected(self):
        """v4.2 모델을 사용한 Phase-C 분석 (수정됨)"""
        print("📊 v4.2 모델을 사용한 Phase-C 분석 중...")
        
        if not self.v4_2_model_results:
            print("⚠️ v4.2 모델 결과가 없어 분석을 진행할 수 없습니다.")
            return None
        
        # Phase-B 로그 파싱
        log_data = self._parse_phase_b_log()
        if not log_data:
            print("⚠️ Phase-B 로그 파싱 실패")
            return None
        
        # Phase-B 성능 지표 추출
        phase_b_performance = self._extract_phase_b_performance_metrics(log_data)
        if not phase_b_performance:
            print("⚠️ Phase-B 성능 지표 추출 실패")
            return None
        
        # v4.2 모델 예측 결과
        v4_2_predictions = self.v4_2_model_results.get('v4_2_predictions', {})
        
        # v4.2 모델 정확도 분석
        model_accuracy_analysis = self._analyze_v4_2_model_accuracy_corrected(v4_2_predictions, phase_b_performance)
        
        # 시기별 성능 비교 분석
        temporal_performance_comparison = self._analyze_temporal_performance_comparison_corrected(v4_2_predictions, phase_b_performance)
        
        # FillRandom 워크로드 특성 분석
        fillrandom_workload_analysis = self._analyze_fillrandom_workload_characteristics_corrected(v4_2_predictions, phase_b_performance)
        
        # Compaction 효율성 분석
        compaction_efficiency_analysis = self._analyze_compaction_efficiency_corrected(v4_2_predictions, phase_b_performance)
        
        self.phase_c_analysis = {
            'v4_2_model_accuracy': model_accuracy_analysis,
            'temporal_performance_comparison': temporal_performance_comparison,
            'fillrandom_workload_analysis': fillrandom_workload_analysis,
            'compaction_efficiency_analysis': compaction_efficiency_analysis,
            'phase_b_performance': phase_b_performance,
            'v4_2_predictions': v4_2_predictions
        }
        
        print("✅ v4.2 모델을 사용한 Phase-C 분석 완료")
        return self.phase_c_analysis
    
    def _analyze_v4_2_model_accuracy_corrected(self, v4_2_predictions, phase_b_performance):
        """v4.2 모델 정확도 분석 (수정됨)"""
        print("📊 v4.2 모델 정확도 분석 중...")
        
        accuracy_analysis = {
            'overall_accuracy': 0.0,
            'phase_specific_accuracy': {},
            'performance_metrics': {},
            'model_improvements': {}
        }
        
        # Phase-B 실제 성능 데이터
        actual_qps = phase_b_performance.get('qps_analysis', {}).get('avg_qps', 0)
        
        if actual_qps > 0:
            # v4.2 모델 예측값과 실제값 비교
            device_envelope = v4_2_predictions.get('device_envelope_temporal', {})
            
            for phase_name, phase_data in device_envelope.items():
                predicted_smax = phase_data.get('s_max', 0)
                
                # 정확도 계산
                if predicted_smax > 0:
                    accuracy = min(100.0, (1.0 - abs(predicted_smax - actual_qps) / actual_qps) * 100)
                else:
                    accuracy = 0.0
                
                accuracy_analysis['phase_specific_accuracy'][phase_name] = {
                    'predicted_smax': predicted_smax,
                    'actual_qps': actual_qps,
                    'accuracy': accuracy
                }
            
            # 전체 정확도 계산
            accuracies = [data['accuracy'] for data in accuracy_analysis['phase_specific_accuracy'].values()]
            accuracy_analysis['overall_accuracy'] = np.mean(accuracies) if accuracies else 0.0
        
        # 성능 지표 분석
        device_envelope = v4_2_predictions.get('device_envelope_temporal', {})
        accuracy_analysis['performance_metrics'] = {
            'actual_qps': actual_qps,
            'model_predictions': len(device_envelope),
            'accuracy_range': {
                'min': min([data['accuracy'] for data in accuracy_analysis['phase_specific_accuracy'].values()]) if accuracy_analysis['phase_specific_accuracy'] else 0,
                'max': max([data['accuracy'] for data in accuracy_analysis['phase_specific_accuracy'].values()]) if accuracy_analysis['phase_specific_accuracy'] else 0
            }
        }
        
        # 모델 개선사항
        accuracy_analysis['model_improvements'] = {
            'fillrandom_workload_specific': True,
            'real_degradation_data_integration': True,
            'compaction_efficiency_analysis': True,
            'temporal_phase_modeling': True
        }
        
        print(f"✅ v4.2 모델 정확도 분석 완료: {accuracy_analysis['overall_accuracy']:.1f}%")
        return accuracy_analysis
    
    def _analyze_temporal_performance_comparison_corrected(self, v4_2_predictions, phase_b_performance):
        """시기별 성능 비교 분석 (수정됨)"""
        print("📊 시기별 성능 비교 분석 중...")
        
        temporal_comparison = {
            'phase_performance_trends': {},
            'performance_degradation_patterns': {},
            'model_vs_actual_comparison': {}
        }
        
        # v4.2 모델 시기별 예측
        device_envelope = v4_2_predictions.get('device_envelope_temporal', {})
        
        for phase_name, phase_data in device_envelope.items():
            temporal_comparison['phase_performance_trends'][phase_name] = {
                'predicted_smax': phase_data.get('s_max', 0),
                'write_performance': phase_data.get('adjusted_performance', {}).get('adjusted_write_bw', 0),
                'compaction_read_performance': phase_data.get('adjusted_performance', {}).get('adjusted_compaction_read_bw', 0),
                'compaction_efficiency': phase_data.get('compaction_efficiency', 0)
            }
        
        # 성능 열화 패턴 분석
        phases = ['initial_phase', 'middle_phase', 'final_phase']
        smax_values = [device_envelope.get(phase, {}).get('s_max', 0) for phase in phases]
        
        if len(smax_values) >= 2:
            degradation_rate = ((smax_values[0] - smax_values[-1]) / smax_values[0]) * 100 if smax_values[0] > 0 else 0
            temporal_comparison['performance_degradation_patterns'] = {
                'initial_to_final_degradation': degradation_rate,
                'performance_trend': 'decreasing' if smax_values[0] > smax_values[-1] else 'increasing',
                'degradation_curve': smax_values
            }
        
        # 모델 vs 실제 비교
        actual_qps = phase_b_performance.get('qps_analysis', {}).get('avg_qps', 0)
        if actual_qps > 0:
            temporal_comparison['model_vs_actual_comparison'] = {
                'actual_qps': actual_qps,
                'model_predictions': smax_values,
                'prediction_accuracy': [min(100.0, (1.0 - abs(pred - actual_qps) / actual_qps) * 100) for pred in smax_values]
            }
        
        print("✅ 시기별 성능 비교 분석 완료")
        return temporal_comparison
    
    def _analyze_fillrandom_workload_characteristics_corrected(self, v4_2_predictions, phase_b_performance):
        """FillRandom 워크로드 특성 분석 (수정됨)"""
        print("📊 FillRandom 워크로드 특성 분석 중...")
        
        workload_analysis = {
            'workload_characteristics': {
                'write_type': 'Sequential Write Only',
                'read_type': 'Compaction Read Only',
                'user_reads': 0,
                'system_reads': 'Compaction Only'
            },
            'performance_characteristics': {},
            'workload_optimization': {}
        }
        
        # v4.2 모델에서 FillRandom 워크로드 특성 분석
        device_envelope = v4_2_predictions.get('device_envelope_temporal', {})
        
        for phase_name, phase_data in device_envelope.items():
            workload_analysis['performance_characteristics'][phase_name] = {
                'write_performance': phase_data.get('adjusted_performance', {}).get('adjusted_write_bw', 0),
                'compaction_read_performance': phase_data.get('adjusted_performance', {}).get('adjusted_compaction_read_bw', 0),
                'compaction_efficiency': phase_data.get('compaction_efficiency', 0),
                'workload_type': 'FillRandom (Sequential Write + Compaction Read)'
            }
        
        # 워크로드 최적화 분석
        workload_analysis['workload_optimization'] = {
            'write_optimization': 'Sequential Write 성능 최적화 필요',
            'compaction_optimization': 'Compaction Read 성능 최적화 필요',
            'efficiency_improvement': 'Compaction 효율성 향상 필요'
        }
        
        print("✅ FillRandom 워크로드 특성 분석 완료")
        return workload_analysis
    
    def _analyze_compaction_efficiency_corrected(self, v4_2_predictions, phase_b_performance):
        """Compaction 효율성 분석 (수정됨)"""
        print("📊 Compaction 효율성 분석 중...")
        
        compaction_analysis = {
            'efficiency_by_phase': {},
            'efficiency_trends': {},
            'optimization_recommendations': {}
        }
        
        # 시기별 Compaction 효율성 분석
        device_envelope = v4_2_predictions.get('device_envelope_temporal', {})
        
        efficiency_values = []
        for phase_name, phase_data in device_envelope.items():
            efficiency = phase_data.get('compaction_efficiency', 0)
            efficiency_values.append(efficiency)
            
            compaction_analysis['efficiency_by_phase'][phase_name] = {
                'compaction_efficiency': efficiency,
                'write_performance': phase_data.get('adjusted_performance', {}).get('adjusted_write_bw', 0),
                'compaction_read_performance': phase_data.get('adjusted_performance', {}).get('adjusted_compaction_read_bw', 0)
            }
        
        # 효율성 트렌드 분석
        if len(efficiency_values) >= 2:
            compaction_analysis['efficiency_trends'] = {
                'efficiency_curve': efficiency_values,
                'trend': 'decreasing' if efficiency_values[0] > efficiency_values[-1] else 'increasing',
                'efficiency_degradation': ((efficiency_values[0] - efficiency_values[-1]) / efficiency_values[0]) * 100 if efficiency_values[0] > 0 else 0
            }
        
        # 최적화 권장사항
        compaction_analysis['optimization_recommendations'] = {
            'compaction_read_optimization': 'Compaction Read 성능 향상 필요',
            'write_optimization': 'Sequential Write 성능 향상 필요',
            'efficiency_improvement': 'Compaction 효율성 향상 필요'
        }
        
        print("✅ Compaction 효율성 분석 완료")
        return compaction_analysis
    
    def create_phase_c_v4_2_visualization_corrected(self):
        """Phase-C v4.2 모델 분석 시각화 생성 (수정됨)"""
        print("📊 Phase-C v4.2 모델 분석 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('Phase-C Analysis with V4.2 FillRandom Enhanced Model (Corrected)', fontsize=16, fontweight='bold')
        
        # 1. v4.2 모델 정확도 분석
        if 'v4_2_model_accuracy' in self.phase_c_analysis:
            accuracy_data = self.phase_c_analysis['v4_2_model_accuracy']
            phase_accuracies = accuracy_data.get('phase_specific_accuracy', {})
            
            if phase_accuracies:
                phases = list(phase_accuracies.keys())
                accuracies = [data['accuracy'] for data in phase_accuracies.values()]
                
                colors = ['green' if acc > 80 else 'orange' if acc > 60 else 'red' for acc in accuracies]
                bars = ax1.bar([p.replace('_phase', '').title() for p in phases], accuracies, color=colors, alpha=0.7)
                ax1.set_ylabel('Accuracy (%)')
                ax1.set_title('V4.2 Model Accuracy by Phase')
                ax1.set_ylim(0, 100)
                ax1.grid(True, alpha=0.3)
                
                for bar, value in zip(bars, accuracies):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height,
                            f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 2. 시기별 성능 비교
        if 'temporal_performance_comparison' in self.phase_c_analysis:
            temporal_data = self.phase_c_analysis['temporal_performance_comparison']
            phase_trends = temporal_data.get('phase_performance_trends', {})
            
            if phase_trends:
                phases = list(phase_trends.keys())
                smax_values = [data['predicted_smax'] for data in phase_trends.values()]
                
                bars = ax2.bar([p.replace('_phase', '').title() for p in phases], smax_values, color='skyblue', alpha=0.7)
                ax2.set_ylabel('S_max (ops/sec)')
                ax2.set_title('V4.2 Model Predictions by Phase')
                ax2.grid(True, alpha=0.3)
                
                for bar, value in zip(bars, smax_values):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 3. Compaction 효율성 분석
        if 'compaction_efficiency_analysis' in self.phase_c_analysis:
            compaction_data = self.phase_c_analysis['compaction_efficiency_analysis']
            efficiency_by_phase = compaction_data.get('efficiency_by_phase', {})
            
            if efficiency_by_phase:
                phases = list(efficiency_by_phase.keys())
                efficiencies = [data['compaction_efficiency'] for data in efficiency_by_phase.values()]
                
                bars = ax3.bar([p.replace('_phase', '').title() for p in phases], efficiencies, color='orange', alpha=0.7)
                ax3.set_ylabel('Compaction Efficiency')
                ax3.set_title('Compaction Efficiency by Phase')
                ax3.grid(True, alpha=0.3)
                
                for bar, value in zip(bars, efficiencies):
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height,
                            f'{value:.2f}', ha='center', va='bottom', fontsize=9)
        
        # 4. FillRandom 워크로드 특성 및 성능 열화
        ax4.text(0.1, 0.9, 'V4.2 FillRandom Enhanced Model Characteristics:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.8, '• Write: Sequential Write Only (User Operations)', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.7, '• Read: Compaction Read Only (System Operations)', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.6, '• User Reads: None', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.5, '• System Reads: Compaction Only', fontsize=12, transform=ax4.transAxes)
        
        if 'v4_2_model_accuracy' in self.phase_c_analysis:
            overall_accuracy = self.phase_c_analysis['v4_2_model_accuracy'].get('overall_accuracy', 0)
            ax4.text(0.1, 0.3, f'Overall Model Accuracy: {overall_accuracy:.1f}%', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        
        if 'phase_b_performance' in self.phase_c_analysis:
            phase_b_perf = self.phase_c_analysis['phase_b_performance']
            if 'qps_analysis' in phase_b_perf:
                actual_qps = phase_b_perf['qps_analysis'].get('avg_qps', 0)
                ax4.text(0.1, 0.2, f'Actual QPS: {actual_qps:.0f}', fontsize=12, transform=ax4.transAxes)
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('V4.2 Model Characteristics')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/phase_c_v4_2_analysis_corrected.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Phase-C v4.2 모델 분석 시각화 완료")
    
    def save_results(self):
        """결과 저장"""
        print("💾 Phase-C v4.2 모델 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/phase_c_v4_2_analysis_corrected_results.json", 'w') as f:
                json.dump(self.phase_c_analysis, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_phase_c_v4_2_report_corrected()
            with open(f"{self.results_dir}/phase_c_v4_2_analysis_corrected_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_phase_c_v4_2_report_corrected(self):
        """Phase-C v4.2 모델 분석 보고서 생성 (수정됨)"""
        report = f"""# Phase-C Analysis with V4.2 FillRandom Enhanced Model (Corrected)

## Overview
This report presents the analysis of Phase-C using the V4.2 FillRandom Enhanced model with correct Phase-B log data.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## V4.2 Model Characteristics
- **Workload Type**: FillRandom (Sequential Write + Compaction Read)
- **Write Operations**: Sequential Write Only (User Operations)
- **Read Operations**: Compaction Read Only (System Operations)
- **User Reads**: None
- **System Reads**: Compaction Only

## Phase-B Log Analysis
- **Log File**: {self.phase_b_log_path}
- **Log Size**: {os.path.getsize(self.phase_b_log_path) / (1024*1024):.1f} MB
- **Analysis Method**: Direct log parsing with performance extraction

## Phase-C Analysis Results
"""
        
        if 'v4_2_model_accuracy' in self.phase_c_analysis:
            accuracy_data = self.phase_c_analysis['v4_2_model_accuracy']
            report += f"""
### V4.2 Model Accuracy Analysis
- **Overall Accuracy**: {accuracy_data.get('overall_accuracy', 0):.1f}%
- **Model Predictions**: {accuracy_data.get('performance_metrics', {}).get('model_predictions', 0)}
- **Actual QPS**: {accuracy_data.get('performance_metrics', {}).get('actual_qps', 0):.0f}

#### Phase-Specific Accuracy
"""
            for phase_name, data in accuracy_data.get('phase_specific_accuracy', {}).items():
                report += f"- **{phase_name.replace('_', ' ').title()}**: {data['accuracy']:.1f}% (Predicted: {data['predicted_smax']:.0f}, Actual: {data['actual_qps']:.0f})\n"
        
        if 'temporal_performance_comparison' in self.phase_c_analysis:
            temporal_data = self.phase_c_analysis['temporal_performance_comparison']
            report += f"""
### Temporal Performance Comparison
- **Performance Trend**: {temporal_data.get('performance_degradation_patterns', {}).get('performance_trend', 'N/A')}
- **Degradation Rate**: {temporal_data.get('performance_degradation_patterns', {}).get('initial_to_final_degradation', 0):.1f}%
"""
        
        if 'compaction_efficiency_analysis' in self.phase_c_analysis:
            compaction_data = self.phase_c_analysis['compaction_efficiency_analysis']
            report += f"""
### Compaction Efficiency Analysis
- **Efficiency Trend**: {compaction_data.get('efficiency_trends', {}).get('trend', 'N/A')}
- **Efficiency Degradation**: {compaction_data.get('efficiency_trends', {}).get('efficiency_degradation', 0):.1f}%
"""
        
        if 'phase_b_performance' in self.phase_c_analysis:
            phase_b_perf = self.phase_c_analysis['phase_b_performance']
            if 'qps_analysis' in phase_b_perf:
                qps_analysis = phase_b_perf['qps_analysis']
                report += f"""
### Phase-B Performance Metrics
- **Average QPS**: {qps_analysis.get('avg_qps', 0):.0f}
- **Max QPS**: {qps_analysis.get('max_qps', 0):.0f}
- **Min QPS**: {qps_analysis.get('min_qps', 0):.0f}
- **QPS Standard Deviation**: {qps_analysis.get('std_qps', 0):.0f}
- **Total Samples**: {qps_analysis.get('total_samples', 0)}
"""
        
        report += f"""
## Key Insights

### 1. V4.2 Model Performance
- **FillRandom Workload Specific**: Sequential Write + Compaction Read만 고려
- **Real Degradation Data**: Phase-A 실제 측정 데이터 반영
- **Compaction Analysis**: Compaction 효율성 및 성능 영향 분석
- **Temporal Modeling**: 시기별 성능 변화 모델링

### 2. Model Accuracy Improvements
- **Workload-Specific Modeling**: FillRandom 워크로드 특성 정확히 반영
- **Real Performance Data**: 실제 측정된 성능 데이터 사용
- **Compaction Efficiency**: Compaction 효율성 분석 포함

### 3. Phase-C Analysis Results
- **Model Validation**: v4.2 모델의 Phase-B 데이터에 대한 검증
- **Performance Prediction**: 시기별 성능 예측 정확도
- **Workload Optimization**: FillRandom 워크로드 최적화 방안

## Visualization
![Phase-C V4.2 Analysis Corrected](phase_c_v4_2_analysis_corrected.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 Phase-C v4.2 모델 분석 시작 (수정됨)")
        print("=" * 60)
        
        self.analyze_phase_c_with_v4_2_corrected()
        self.create_phase_c_v4_2_visualization_corrected()
        self.save_results()
        
        print("=" * 60)
        print("✅ Phase-C v4.2 모델 분석 완료 (수정됨)!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = Phase_C_V4_2_Analyzer_Corrected()
    analyzer.run_analysis()










