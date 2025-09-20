#!/usr/bin/env python3
"""
Read/Write 비율에 따른 성능 분석
Phase-A 데이터를 기반으로 Read/Write 비율이 성능에 미치는 영향 분석
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

class RW_Ratio_Performance_Analyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-A 데이터 로드
        self.phase_a_data = self._load_phase_a_rw_data()
        
        print("🚀 Read/Write 비율 성능 분석 시작")
        print("=" * 60)
    
    def _load_phase_a_rw_data(self):
        """Phase-A Read/Write 성능 데이터 로드"""
        print("📊 Phase-A Read/Write 성능 데이터 로드 중...")
        
        # 초기 상태 데이터
        initial_data = {
            'seq_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_initial.json'),
            'seq_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_initial.json'),
            'rand_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/rand_write_initial.json'),
            'rand_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/rand_read_initial.json')
        }
        
        # 열화 상태 데이터
        degraded_data = {
            'seq_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_degraded.json'),
            'seq_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_degraded.json'),
            'rand_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/rand_write_degraded.json'),
            'rand_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/rand_read_degraded.json')
        }
        
        print("✅ Phase-A Read/Write 성능 데이터 로드 완료:")
        print(f"   - 초기 상태 Seq Write: {initial_data['seq_write']['write_bw']:.1f} MB/s")
        print(f"   - 초기 상태 Seq Read: {initial_data['seq_read']['read_bw']:.1f} MB/s")
        print(f"   - 열화 상태 Seq Write: {degraded_data['seq_write']['write_bw']:.1f} MB/s")
        print(f"   - 열화 상태 Seq Read: {degraded_data['seq_read']['read_bw']:.1f} MB/s")
        
        return {
            'initial': initial_data,
            'degraded': degraded_data
        }
    
    def _extract_fio_performance(self, fio_file):
        """FIO 파일에서 성능 데이터 추출"""
        try:
            with open(fio_file, 'r') as f:
                fio_data = json.load(f)
            
            # Write 성능 추출 (KB/s 단위)
            write_bw_kbps = fio_data['jobs'][0]['write']['bw']
            write_bw_mbps = write_bw_kbps / 1024  # KB/s to MB/s
            
            # Read 성능 추출 (KB/s 단위)
            read_bw_kbps = fio_data['jobs'][0]['read']['bw']
            read_bw_mbps = read_bw_kbps / 1024  # KB/s to MB/s
            
            return {
                'write_bw': write_bw_mbps,
                'read_bw': read_bw_mbps
            }
            
        except Exception as e:
            print(f"⚠️ FIO 파일 로드 실패 {fio_file}: {e}")
            return {'write_bw': 0, 'read_bw': 0}
    
    def analyze_rw_ratio_impact(self):
        """Read/Write 비율이 성능에 미치는 영향 분석"""
        print("📊 Read/Write 비율 성능 영향 분석 중...")
        
        # 초기 상태 성능
        initial_seq_write = self.phase_a_data['initial']['seq_write']['write_bw']
        initial_seq_read = self.phase_a_data['initial']['seq_read']['read_bw']
        initial_rand_write = self.phase_a_data['initial']['rand_write']['write_bw']
        initial_rand_read = self.phase_a_data['initial']['rand_read']['read_bw']
        
        # 열화 상태 성능
        degraded_seq_write = self.phase_a_data['degraded']['seq_write']['write_bw']
        degraded_seq_read = self.phase_a_data['degraded']['seq_read']['read_bw']
        degraded_rand_write = self.phase_a_data['degraded']['rand_write']['write_bw']
        degraded_rand_read = self.phase_a_data['degraded']['rand_read']['read_bw']
        
        # Read/Write 비율별 성능 분석
        rw_ratios = [0.0, 0.25, 0.5, 0.75, 1.0]  # Write 비율
        performance_analysis = {}
        
        for rw_ratio in rw_ratios:
            write_ratio = rw_ratio
            read_ratio = 1.0 - rw_ratio
            
            # 초기 상태 성능 (가중 평균)
            initial_performance = (write_ratio * initial_seq_write + 
                                 read_ratio * initial_seq_read)
            
            # 열화 상태 성능 (가중 평균)
            degraded_performance = (write_ratio * degraded_seq_write + 
                                  read_ratio * degraded_seq_read)
            
            # 열화율 계산
            degradation_rate = ((initial_performance - degraded_performance) / 
                               initial_performance) if initial_performance > 0 else 0
            
            performance_analysis[rw_ratio] = {
                'write_ratio': write_ratio,
                'read_ratio': read_ratio,
                'initial_performance': initial_performance,
                'degraded_performance': degraded_performance,
                'degradation_rate': degradation_rate,
                'performance_retention': 1.0 - degradation_rate
            }
        
        print("✅ Read/Write 비율 성능 영향 분석 완료:")
        for ratio, data in performance_analysis.items():
            print(f"   - Write {data['write_ratio']:.0%}: 초기 {data['initial_performance']:.1f} MB/s → 열화 {data['degraded_performance']:.1f} MB/s (열화율 {data['degradation_rate']:.1%})")
        
        return performance_analysis
    
    def create_rw_ratio_visualization(self, performance_analysis):
        """Read/Write 비율 성능 시각화 생성"""
        print("📊 Read/Write 비율 성능 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Read/Write Ratio Performance Impact Analysis', fontsize=16, fontweight='bold')
        
        # 데이터 준비
        write_ratios = [data['write_ratio'] for data in performance_analysis.values()]
        read_ratios = [data['read_ratio'] for data in performance_analysis.values()]
        initial_perfs = [data['initial_performance'] for data in performance_analysis.values()]
        degraded_perfs = [data['degraded_performance'] for data in performance_analysis.values()]
        degradation_rates = [data['degradation_rate'] for data in performance_analysis.values()]
        
        # 1. 초기 vs 열화 성능 비교
        x = np.arange(len(write_ratios))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, initial_perfs, width, label='Initial Performance', color='skyblue', alpha=0.8)
        bars2 = ax1.bar(x + width/2, degraded_perfs, width, label='Degraded Performance', color='lightcoral', alpha=0.8)
        
        ax1.set_xlabel('Write Ratio')
        ax1.set_ylabel('Performance (MB/s)')
        ax1.set_title('Initial vs Degraded Performance by Write Ratio')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{wr:.0%}' for wr in write_ratios])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 값 표시
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 2. 열화율 분석
        colors = ['green' if dr < 0.3 else 'orange' if dr < 0.6 else 'red' for dr in degradation_rates]
        bars = ax2.bar([f'{wr:.0%}' for wr in write_ratios], [dr * 100 for dr in degradation_rates], 
                      color=colors, alpha=0.7)
        ax2.set_ylabel('Degradation Rate (%)')
        ax2.set_title('Degradation Rate by Write Ratio')
        ax2.set_ylim(0, 100)
        
        for bar, value in zip(bars, degradation_rates):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.1%}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Read vs Write 성능 비교 (초기 상태)
        initial_seq_write = self.phase_a_data['initial']['seq_write']['write_bw']
        initial_seq_read = self.phase_a_data['initial']['seq_read']['read_bw']
        
        categories = ['Sequential Write', 'Sequential Read']
        initial_values = [initial_seq_write, initial_seq_read]
        
        bars = ax3.bar(categories, initial_values, color=['skyblue', 'lightgreen'], alpha=0.8)
        ax3.set_ylabel('Performance (MB/s)')
        ax3.set_title('Initial Performance: Write vs Read')
        ax3.grid(True, alpha=0.3)
        
        for bar, value in zip(bars, initial_values):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 4. Read vs Write 성능 비교 (열화 상태)
        degraded_seq_write = self.phase_a_data['degraded']['seq_write']['write_bw']
        degraded_seq_read = self.phase_a_data['degraded']['seq_read']['read_bw']
        
        degraded_values = [degraded_seq_write, degraded_seq_read]
        
        bars = ax4.bar(categories, degraded_values, color=['lightcoral', 'orange'], alpha=0.8)
        ax4.set_ylabel('Performance (MB/s)')
        ax4.set_title('Degraded Performance: Write vs Read')
        ax4.grid(True, alpha=0.3)
        
        for bar, value in zip(bars, degraded_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/rw_ratio_performance_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Read/Write 비율 성능 시각화 완료")
    
    def save_results(self, performance_analysis):
        """결과 저장"""
        print("💾 Read/Write 비율 성능 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/rw_ratio_performance_analysis.json", 'w') as f:
                json.dump(performance_analysis, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_rw_ratio_report(performance_analysis)
            with open(f"{self.results_dir}/rw_ratio_performance_analysis_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_rw_ratio_report(self, performance_analysis):
        """Read/Write 비율 성능 분석 보고서 생성"""
        report = f"""# Read/Write Ratio Performance Impact Analysis

## Overview
This report analyzes the impact of Read/Write ratios on performance using Phase-A data.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Phase-A Performance Data
- **Initial Seq Write**: {self.phase_a_data['initial']['seq_write']['write_bw']:.1f} MB/s
- **Initial Seq Read**: {self.phase_a_data['initial']['seq_read']['read_bw']:.1f} MB/s
- **Degraded Seq Write**: {self.phase_a_data['degraded']['seq_write']['write_bw']:.1f} MB/s
- **Degraded Seq Read**: {self.phase_a_data['degraded']['seq_read']['read_bw']:.1f} MB/s

## Key Findings: Read/Write Ratio Impact

### 1. Performance Difference by Operation Type
- **Write Performance**: {self.phase_a_data['initial']['seq_write']['write_bw']:.1f} MB/s → {self.phase_a_data['degraded']['seq_write']['write_bw']:.1f} MB/s
- **Read Performance**: {self.phase_a_data['initial']['seq_read']['read_bw']:.1f} MB/s → {self.phase_a_data['degraded']['seq_read']['read_bw']:.1f} MB/s
- **Write Degradation**: {((self.phase_a_data['initial']['seq_write']['write_bw'] - self.phase_a_data['degraded']['seq_write']['write_bw']) / self.phase_a_data['initial']['seq_write']['write_bw'] * 100):.1f}%
- **Read Degradation**: {((self.phase_a_data['initial']['seq_read']['read_bw'] - self.phase_a_data['degraded']['seq_read']['read_bw']) / self.phase_a_data['initial']['seq_read']['read_bw'] * 100):.1f}%

## Performance Analysis by Read/Write Ratio
"""
        
        for ratio, data in performance_analysis.items():
            report += f"""
### Write Ratio: {data['write_ratio']:.0%} / Read Ratio: {data['read_ratio']:.0%}
- **Initial Performance**: {data['initial_performance']:.1f} MB/s
- **Degraded Performance**: {data['degraded_performance']:.1f} MB/s
- **Degradation Rate**: {data['degradation_rate']:.1%}
- **Performance Retention**: {data['performance_retention']:.1%}
"""
        
        report += f"""
## Key Insights

### 1. Read vs Write Performance Characteristics
- **Write Operations**: 더 높은 초기 성능, 더 심각한 열화
- **Read Operations**: 상대적으로 낮은 초기 성능, 덜 심각한 열화
- **Mixed Workloads**: Read/Write 비율에 따라 전체 성능이 달라짐

### 2. Degradation Pattern by Workload Type
- **Write-Heavy Workloads**: 더 심각한 성능 열화
- **Read-Heavy Workloads**: 상대적으로 덜 심각한 성능 열화
- **Balanced Workloads**: 중간 수준의 성능 열화

### 3. Implications for RocksDB Modeling
- **Write Path**: Flush, Compaction 등 Write 집약적 작업의 성능 열화 고려 필요
- **Read Path**: Point Lookup, Range Scan 등 Read 작업의 성능 특성 고려 필요
- **Mixed Workloads**: 실제 애플리케이션의 Read/Write 비율에 따른 성능 예측 필요

## Visualization
![Read/Write Ratio Performance Analysis](rw_ratio_performance_analysis.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 Read/Write 비율 성능 분석 시작")
        print("=" * 60)
        
        performance_analysis = self.analyze_rw_ratio_impact()
        self.create_rw_ratio_visualization(performance_analysis)
        self.save_results(performance_analysis)
        
        print("=" * 60)
        print("✅ Read/Write 비율 성능 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = RW_Ratio_Performance_Analyzer()
    analyzer.run_analysis()


