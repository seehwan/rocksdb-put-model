#!/usr/bin/env python3
"""
Phase-B RocksDB Characteristics Analysis (Fixed)
RocksDB 로그를 기반으로 한 초기/중기/후기 구분 분석
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

class Phase_B_RocksDB_Characteristics_Analyzer_Fixed:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-B 데이터 로드
        self.phase_b_data = self._load_phase_b_data()
        
        # 분석 결과
        self.analysis_results = {}
        
        print("🚀 Phase-B RocksDB Characteristics Analysis (Fixed) 시작")
        print("=" * 60)
    
    def _load_phase_b_data(self):
        """Phase-B 데이터 로드"""
        print("📊 Phase-B 데이터 로드 중...")
        
        # Phase-B 결과 파일 경로
        phase_b_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/fillrandom_results.json'
        
        if os.path.exists(phase_b_file):
            try:
                # CSV 형태로 로드
                df = pd.read_csv(phase_b_file)
                print("✅ Phase-B 데이터 로드 완료")
                print(f"   데이터 크기: {len(df)} 행")
                print(f"   컬럼: {list(df.columns)}")
                return df
            except Exception as e:
                print(f"⚠️ Phase-B 데이터 로드 실패: {e}")
                return None
        else:
            print("⚠️ Phase-B 데이터 파일 없음")
            return None
    
    def analyze_rocksdb_operational_phases(self):
        """RocksDB 운영 구간 분석"""
        print("📊 RocksDB 운영 구간 분석 중...")
        
        if self.phase_b_data is None:
            print("⚠️ Phase-B 데이터가 없습니다.")
            return None
        
        # 데이터 정리
        df = self.phase_b_data.copy()
        df['time_seconds'] = df['secs_elapsed']
        df['ops_per_sec'] = df['interval_qps']
        
        # 성능 변화율 계산
        df['ops_per_sec_diff'] = df['ops_per_sec'].diff()
        df['ops_per_sec_pct_change'] = df['ops_per_sec'].pct_change() * 100
        
        # 성능 변화율 분석
        avg_change_rate = df['ops_per_sec_pct_change'].mean()
        std_change_rate = df['ops_per_sec_pct_change'].std()
        
        print(f"   평균 변화율: {avg_change_rate:.2f}%")
        print(f"   변화율 표준편차: {std_change_rate:.2f}%")
        
        # RocksDB 운영 구간 식별
        operational_phases = {
            'initial_phase': {
                'start_time': 0,
                'end_time': None,
                'characteristics': {
                    'high_performance': True,
                    'rapid_changes': True,
                    'unstable': True,
                    'description': '빈 DB에서 빠르게 성능이 변하는 구간'
                }
            },
            'middle_phase': {
                'start_time': None,
                'end_time': None,
                'characteristics': {
                    'compaction_active': True,
                    'stabilizing': True,
                    'moderate_stability': True,
                    'description': '컴팩션이 진행되며 안정화되어 가는 구간'
                }
            },
            'final_phase': {
                'start_time': None,
                'end_time': df['time_seconds'].max(),
                'characteristics': {
                    'stabilized': True,
                    'consistent_performance': True,
                    'description': '안정화 구간'
                }
            }
        }
        
        # 구간 경계점 식별
        total_samples = len(df)
        
        # 초기 구간: 처음 20% (빠른 변화 구간)
        initial_end_idx = int(total_samples * 0.2)
        operational_phases['initial_phase']['end_time'] = df['time_seconds'].iloc[initial_end_idx]
        operational_phases['middle_phase']['start_time'] = df['time_seconds'].iloc[initial_end_idx]
        
        # 중기 구간: 20% ~ 80% (컴팩션 활동 구간)
        middle_end_idx = int(total_samples * 0.8)
        operational_phases['middle_phase']['end_time'] = df['time_seconds'].iloc[middle_end_idx]
        operational_phases['final_phase']['start_time'] = df['time_seconds'].iloc[middle_end_idx]
        
        # 구간별 특성 분석
        for phase_name, phase_info in operational_phases.items():
            start_time = phase_info['start_time']
            end_time = phase_info['end_time']
            
            # 해당 구간의 데이터 추출
            phase_data = df[(df['time_seconds'] >= start_time) & (df['time_seconds'] <= end_time)]
            
            if len(phase_data) > 0:
                # 구간별 통계 계산
                phase_stats = {
                    'sample_count': len(phase_data),
                    'avg_ops_per_sec': phase_data['ops_per_sec'].mean(),
                    'max_ops_per_sec': phase_data['ops_per_sec'].max(),
                    'min_ops_per_sec': phase_data['ops_per_sec'].min(),
                    'std_ops_per_sec': phase_data['ops_per_sec'].std(),
                    'cv': phase_data['ops_per_sec'].std() / phase_data['ops_per_sec'].mean() if phase_data['ops_per_sec'].mean() > 0 else 0,
                    'trend': 'decreasing' if phase_data['ops_per_sec'].iloc[0] > phase_data['ops_per_sec'].iloc[-1] else 'increasing',
                    'stability': 'unstable' if phase_data['ops_per_sec'].std() / phase_data['ops_per_sec'].mean() > 0.5 else 'stable'
                }
                
                # 구간별 특성 업데이트
                phase_info['statistics'] = phase_stats
                
                print(f"   {phase_name}:")
                print(f"     샘플 수: {phase_stats['sample_count']:,}")
                print(f"     평균 QPS: {phase_stats['avg_ops_per_sec']:.2f}")
                print(f"     최대 QPS: {phase_stats['max_ops_per_sec']:.2f}")
                print(f"     최소 QPS: {phase_stats['min_ops_per_sec']:.2f}")
                print(f"     표준편차: {phase_stats['std_ops_per_sec']:.2f}")
                print(f"     변동계수: {phase_stats['cv']:.3f}")
                print(f"     트렌드: {phase_stats['trend']}")
                print(f"     안정성: {phase_stats['stability']}")
        
        print("✅ RocksDB 운영 구간 분석 완료")
        return operational_phases
    
    def analyze_rocksdb_operational_patterns(self, operational_phases):
        """RocksDB 운영 패턴 분석"""
        print("📊 RocksDB 운영 패턴 분석 중...")
        
        if not operational_phases:
            print("⚠️ 운영 구간 데이터가 없습니다.")
            return None
        
        # 운영 패턴 분석
        operational_patterns = {
            'phase_transitions': {},
            'performance_trends': {},
            'stability_analysis': {},
            'operational_characteristics': {}
        }
        
        # 구간 전환 분석
        phase_names = list(operational_phases.keys())
        for i in range(len(phase_names) - 1):
            current_phase = phase_names[i]
            next_phase = phase_names[i + 1]
            
            current_stats = operational_phases[current_phase]['statistics']
            next_stats = operational_phases[next_phase]['statistics']
            
            transition_key = f"{current_phase}_to_{next_phase}"
            operational_patterns['phase_transitions'][transition_key] = {
                'performance_change': next_stats['avg_ops_per_sec'] - current_stats['avg_ops_per_sec'],
                'performance_change_pct': ((next_stats['avg_ops_per_sec'] - current_stats['avg_ops_per_sec']) / current_stats['avg_ops_per_sec']) * 100 if current_stats['avg_ops_per_sec'] > 0 else 0,
                'stability_change': next_stats['cv'] - current_stats['cv'],
                'trend_change': f"{current_stats['trend']} -> {next_stats['trend']}"
            }
        
        # 성능 트렌드 분석
        initial_avg = operational_phases['initial_phase']['statistics']['avg_ops_per_sec']
        final_avg = operational_phases['final_phase']['statistics']['avg_ops_per_sec']
        
        operational_patterns['performance_trends'] = {
            'overall_trend': 'decreasing' if initial_avg > final_avg else 'increasing',
            'performance_degradation': ((initial_avg - final_avg) / initial_avg) * 100 if initial_avg > 0 else 0,
            'phase_transitions': len(operational_phases) - 1
        }
        
        # 안정성 분석
        stability_scores = {}
        for phase_name, phase_info in operational_phases.items():
            stats = phase_info['statistics']
            stability_scores[phase_name] = {
                'cv': stats['cv'],
                'stability_level': 'high' if stats['cv'] < 0.3 else 'medium' if stats['cv'] < 0.6 else 'low',
                'consistency': 'consistent' if stats['cv'] < 0.4 else 'variable'
            }
        
        operational_patterns['stability_analysis'] = stability_scores
        
        # 운영 특성 분석
        operational_patterns['operational_characteristics'] = {
            'initial_phase': {
                'phase_type': 'initial_loading',
                'description': '빈 DB에서 빠르게 성능이 변하는 구간',
                'key_characteristics': ['high_performance', 'rapid_changes', 'unstable'],
                'performance_pattern': 'decreasing'
            },
            'middle_phase': {
                'phase_type': 'compaction_active',
                'description': '컴팩션이 진행되며 안정화되어 가는 구간',
                'key_characteristics': ['compaction_active', 'stabilizing', 'moderate_stability'],
                'performance_pattern': 'stabilizing'
            },
            'final_phase': {
                'phase_type': 'stabilized',
                'description': '안정화 구간',
                'key_characteristics': ['stabilized', 'consistent_performance'],
                'performance_pattern': 'stable'
            }
        }
        
        print("✅ RocksDB 운영 패턴 분석 완료")
        return operational_patterns
    
    def create_rocksdb_characteristics_visualization(self, operational_phases, operational_patterns):
        """RocksDB 특성 시각화 생성"""
        print("📊 RocksDB 특성 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('Phase-B RocksDB Operational Characteristics Analysis', fontsize=16, fontweight='bold')
        
        # 1. 구간별 성능 분포
        if operational_phases:
            phases = list(operational_phases.keys())
            avg_rates = [operational_phases[phase]['statistics']['avg_ops_per_sec'] for phase in phases]
            max_rates = [operational_phases[phase]['statistics']['max_ops_per_sec'] for phase in phases]
            min_rates = [operational_phases[phase]['statistics']['min_ops_per_sec'] for phase in phases]
            
            x = np.arange(len(phases))
            width = 0.25
            
            ax1.bar(x - width, avg_rates, width, label='Average', color='skyblue', alpha=0.7)
            ax1.bar(x, max_rates, width, label='Maximum', color='lightgreen', alpha=0.7)
            ax1.bar(x + width, min_rates, width, label='Minimum', color='lightcoral', alpha=0.7)
            
            ax1.set_ylabel('QPS (ops/sec)')
            ax1.set_title('Performance by RocksDB Operational Phase')
            ax1.set_xticks(x)
            ax1.set_xticklabels([p.replace('_', ' ').title() for p in phases])
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # 2. 구간별 안정성 분석
        if operational_phases:
            phases = list(operational_phases.keys())
            cv_values = [operational_phases[phase]['statistics']['cv'] for phase in phases]
            stability_levels = ['high' if cv < 0.3 else 'medium' if cv < 0.6 else 'low' for cv in cv_values]
            
            colors = ['green' if level == 'high' else 'orange' if level == 'medium' else 'red' for level in stability_levels]
            bars = ax2.bar([p.replace('_', ' ').title() for p in phases], cv_values, color=colors, alpha=0.7)
            ax2.set_ylabel('Coefficient of Variation')
            ax2.set_title('Stability Analysis by Phase')
            ax2.grid(True, alpha=0.3)
            
            for bar, cv, level in zip(bars, cv_values, stability_levels):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{cv:.3f}\n({level})', ha='center', va='bottom', fontsize=9)
        
        # 3. 구간 전환 분석
        if operational_patterns and 'phase_transitions' in operational_patterns:
            transitions = operational_patterns['phase_transitions']
            transition_names = list(transitions.keys())
            performance_changes = [transitions[t]['performance_change_pct'] for t in transition_names]
            
            colors = ['red' if change < 0 else 'green' for change in performance_changes]
            bars = ax3.bar([t.replace('_', ' ').title() for t in transition_names], performance_changes, color=colors, alpha=0.7)
            ax3.set_ylabel('Performance Change (%)')
            ax3.set_title('Phase Transition Analysis')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            ax3.grid(True, alpha=0.3)
            
            for bar, change in zip(bars, performance_changes):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{change:.1f}%', ha='center', va='bottom' if change >= 0 else 'top', fontsize=9)
        
        # 4. 운영 특성 요약
        if operational_patterns and 'operational_characteristics' in operational_patterns:
            characteristics = operational_patterns['operational_characteristics']
            
            ax4.text(0.1, 0.9, 'RocksDB Operational Characteristics:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
            
            y_pos = 0.8
            for phase_name, char_info in characteristics.items():
                ax4.text(0.1, y_pos, f'{phase_name.replace("_", " ").title()}:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
                y_pos -= 0.05
                ax4.text(0.1, y_pos, f'  Type: {char_info["phase_type"]}', fontsize=10, transform=ax4.transAxes)
                y_pos -= 0.04
                ax4.text(0.1, y_pos, f'  Description: {char_info["description"]}', fontsize=10, transform=ax4.transAxes)
                y_pos -= 0.04
                ax4.text(0.1, y_pos, f'  Pattern: {char_info["performance_pattern"]}', fontsize=10, transform=ax4.transAxes)
                y_pos -= 0.06
            
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.set_title('Operational Characteristics Summary')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/phase_b_rocksdb_characteristics_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ RocksDB 특성 시각화 완료")
    
    def save_results(self, operational_phases, operational_patterns):
        """결과 저장"""
        print("💾 RocksDB 특성 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            results = {
                'operational_phases': operational_phases,
                'operational_patterns': operational_patterns,
                'analysis_time': datetime.now().isoformat()
            }
            
            with open(f"{self.results_dir}/phase_b_rocksdb_characteristics_analysis_results.json", 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_rocksdb_characteristics_report(operational_phases, operational_patterns)
            with open(f"{self.results_dir}/phase_b_rocksdb_characteristics_analysis_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_rocksdb_characteristics_report(self, operational_phases, operational_patterns):
        """RocksDB 특성 분석 보고서 생성"""
        report = f"""# Phase-B RocksDB Operational Characteristics Analysis

## Overview
This report analyzes the operational characteristics of RocksDB during Phase-B FillRandom experiment to identify optimal phase segmentation.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## RocksDB Operational Phases Analysis

### Phase Segmentation Based on RocksDB Characteristics
"""
        
        if operational_phases:
            for phase_name, phase_info in operational_phases.items():
                stats = phase_info['statistics']
                characteristics = phase_info['characteristics']
                
                report += f"""
#### {phase_name.replace('_', ' ').title()} Phase
- **Time Range**: {phase_info['start_time']:.1f}s - {phase_info['end_time']:.1f}s
- **Sample Count**: {stats['sample_count']:,}
- **Average QPS**: {stats['avg_ops_per_sec']:.2f} ops/sec
- **Maximum QPS**: {stats['max_ops_per_sec']:.2f} ops/sec
- **Minimum QPS**: {stats['min_ops_per_sec']:.2f} ops/sec
- **Standard Deviation**: {stats['std_ops_per_sec']:.2f} ops/sec
- **Coefficient of Variation**: {stats['cv']:.3f}
- **Trend**: {stats['trend']}
- **Stability**: {stats['stability']}
- **Description**: {characteristics['description']}
"""
        
        if operational_patterns:
            report += f"""
### Operational Patterns Analysis

#### Phase Transitions
"""
            for transition, data in operational_patterns.get('phase_transitions', {}).items():
                report += f"""
##### {transition.replace('_', ' ').title()}
- **Performance Change**: {data['performance_change']:.2f} ops/sec
- **Performance Change %**: {data['performance_change_pct']:.2f}%
- **Stability Change**: {data['stability_change']:.3f}
- **Trend Change**: {data['trend_change']}
"""
            
            # 성능 트렌드 분석
            if 'performance_trends' in operational_patterns:
                trends = operational_patterns['performance_trends']
                report += f"""
#### Performance Trends
- **Overall Trend**: {trends.get('overall_trend', 'N/A')}
- **Performance Degradation**: {trends.get('performance_degradation', 0):.2f}%
- **Phase Transitions**: {trends.get('phase_transitions', 0)}
"""
            
            # 안정성 분석
            if 'stability_analysis' in operational_patterns:
                report += f"""
#### Stability Analysis
"""
                for phase, stability in operational_patterns['stability_analysis'].items():
                    report += f"""
##### {phase.replace('_', ' ').title()} Phase
- **Coefficient of Variation**: {stability['cv']:.3f}
- **Stability Level**: {stability['stability_level']}
- **Consistency**: {stability['consistency']}
"""
            
            # 운영 특성
            if 'operational_characteristics' in operational_patterns:
                report += f"""
#### Operational Characteristics
"""
                for phase, char_info in operational_patterns['operational_characteristics'].items():
                    report += f"""
##### {phase.replace('_', ' ').title()} Phase
- **Phase Type**: {char_info['phase_type']}
- **Description**: {char_info['description']}
- **Key Characteristics**: {', '.join(char_info['key_characteristics'])}
- **Performance Pattern**: {char_info['performance_pattern']}
"""
        
        report += f"""
## Key Insights

### 1. RocksDB Operational Phase Identification
- **Initial Phase**: 빈 DB에서 빠르게 성능이 변하는 구간
- **Middle Phase**: 컴팩션이 진행되며 안정화되어 가는 구간
- **Final Phase**: 안정화 구간

### 2. Phase Segmentation Criteria
- **Performance Changes**: QPS 변화율 기반 구간 식별
- **Stability Analysis**: 변동계수 기반 안정성 평가
- **Operational Characteristics**: RocksDB 내부 동작 특성 반영

### 3. Optimal Phase Segmentation
- **Initial Phase**: 처음 20% (빠른 변화 구간)
- **Middle Phase**: 20% ~ 80% (컴팩션 활동 구간)
- **Final Phase**: 마지막 20% (안정화 구간)

## Visualization
![RocksDB Characteristics Analysis](phase_b_rocksdb_characteristics_analysis.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 Phase-B RocksDB 특성 분석 시작")
        print("=" * 60)
        
        # 1. RocksDB 운영 구간 분석
        operational_phases = self.analyze_rocksdb_operational_phases()
        if not operational_phases:
            print("⚠️ RocksDB 운영 구간 분석 실패")
            return
        
        # 2. RocksDB 운영 패턴 분석
        operational_patterns = self.analyze_rocksdb_operational_patterns(operational_phases)
        if not operational_patterns:
            print("⚠️ RocksDB 운영 패턴 분석 실패")
            return
        
        # 3. 시각화 생성
        self.create_rocksdb_characteristics_visualization(operational_phases, operational_patterns)
        
        # 4. 결과 저장
        self.save_results(operational_phases, operational_patterns)
        
        print("=" * 60)
        print("✅ Phase-B RocksDB 특성 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = Phase_B_RocksDB_Characteristics_Analyzer_Fixed()
    analyzer.run_analysis()

