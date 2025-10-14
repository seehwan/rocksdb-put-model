#!/usr/bin/env python3
"""
FillRandom 워크로드 성능 분석
FillRandom 워크로드의 실제 특성을 반영한 성능 분석
- Write: Sequential Write만 발생
- Read: Compaction에서만 발생
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

class FillRandom_Workload_Performance_Analyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-A 데이터 로드
        self.phase_a_data = self._load_phase_a_fillrandom_data()
        
        print("🚀 FillRandom 워크로드 성능 분석 시작")
        print("=" * 60)
    
    def _load_phase_a_fillrandom_data(self):
        """Phase-A FillRandom 워크로드 데이터 로드"""
        print("📊 Phase-A FillRandom 워크로드 데이터 로드 중...")
        
        # FillRandom 워크로드 특성
        # - Write: Sequential Write만 발생
        # - Read: Compaction에서만 발생
        
        # 초기 상태 데이터 (Sequential Write 성능)
        initial_data = {
            'seq_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_initial.json'),
            'seq_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_initial.json')
        }
        
        # 열화 상태 데이터 (Sequential Write 성능)
        degraded_data = {
            'seq_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_degraded.json'),
            'seq_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_degraded.json')
        }
        
        print("✅ Phase-A FillRandom 워크로드 데이터 로드 완료:")
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
    
    def analyze_fillrandom_workload_performance(self):
        """FillRandom 워크로드 성능 분석"""
        print("📊 FillRandom 워크로드 성능 분석 중...")
        
        # FillRandom 워크로드 특성
        # - Write: Sequential Write만 발생 (사용자 Write)
        # - Read: Compaction에서만 발생 (시스템 Read)
        
        # 초기 상태 성능
        initial_seq_write = self.phase_a_data['initial']['seq_write']['write_bw']
        initial_seq_read = self.phase_a_data['initial']['seq_read']['read_bw']
        
        # 열화 상태 성능
        degraded_seq_write = self.phase_a_data['degraded']['seq_write']['write_bw']
        degraded_seq_read = self.phase_a_data['degraded']['seq_read']['read_bw']
        
        # FillRandom 워크로드 성능 분석
        fillrandom_analysis = {
            'workload_characteristics': {
                'write_type': 'Sequential Write Only',
                'read_type': 'Compaction Read Only',
                'user_reads': 0,
                'system_reads': 'Compaction Only'
            },
            'performance_analysis': {
                'initial': {
                    'user_write_performance': initial_seq_write,
                    'compaction_read_performance': initial_seq_read,
                    'write_degradation_rate': 0.0
                },
                'degraded': {
                    'user_write_performance': degraded_seq_write,
                    'compaction_read_performance': degraded_seq_read,
                    'write_degradation_rate': ((initial_seq_write - degraded_seq_write) / initial_seq_write) if initial_seq_write > 0 else 0
                }
            },
            'compaction_impact': {
                'initial_compaction_read_performance': initial_seq_read,
                'degraded_compaction_read_performance': degraded_seq_read,
                'compaction_read_degradation_rate': ((initial_seq_read - degraded_seq_read) / initial_seq_read) if initial_seq_read > 0 else 0
            }
        }
        
        # Write 성능 열화율
        write_degradation_rate = fillrandom_analysis['performance_analysis']['degraded']['write_degradation_rate']
        
        # Compaction Read 성능 열화율
        compaction_read_degradation_rate = fillrandom_analysis['compaction_impact']['compaction_read_degradation_rate']
        
        print("✅ FillRandom 워크로드 성능 분석 완료:")
        print(f"   - Write 성능 열화율: {write_degradation_rate:.1%}")
        print(f"   - Compaction Read 성능 열화율: {compaction_read_degradation_rate:.1%}")
        print(f"   - 초기 Write 성능: {initial_seq_write:.1f} MB/s")
        print(f"   - 열화 Write 성능: {degraded_seq_write:.1f} MB/s")
        print(f"   - 초기 Compaction Read 성능: {initial_seq_read:.1f} MB/s")
        print(f"   - 열화 Compaction Read 성능: {degraded_seq_read:.1f} MB/s")
        
        return fillrandom_analysis
    
    def create_fillrandom_workload_visualization(self, fillrandom_analysis):
        """FillRandom 워크로드 성능 시각화 생성"""
        print("📊 FillRandom 워크로드 성능 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('FillRandom Workload Performance Analysis', fontsize=16, fontweight='bold')
        
        # 초기 상태 성능
        initial_seq_write = self.phase_a_data['initial']['seq_write']['write_bw']
        initial_seq_read = self.phase_a_data['initial']['seq_read']['read_bw']
        
        # 열화 상태 성능
        degraded_seq_write = self.phase_a_data['degraded']['seq_write']['write_bw']
        degraded_seq_read = self.phase_a_data['degraded']['seq_read']['read_bw']
        
        # 1. Write 성능 비교 (사용자 Write)
        categories = ['Initial', 'Degraded']
        write_performance = [initial_seq_write, degraded_seq_write]
        
        bars = ax1.bar(categories, write_performance, color=['skyblue', 'lightcoral'], alpha=0.8)
        ax1.set_ylabel('Write Performance (MB/s)')
        ax1.set_title('User Write Performance (Sequential Write Only)')
        ax1.grid(True, alpha=0.3)
        
        for bar, value in zip(bars, write_performance):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 2. Compaction Read 성능 비교
        read_performance = [initial_seq_read, degraded_seq_read]
        
        bars = ax2.bar(categories, read_performance, color=['lightgreen', 'orange'], alpha=0.8)
        ax2.set_ylabel('Read Performance (MB/s)')
        ax2.set_title('Compaction Read Performance (System Read Only)')
        ax2.grid(True, alpha=0.3)
        
        for bar, value in zip(bars, read_performance):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 3. 성능 열화율 분석
        write_degradation_rate = fillrandom_analysis['performance_analysis']['degraded']['write_degradation_rate']
        compaction_read_degradation_rate = fillrandom_analysis['compaction_impact']['compaction_read_degradation_rate']
        
        degradation_categories = ['Write Degradation', 'Compaction Read Degradation']
        degradation_rates = [write_degradation_rate * 100, compaction_read_degradation_rate * 100]
        
        colors = ['red' if dr > 50 else 'orange' if dr > 20 else 'green' for dr in degradation_rates]
        bars = ax3.bar(degradation_categories, degradation_rates, color=colors, alpha=0.7)
        ax3.set_ylabel('Degradation Rate (%)')
        ax3.set_title('Performance Degradation Rates')
        ax3.set_ylim(0, 100)
        
        for bar, value in zip(bars, degradation_rates):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 4. FillRandom 워크로드 특성
        workload_characteristics = [
            'Sequential Write Only',
            'Compaction Read Only',
            'No User Reads',
            'System Reads Only'
        ]
        
        # 성능 특성 표시
        ax4.text(0.1, 0.8, 'FillRandom Workload Characteristics:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.7, '• Write: Sequential Write만 발생', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.6, '• Read: Compaction에서만 발생', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.5, '• 사용자 Read: 없음', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.4, '• 시스템 Read: Compaction만', fontsize=12, transform=ax4.transAxes)
        
        ax4.text(0.1, 0.2, 'Performance Impact:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.1, f'• Write 열화율: {write_degradation_rate:.1%}', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.05, f'• Compaction Read 열화율: {compaction_read_degradation_rate:.1%}', fontsize=12, transform=ax4.transAxes)
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('FillRandom Workload Characteristics')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/fillrandom_workload_performance_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ FillRandom 워크로드 성능 시각화 완료")
    
    def save_results(self, fillrandom_analysis):
        """결과 저장"""
        print("💾 FillRandom 워크로드 성능 분석 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/fillrandom_workload_performance_analysis.json", 'w') as f:
                json.dump(fillrandom_analysis, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_fillrandom_workload_report(fillrandom_analysis)
            with open(f"{self.results_dir}/fillrandom_workload_performance_analysis_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_fillrandom_workload_report(self, fillrandom_analysis):
        """FillRandom 워크로드 성능 분석 보고서 생성"""
        report = f"""# FillRandom Workload Performance Analysis

## Overview
This report analyzes the performance characteristics of FillRandom workload using Phase-A data.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## FillRandom Workload Characteristics
- **Write Type**: Sequential Write Only (사용자 Write)
- **Read Type**: Compaction Read Only (시스템 Read)
- **User Reads**: None
- **System Reads**: Compaction Only

## Phase-A Performance Data
- **Initial Seq Write**: {self.phase_a_data['initial']['seq_write']['write_bw']:.1f} MB/s
- **Initial Seq Read**: {self.phase_a_data['initial']['seq_read']['read_bw']:.1f} MB/s
- **Degraded Seq Write**: {self.phase_a_data['degraded']['seq_write']['write_bw']:.1f} MB/s
- **Degraded Seq Read**: {self.phase_a_data['degraded']['seq_read']['read_bw']:.1f} MB/s

## Key Findings: FillRandom Workload Performance

### 1. Write Performance (User Operations)
- **Initial Performance**: {self.phase_a_data['initial']['seq_write']['write_bw']:.1f} MB/s
- **Degraded Performance**: {self.phase_a_data['degraded']['seq_write']['write_bw']:.1f} MB/s
- **Degradation Rate**: {fillrandom_analysis['performance_analysis']['degraded']['write_degradation_rate']:.1%}

### 2. Compaction Read Performance (System Operations)
- **Initial Performance**: {self.phase_a_data['initial']['seq_read']['read_bw']:.1f} MB/s
- **Degraded Performance**: {self.phase_a_data['degraded']['seq_read']['read_bw']:.1f} MB/s
- **Degradation Rate**: {fillrandom_analysis['compaction_impact']['compaction_read_degradation_rate']:.1%}

## Performance Analysis

### 1. Write Path Performance
- **Operation Type**: Sequential Write Only
- **Performance Impact**: {fillrandom_analysis['performance_analysis']['degraded']['write_degradation_rate']:.1%} degradation
- **Implication**: 사용자 Write 성능이 크게 저하됨

### 2. Compaction Read Performance
- **Operation Type**: Compaction Read Only
- **Performance Impact**: {fillrandom_analysis['compaction_impact']['compaction_read_degradation_rate']:.1%} degradation
- **Implication**: Compaction 과정에서 Read 성능 저하

### 3. Overall Workload Impact
- **Write-Heavy Workload**: Sequential Write만 발생
- **No User Reads**: 사용자 Read 없음
- **System Reads Only**: Compaction에서만 Read 발생
- **Performance Bottleneck**: Write 성능 열화가 주요 병목

## Key Insights

### 1. FillRandom Workload 특성
- **Write Operations**: Sequential Write만 발생 (Random Write 없음)
- **Read Operations**: Compaction에서만 발생 (사용자 Read 없음)
- **Workload Pattern**: Write-Heavy, No User Reads

### 2. Performance Degradation Pattern
- **Write Performance**: {fillrandom_analysis['performance_analysis']['degraded']['write_degradation_rate']:.1%} degradation
- **Compaction Read Performance**: {fillrandom_analysis['compaction_impact']['compaction_read_degradation_rate']:.1%} degradation
- **Overall Impact**: Write 성능 열화가 전체 성능에 미치는 영향이 큼

### 3. Implications for RocksDB Modeling
- **Write Path**: Sequential Write 성능이 전체 성능에 미치는 영향
- **Compaction Path**: Compaction Read 성능이 Compaction 효율성에 미치는 영향
- **Model Accuracy**: FillRandom 워크로드 특성을 정확히 반영한 모델링 필요

## Visualization
![FillRandom Workload Performance Analysis](fillrandom_workload_performance_analysis.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 FillRandom 워크로드 성능 분석 시작")
        print("=" * 60)
        
        fillrandom_analysis = self.analyze_fillrandom_workload_performance()
        self.create_fillrandom_workload_visualization(fillrandom_analysis)
        self.save_results(fillrandom_analysis)
        
        print("=" * 60)
        print("✅ FillRandom 워크로드 성능 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = FillRandom_Workload_Performance_Analyzer()
    analyzer.run_analysis()










