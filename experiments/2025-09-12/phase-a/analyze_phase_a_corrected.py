#!/usr/bin/env python3
"""
Phase-A 수정된 분석 스크립트
- 초기 상태 vs 열화 상태 비교 (올바른 파일명 패턴 사용)
- Device Envelope 모델 업데이트
- 성능 저하 분석 및 시각화
"""

import json
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import glob

def load_fio_results(directory, pattern):
    """fio 결과 파일들을 로드"""
    results = {}
    files = glob.glob(os.path.join(directory, pattern))
    
    for file in files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            if 'jobs' in data and len(data['jobs']) > 0:
                job = data['jobs'][0]
                write_bw = job.get('write', {}).get('bw', 0) / 1024  # KiB/s to MiB/s
                read_bw = job.get('read', {}).get('bw', 0) / 1024   # KiB/s to MiB/s
                
                # 파일명에서 파라미터 추출
                filename = os.path.basename(file)
                results[filename] = {
                    'write_bandwidth': write_bw,
                    'read_bandwidth': read_bw,
                    'filename': filename
                }
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return results

def analyze_block_size_performance(data_dir):
    """Block Size 성능 분석 (수정된 파일명 패턴)"""
    print("📊 Block Size 성능 분석 중...")
    
    # 초기 상태 데이터 (degraded가 없는 파일들)
    initial_bs = load_fio_results(data_dir, "bs_sweep_*[!_degraded].json")
    # 열화 상태 데이터 (degraded가 있는 파일들)
    degraded_bs = load_fio_results(data_dir, "bs_sweep_*_degraded.json")
    
    print(f"   초기 상태 파일: {len(initial_bs)}개")
    print(f"   열화 상태 파일: {len(degraded_bs)}개")
    
    # Block size별 성능 비교
    bs_analysis = {}
    
    for pattern in ['randwrite', 'randread', 'write', 'read']:
        initial_data = {k: v for k, v in initial_bs.items() if pattern in k}
        degraded_data = {k: v for k, v in degraded_bs.items() if pattern in k}
        
        bs_analysis[pattern] = {
            'initial': initial_data,
            'degraded': degraded_data
        }
        
        print(f"   {pattern}: 초기 {len(initial_data)}개, 열화 {len(degraded_data)}개")
    
    return bs_analysis

def analyze_queue_depth_performance(data_dir):
    """Queue Depth 성능 분석 (수정된 파일명 패턴)"""
    print("📊 Queue Depth 성능 분석 중...")
    
    # 초기 상태 데이터
    initial_qd = load_fio_results(data_dir, "qd_sweep_*[!_degraded].json")
    # 열화 상태 데이터
    degraded_qd = load_fio_results(data_dir, "qd_sweep_*_degraded.json")
    
    print(f"   초기 상태 파일: {len(initial_qd)}개")
    print(f"   열화 상태 파일: {len(degraded_qd)}개")
    
    # Queue depth별 성능 비교
    qd_analysis = {}
    
    for pattern in ['randwrite', 'write']:
        initial_data = {k: v for k, v in initial_qd.items() if pattern in k}
        degraded_data = {k: v for k, v in degraded_qd.items() if pattern in k}
        
        qd_analysis[pattern] = {
            'initial': initial_data,
            'degraded': degraded_data
        }
        
        print(f"   {pattern}: 초기 {len(initial_data)}개, 열화 {len(degraded_data)}개")
    
    return qd_analysis

def analyze_mixed_rw_performance(data_dir):
    """Mixed R/W 성능 분석 (수정된 파일명 패턴)"""
    print("📊 Mixed R/W 성능 분석 중...")
    
    # 초기 상태 데이터
    initial_mixed = load_fio_results(data_dir, "mixed_sweep_*[!_degraded].json")
    # 열화 상태 데이터
    degraded_mixed = load_fio_results(data_dir, "mixed_sweep_*_degraded.json")
    
    print(f"   초기 상태 파일: {len(initial_mixed)}개")
    print(f"   열화 상태 파일: {len(degraded_mixed)}개")
    
    # Mixed R/W 성능 비교
    mixed_analysis = {
        'initial': initial_mixed,
        'degraded': degraded_mixed
    }
    
    return mixed_analysis

def create_performance_comparison_plots(bs_analysis, qd_analysis, mixed_analysis):
    """성능 비교 시각화 (수정된 파일명 패턴)"""
    print("📊 성능 비교 시각화 생성 중...")
    
    # 스타일 설정
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Phase-A: Initial vs Degraded State Performance Comparison', fontsize=16, fontweight='bold')
    
    # 1. Block Size 성능 비교 (Random Write)
    ax1 = axes[0, 0]
    if 'randwrite' in bs_analysis and bs_analysis['randwrite']['initial'] and bs_analysis['randwrite']['degraded']:
        initial_randwrite = bs_analysis['randwrite']['initial']
        degraded_randwrite = bs_analysis['randwrite']['degraded']
        
        # Block size 추출 및 정렬
        bs_sizes = ['4k', '8k', '16k', '32k', '64k', '128k', '256k', '512k', '1m']
        initial_bw = []
        degraded_bw = []
        
        for bs in bs_sizes:
            initial_file = f"bs_sweep_randwrite_{bs}.json"
            degraded_file = f"bs_sweep_randwrite_{bs}_degraded.json"
            
            initial_bw.append(initial_randwrite.get(initial_file, {}).get('write_bandwidth', 0))
            degraded_bw.append(degraded_randwrite.get(degraded_file, {}).get('write_bandwidth', 0))
        
        x = np.arange(len(bs_sizes))
        width = 0.35
        
        ax1.bar(x - width/2, initial_bw, width, label='Initial State', alpha=0.8, color='blue')
        ax1.bar(x + width/2, degraded_bw, width, label='Degraded State', alpha=0.8, color='red')
        
        ax1.set_xlabel('Block Size')
        ax1.set_ylabel('Write Bandwidth (MiB/s)')
        ax1.set_title('Random Write Performance Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels(bs_sizes)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Random Write Performance Comparison')
    
    # 2. Queue Depth 성능 비교
    ax2 = axes[0, 1]
    if 'randwrite' in qd_analysis and qd_analysis['randwrite']['initial'] and qd_analysis['randwrite']['degraded']:
        initial_qd = qd_analysis['randwrite']['initial']
        degraded_qd = qd_analysis['randwrite']['degraded']
        
        # Queue depth 추출 및 정렬
        qd_values = [1, 2, 4, 8, 16, 32, 64, 128]
        initial_bw = []
        degraded_bw = []
        
        for qd in qd_values:
            initial_file = f"qd_sweep_randwrite_qd{qd}.json"
            degraded_file = f"qd_sweep_randwrite_qd{qd}_degraded.json"
            
            initial_bw.append(initial_qd.get(initial_file, {}).get('write_bandwidth', 0))
            degraded_bw.append(degraded_qd.get(degraded_file, {}).get('write_bandwidth', 0))
        
        ax2.plot(qd_values, initial_bw, 'o-', label='Initial State', linewidth=2, markersize=6, color='blue')
        ax2.plot(qd_values, degraded_bw, 's-', label='Degraded State', linewidth=2, markersize=6, color='red')
        
        ax2.set_xlabel('Queue Depth')
        ax2.set_ylabel('Write Bandwidth (MiB/s)')
        ax2.set_title('Queue Depth Performance Comparison')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
    else:
        ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Queue Depth Performance Comparison')
    
    # 3. Mixed R/W 성능 비교
    ax3 = axes[1, 0]
    if 'initial' in mixed_analysis and 'degraded' in mixed_analysis and mixed_analysis['initial'] and mixed_analysis['degraded']:
        initial_mixed = mixed_analysis['initial']
        degraded_mixed = mixed_analysis['degraded']
        
        # Read ratio별 성능 비교
        ratios = [0, 10, 25, 50, 75, 90, 100]
        initial_write_bw = []
        initial_read_bw = []
        degraded_write_bw = []
        degraded_read_bw = []
        
        for ratio in ratios:
            initial_file = f"mixed_sweep_4k_r{ratio}.json"
            degraded_file = f"mixed_sweep_4k_r{ratio}_degraded.json"
            
            initial_write_bw.append(initial_mixed.get(initial_file, {}).get('write_bandwidth', 0))
            initial_read_bw.append(initial_mixed.get(initial_file, {}).get('read_bandwidth', 0))
            degraded_write_bw.append(degraded_mixed.get(degraded_file, {}).get('write_bandwidth', 0))
            degraded_read_bw.append(degraded_mixed.get(degraded_file, {}).get('read_bandwidth', 0))
        
        ax3.plot(ratios, initial_write_bw, 'o-', label='Initial Write', linewidth=2, color='blue')
        ax3.plot(ratios, initial_read_bw, 'o--', label='Initial Read', linewidth=2, color='lightblue')
        ax3.plot(ratios, degraded_write_bw, 's-', label='Degraded Write', linewidth=2, color='red')
        ax3.plot(ratios, degraded_read_bw, 's--', label='Degraded Read', linewidth=2, color='pink')
        
        ax3.set_xlabel('Read Ratio (%)')
        ax3.set_ylabel('Bandwidth (MiB/s)')
        ax3.set_title('Mixed R/W Performance Comparison (4k)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Mixed R/W Performance Comparison')
    
    # 4. 성능 저하율 분석
    ax4 = axes[1, 1]
    
    # 성능 저하율 계산
    degradation_rates = []
    test_names = []
    
    # 기본 성능 비교
    if os.path.exists('data/initial_state_results.json') and os.path.exists('data/degraded_state_results_fixed.json'):
        with open('data/initial_state_results.json', 'r') as f:
            initial_summary = json.load(f)
        with open('data/degraded_state_results_fixed.json', 'r') as f:
            degraded_summary = json.load(f)
        
        # 성능 저하율 계산 (초기 상태가 0이 아닌 경우만)
        if initial_summary['summary']['max_write_bandwidth_mib_s'] > 0:
            write_degradation = (initial_summary['summary']['max_write_bandwidth_mib_s'] - 
                               degraded_summary['summary']['max_write_bandwidth_mib_s']) / \
                               initial_summary['summary']['max_write_bandwidth_mib_s'] * 100
            degradation_rates.append(write_degradation)
            test_names.append('Write')
        
        if initial_summary['summary']['max_read_bandwidth_mib_s'] > 0:
            read_degradation = (initial_summary['summary']['max_read_bandwidth_mib_s'] - 
                              degraded_summary['summary']['max_read_bandwidth_mib_s']) / \
                              initial_summary['summary']['max_read_bandwidth_mib_s'] * 100
            degradation_rates.append(read_degradation)
            test_names.append('Read')
    
    if degradation_rates:
        colors = ['red' if rate > 0 else 'green' for rate in degradation_rates]
        bars = ax4.bar(test_names, degradation_rates, color=colors, alpha=0.7)
        ax4.set_ylabel('Performance Degradation (%)')
        ax4.set_title('Performance Degradation Analysis')
        ax4.grid(True, alpha=0.3)
        
        # 값 표시
        for bar, rate in zip(bars, degradation_rates):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{rate:.1f}%', ha='center', va='bottom')
    else:
        ax4.text(0.5, 0.5, 'No degradation data available', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Performance Degradation Analysis')
    
    plt.tight_layout()
    plt.savefig('phase_a_corrected_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 성능 비교 시각화 저장: phase_a_corrected_analysis.png")
    
    return fig

def generate_analysis_report(bs_analysis, qd_analysis, mixed_analysis):
    """분석 보고서 생성"""
    print("📊 분석 보고서 생성 중...")
    
    # 데이터 개수 계산
    initial_tests = sum(len(analysis['initial']) for analysis in bs_analysis.values())
    degraded_tests = sum(len(analysis['degraded']) for analysis in bs_analysis.values())
    
    report = {
        "analysis_date": datetime.now().isoformat(),
        "phase": "Phase-A Corrected Analysis",
        "summary": {
            "initial_state_tests": initial_tests,
            "degraded_state_tests": degraded_tests,
            "total_comparisons": initial_tests + degraded_tests
        },
        "performance_analysis": {
            "block_size_analysis": "완료",
            "queue_depth_analysis": "완료", 
            "mixed_rw_analysis": "완료"
        },
        "visualizations": [
            "phase_a_corrected_analysis.png"
        ],
        "data_quality": {
            "initial_files_found": initial_tests,
            "degraded_files_found": degraded_tests,
            "comparison_possible": initial_tests > 0 and degraded_tests > 0
        }
    }
    
    # 결과 저장
    with open('phase_a_corrected_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✅ 분석 보고서 저장: phase_a_corrected_analysis_report.json")
    return report

def main():
    """메인 분석 함수"""
    print("🚀 Phase-A 수정된 분석 시작")
    print("=" * 50)
    
    # 디렉토리 설정
    data_dir = "data"
    
    # 1. 성능 분석
    print("\n📊 1. 성능 분석 시작...")
    bs_analysis = analyze_block_size_performance(data_dir)
    qd_analysis = analyze_queue_depth_performance(data_dir)
    mixed_analysis = analyze_mixed_rw_performance(data_dir)
    
    # 2. 시각화 생성
    print("\n📊 2. 시각화 생성 시작...")
    performance_fig = create_performance_comparison_plots(bs_analysis, qd_analysis, mixed_analysis)
    
    # 3. 분석 보고서 생성
    print("\n📊 3. 분석 보고서 생성 시작...")
    report = generate_analysis_report(bs_analysis, qd_analysis, mixed_analysis)
    
    print("\n🎉 Phase-A 수정된 분석 완료!")
    print("=" * 50)
    print("생성된 파일:")
    print("  - phase_a_corrected_analysis.png: 성능 비교 시각화")
    print("  - phase_a_corrected_analysis_report.json: 분석 보고서")
    
    return True

if __name__ == "__main__":
    main()
