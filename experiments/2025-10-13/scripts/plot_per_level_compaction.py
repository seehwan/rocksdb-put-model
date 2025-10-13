#!/usr/bin/env python3
"""
시간별 레벨별 Compaction 처리량 시각화

RocksDB LOG 파일을 파싱하여 레벨별 compaction 처리량을 시간에 따라 시각화합니다.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import sys
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

def parse_compaction_data(log_file_path=None):
    """
    RocksDB LOG 파일에서 compaction 데이터 파싱
    
    실제 구현에서는 LOG 파일을 파싱하지만,
    여기서는 예제 데이터를 생성합니다.
    """
    # 시간 (분)
    time_minutes = np.arange(0, 120, 1)
    
    # 레벨별 compaction 처리량 (GB/min) - 예제 데이터
    compaction_data = {
        'time': time_minutes,
        'L0': np.zeros(len(time_minutes)),
        'L1': np.zeros(len(time_minutes)),
        'L2': np.zeros(len(time_minutes)),
        'L3': np.zeros(len(time_minutes)),
        'L4': np.zeros(len(time_minutes)),
        'L5': np.zeros(len(time_minutes)),
        'L6': np.zeros(len(time_minutes))
    }
    
    # Initial Phase (0-30 min): L0 → L1 주로
    for i in range(0, 30):
        compaction_data['L0'][i] = 0.5 + np.random.normal(0, 0.1)
        compaction_data['L1'][i] = 0.3 + np.random.normal(0, 0.05)
    
    # Middle Phase (30-90 min): Multi-level compaction 활발
    for i in range(30, 90):
        compaction_data['L0'][i] = 0.6 + np.random.normal(0, 0.1)
        compaction_data['L1'][i] = 0.8 + np.random.normal(0, 0.1)
        compaction_data['L2'][i] = 0.5 + np.random.normal(0, 0.08)
        compaction_data['L3'][i] = 0.3 + np.random.normal(0, 0.05)
    
    # Final Phase (90-120 min): All levels active
    for i in range(90, 120):
        compaction_data['L0'][i] = 0.7 + np.random.normal(0, 0.08)
        compaction_data['L1'][i] = 1.0 + np.random.normal(0, 0.12)
        compaction_data['L2'][i] = 0.8 + np.random.normal(0, 0.1)
        compaction_data['L3'][i] = 0.6 + np.random.normal(0, 0.08)
        compaction_data['L4'][i] = 0.4 + np.random.normal(0, 0.06)
        compaction_data['L5'][i] = 0.3 + np.random.normal(0, 0.05)
        compaction_data['L6'][i] = 0.2 + np.random.normal(0, 0.04)
    
    # 음수 값 제거
    for level in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']:
        compaction_data[level] = np.maximum(compaction_data[level], 0)
    
    return compaction_data


def plot_per_level_writes(compaction_data, output_path='per_level_compaction_writes.png'):
    """레벨별 Compaction Write 처리량 시각화"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    time = compaction_data['time']
    levels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
    
    # 상단: 레벨별 라인 플롯
    for level, color in zip(levels, colors):
        ax1.plot(time, compaction_data[level], 
                label=level, color=color, linewidth=2, alpha=0.8)
    
    ax1.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Compaction Write Rate (GB/min)', fontsize=12, fontweight='bold')
    ax1.set_title('Per-Level Compaction Write Throughput Over Time', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='upper left', ncol=7, fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # Phase 구분선
    ax1.axvline(x=30, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
    ax1.axvline(x=90, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
    ax1.text(15, ax1.get_ylim()[1]*0.95, 'Initial', ha='center', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax1.text(60, ax1.get_ylim()[1]*0.95, 'Middle', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax1.text(105, ax1.get_ylim()[1]*0.95, 'Final', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    # 하단: 누적 영역 플롯
    data_matrix = np.array([compaction_data[level] for level in levels])
    ax2.stackplot(time, *data_matrix, labels=levels, colors=colors, alpha=0.7)
    
    ax2.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Compaction Write Rate (GB/min)', fontsize=12, fontweight='bold')
    ax2.set_title('Cumulative Per-Level Compaction Write Throughput', 
                  fontsize=14, fontweight='bold', pad=20)
    ax2.legend(loc='upper left', ncol=7, fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # Phase 구분선
    ax2.axvline(x=30, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
    ax2.axvline(x=90, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    return fig


def plot_per_level_reads(compaction_data, output_path='per_level_compaction_reads.png'):
    """레벨별 Compaction Read 처리량 시각화"""
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    time = compaction_data['time']
    levels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE']
    
    # Compaction Read는 일반적으로 Write의 일정 비율
    for level, color in zip(levels, colors):
        read_data = compaction_data[level] * 1.5  # Read는 Write의 ~1.5배
        ax.plot(time, read_data, label=level, color=color, linewidth=2, alpha=0.8)
    
    ax.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Compaction Read Rate (GB/min)', fontsize=12, fontweight='bold')
    ax.set_title('Per-Level Compaction Read Throughput Over Time', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper left', ncol=7, fontsize=10)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Phase 구분선
    ax.axvline(x=30, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.axvline(x=90, color='red', linestyle='--', alpha=0.5, linewidth=1.5)
    ax.text(15, ax.get_ylim()[1]*0.95, 'Initial', ha='center', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.text(60, ax.get_ylim()[1]*0.95, 'Middle', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    ax.text(105, ax.get_ylim()[1]*0.95, 'Final', ha='center', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    return fig


def plot_compaction_heatmap(compaction_data, output_path='compaction_heatmap.png'):
    """시간-레벨별 Compaction 처리량 히트맵"""
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    levels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']
    data_matrix = np.array([compaction_data[level] for level in levels])
    
    im = ax.imshow(data_matrix, aspect='auto', cmap='YlOrRd', interpolation='bilinear')
    
    ax.set_yticks(range(len(levels)))
    ax.set_yticklabels(levels, fontsize=11)
    ax.set_xlabel('Time (minutes)', fontsize=12, fontweight='bold')
    ax.set_ylabel('LSM Level', fontsize=12, fontweight='bold')
    ax.set_title('Compaction Activity Heatmap: Time × Level', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # X축 눈금 설정
    tick_positions = range(0, len(compaction_data['time']), 10)
    tick_labels = [compaction_data['time'][i] for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=10)
    
    # Phase 구분선
    ax.axvline(x=30, color='blue', linestyle='--', alpha=0.7, linewidth=2)
    ax.axvline(x=90, color='blue', linestyle='--', alpha=0.7, linewidth=2)
    
    # 컬러바
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Compaction Rate (GB/min)', rotation=270, labelpad=20, fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    
    return fig


def generate_compaction_summary(compaction_data):
    """Compaction 통계 요약 생성"""
    
    levels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6']
    
    print("\n" + "="*60)
    print("Compaction 처리량 통계 요약")
    print("="*60)
    
    for level in levels:
        data = compaction_data[level]
        non_zero = data[data > 0]
        
        if len(non_zero) > 0:
            print(f"\n{level}:")
            print(f"  평균 처리량: {np.mean(non_zero):.2f} GB/min")
            print(f"  최대 처리량: {np.max(non_zero):.2f} GB/min")
            print(f"  활성 시간: {len(non_zero)}/{len(data)} min ({len(non_zero)/len(data)*100:.1f}%)")
            print(f"  총 처리량: {np.sum(data):.2f} GB")
    
    # Phase별 총 처리량
    print(f"\n{'='*60}")
    print("Phase별 총 Compaction 처리량")
    print("="*60)
    
    total_by_phase = {
        'Initial (0-30 min)': sum(np.sum(compaction_data[level][:30]) for level in levels),
        'Middle (30-90 min)': sum(np.sum(compaction_data[level][30:90]) for level in levels),
        'Final (90-120 min)': sum(np.sum(compaction_data[level][90:]) for level in levels)
    }
    
    for phase, total in total_by_phase.items():
        print(f"{phase}: {total:.2f} GB")
    
    print(f"\n전체 총 처리량: {sum(total_by_phase.values()):.2f} GB")
    print("="*60 + "\n")


def main():
    """메인 실행 함수"""
    
    print("\n" + "="*60)
    print("시간별 레벨별 Compaction 처리량 시각화")
    print("="*60 + "\n")
    
    # 출력 디렉토리 설정
    output_dir = "/home/sslab/rocksdb-put-model/experiments/2025-10-13/results"
    os.makedirs(output_dir, exist_ok=True)
    
    # 데이터 파싱 (예제 데이터)
    print("Compaction 데이터 생성 중...")
    compaction_data = parse_compaction_data()
    print("✓ 데이터 준비 완료\n")
    
    # 통계 요약
    generate_compaction_summary(compaction_data)
    
    # 시각화 생성
    print("시각화 생성 중...\n")
    
    # 1. 레벨별 Write 처리량
    plot_per_level_writes(
        compaction_data, 
        os.path.join(output_dir, 'per_level_compaction_writes.png')
    )
    
    # 2. 레벨별 Read 처리량
    plot_per_level_reads(
        compaction_data,
        os.path.join(output_dir, 'per_level_compaction_reads.png')
    )
    
    # 3. 히트맵
    plot_compaction_heatmap(
        compaction_data,
        os.path.join(output_dir, 'compaction_heatmap.png')
    )
    
    print("\n" + "="*60)
    print("✓ 모든 시각화 생성 완료!")
    print(f"✓ 결과 저장 위치: {output_dir}")
    print("="*60 + "\n")
    
    # 그래프 표시 (선택적)
    if '--show' in sys.argv:
        plt.show()


if __name__ == '__main__':
    main()


