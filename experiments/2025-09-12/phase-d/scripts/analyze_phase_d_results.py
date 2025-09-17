#!/usr/bin/env python3
"""
Phase-D 결과 분석 및 시각화 스크립트
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class PhaseDAnalyzer:
    def __init__(self):
        self.results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        self.data = {}
        
    def load_results(self):
        """Phase-D 결과 데이터 로드"""
        print("📊 Phase-D 결과 데이터 로드 중...")
        
        # 각 결과 파일 로드
        files = {
            'phase_d_report': 'phase_d_report.json',
            'integration_results': 'integration_results.json',
            'performance_report': 'performance_report.json',
            'auto_tuning_records': 'auto_tuning_records.json',
            'real_time_metrics': 'real_time_metrics.json',
            'model_deployment': 'model_deployment.json'
        }
        
        for key, filename in files.items():
            filepath = os.path.join(self.results_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    self.data[key] = json.load(f)
                print(f"✅ {filename} 로드 완료")
            else:
                print(f"❌ {filename} 파일을 찾을 수 없습니다")
        
        print(f"📊 총 {len(self.data)} 개 결과 파일 로드 완료")
    
    def analyze_performance_metrics(self):
        """성능 메트릭 분석"""
        print("📈 성능 메트릭 분석 중...")
        
        if 'integration_results' not in self.data:
            print("❌ 통합 결과 데이터가 없습니다.")
            return
        
        # 데이터프레임 생성
        df = pd.DataFrame(self.data['integration_results'])
        
        # 메트릭 분석
        analysis = {
            'total_loops': len(df),
            'time_span': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            },
            'qps_analysis': {
                'mean': df['metrics'].apply(lambda x: x['qps']).mean(),
                'std': df['metrics'].apply(lambda x: x['qps']).std(),
                'min': df['metrics'].apply(lambda x: x['qps']).min(),
                'max': df['metrics'].apply(lambda x: x['qps']).max(),
                'trend': 'stable' if df['metrics'].apply(lambda x: x['qps']).std() < 200 else 'variable'
            },
            'latency_analysis': {
                'mean': df['metrics'].apply(lambda x: x['latency']).mean(),
                'std': df['metrics'].apply(lambda x: x['latency']).std(),
                'min': df['metrics'].apply(lambda x: x['latency']).min(),
                'max': df['metrics'].apply(lambda x: x['latency']).max(),
                'trend': 'stable' if df['metrics'].apply(lambda x: x['latency']).std() < 0.5 else 'variable'
            },
            'prediction_accuracy': {
                'mean_prediction': df['prediction'].mean(),
                'prediction_std': df['prediction'].std(),
                'prediction_consistency': 'high' if df['prediction'].std() < 1.0 else 'low'
            }
        }
        
        return analysis
    
    def analyze_auto_tuning(self):
        """자동 튜닝 분석"""
        print("🔧 자동 튜닝 분석 중...")
        
        if 'auto_tuning_records' not in self.data:
            print("❌ 자동 튜닝 기록이 없습니다.")
            return
        
        tuning_data = self.data['auto_tuning_records']
        
        analysis = {
            'total_adjustments': len(tuning_data),
            'models_tuned': list(set([record.get('model', 'unknown') for record in tuning_data])),
            'parameter_changes': self._analyze_parameter_changes(tuning_data),
            'tuning_effectiveness': self._assess_tuning_effectiveness(tuning_data)
        }
        
        return analysis
    
    def _analyze_parameter_changes(self, tuning_data):
        """파라미터 변화 분석"""
        if not tuning_data:
            return {}
        
        # 파라미터 변화 추적
        parameter_changes = {}
        
        for record in tuning_data:
            if 'adjusted_parameters' in record:
                for param, value in record['adjusted_parameters'].items():
                    if param not in parameter_changes:
                        parameter_changes[param] = []
                    parameter_changes[param].append(value)
        
        # 변화 통계 계산
        changes_stats = {}
        for param, values in parameter_changes.items():
            changes_stats[param] = {
                'count': len(values),
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'variability': 'high' if np.std(values) > 0.2 else 'low'
            }
        
        return changes_stats
    
    def _assess_tuning_effectiveness(self, tuning_data):
        """튜닝 효과성 평가"""
        if len(tuning_data) < 2:
            return {'status': 'insufficient_data'}
        
        # 성능 개선 추세 분석
        performance_trends = []
        for record in tuning_data:
            if 'performance_data' in record:
                perf_data = record['performance_data']
                if 'accuracy' in perf_data:
                    performance_trends.append(perf_data['accuracy'])
        
        if len(performance_trends) >= 2:
            trend = 'improving' if performance_trends[-1] > performance_trends[0] else 'degrading'
            improvement = performance_trends[-1] - performance_trends[0]
        else:
            trend = 'unknown'
            improvement = 0
        
        return {
            'trend': trend,
            'improvement': improvement,
            'effectiveness': 'high' if improvement > 0.1 else 'moderate' if improvement > 0 else 'low'
        }
    
    def create_visualizations(self):
        """시각화 생성"""
        print("📊 시각화 생성 중...")
        
        if 'integration_results' not in self.data:
            print("❌ 통합 결과 데이터가 없습니다.")
            return
        
        # 데이터 준비
        df = pd.DataFrame(self.data['integration_results'])
        
        # 메트릭 추출
        df['qps'] = df['metrics'].apply(lambda x: x['qps'])
        df['latency'] = df['metrics'].apply(lambda x: x['latency'])
        df['cpu_usage'] = df['metrics'].apply(lambda x: x['cpu_usage'])
        df['memory_usage'] = df['metrics'].apply(lambda x: x['memory_usage'])
        df['io_utilization'] = df['metrics'].apply(lambda x: x['io_utilization'])
        df['compaction_activity'] = df['metrics'].apply(lambda x: x['compaction_activity'])
        
        # 시각화 생성
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Phase-D: Enhanced Models Production Integration Results', fontsize=16, fontweight='bold')
        
        # 1. QPS 트렌드
        axes[0, 0].plot(range(len(df)), df['qps'], marker='o', linewidth=2, markersize=6)
        axes[0, 0].set_title('QPS Trend Over Time')
        axes[0, 0].set_xlabel('Loop Count')
        axes[0, 0].set_ylabel('QPS')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 지연시간 트렌드
        axes[0, 1].plot(range(len(df)), df['latency'], marker='s', color='red', linewidth=2, markersize=6)
        axes[0, 1].set_title('Latency Trend Over Time')
        axes[0, 1].set_xlabel('Loop Count')
        axes[0, 1].set_ylabel('Latency (ms)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 시스템 리소스 사용률
        axes[0, 2].plot(range(len(df)), df['cpu_usage'], marker='o', label='CPU Usage', linewidth=2)
        axes[0, 2].plot(range(len(df)), df['memory_usage'], marker='s', label='Memory Usage', linewidth=2)
        axes[0, 2].set_title('System Resource Usage')
        axes[0, 2].set_xlabel('Loop Count')
        axes[0, 2].set_ylabel('Usage (%)')
        axes[0, 2].legend()
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. I/O 및 컴팩션 활동
        axes[1, 0].plot(range(len(df)), df['io_utilization'], marker='o', label='I/O Utilization', linewidth=2)
        axes[1, 0].plot(range(len(df)), df['compaction_activity'], marker='s', label='Compaction Activity', linewidth=2)
        axes[1, 0].set_title('I/O and Compaction Activity')
        axes[1, 0].set_xlabel('Loop Count')
        axes[1, 0].set_ylabel('Activity (%)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. 예측 vs 실제 성능
        axes[1, 1].plot(range(len(df)), df['qps'], marker='o', label='Actual QPS', linewidth=2)
        axes[1, 1].axhline(y=df['prediction'].iloc[0], color='red', linestyle='--', label=f'Predicted S_max: {df["prediction"].iloc[0]:.1f}')
        axes[1, 1].set_title('Predicted vs Actual Performance')
        axes[1, 1].set_xlabel('Loop Count')
        axes[1, 1].set_ylabel('QPS')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. 성능 분포
        axes[1, 2].hist(df['qps'], bins=10, alpha=0.7, color='skyblue', edgecolor='black')
        axes[1, 2].axvline(df['qps'].mean(), color='red', linestyle='--', label=f'Mean: {df["qps"].mean():.1f}')
        axes[1, 2].set_title('QPS Distribution')
        axes[1, 2].set_xlabel('QPS')
        axes[1, 2].set_ylabel('Frequency')
        axes[1, 2].legend()
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 시각화 저장
        output_file = os.path.join(self.results_dir, 'phase_d_analysis_visualization.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ 시각화 저장: {output_file}")
        
        plt.show()
    
    def generate_comprehensive_report(self):
        """종합 보고서 생성"""
        print("📝 Phase-D 종합 보고서 생성 중...")
        
        # 분석 수행
        performance_analysis = self.analyze_performance_metrics()
        tuning_analysis = self.analyze_auto_tuning()
        
        # 보고서 생성
        report = {
            'phase_d_summary': {
                'phase': 'Phase-D: Enhanced Models Production Integration',
                'execution_time': datetime.now().isoformat(),
                'status': 'completed',
                'objectives_achieved': [
                    'Production Integration',
                    'Real-time Monitoring',
                    'Auto-tuning',
                    'Performance Validation'
                ]
            },
            'performance_analysis': performance_analysis,
            'auto_tuning_analysis': tuning_analysis,
            'key_findings': self._generate_key_findings(performance_analysis, tuning_analysis),
            'recommendations': self._generate_recommendations(performance_analysis, tuning_analysis)
        }
        
        # 보고서 저장
        report_file = os.path.join(self.results_dir, 'phase_d_comprehensive_report.json')
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ 종합 보고서 생성: {report_file}")
        
        return report
    
    def _generate_key_findings(self, performance_analysis, tuning_analysis):
        """주요 발견사항 생성"""
        findings = []
        
        if performance_analysis:
            qps_trend = performance_analysis['qps_analysis']['trend']
            findings.append(f"QPS 성능이 {qps_trend} 상태를 유지했습니다.")
            
            prediction_consistency = performance_analysis['prediction_accuracy']['prediction_consistency']
            findings.append(f"모델 예측의 일관성이 {prediction_consistency} 수준입니다.")
        
        if tuning_analysis:
            total_adjustments = tuning_analysis['total_adjustments']
            findings.append(f"총 {total_adjustments} 회의 자동 파라미터 조정이 수행되었습니다.")
            
            if 'tuning_effectiveness' in tuning_analysis:
                effectiveness = tuning_analysis['tuning_effectiveness']['effectiveness']
                findings.append(f"자동 튜닝의 효과성은 {effectiveness} 수준입니다.")
        
        return findings
    
    def _generate_recommendations(self, performance_analysis, tuning_analysis):
        """권장사항 생성"""
        recommendations = []
        
        if performance_analysis:
            qps_std = performance_analysis['qps_analysis']['std']
            if qps_std > 200:
                recommendations.append("QPS 변동성이 높습니다. 시스템 안정성 개선이 필요합니다.")
            
            latency_std = performance_analysis['latency_analysis']['std']
            if latency_std > 0.5:
                recommendations.append("지연시간 변동성이 높습니다. 성능 최적화가 필요합니다.")
        
        if tuning_analysis and 'parameter_changes' in tuning_analysis:
            high_variability_params = [
                param for param, stats in tuning_analysis['parameter_changes'].items()
                if stats['variability'] == 'high'
            ]
            if high_variability_params:
                recommendations.append(f"다음 파라미터들의 변동성이 높습니다: {', '.join(high_variability_params)}. 튜닝 알고리즘 개선이 필요합니다.")
        
        recommendations.append("프로덕션 환경에서의 장기간 모니터링을 통해 모델 성능을 지속적으로 검증하세요.")
        recommendations.append("실제 워크로드에 대한 모델 적응성을 더욱 향상시키기 위한 추가 연구가 필요합니다.")
        
        return recommendations

def main():
    """Phase-D 결과 분석 메인 실행"""
    print("🔍 Phase-D 결과 분석 시작")
    print("=" * 50)
    
    # 분석기 생성
    analyzer = PhaseDAnalyzer()
    
    # 결과 로드
    analyzer.load_results()
    
    # 시각화 생성
    analyzer.create_visualizations()
    
    # 종합 보고서 생성
    report = analyzer.generate_comprehensive_report()
    
    print("\n" + "=" * 50)
    print("🎉 Phase-D 결과 분석 완료!")
    print("=" * 50)

if __name__ == "__main__":
    main()
