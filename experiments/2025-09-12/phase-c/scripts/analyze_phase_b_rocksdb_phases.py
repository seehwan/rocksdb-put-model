#!/usr/bin/env python3
"""
Phase-B RocksDB Phases Analysis
Phase-B RocksDB 동작 특성 기반 구간 분석
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
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class Phase_B_RocksDB_Phases_Analyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-B 데이터 로드
        self.phase_b_data = self._load_phase_b_data()
        
        # 분석 결과
        self.analysis_results = {}
        
        print("🚀 Phase-B RocksDB Phases Analysis 시작")
        print("=" * 60)
    
    def _load_phase_b_data(self):
        """Phase-B 데이터 로드"""
        print("📊 Phase-B 데이터 로드 중...")
        
        phase_b_data = {}
        
        # Phase-B FillRandom 결과 데이터
        phase_b_fillrandom_path = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/fillrandom_results.json'
        if os.path.exists(phase_b_fillrandom_path):
            try:
                df = pd.read_csv(phase_b_fillrandom_path)
                phase_b_data['fillrandom_results'] = {
                    'dataframe': df,
                    'avg_qps': df['interval_qps'].mean(),
                    'max_qps': df['interval_qps'].max(),
                    'min_qps': df['interval_qps'].min(),
                    'std_qps': df['interval_qps'].std(),
                    'total_samples': len(df)
                }
                print("✅ Phase-B FillRandom 결과 데이터 로드 완료")
                return phase_b_data
            except Exception as e:
                print(f"⚠️ Phase-B FillRandom 결과 데이터 로드 실패: {e}")
                return None
        else:
            print("⚠️ Phase-B FillRandom 결과 파일 없음")
            return None
    
    def analyze_rocksdb_phases(self):
        """RocksDB 동작 특성 기반 구간 분석"""
        print("📊 RocksDB 동작 특성 기반 구간 분석 중...")
        
        if not self.phase_b_data or 'fillrandom_results' not in self.phase_b_data:
            print("⚠️ Phase-B 데이터가 없습니다.")
            return None
        
        df = self.phase_b_data['fillrandom_results']['dataframe']
        
        # 1. 성능 변화율 분석
        performance_changes = self._analyze_performance_changes(df)
        
        # 2. RocksDB 동작 특성 기반 구간 분할
        rocksdb_phases = self._create_rocksdb_phases(df, performance_changes)
        
        # 3. 구간별 특성 분석
        phase_characteristics = self._analyze_phase_characteristics(df, rocksdb_phases)
        
        # 4. 성능 트렌드 분석
        performance_trends = self._analyze_performance_trends(df, rocksdb_phases)
        
        self.analysis_results = {
            'performance_changes': performance_changes,
            'rocksdb_phases': rocksdb_phases,
            'phase_characteristics': phase_characteristics,
            'performance_trends': performance_trends
        }
        
        print("✅ RocksDB 동작 특성 기반 구간 분석 완료")
        return self.analysis_results
    
    def _analyze_performance_changes(self, df):
        """성능 변화율 분석"""
        print("📊 성능 변화율 분석 중...")
        
        # 이동 평균 계산 (100개 샘플 윈도우)
        window_size = 100
        df['rolling_mean'] = df['interval_qps'].rolling(window=window_size, center=True).mean()
        df['rolling_std'] = df['interval_qps'].rolling(window=window_size, center=True).std()
        
        # 변화율 계산
        df['qps_change'] = df['interval_qps'].diff()
        df['qps_change_pct'] = df['interval_qps'].pct_change() * 100
        
        # 변화율 통계
        change_stats = {
            'mean_change': df['qps_change'].mean(),
            'std_change': df['qps_change'].std(),
            'mean_change_pct': df['qps_change_pct'].mean(),
            'std_change_pct': df['qps_change_pct'].std(),
            'max_increase': df['qps_change'].max(),
            'max_decrease': df['qps_change'].min(),
            'max_increase_pct': df['qps_change_pct'].max(),
            'max_decrease_pct': df['qps_change_pct'].min()
        }
        
        print(f"   평균 변화율: {change_stats['mean_change_pct']:.2f}%")
        print(f"   변화율 표준편차: {change_stats['std_change_pct']:.2f}%")
        
        return {
            'change_stats': change_stats,
            'dataframe': df
        }
    
    def _create_rocksdb_phases(self, df, performance_changes):
        """RocksDB 동작 특성 기반 구간 생성"""
        print("📊 RocksDB 동작 특성 기반 구간 생성 중...")
        
        # 1. 초기 구간: 빈 DB에서 빠르게 성능이 변하는 구간
        # - 성능 변화율이 큰 구간
        # - 초기 10% 구간에서 성능 변화가 큰 부분
        initial_phase_end = self._find_initial_phase_end(df)
        
        # 2. 후기 구간: 안정화 구간
        # - 성능이 안정된 구간
        # - 마지막 20% 구간에서 성능이 안정된 부분
        final_phase_start = self._find_final_phase_start(df)
        
        # 3. 중기 구간: 컴팩션이 진행되며 안정화되어 가는 구간
        # - 초기와 후기 사이의 구간
        middle_phase_start = initial_phase_end
        middle_phase_end = final_phase_start
        
        # 구간 정의
        rocksdb_phases = {
            'initial_phase': {
                'start': 0,
                'end': initial_phase_end,
                'type': 'initial_loading',
                'description': '빈 DB에서 빠르게 성능이 변하는 구간'
            },
            'middle_phase': {
                'start': middle_phase_start,
                'end': middle_phase_end,
                'type': 'compaction_active',
                'description': '컴팩션이 진행되며 안정화되어 가는 구간'
            },
            'final_phase': {
                'start': final_phase_start,
                'end': len(df),
                'type': 'stabilized',
                'description': '안정화 구간'
            }
        }
        
        print(f"   초기 구간: 0-{initial_phase_end} ({initial_phase_end:,} 샘플)")
        print(f"   중기 구간: {middle_phase_start}-{middle_phase_end} ({middle_phase_end - middle_phase_start:,} 샘플)")
        print(f"   후기 구간: {final_phase_start}-{len(df)} ({len(df) - final_phase_start:,} 샘플)")
        
        return rocksdb_phases
    
    def _find_initial_phase_end(self, df):
        """초기 구간 끝점 찾기"""
        # 초기 20% 구간에서 성능 변화가 큰 지점 찾기
        initial_20_percent = int(len(df) * 0.2)
        initial_data = df.iloc[:initial_20_percent]
        
        # 성능 변화율이 큰 지점들 찾기
        change_threshold = initial_data['interval_qps'].std() * 2
        large_changes = initial_data[abs(initial_data['interval_qps'].diff()) > change_threshold]
        
        if len(large_changes) > 0:
            # 마지막 큰 변화 지점을 초기 구간 끝으로 설정
            initial_phase_end = large_changes.index[-1]
        else:
            # 큰 변화가 없으면 초기 10% 지점
            initial_phase_end = int(len(df) * 0.1)
        
        return initial_phase_end
    
    def _find_final_phase_start(self, df):
        """후기 구간 시작점 찾기"""
        # 마지막 30% 구간에서 성능이 안정된 지점 찾기
        final_30_percent_start = int(len(df) * 0.7)
        final_data = df.iloc[final_30_percent_start:]
        
        # 성능이 안정된 지점 찾기 (변화율이 작은 구간)
        stability_window = 1000  # 1000 샘플 윈도우
        if len(final_data) > stability_window:
            # 이동 표준편차가 작은 구간 찾기
            rolling_std = final_data['interval_qps'].rolling(window=stability_window).std()
            min_std_idx = rolling_std.idxmin()
            final_phase_start = min_std_idx
        else:
            # 데이터가 부족하면 마지막 20% 지점
            final_phase_start = int(len(df) * 0.8)
        
        return final_phase_start
    
    def _analyze_phase_characteristics(self, df, rocksdb_phases):
        """구간별 특성 분석"""
        print("📊 구간별 특성 분석 중...")
        
        phase_characteristics = {}
        
        for phase_name, phase_info in rocksdb_phases.items():
            start_idx = phase_info['start']
            end_idx = phase_info['end']
            
            # 구간 데이터 추출
            phase_data = df.iloc[start_idx:end_idx]['interval_qps']
            
            # 구간별 통계
            characteristics = {
                'sample_count': len(phase_data),
                'avg_qps': phase_data.mean(),
                'max_qps': phase_data.max(),
                'min_qps': phase_data.min(),
                'std_qps': phase_data.std(),
                'median_qps': phase_data.median(),
                'q25': phase_data.quantile(0.25),
                'q75': phase_data.quantile(0.75),
                'cv': phase_data.std() / phase_data.mean() if phase_data.mean() > 0 else 0,
                'trend': self._calculate_trend(phase_data),
                'stability': self._calculate_stability(phase_data),
                'phase_type': phase_info['type'],
                'description': phase_info['description']
            }
            
            phase_characteristics[phase_name] = characteristics
            
            print(f"   {phase_name}:")
            print(f"     샘플 수: {characteristics['sample_count']:,}")
            print(f"     평균 QPS: {characteristics['avg_qps']:.2f}")
            print(f"     최대 QPS: {characteristics['max_qps']:.2f}")
            print(f"     최소 QPS: {characteristics['min_qps']:.2f}")
            print(f"     표준편차: {characteristics['std_qps']:.2f}")
            print(f"     변동계수: {characteristics['cv']:.3f}")
            print(f"     트렌드: {characteristics['trend']}")
            print(f"     안정성: {characteristics['stability']}")
        
        return phase_characteristics
    
    def _calculate_trend(self, data):
        """데이터 트렌드 계산"""
        if len(data) < 2:
            return 'insufficient_data'
        
        # 선형 회귀를 사용한 트렌드 계산
        x = np.arange(len(data))
        y = data.values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        if abs(slope) < std_err:
            return 'stable'
        elif slope > 0:
            return 'increasing'
        else:
            return 'decreasing'
    
    def _calculate_stability(self, data):
        """데이터 안정성 계산"""
        if len(data) < 10:
            return 'insufficient_data'
        
        # 변동계수 기반 안정성 평가
        cv = data.std() / data.mean() if data.mean() > 0 else 0
        
        if cv < 0.1:
            return 'very_stable'
        elif cv < 0.3:
            return 'stable'
        elif cv < 0.5:
            return 'moderate'
        else:
            return 'unstable'
    
    def _analyze_performance_trends(self, df, rocksdb_phases):
        """성능 트렌드 분석"""
        print("📊 성능 트렌드 분석 중...")
        
        trends = {
            'overall_trend': 'decreasing',
            'phase_transitions': [],
            'performance_degradation': {},
            'stability_analysis': {}
        }
        
        # 전체 트렌드 분석
        overall_slope, _, _, _, _ = stats.linregress(range(len(df)), df['interval_qps'])
        trends['overall_trend'] = 'decreasing' if overall_slope < 0 else 'increasing'
        
        # 구간 간 전환 분석
        phase_names = list(rocksdb_phases.keys())
        for i in range(len(phase_names) - 1):
            current_phase = phase_names[i]
            next_phase = phase_names[i + 1]
            
            current_end = rocksdb_phases[current_phase]['end']
            next_start = rocksdb_phases[next_phase]['start']
            
            # 전환 구간의 성능 변화
            transition_data = df.iloc[current_end-100:next_start+100]['interval_qps']
            if len(transition_data) > 0:
                transition_slope, _, _, _, _ = stats.linregress(range(len(transition_data)), transition_data)
                
                trends['phase_transitions'].append({
                    'from_phase': current_phase,
                    'to_phase': next_phase,
                    'transition_slope': transition_slope,
                    'transition_type': 'decreasing' if transition_slope < 0 else 'increasing'
                })
        
        # 성능 열화 분석
        if len(phase_names) >= 2:
            first_phase = phase_names[0]
            last_phase = phase_names[-1]
            
            first_avg = df.iloc[rocksdb_phases[first_phase]['start']:rocksdb_phases[first_phase]['end']]['interval_qps'].mean()
            last_avg = df.iloc[rocksdb_phases[last_phase]['start']:rocksdb_phases[last_phase]['end']]['interval_qps'].mean()
            
            degradation = ((first_avg - last_avg) / first_avg) * 100 if first_avg > 0 else 0
            
            trends['performance_degradation'] = {
                'first_phase_avg': first_avg,
                'last_phase_avg': last_avg,
                'degradation_percent': degradation
            }
        
        print(f"   전체 트렌드: {trends['overall_trend']}")
        print(f"   구간 전환: {len(trends['phase_transitions'])}개")
        if trends['performance_degradation']:
            print(f"   성능 열화: {trends['performance_degradation']['degradation_percent']:.1f}%")
        
        return trends
    
    def create_rocksdb_phases_visualization(self):
        """RocksDB 구간 시각화 생성"""
        print("📊 RocksDB 구간 시각화 생성 중...")
        
        if not self.analysis_results:
            print("⚠️ 분석 결과가 없습니다.")
            return
        
        df = self.phase_b_data['fillrandom_results']['dataframe']
        rocksdb_phases = self.analysis_results['rocksdb_phases']
        phase_characteristics = self.analysis_results['phase_characteristics']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('Phase-B RocksDB Phases Analysis', fontsize=16, fontweight='bold')
        
        # 1. 전체 성능 곡선과 RocksDB 구간
        ax1.plot(df.index, df['interval_qps'], alpha=0.6, color='lightblue', label='QPS')
        
        # 구간별 평균선 표시
        colors = ['red', 'green', 'blue']
        for i, (phase_name, phase_info) in enumerate(rocksdb_phases.items()):
            start_idx = phase_info['start']
            end_idx = phase_info['end']
            avg_qps = phase_characteristics[phase_name]['avg_qps']
            
            ax1.axvspan(start_idx, end_idx, alpha=0.2, color=colors[i])
            ax1.axhline(y=avg_qps, xmin=start_idx/len(df), xmax=end_idx/len(df), 
                      color=colors[i], linewidth=2, 
                      label=f'{phase_name.replace("_", " ").title()}: {avg_qps:.0f}')
        
        ax1.set_xlabel('Sample Index')
        ax1.set_ylabel('QPS (ops/sec)')
        ax1.set_title('Performance Curve with RocksDB Phases')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 구간별 성능 통계
        phase_names = list(rocksdb_phases.keys())
        avg_qps = [phase_characteristics[phase]['avg_qps'] for phase in phase_names]
        max_qps = [phase_characteristics[phase]['max_qps'] for phase in phase_names]
        min_qps = [phase_characteristics[phase]['min_qps'] for phase in phase_names]
        
        x = np.arange(len(phase_names))
        width = 0.25
        
        ax2.bar(x - width, avg_qps, width, label='Average', color='skyblue', alpha=0.7)
        ax2.bar(x, max_qps, width, label='Maximum', color='lightgreen', alpha=0.7)
        ax2.bar(x + width, min_qps, width, label='Minimum', color='lightcoral', alpha=0.7)
        
        ax2.set_ylabel('QPS (ops/sec)')
        ax2.set_title('Performance Statistics by RocksDB Phase')
        ax2.set_xticks(x)
        ax2.set_xticklabels([p.replace('_', ' ').title() for p in phase_names])
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 구간별 안정성 분석
        cv_values = [phase_characteristics[phase]['cv'] for phase in phase_names]
        stability_values = [self._stability_to_numeric(phase_characteristics[phase]['stability']) for phase in phase_names]
        
        ax3.bar(x - width/2, cv_values, width, label='Coefficient of Variation', color='orange', alpha=0.7)
        ax3.bar(x + width/2, stability_values, width, label='Stability Score', color='purple', alpha=0.7)
        
        ax3.set_ylabel('Stability Metrics')
        ax3.set_title('Performance Stability by RocksDB Phase')
        ax3.set_xticks(x)
        ax3.set_xticklabels([p.replace('_', ' ').title() for p in phase_names])
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 구간별 특성 요약
        trends = self.analysis_results['performance_trends']
        
        ax4.text(0.1, 0.9, 'RocksDB Phases Analysis Summary:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.8, f'Overall Trend: {trends["overall_trend"]}', fontsize=12, transform=ax4.transAxes)
        
        if trends['performance_degradation']:
            degradation = trends['performance_degradation']['degradation_percent']
            ax4.text(0.1, 0.7, f'Performance Degradation: {degradation:.1f}%', fontsize=12, transform=ax4.transAxes)
        
        ax4.text(0.1, 0.6, f'Phase Transitions: {len(trends["phase_transitions"])}', fontsize=12, transform=ax4.transAxes)
        
        # 구간별 특성 요약
        y_pos = 0.5
        for phase_name, characteristics in phase_characteristics.items():
            ax4.text(0.1, y_pos, f'{phase_name.replace("_", " ").title()}:', fontsize=10, fontweight='bold', transform=ax4.transAxes)
            y_pos -= 0.03
            ax4.text(0.1, y_pos, f'  Avg: {characteristics["avg_qps"]:.0f}, CV: {characteristics["cv"]:.3f}, Trend: {characteristics["trend"]}', fontsize=9, transform=ax4.transAxes)
            y_pos -= 0.03
            ax4.text(0.1, y_pos, f'  Stability: {characteristics["stability"]}, Type: {characteristics["phase_type"]}', fontsize=9, transform=ax4.transAxes)
            y_pos -= 0.03
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('Analysis Summary')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/phase_b_rocksdb_phases_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ RocksDB 구간 시각화 완료")
    
    def _stability_to_numeric(self, stability):
        """안정성을 숫자로 변환"""
        stability_map = {
            'very_stable': 1.0,
            'stable': 0.8,
            'moderate': 0.6,
            'unstable': 0.4,
            'insufficient_data': 0.0
        }
        return stability_map.get(stability, 0.0)
    
    def save_results(self):
        """결과 저장"""
        print("💾 RocksDB 구간 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/phase_b_rocksdb_phases_analysis_results.json", 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_rocksdb_phases_report()
            with open(f"{self.results_dir}/phase_b_rocksdb_phases_analysis_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_rocksdb_phases_report(self):
        """RocksDB 구간 분석 보고서 생성"""
        report = f"""# Phase-B RocksDB Phases Analysis

## Overview
This report presents the analysis of Phase-B data based on RocksDB operational characteristics: initial loading, compaction active, and stabilized phases.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## RocksDB Phases Analysis Results
"""
        
        if 'rocksdb_phases' in self.analysis_results:
            phases = self.analysis_results['rocksdb_phases']
            report += f"""
### RocksDB Phases
- **Total Phases**: {len(phases)}
- **Segmentation Method**: RocksDB operational characteristics
"""
            for phase_name, phase_info in phases.items():
                report += f"""
#### {phase_name.replace('_', ' ').title()} Phase
- **Start Index**: {phase_info['start']:,}
- **End Index**: {phase_info['end']:,}
- **Sample Count**: {phase_info['end'] - phase_info['start']:,}
- **Phase Type**: {phase_info['type']}
- **Description**: {phase_info['description']}
"""
        
        if 'phase_characteristics' in self.analysis_results:
            characteristics = self.analysis_results['phase_characteristics']
            report += f"""
### Phase Characteristics
"""
            for phase_name, char in characteristics.items():
                report += f"""
#### {phase_name.replace('_', ' ').title()} Phase Characteristics
- **Sample Count**: {char['sample_count']:,}
- **Average QPS**: {char['avg_qps']:.2f} ops/sec
- **Maximum QPS**: {char['max_qps']:.2f} ops/sec
- **Minimum QPS**: {char['min_qps']:.2f} ops/sec
- **Standard Deviation**: {char['std_qps']:.2f} ops/sec
- **Coefficient of Variation**: {char['cv']:.3f}
- **Trend**: {char['trend']}
- **Stability**: {char['stability']}
- **Phase Type**: {char['phase_type']}
"""
        
        if 'performance_trends' in self.analysis_results:
            trends = self.analysis_results['performance_trends']
            report += f"""
### Performance Trends Analysis
- **Overall Trend**: {trends['overall_trend']}
- **Phase Transitions**: {len(trends['phase_transitions'])}
"""
            if trends['performance_degradation']:
                degradation = trends['performance_degradation']
                report += f"""
- **Performance Degradation**: {degradation['degradation_percent']:.1f}%
- **First Phase Average**: {degradation['first_phase_avg']:.2f} ops/sec
- **Last Phase Average**: {degradation['last_phase_avg']:.2f} ops/sec
"""
        
        report += f"""
## Key Insights

### 1. RocksDB Operational Phases
- **Initial Phase**: Empty DB with rapid performance changes
- **Middle Phase**: Compaction active with stabilization
- **Final Phase**: Stabilized performance

### 2. Performance Characteristics
- **Phase-specific Patterns**: Each phase has unique performance characteristics
- **Stability Analysis**: Different stability levels across phases
- **Trend Identification**: Phase-specific performance trends

### 3. Model Improvement Implications
- **RocksDB-aware Segmentation**: Natural operational phases for better model training
- **Phase-specific Modeling**: Different models for different operational phases
- **Stability-based Predictions**: Stability analysis for better performance prediction

## Visualization
![Phase-B RocksDB Phases Analysis](phase_b_rocksdb_phases_analysis.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 Phase-B RocksDB 구간 분석 시작")
        print("=" * 60)
        
        # 1. RocksDB 동작 특성 기반 구간 분석
        self.analyze_rocksdb_phases()
        
        # 2. 시각화 생성
        self.create_rocksdb_phases_visualization()
        
        # 3. 결과 저장
        self.save_results()
        
        print("=" * 60)
        print("✅ Phase-B RocksDB 구간 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = Phase_B_RocksDB_Phases_Analyzer()
    analyzer.run_analysis()

