#!/usr/bin/env python3
"""
Phase-B Meaningful Performance Segments Analysis
Phase-B 의미있는 성능 구간 분석
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
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class Phase_B_Meaningful_Segments_Analyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-B 데이터 로드
        self.phase_b_data = self._load_phase_b_data()
        
        # 분석 결과
        self.analysis_results = {}
        
        print("🚀 Phase-B Meaningful Performance Segments Analysis 시작")
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
    
    def analyze_meaningful_segments(self):
        """의미있는 구간 분석"""
        print("📊 의미있는 구간 분석 중...")
        
        if not self.phase_b_data or 'fillrandom_results' not in self.phase_b_data:
            print("⚠️ Phase-B 데이터가 없습니다.")
            return None
        
        df = self.phase_b_data['fillrandom_results']['dataframe']
        
        # 1. 성능 변화율 분석 (더 큰 임계값 사용)
        performance_changes = self._analyze_performance_changes(df)
        
        # 2. 의미있는 구간 분할 (큰 변화만 고려)
        meaningful_segments = self._create_meaningful_segments(df, performance_changes)
        
        # 3. 구간별 특성 분석
        segment_characteristics = self._analyze_segment_characteristics(df, meaningful_segments)
        
        # 4. 성능 트렌드 분석
        performance_trends = self._analyze_performance_trends(df, meaningful_segments)
        
        self.analysis_results = {
            'performance_changes': performance_changes,
            'meaningful_segments': meaningful_segments,
            'segment_characteristics': segment_characteristics,
            'performance_trends': performance_trends
        }
        
        print("✅ 의미있는 구간 분석 완료")
        return self.analysis_results
    
    def _analyze_performance_changes(self, df):
        """성능 변화율 분석"""
        print("📊 성능 변화율 분석 중...")
        
        # 이동 평균 계산 (50개 샘플 윈도우)
        window_size = 50
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
        
        # 큰 변화 지점 찾기 (표준편차의 3배 이상)
        threshold = change_stats['std_change'] * 3
        large_changes = df[abs(df['qps_change']) > threshold].copy()
        large_changes['change_magnitude'] = abs(large_changes['qps_change'])
        large_changes = large_changes.sort_values('change_magnitude', ascending=False)
        
        print(f"   평균 변화율: {change_stats['mean_change_pct']:.2f}%")
        print(f"   변화율 표준편차: {change_stats['std_change_pct']:.2f}%")
        print(f"   큰 변화 지점: {len(large_changes)}개")
        
        return {
            'change_stats': change_stats,
            'large_changes': large_changes,
            'threshold': threshold
        }
    
    def _create_meaningful_segments(self, df, performance_changes):
        """의미있는 구간 생성"""
        print("📊 의미있는 구간 생성 중...")
        
        # 큰 변화 지점들을 기준으로 구간 분할
        large_changes = performance_changes['large_changes']
        
        if len(large_changes) == 0:
            # 큰 변화가 없으면 단순히 3등분
            total_samples = len(df)
            segments = {
                'initial_phase': {'start': 0, 'end': total_samples // 3, 'type': 'time_based'},
                'middle_phase': {'start': total_samples // 3, 'end': (total_samples * 2) // 3, 'type': 'time_based'},
                'final_phase': {'start': (total_samples * 2) // 3, 'end': total_samples, 'type': 'time_based'}
            }
        else:
            # 큰 변화 지점들을 기준으로 구간 분할 (상위 10개만 고려)
            top_changes = large_changes.head(10)
            change_points = sorted(top_changes.index.tolist())
            
            # 구간 경계점 설정
            segment_boundaries = [0] + change_points + [len(df)]
            segment_boundaries = sorted(list(set(segment_boundaries)))
            
            # 구간 정의
            segments = {}
            for i in range(len(segment_boundaries) - 1):
                start_idx = segment_boundaries[i]
                end_idx = segment_boundaries[i + 1]
                
                if i == 0:
                    phase_name = 'initial_phase'
                elif i == len(segment_boundaries) - 2:
                    phase_name = 'final_phase'
                else:
                    phase_name = f'middle_phase_{i}'
                
                segments[phase_name] = {
                    'start': start_idx,
                    'end': end_idx,
                    'type': 'change_based',
                    'change_point': change_points[i-1] if i > 0 else None
                }
        
        print(f"   구간 수: {len(segments)}개")
        for phase_name, segment in segments.items():
            print(f"   {phase_name}: {segment['start']}-{segment['end']} ({segment['type']})")
        
        return segments
    
    def _analyze_segment_characteristics(self, df, meaningful_segments):
        """구간별 특성 분석"""
        print("📊 구간별 특성 분석 중...")
        
        segment_characteristics = {}
        
        for phase_name, segment in meaningful_segments.items():
            start_idx = segment['start']
            end_idx = segment['end']
            
            # 구간 데이터 추출
            segment_data = df.iloc[start_idx:end_idx]['interval_qps']
            
            # 구간별 통계
            characteristics = {
                'sample_count': len(segment_data),
                'avg_qps': segment_data.mean(),
                'max_qps': segment_data.max(),
                'min_qps': segment_data.min(),
                'std_qps': segment_data.std(),
                'median_qps': segment_data.median(),
                'q25': segment_data.quantile(0.25),
                'q75': segment_data.quantile(0.75),
                'cv': segment_data.std() / segment_data.mean() if segment_data.mean() > 0 else 0,
                'trend': self._calculate_trend(segment_data)
            }
            
            segment_characteristics[phase_name] = characteristics
            
            print(f"   {phase_name}:")
            print(f"     샘플 수: {characteristics['sample_count']:,}")
            print(f"     평균 QPS: {characteristics['avg_qps']:.2f}")
            print(f"     최대 QPS: {characteristics['max_qps']:.2f}")
            print(f"     최소 QPS: {characteristics['min_qps']:.2f}")
            print(f"     표준편차: {characteristics['std_qps']:.2f}")
            print(f"     변동계수: {characteristics['cv']:.3f}")
            print(f"     트렌드: {characteristics['trend']}")
        
        return segment_characteristics
    
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
    
    def _analyze_performance_trends(self, df, meaningful_segments):
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
        phase_names = list(meaningful_segments.keys())
        for i in range(len(phase_names) - 1):
            current_phase = phase_names[i]
            next_phase = phase_names[i + 1]
            
            current_end = meaningful_segments[current_phase]['end']
            next_start = meaningful_segments[next_phase]['start']
            
            # 전환 구간의 성능 변화
            transition_data = df.iloc[current_end-10:next_start+10]['interval_qps']
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
            
            first_avg = df.iloc[meaningful_segments[first_phase]['start']:meaningful_segments[first_phase]['end']]['interval_qps'].mean()
            last_avg = df.iloc[meaningful_segments[last_phase]['start']:meaningful_segments[last_phase]['end']]['interval_qps'].mean()
            
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
    
    def create_meaningful_segments_visualization(self):
        """의미있는 구간 시각화 생성"""
        print("📊 의미있는 구간 시각화 생성 중...")
        
        if not self.analysis_results:
            print("⚠️ 분석 결과가 없습니다.")
            return
        
        df = self.phase_b_data['fillrandom_results']['dataframe']
        meaningful_segments = self.analysis_results['meaningful_segments']
        segment_characteristics = self.analysis_results['segment_characteristics']
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('Phase-B Meaningful Performance Segments Analysis', fontsize=16, fontweight='bold')
        
        # 1. 전체 성능 곡선과 의미있는 구간
        ax1.plot(df.index, df['interval_qps'], alpha=0.6, color='lightblue', label='QPS')
        
        # 구간별 평균선 표시
        colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        for i, (phase_name, segment) in enumerate(meaningful_segments.items()):
            start_idx = segment['start']
            end_idx = segment['end']
            avg_qps = segment_characteristics[phase_name]['avg_qps']
            
            ax1.axvspan(start_idx, end_idx, alpha=0.2, color=colors[i % len(colors)])
            ax1.axhline(y=avg_qps, xmin=start_idx/len(df), xmax=end_idx/len(df), 
                      color=colors[i % len(colors)], linewidth=2, 
                      label=f'{phase_name.replace("_", " ").title()}: {avg_qps:.0f}')
        
        ax1.set_xlabel('Sample Index')
        ax1.set_ylabel('QPS (ops/sec)')
        ax1.set_title('Performance Curve with Meaningful Segments')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 구간별 성능 통계
        phase_names = list(meaningful_segments.keys())
        avg_qps = [segment_characteristics[phase]['avg_qps'] for phase in phase_names]
        max_qps = [segment_characteristics[phase]['max_qps'] for phase in phase_names]
        min_qps = [segment_characteristics[phase]['min_qps'] for phase in phase_names]
        
        x = np.arange(len(phase_names))
        width = 0.25
        
        ax2.bar(x - width, avg_qps, width, label='Average', color='skyblue', alpha=0.7)
        ax2.bar(x, max_qps, width, label='Maximum', color='lightgreen', alpha=0.7)
        ax2.bar(x + width, min_qps, width, label='Minimum', color='lightcoral', alpha=0.7)
        
        ax2.set_ylabel('QPS (ops/sec)')
        ax2.set_title('Performance Statistics by Meaningful Segment')
        ax2.set_xticks(x)
        ax2.set_xticklabels([p.replace('_', ' ').title() for p in phase_names], rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 구간별 변동성 분석
        cv_values = [segment_characteristics[phase]['cv'] for phase in phase_names]
        std_values = [segment_characteristics[phase]['std_qps'] for phase in phase_names]
        
        ax3.bar(x - width/2, cv_values, width, label='Coefficient of Variation', color='orange', alpha=0.7)
        ax3.bar(x + width/2, [std/1000 for std in std_values], width, label='Std Dev (×1000)', color='purple', alpha=0.7)
        
        ax3.set_ylabel('Variability')
        ax3.set_title('Performance Variability by Meaningful Segment')
        ax3.set_xticks(x)
        ax3.set_xticklabels([p.replace('_', ' ').title() for p in phase_names], rotation=45)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 성능 트렌드 분석
        trends = self.analysis_results['performance_trends']
        
        ax4.text(0.1, 0.9, 'Performance Trend Analysis:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.8, f'Overall Trend: {trends["overall_trend"]}', fontsize=12, transform=ax4.transAxes)
        
        if trends['performance_degradation']:
            degradation = trends['performance_degradation']['degradation_percent']
            ax4.text(0.1, 0.7, f'Performance Degradation: {degradation:.1f}%', fontsize=12, transform=ax4.transAxes)
        
        ax4.text(0.1, 0.6, f'Segment Transitions: {len(trends["phase_transitions"])}', fontsize=12, transform=ax4.transAxes)
        
        # 구간별 특성 요약
        y_pos = 0.5
        for phase_name, characteristics in segment_characteristics.items():
            ax4.text(0.1, y_pos, f'{phase_name.replace("_", " ").title()}:', fontsize=10, fontweight='bold', transform=ax4.transAxes)
            y_pos -= 0.03
            ax4.text(0.1, y_pos, f'  Avg: {characteristics["avg_qps"]:.0f}, CV: {characteristics["cv"]:.3f}, Trend: {characteristics["trend"]}', fontsize=9, transform=ax4.transAxes)
            y_pos -= 0.03
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('Trend Analysis Summary')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/phase_b_meaningful_segments_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 의미있는 구간 시각화 완료")
    
    def save_results(self):
        """결과 저장"""
        print("💾 의미있는 구간 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/phase_b_meaningful_segments_analysis_results.json", 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_meaningful_segments_report()
            with open(f"{self.results_dir}/phase_b_meaningful_segments_analysis_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_meaningful_segments_report(self):
        """의미있는 구간 분석 보고서 생성"""
        report = f"""# Phase-B Meaningful Performance Segments Analysis

## Overview
This report presents the analysis of meaningful performance segments in Phase-B data, identifying natural performance phases based on significant performance changes.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Meaningful Performance Segments Analysis Results
"""
        
        if 'meaningful_segments' in self.analysis_results:
            segments = self.analysis_results['meaningful_segments']
            report += f"""
### Meaningful Performance Segments
- **Total Segments**: {len(segments)}
- **Segmentation Method**: Significant change-based analysis
"""
            for phase_name, segment in segments.items():
                report += f"""
#### {phase_name.replace('_', ' ').title()} Phase
- **Start Index**: {segment['start']:,}
- **End Index**: {segment['end']:,}
- **Sample Count**: {segment['end'] - segment['start']:,}
- **Segmentation Type**: {segment['type']}
"""
        
        if 'segment_characteristics' in self.analysis_results:
            characteristics = self.analysis_results['segment_characteristics']
            report += f"""
### Segment Characteristics
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
"""
        
        if 'performance_trends' in self.analysis_results:
            trends = self.analysis_results['performance_trends']
            report += f"""
### Performance Trends Analysis
- **Overall Trend**: {trends['overall_trend']}
- **Segment Transitions**: {len(trends['phase_transitions'])}
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

### 1. Meaningful Performance Segments
- **Significant Change-based Segmentation**: Segments identified based on significant performance changes
- **Performance Variability**: Different segments show different variability patterns
- **Trend Analysis**: Each segment has distinct performance trends

### 2. Performance Characteristics
- **Segment-specific Patterns**: Each segment has unique performance characteristics
- **Variability Analysis**: Coefficient of variation shows stability differences
- **Trend Identification**: Linear regression analysis reveals performance trends

### 3. Model Improvement Implications
- **Accurate Segment Definition**: Natural performance segments for better model training
- **Segment-specific Modeling**: Different models for different performance segments
- **Trend-based Predictions**: Trend analysis for better performance prediction

## Visualization
![Phase-B Meaningful Segments Analysis](phase_b_meaningful_segments_analysis.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 Phase-B 의미있는 구간 분석 시작")
        print("=" * 60)
        
        # 1. 의미있는 구간 분석
        self.analyze_meaningful_segments()
        
        # 2. 시각화 생성
        self.create_meaningful_segments_visualization()
        
        # 3. 결과 저장
        self.save_results()
        
        print("=" * 60)
        print("✅ Phase-B 의미있는 구간 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = Phase_B_Meaningful_Segments_Analyzer()
    analyzer.run_analysis()

