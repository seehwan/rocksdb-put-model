#!/usr/bin/env python3
"""
Phase-A Device Envelope 시각화 스크립트
fio 그리드 스윕 결과를 다양한 방식으로 시각화합니다.
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 16

def parse_fio_json(file_path: str) -> Dict:
    """fio JSON 결과 파일을 파싱합니다."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    jobs = data.get('jobs', [])
    if not jobs:
        raise ValueError(f"No jobs found in {file_path}")
    
    # 총 대역폭 계산
    total_read_bw = 0
    total_write_bw = 0
    total_read_iops = 0
    total_write_iops = 0
    
    for job in jobs:
        read_bw = job.get('read', {}).get('bw', 0)  # KiB/s
        write_bw = job.get('write', {}).get('bw', 0)  # KiB/s
        read_iops = job.get('read', {}).get('iops', 0)
        write_iops = job.get('write', {}).get('iops', 0)
        
        total_read_bw += read_bw
        total_write_bw += write_bw
        total_read_iops += read_iops
        total_write_iops += write_iops
    
    # MiB/s로 변환
    total_bw_mibs = (total_read_bw + total_write_bw) / 1024
    read_bw_mibs = total_read_bw / 1024
    write_bw_mibs = total_write_bw / 1024
    
    return {
        'read_bw_mibs': read_bw_mibs,
        'write_bw_mibs': write_bw_mibs,
        'total_bw_mibs': total_bw_mibs,
        'read_iops': total_read_iops,
        'write_iops': total_write_iops,
        'total_iops': total_read_iops + total_write_iops,
        'read_ratio': total_read_bw / (total_read_bw + total_write_bw) if (total_read_bw + total_write_bw) > 0 else 0
    }

def load_grid_data(results_dir: str) -> pd.DataFrame:
    """그리드 스윕 결과를 DataFrame으로 로드합니다."""
    results_dir = Path(results_dir)
    
    # 그리드 파라미터
    rho_r_values = [0, 25, 50, 75, 100]
    iodepth_values = [1, 4, 16, 64]
    numjobs_values = [1, 2, 4]
    bs_values = [4, 64, 1024]
    
    data = []
    
    for rho_r in rho_r_values:
        for iodepth in iodepth_values:
            for numjobs in numjobs_values:
                for bs_k in bs_values:
                    result_file = results_dir / f"result_{rho_r}_{iodepth}_{numjobs}_{bs_k}.json"
                    
                    if result_file.exists():
                        try:
                            result = parse_fio_json(str(result_file))
                            data.append({
                                'rho_r': rho_r,
                                'iodepth': iodepth,
                                'numjobs': numjobs,
                                'bs_k': bs_k,
                                'read_bw_mibs': result['read_bw_mibs'],
                                'write_bw_mibs': result['write_bw_mibs'],
                                'total_bw_mibs': result['total_bw_mibs'],
                                'read_iops': result['read_iops'],
                                'write_iops': result['write_iops'],
                                'total_iops': result['total_iops'],
                                'read_ratio': result['read_ratio']
                            })
                        except Exception as e:
                            print(f"Warning: Failed to parse {result_file}: {e}")
    
    return pd.DataFrame(data)

def create_bandwidth_heatmap(df: pd.DataFrame, output_dir: str):
    """대역폭 히트맵을 생성합니다."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Device Envelope: Bandwidth Heatmaps', fontsize=16)
    
    # 1. Read Ratio vs IODepth (numjobs=4, bs=64K)
    pivot1 = df[(df['numjobs'] == 4) & (df['bs_k'] == 64)].pivot_table(
        values='total_bw_mibs', index='rho_r', columns='iodepth', aggfunc='mean'
    )
    sns.heatmap(pivot1, annot=True, fmt='.0f', cmap='viridis', ax=axes[0,0])
    axes[0,0].set_title('Total BW: Read Ratio vs IODepth\n(numjobs=4, bs=64K)')
    axes[0,0].set_xlabel('IODepth')
    axes[0,0].set_ylabel('Read Ratio (%)')
    
    # 2. IODepth vs Block Size (rho_r=50%, numjobs=4)
    pivot2 = df[(df['rho_r'] == 50) & (df['numjobs'] == 4)].pivot_table(
        values='total_bw_mibs', index='iodepth', columns='bs_k', aggfunc='mean'
    )
    sns.heatmap(pivot2, annot=True, fmt='.0f', cmap='plasma', ax=axes[0,1])
    axes[0,1].set_title('Total BW: IODepth vs Block Size\n(rho_r=50%, numjobs=4)')
    axes[0,1].set_xlabel('Block Size (KiB)')
    axes[0,1].set_ylabel('IODepth')
    
    # 3. Read vs Write Bandwidth (numjobs=4, bs=64K)
    pivot3_read = df[(df['numjobs'] == 4) & (df['bs_k'] == 64)].pivot_table(
        values='read_bw_mibs', index='rho_r', columns='iodepth', aggfunc='mean'
    )
    sns.heatmap(pivot3_read, annot=True, fmt='.0f', cmap='Blues', ax=axes[1,0])
    axes[1,0].set_title('Read BW: Read Ratio vs IODepth\n(numjobs=4, bs=64K)')
    axes[1,0].set_xlabel('IODepth')
    axes[1,0].set_ylabel('Read Ratio (%)')
    
    pivot3_write = df[(df['numjobs'] == 4) & (df['bs_k'] == 64)].pivot_table(
        values='write_bw_mibs', index='rho_r', columns='iodepth', aggfunc='mean'
    )
    sns.heatmap(pivot3_write, annot=True, fmt='.0f', cmap='Reds', ax=axes[1,1])
    axes[1,1].set_title('Write BW: Read Ratio vs IODepth\n(numjobs=4, bs=64K)')
    axes[1,1].set_xlabel('IODepth')
    axes[1,1].set_ylabel('Read Ratio (%)')
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/bandwidth_heatmaps.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_curves(df: pd.DataFrame, output_dir: str):
    """성능 곡선을 생성합니다."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Device Envelope: Performance Curves', fontsize=16)
    
    # 1. Read Ratio vs Total Bandwidth (iodepth=64, numjobs=4)
    subset = df[(df['iodepth'] == 64) & (df['numjobs'] == 4)]
    for bs in [4, 64, 1024]:
        bs_data = subset[subset['bs_k'] == bs]
        axes[0,0].plot(bs_data['rho_r'], bs_data['total_bw_mibs'], 
                      marker='o', label=f'bs={bs}K', linewidth=2)
    axes[0,0].set_xlabel('Read Ratio (%)')
    axes[0,0].set_ylabel('Total Bandwidth (MiB/s)')
    axes[0,0].set_title('Total BW vs Read Ratio\n(iodepth=64, numjobs=4)')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. IODepth vs Total Bandwidth (rho_r=50%, numjobs=4)
    subset = df[(df['rho_r'] == 50) & (df['numjobs'] == 4)]
    for bs in [4, 64, 1024]:
        bs_data = subset[subset['bs_k'] == bs]
        axes[0,1].plot(bs_data['iodepth'], bs_data['total_bw_mibs'], 
                      marker='s', label=f'bs={bs}K', linewidth=2)
    axes[0,1].set_xlabel('IODepth')
    axes[0,1].set_ylabel('Total Bandwidth (MiB/s)')
    axes[0,1].set_title('Total BW vs IODepth\n(rho_r=50%, numjobs=4)')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    # 3. NumJobs vs Total Bandwidth (rho_r=50%, iodepth=64)
    subset = df[(df['rho_r'] == 50) & (df['iodepth'] == 64)]
    for bs in [4, 64, 1024]:
        bs_data = subset[subset['bs_k'] == bs]
        axes[1,0].plot(bs_data['numjobs'], bs_data['total_bw_mibs'], 
                      marker='^', label=f'bs={bs}K', linewidth=2)
    axes[1,0].set_xlabel('NumJobs')
    axes[1,0].set_ylabel('Total Bandwidth (MiB/s)')
    axes[1,0].set_title('Total BW vs NumJobs\n(rho_r=50%, iodepth=64)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. Block Size vs Total Bandwidth (rho_r=50%, iodepth=64, numjobs=4)
    subset = df[(df['rho_r'] == 50) & (df['iodepth'] == 64) & (df['numjobs'] == 4)]
    axes[1,1].plot(subset['bs_k'], subset['total_bw_mibs'], 
                  marker='d', color='red', linewidth=3, markersize=8)
    axes[1,1].set_xlabel('Block Size (KiB)')
    axes[1,1].set_ylabel('Total Bandwidth (MiB/s)')
    axes[1,1].set_title('Total BW vs Block Size\n(rho_r=50%, iodepth=64, numjobs=4)')
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/performance_curves.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_io_characteristics(df: pd.DataFrame, output_dir: str):
    """I/O 특성을 분석합니다."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Device Envelope: I/O Characteristics', fontsize=16)
    
    # 1. Read/Write Bandwidth 분포
    axes[0,0].scatter(df['read_bw_mibs'], df['write_bw_mibs'], 
                     c=df['rho_r'], cmap='viridis', alpha=0.6, s=50)
    axes[0,0].set_xlabel('Read Bandwidth (MiB/s)')
    axes[0,0].set_ylabel('Write Bandwidth (MiB/s)')
    axes[0,0].set_title('Read vs Write Bandwidth\n(Color: Read Ratio %)')
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. IOPS vs Bandwidth
    axes[0,1].scatter(df['total_iops'], df['total_bw_mibs'], 
                     c=df['bs_k'], cmap='plasma', alpha=0.6, s=50)
    axes[0,1].set_xlabel('Total IOPS')
    axes[0,1].set_ylabel('Total Bandwidth (MiB/s)')
    axes[0,1].set_title('IOPS vs Bandwidth\n(Color: Block Size KiB)')
    axes[0,1].grid(True, alpha=0.3)
    
    # 3. IODepth vs IOPS
    subset = df[df['numjobs'] == 4]
    for bs in [4, 64, 1024]:
        bs_data = subset[subset['bs_k'] == bs]
        axes[1,0].plot(bs_data['iodepth'], bs_data['total_iops'], 
                      marker='o', label=f'bs={bs}K', linewidth=2)
    axes[1,0].set_xlabel('IODepth')
    axes[1,0].set_ylabel('Total IOPS')
    axes[1,0].set_title('IODepth vs IOPS\n(numjobs=4)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. 최대 성능 요약
    max_bw = df['total_bw_mibs'].max()
    max_iops = df['total_iops'].max()
    max_read_bw = df['read_bw_mibs'].max()
    max_write_bw = df['write_bw_mibs'].max()
    
    metrics = ['Max Total BW', 'Max IOPS', 'Max Read BW', 'Max Write BW']
    values = [max_bw, max_iops, max_read_bw, max_write_bw]
    colors = ['blue', 'green', 'orange', 'red']
    
    bars = axes[1,1].bar(metrics, values, color=colors, alpha=0.7)
    axes[1,1].set_ylabel('Value')
    axes[1,1].set_title('Peak Performance Summary')
    axes[1,1].tick_params(axis='x', rotation=45)
    axes[1,1].grid(True, alpha=0.3)
    
    for bar, val in zip(bars, values):
        axes[1,1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                      f'{val:.0f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(f"{output_dir}/io_characteristics.png", dpi=300, bbox_inches='tight')
    plt.close()

def create_summary_statistics(df: pd.DataFrame, output_dir: str):
    """요약 통계를 생성합니다."""
    # 통계 계산
    stats = {
        'Total Tests': len(df),
        'Max Total BW (MiB/s)': df['total_bw_mibs'].max(),
        'Min Total BW (MiB/s)': df['total_bw_mibs'].min(),
        'Mean Total BW (MiB/s)': df['total_bw_mibs'].mean(),
        'Max Read BW (MiB/s)': df['read_bw_mibs'].max(),
        'Max Write BW (MiB/s)': df['write_bw_mibs'].max(),
        'Max IOPS': df['total_iops'].max(),
        'Mean IOPS': df['total_iops'].mean()
    }
    
    # 최적 설정 찾기
    max_bw_idx = df['total_bw_mibs'].idxmax()
    max_bw_config = df.loc[max_bw_idx]
    
    print("\n=== Phase-A Device Envelope Summary ===")
    print(f"Total tests completed: {stats['Total Tests']}")
    print(f"Max Total Bandwidth: {stats['Max Total BW (MiB/s)']:.1f} MiB/s")
    print(f"Max Read Bandwidth: {stats['Max Read BW (MiB/s)']:.1f} MiB/s")
    print(f"Max Write Bandwidth: {stats['Max Write BW (MiB/s)']:.1f} MiB/s")
    print(f"Max IOPS: {stats['Max IOPS']:.0f}")
    print(f"\nOptimal Configuration:")
    print(f"  Read Ratio: {max_bw_config['rho_r']}%")
    print(f"  IODepth: {max_bw_config['iodepth']}")
    print(f"  NumJobs: {max_bw_config['numjobs']}")
    print(f"  Block Size: {max_bw_config['bs_k']} KiB")
    print(f"  Total BW: {max_bw_config['total_bw_mibs']:.1f} MiB/s")
    
    # 통계를 파일로 저장
    with open(f"{output_dir}/summary_statistics.txt", 'w') as f:
        f.write("Phase-A Device Envelope Summary\n")
        f.write("=" * 40 + "\n\n")
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
        f.write(f"\nOptimal Configuration:\n")
        f.write(f"  Read Ratio: {max_bw_config['rho_r']}%\n")
        f.write(f"  IODepth: {max_bw_config['iodepth']}\n")
        f.write(f"  NumJobs: {max_bw_config['numjobs']}\n")
        f.write(f"  Block Size: {max_bw_config['bs_k']} KiB\n")
        f.write(f"  Total BW: {max_bw_config['total_bw_mibs']:.1f} MiB/s\n")

def main():
    parser = argparse.ArgumentParser(description='Visualize Phase-A Device Envelope results')
    parser.add_argument('results_dir', help='Directory containing fio JSON result files')
    parser.add_argument('--output', '-o', default='visualizations', 
                       help='Output directory for visualizations')
    
    args = parser.parse_args()
    
    # 출력 디렉토리 생성
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print(f"Loading data from: {args.results_dir}")
    
    # 데이터 로드
    df = load_grid_data(args.results_dir)
    print(f"Loaded {len(df)} test results")
    
    if len(df) == 0:
        print("No data found! Please check the results directory.")
        return
    
    # 시각화 생성
    print("Creating visualizations...")
    
    print("  - Bandwidth heatmaps...")
    create_bandwidth_heatmap(df, str(output_dir))
    
    print("  - Performance curves...")
    create_performance_curves(df, str(output_dir))
    
    print("  - I/O characteristics...")
    create_io_characteristics(df, str(output_dir))
    
    print("  - Summary statistics...")
    create_summary_statistics(df, str(output_dir))
    
    print(f"\nVisualizations saved to: {output_dir}")
    print("Generated files:")
    print("  - bandwidth_heatmaps.png")
    print("  - performance_curves.png")
    print("  - io_characteristics.png")
    print("  - summary_statistics.txt")

if __name__ == "__main__":
    main()


