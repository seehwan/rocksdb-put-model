#!/usr/bin/env python3
"""
RocksDB Log Analysis for V4.2 Model Evaluation
v4.2 모델 평가를 위한 RocksDB 로그 분석
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
import re
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class RocksDB_Log_Analyzer_V4_2:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # RocksDB 로그 파일 경로
        self.log_file_path = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/rocksdb_log_phase_b.log'
        
        # 분석 결과
        self.log_analysis = {}
        self.performance_data = {}
        
        print("🚀 RocksDB Log Analysis for V4.2 Model Evaluation 시작")
        print("=" * 70)
    
    def parse_rocksdb_log(self):
        """RocksDB 로그 파싱"""
        print("📊 RocksDB 로그 파싱 중...")
        
        if not os.path.exists(self.log_file_path):
            print(f"⚠️ 로그 파일이 없습니다: {self.log_file_path}")
            return None
        
        log_data = {
            'timestamps': [],
            'put_rates': [],
            'flush_events': [],
            'compaction_events': [],
            'level_stats': [],
            'performance_metrics': []
        }
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num % 10000 == 0:
                        print(f"   처리 중: {line_num:,} 라인")
                    
                    # 타임스탬프 추출
                    timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d{6})', line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        log_data['timestamps'].append(timestamp)
                    
                    # Put rate 추출
                    put_rate_match = re.search(r'put_rate: ([\d.]+)', line)
                    if put_rate_match:
                        put_rate = float(put_rate_match.group(1))
                        log_data['put_rates'].append({
                            'timestamp': timestamp if 'timestamp' in locals() else None,
                            'put_rate': put_rate
                        })
                    
                    # Flush 이벤트 추출
                    if 'flush_started' in line or 'flush_finished' in line:
                        flush_data = self._parse_flush_event(line, timestamp if 'timestamp' in locals() else None)
                        if flush_data:
                            log_data['flush_events'].append(flush_data)
                    
                    # Compaction 이벤트 추출
                    if 'compaction_started' in line or 'compaction_finished' in line:
                        compaction_data = self._parse_compaction_event(line, timestamp if 'timestamp' in locals() else None)
                        if compaction_data:
                            log_data['compaction_events'].append(compaction_data)
                    
                    # Level 통계 추출
                    if 'level' in line and 'files' in line:
                        level_data = self._parse_level_stats(line, timestamp if 'timestamp' in locals() else None)
                        if level_data:
                            log_data['level_stats'].append(level_data)
            
            print(f"✅ RocksDB 로그 파싱 완료:")
            print(f"   - 타임스탬프: {len(log_data['timestamps']):,}개")
            print(f"   - Put rates: {len(log_data['put_rates']):,}개")
            print(f"   - Flush 이벤트: {len(log_data['flush_events']):,}개")
            print(f"   - Compaction 이벤트: {len(log_data['compaction_events']):,}개")
            print(f"   - Level 통계: {len(log_data['level_stats']):,}개")
            
            return log_data
            
        except Exception as e:
            print(f"⚠️ 로그 파싱 실패: {e}")
            return None
    
    def _parse_flush_event(self, line, timestamp):
        """Flush 이벤트 파싱"""
        try:
            if 'flush_started' in line:
                # flush_started 이벤트 파싱
                match = re.search(r'flush_started: (\d+)', line)
                if match:
                    return {
                        'event_type': 'flush_started',
                        'timestamp': timestamp,
                        'memtable_id': int(match.group(1))
                    }
            elif 'flush_finished' in line:
                # flush_finished 이벤트 파싱
                match = re.search(r'flush_finished: (\d+)', line)
                if match:
                    return {
                        'event_type': 'flush_finished',
                        'timestamp': timestamp,
                        'memtable_id': int(match.group(1))
                    }
        except Exception as e:
            pass
        return None
    
    def _parse_compaction_event(self, line, timestamp):
        """Compaction 이벤트 파싱"""
        try:
            if 'compaction_started' in line:
                # compaction_started 이벤트 파싱
                match = re.search(r'compaction_started: level=(\d+)', line)
                if match:
                    return {
                        'event_type': 'compaction_started',
                        'timestamp': timestamp,
                        'level': int(match.group(1))
                    }
            elif 'compaction_finished' in line:
                # compaction_finished 이벤트 파싱
                match = re.search(r'compaction_finished: level=(\d+)', line)
                if match:
                    return {
                        'event_type': 'compaction_finished',
                        'timestamp': timestamp,
                        'level': int(match.group(1))
                    }
        except Exception as e:
            pass
        return None
    
    def _parse_level_stats(self, line, timestamp):
        """Level 통계 파싱"""
        try:
            # Level 통계 파싱 (간단한 예시)
            match = re.search(r'level (\d+): (\d+) files', line)
            if match:
                return {
                    'timestamp': timestamp,
                    'level': int(match.group(1)),
                    'files': int(match.group(2))
                }
        except Exception as e:
            pass
        return None
    
    def analyze_temporal_performance(self, log_data):
        """시기별 성능 분석"""
        print("📊 시기별 성능 분석 중...")
        
        if not log_data or not log_data['put_rates']:
            print("⚠️ Put rate 데이터가 없습니다.")
            return None
        
        # Put rate 데이터를 시간순으로 정렬
        put_rates = sorted(log_data['put_rates'], key=lambda x: x['timestamp'] if x['timestamp'] else '')
        
        # 전체 기간을 3개 구간으로 나누기
        total_periods = len(put_rates)
        initial_period = total_periods // 3
        middle_period = (total_periods * 2) // 3
        
        # 시기별 성능 분석
        temporal_performance = {
            'initial_phase': {
                'period': '0-33%',
                'data_points': put_rates[:initial_period],
                'avg_put_rate': 0,
                'max_put_rate': 0,
                'min_put_rate': 0,
                'std_put_rate': 0
            },
            'middle_phase': {
                'period': '33-66%',
                'data_points': put_rates[initial_period:middle_period],
                'avg_put_rate': 0,
                'max_put_rate': 0,
                'min_put_rate': 0,
                'std_put_rate': 0
            },
            'final_phase': {
                'period': '66-100%',
                'data_points': put_rates[middle_period:],
                'avg_put_rate': 0,
                'min_put_rate': 0,
                'std_put_rate': 0
            }
        }
        
        # 각 시기별 통계 계산
        for phase_name, phase_data in temporal_performance.items():
            if phase_data['data_points']:
                put_rates_values = [point['put_rate'] for point in phase_data['data_points']]
                phase_data['avg_put_rate'] = np.mean(put_rates_values)
                phase_data['max_put_rate'] = np.max(put_rates_values)
                phase_data['min_put_rate'] = np.min(put_rates_values)
                phase_data['std_put_rate'] = np.std(put_rates_values)
                
                print(f"   {phase_name}: {phase_data['avg_put_rate']:.2f} ops/sec (avg)")
        
        return temporal_performance
    
    def analyze_compaction_performance(self, log_data):
        """Compaction 성능 분석"""
        print("📊 Compaction 성능 분석 중...")
        
        if not log_data or not log_data['compaction_events']:
            print("⚠️ Compaction 이벤트 데이터가 없습니다.")
            return None
        
        # Compaction 이벤트 분석
        compaction_analysis = {
            'total_compactions': len(log_data['compaction_events']),
            'compaction_by_level': {},
            'compaction_timeline': [],
            'compaction_efficiency': {}
        }
        
        # Level별 Compaction 통계
        for event in log_data['compaction_events']:
            if 'level' in event:
                level = event['level']
                if level not in compaction_analysis['compaction_by_level']:
                    compaction_analysis['compaction_by_level'][level] = 0
                compaction_analysis['compaction_by_level'][level] += 1
        
        print(f"   총 Compaction 이벤트: {compaction_analysis['total_compactions']:,}개")
        for level, count in compaction_analysis['compaction_by_level'].items():
            print(f"   Level {level}: {count:,}개")
        
        return compaction_analysis
    
    def analyze_flush_performance(self, log_data):
        """Flush 성능 분석"""
        print("📊 Flush 성능 분석 중...")
        
        if not log_data or not log_data['flush_events']:
            print("⚠️ Flush 이벤트 데이터가 없습니다.")
            return None
        
        # Flush 이벤트 분석
        flush_analysis = {
            'total_flushes': len(log_data['flush_events']),
            'flush_timeline': [],
            'flush_efficiency': {}
        }
        
        print(f"   총 Flush 이벤트: {flush_analysis['total_flushes']:,}개")
        
        return flush_analysis
    
    def evaluate_v4_2_model_with_log_data(self, temporal_performance):
        """로그 데이터를 사용한 v4.2 모델 평가"""
        print("📊 로그 데이터를 사용한 v4.2 모델 평가 중...")
        
        # v4.2 모델 결과 로드
        v4_2_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/scripts/results/v4_2_fillrandom_enhanced_model_results.json'
        
        if not os.path.exists(v4_2_file):
            print("⚠️ v4.2 모델 결과 파일이 없습니다.")
            return None
        
        try:
            with open(v4_2_file, 'r') as f:
                v4_2_results = json.load(f)
        except Exception as e:
            print(f"⚠️ v4.2 모델 결과 로드 실패: {e}")
            return None
        
        # v4.2 모델 예측값
        v4_2_predictions = v4_2_results.get('v4_2_predictions', {})
        device_envelope = v4_2_predictions.get('device_envelope_temporal', {})
        
        # 로그 데이터와 모델 예측 비교
        model_evaluation = {
            'phase_comparison': {},
            'accuracy_analysis': {},
            'performance_trends': {}
        }
        
        for phase_name, phase_data in temporal_performance.items():
            actual_avg_rate = phase_data['avg_put_rate']
            model_prediction = device_envelope.get(phase_name, {}).get('s_max', 0)
            
            # 정확도 계산
            if actual_avg_rate > 0 and model_prediction > 0:
                accuracy = min(100.0, (1.0 - abs(model_prediction - actual_avg_rate) / actual_avg_rate) * 100)
            else:
                accuracy = 0.0
            
            model_evaluation['phase_comparison'][phase_name] = {
                'actual_avg_rate': actual_avg_rate,
                'model_prediction': model_prediction,
                'accuracy': accuracy,
                'difference': abs(model_prediction - actual_avg_rate),
                'relative_error': abs(model_prediction - actual_avg_rate) / actual_avg_rate * 100 if actual_avg_rate > 0 else 0
            }
            
            print(f"   {phase_name}:")
            print(f"     실제 평균: {actual_avg_rate:.2f} ops/sec")
            print(f"     모델 예측: {model_prediction:.2f} ops/sec")
            print(f"     정확도: {accuracy:.1f}%")
        
        # 전체 정확도 계산
        accuracies = [data['accuracy'] for data in model_evaluation['phase_comparison'].values()]
        model_evaluation['accuracy_analysis'] = {
            'overall_accuracy': np.mean(accuracies) if accuracies else 0.0,
            'accuracy_by_phase': {phase: data['accuracy'] for phase, data in model_evaluation['phase_comparison'].items()},
            'best_phase': max(model_evaluation['phase_comparison'].items(), key=lambda x: x[1]['accuracy'])[0] if model_evaluation['phase_comparison'] else None,
            'worst_phase': min(model_evaluation['phase_comparison'].items(), key=lambda x: x[1]['accuracy'])[0] if model_evaluation['phase_comparison'] else None
        }
        
        print(f"✅ 로그 데이터 기반 v4.2 모델 평가 완료:")
        print(f"   전체 정확도: {model_evaluation['accuracy_analysis']['overall_accuracy']:.1f}%")
        
        return model_evaluation
    
    def create_log_analysis_visualization(self, temporal_performance, model_evaluation):
        """로그 분석 시각화 생성"""
        print("📊 로그 분석 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('RocksDB Log Analysis for V4.2 Model Evaluation', fontsize=16, fontweight='bold')
        
        # 1. 시기별 실제 성능
        if temporal_performance:
            phases = list(temporal_performance.keys())
            avg_rates = [phase_data['avg_put_rate'] for phase_data in temporal_performance.values()]
            max_rates = [phase_data['max_put_rate'] for phase_data in temporal_performance.values()]
            min_rates = [phase_data['min_put_rate'] for phase_data in temporal_performance.values()]
            
            x = np.arange(len(phases))
            width = 0.25
            
            ax1.bar(x - width, avg_rates, width, label='Average', color='skyblue', alpha=0.7)
            ax1.bar(x, max_rates, width, label='Maximum', color='lightgreen', alpha=0.7)
            ax1.bar(x + width, min_rates, width, label='Minimum', color='lightcoral', alpha=0.7)
            
            ax1.set_ylabel('Put Rate (ops/sec)')
            ax1.set_title('Actual Performance by Phase (from RocksDB Log)')
            ax1.set_xticks(x)
            ax1.set_xticklabels([p.replace('_phase', '').title() for p in phases])
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # 2. 모델 예측 vs 실제 성능
        if model_evaluation and 'phase_comparison' in model_evaluation:
            phases = list(model_evaluation['phase_comparison'].keys())
            actual_rates = [data['actual_avg_rate'] for data in model_evaluation['phase_comparison'].values()]
            predicted_rates = [data['model_prediction'] for data in model_evaluation['phase_comparison'].values()]
            
            x = np.arange(len(phases))
            width = 0.35
            
            bars1 = ax2.bar(x - width/2, actual_rates, width, label='Actual (Log)', color='lightblue', alpha=0.7)
            bars2 = ax2.bar(x + width/2, predicted_rates, width, label='Predicted (V4.2)', color='lightcoral', alpha=0.7)
            
            ax2.set_ylabel('Put Rate (ops/sec)')
            ax2.set_title('V4.2 Model Prediction vs Actual Performance')
            ax2.set_xticks(x)
            ax2.set_xticklabels([p.replace('_phase', '').title() for p in phases])
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # 정확도 표시
            for i, (actual, predicted) in enumerate(zip(actual_rates, predicted_rates)):
                accuracy = model_evaluation['phase_comparison'][phases[i]]['accuracy']
                ax2.text(i, max(actual, predicted) + 0.1 * max(actual, predicted),
                        f'{accuracy:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # 3. 정확도 분석
        if model_evaluation and 'accuracy_analysis' in model_evaluation:
            accuracy_data = model_evaluation['accuracy_analysis']
            phase_accuracies = accuracy_data.get('accuracy_by_phase', {})
            
            if phase_accuracies:
                phases = list(phase_accuracies.keys())
                accuracies = list(phase_accuracies.values())
                
                colors = ['green' if acc > 80 else 'orange' if acc > 60 else 'red' for acc in accuracies]
                bars = ax3.bar([p.replace('_phase', '').title() for p in phases], accuracies, color=colors, alpha=0.7)
                ax3.set_ylabel('Accuracy (%)')
                ax3.set_title('V4.2 Model Accuracy by Phase (Log-based)')
                ax3.set_ylim(0, 100)
                ax3.grid(True, alpha=0.3)
                
                for bar, accuracy in zip(bars, accuracies):
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height,
                            f'{accuracy:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 4. 평가 요약
        if model_evaluation and 'accuracy_analysis' in model_evaluation:
            accuracy_data = model_evaluation['accuracy_analysis']
            
            ax4.text(0.1, 0.9, 'V4.2 Model Evaluation Summary (Log-based):', fontsize=14, fontweight='bold', transform=ax4.transAxes)
            
            overall_accuracy = accuracy_data.get('overall_accuracy', 0)
            ax4.text(0.1, 0.8, f'Overall Accuracy: {overall_accuracy:.1f}%', fontsize=12, transform=ax4.transAxes)
            
            best_phase = accuracy_data.get('best_phase', 'N/A')
            worst_phase = accuracy_data.get('worst_phase', 'N/A')
            ax4.text(0.1, 0.7, f'Best Phase: {best_phase.replace("_", " ").title()}', fontsize=10, transform=ax4.transAxes)
            ax4.text(0.1, 0.65, f'Worst Phase: {worst_phase.replace("_", " ").title()}', fontsize=10, transform=ax4.transAxes)
            
            # 시기별 정확도
            phase_accuracies = accuracy_data.get('accuracy_by_phase', {})
            y_pos = 0.55
            for phase, accuracy in phase_accuracies.items():
                ax4.text(0.1, y_pos, f'{phase.replace("_", " ").title()}: {accuracy:.1f}%', fontsize=10, transform=ax4.transAxes)
                y_pos -= 0.05
            
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.set_title('Evaluation Summary')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/rocksdb_log_analysis_v4_2_evaluation.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 로그 분석 시각화 완료")
    
    def save_results(self, log_data, temporal_performance, model_evaluation):
        """결과 저장"""
        print("💾 로그 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            results = {
                'log_analysis': log_data,
                'temporal_performance': temporal_performance,
                'model_evaluation': model_evaluation,
                'analysis_time': datetime.now().isoformat()
            }
            
            with open(f"{self.results_dir}/rocksdb_log_analysis_v4_2_evaluation_results.json", 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_log_analysis_report(temporal_performance, model_evaluation)
            with open(f"{self.results_dir}/rocksdb_log_analysis_v4_2_evaluation_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_log_analysis_report(self, temporal_performance, model_evaluation):
        """로그 분석 보고서 생성"""
        report = f"""# RocksDB Log Analysis for V4.2 Model Evaluation

## Overview
This report presents the analysis of RocksDB log data to evaluate the V4.2 FillRandom Enhanced model with actual performance data from the log.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## RocksDB Log Analysis Results

### Temporal Performance Analysis (from Log Data)
"""
        
        if temporal_performance:
            for phase_name, phase_data in temporal_performance.items():
                report += f"""
#### {phase_name.replace('_', ' ').title()} Phase
- **Period**: {phase_data['period']}
- **Data Points**: {len(phase_data['data_points']):,}
- **Average Put Rate**: {phase_data['avg_put_rate']:.2f} ops/sec
- **Maximum Put Rate**: {phase_data['max_put_rate']:.2f} ops/sec
- **Minimum Put Rate**: {phase_data['min_put_rate']:.2f} ops/sec
- **Standard Deviation**: {phase_data['std_put_rate']:.2f} ops/sec
"""
        
        if model_evaluation:
            report += f"""
### V4.2 Model Evaluation (Log-based)

#### Overall Accuracy
- **Overall Accuracy**: {model_evaluation.get('accuracy_analysis', {}).get('overall_accuracy', 0):.1f}%
- **Best Phase**: {model_evaluation.get('accuracy_analysis', {}).get('best_phase', 'N/A').replace('_', ' ').title()}
- **Worst Phase**: {model_evaluation.get('accuracy_analysis', {}).get('worst_phase', 'N/A').replace('_', ' ').title()}

#### Phase-specific Comparison
"""
            for phase_name, phase_data in model_evaluation.get('phase_comparison', {}).items():
                report += f"""
##### {phase_name.replace('_', ' ').title()} Phase
- **Actual Average Rate**: {phase_data['actual_avg_rate']:.2f} ops/sec
- **Model Prediction**: {phase_data['model_prediction']:.2f} ops/sec
- **Accuracy**: {phase_data['accuracy']:.1f}%
- **Difference**: {phase_data['difference']:.2f} ops/sec
- **Relative Error**: {phase_data['relative_error']:.1f}%
"""
        
        report += f"""
## Key Insights

### 1. Log-based Performance Analysis
- **Data Source**: RocksDB log file analysis
- **Temporal Phases**: Initial, Middle, Final phases identified
- **Performance Metrics**: Put rates, Flush events, Compaction events
- **Accuracy**: Based on actual log data rather than summary statistics

### 2. V4.2 Model Evaluation
- **Evaluation Method**: Log-based performance comparison
- **Accuracy Calculation**: Direct comparison with actual log data
- **Phase Analysis**: Phase-specific accuracy assessment
- **Performance Trends**: Temporal performance trend analysis

### 3. Model Accuracy Insights
- **Log-based Accuracy**: More accurate than summary-based evaluation
- **Phase-specific Performance**: Detailed phase-by-phase analysis
- **Real Performance Data**: Actual RocksDB performance from logs
- **Temporal Trends**: Performance changes over time

## Visualization
![RocksDB Log Analysis for V4.2 Evaluation](rocksdb_log_analysis_v4_2_evaluation.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 RocksDB 로그 분석 시작")
        print("=" * 70)
        
        # 1. RocksDB 로그 파싱
        log_data = self.parse_rocksdb_log()
        if not log_data:
            print("⚠️ 로그 파싱 실패")
            return
        
        # 2. 시기별 성능 분석
        temporal_performance = self.analyze_temporal_performance(log_data)
        if not temporal_performance:
            print("⚠️ 시기별 성능 분석 실패")
            return
        
        # 3. Compaction 성능 분석
        compaction_analysis = self.analyze_compaction_performance(log_data)
        
        # 4. Flush 성능 분석
        flush_analysis = self.analyze_flush_performance(log_data)
        
        # 5. v4.2 모델 평가
        model_evaluation = self.evaluate_v4_2_model_with_log_data(temporal_performance)
        if not model_evaluation:
            print("⚠️ v4.2 모델 평가 실패")
            return
        
        # 6. 시각화 생성
        self.create_log_analysis_visualization(temporal_performance, model_evaluation)
        
        # 7. 결과 저장
        self.save_results(log_data, temporal_performance, model_evaluation)
        
        print("=" * 70)
        print("✅ RocksDB 로그 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = RocksDB_Log_Analyzer_V4_2()
    analyzer.run_analysis()

