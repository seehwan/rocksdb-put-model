#!/usr/bin/env python3
"""
시간별 QPS와 S_max 시각화
X축: 시간, Y축: QPS와 S_max
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 시간별 QPS vs S_max 시각화")
    print("=" * 80)
    
    # 데이터 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['qps'] = df['interval_qps']
    
    # Phase 구분
    def assign_phase(hour):
        if hour < 9.81:
            return 'initial'
        elif hour < 42.00:
            return 'middle'
        else:
            return 'final'
    
    df['phase'] = df['time_hours'].apply(assign_phase)
    
    # 모델 파라미터
    device_write_bw = 1484.0  # MB/s
    record_size = 1040  # bytes
    
    params = {
        'initial': {'U': 0.033, 'C': 3.40},
        'middle': {'U': 0.139, 'C': 0.60},
        'final': {'U': 0.067, 'C': 1.10}
    }
    
    # Phase별로 S_max 계산 (동적 계산)
    def calculate_dynamic_smax(row):
        phase = row['phase']
        time_hours = row['time_hours']
        
        # Base U, C
        U = params[phase]['U']
        C = params[phase]['C']
        
        # Phase 내부에서 시간에 따른 변화 반영
        # Device BW가 시간에 따라 감소할 수 있음을 모델링
        if phase == 'initial':
            # Initial: 높은 성능 유지 (처음부터 빠름)
            time_factor = 1.0
        elif phase == 'middle':
            # Middle: 약간의 감소 (0.95-1.0)
            progress = (time_hours - 9.81) / (42.00 - 9.81)
            time_factor = 1.0 - progress * 0.05
        else:  # final
            # Final: 더 큰 감소 (0.90-1.0)
            progress = (time_hours - 42.00) / (96.61 - 42.00)
            time_factor = 1.0 - progress * 0.10
        
        return (device_write_bw * 1024 * 1024) / record_size * U * C * time_factor
    
    df['s_max'] = df.apply(calculate_dynamic_smax, axis=1)
    
    # 실제 QPS (MiB/s로 변환)
    df['qps_mbps'] = df['qps'] * 1040 / (1024 * 1024)
    df['s_max_mbps'] = df['s_max'] * 1040 / (1024 * 1024)
    
    # Phase별 색상
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    # 시각화 (크고 명확한 대비)
    fig, axes = plt.subplots(2, 1, figsize=(18, 16))
    
    # Phase별 색상 개선 (더 강한 대비)
    phase_colors = {
        'initial': {'qps': '#E74C3C', 'smax': '#8E44AD'},  # 빨강과 보라
        'middle': {'qps': '#2ECC71', 'smax': '#16A085'},   # 녹색과 청록
        'final': {'qps': '#3498DB', 'smax': '#2980B9'}     # 파랑과 진파랑
    }
    
    # 1. QPS vs S_max (단위: MiB/s)
    ax1 = axes[0]
    
    # Phase별로 QPS와 S_max를 다른 색으로 표시
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        
        # QPS (실제 값)
        ax1.plot(phase_df['time_hours'], phase_df['qps_mbps'], 
                color=phase_colors[phase]['qps'], alpha=0.8, linewidth=2.5, 
                label=f'{phase.title()} Actual QPS', linestyle='-')
        
        # S_max (예측 값) - 해당 phase 구간에서만 표시
        avg_smax = phase_df['s_max_mbps'].mean()
        t_min = phase_df['time_hours'].min()
        t_max = phase_df['time_hours'].max()
        ax1.plot([t_min, t_max], [avg_smax, avg_smax], 
                color=phase_colors[phase]['smax'], linestyle='--', 
                linewidth=3, alpha=0.9, label=f'{phase.title()} Predicted S_max')
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Write Rate (MiB/s)', fontsize=22, fontfamily='Times')
    ax1.set_title('QPS vs S_max Comparison: Write Rate', 
                 fontsize=24, fontfamily='Times', fontweight='bold', pad=20)
    ax1.legend(fontsize=16, loc='upper right')
    ax1.grid(True, alpha=0.3, linewidth=1.5)
    ax1.tick_params(axis='both', which='major', labelsize=20)
    # 1e6 표시 크기 키우기
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))
    for label in ax1.get_yticklabels():
        label.set_fontsize(20)
        label.set_fontfamily('Times')
    
    # Phase 경계 표시
    ax1.axvline(x=9.81, color='black', linestyle=':', linewidth=3, alpha=0.8)
    ax1.axvline(x=42.00, color='black', linestyle=':', linewidth=3, alpha=0.8)
    ax1.text(9.81, ax1.get_ylim()[1]*0.95, '9.81h', fontsize=18, fontfamily='Times', 
             ha='center', va='bottom', weight='bold')
    ax1.text(42.00, ax1.get_ylim()[1]*0.95, '42.00h', fontsize=18, fontfamily='Times', 
             ha='center', va='bottom', weight='bold')
    
    # 2. QPS vs S_max (단위: ops/sec)
    ax2 = axes[1]
    
    # Phase별로 QPS와 S_max를 다른 색으로 표시
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        
        # QPS (실제 값)
        ax2.plot(phase_df['time_hours'], phase_df['qps'], 
                color=phase_colors[phase]['qps'], alpha=0.8, linewidth=2.5, 
                label=f'{phase.title()} Actual QPS', linestyle='-')
        
        # S_max (예측 값) - 해당 phase 구간에서만 표시
        avg_smax = phase_df['s_max'].mean()
        t_min = phase_df['time_hours'].min()
        t_max = phase_df['time_hours'].max()
        ax2.plot([t_min, t_max], [avg_smax, avg_smax], 
                color=phase_colors[phase]['smax'], linestyle='--', 
                linewidth=3, alpha=0.9, label=f'{phase.title()} Predicted S_max')
    
    ax2.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('QPS (ops/sec)', fontsize=22, fontfamily='Times')
    ax2.set_title('QPS vs S_max Comparison: Operations per Second', 
                 fontsize=24, fontfamily='Times', fontweight='bold', pad=20)
    ax2.legend(fontsize=16, loc='upper right')
    ax2.grid(True, alpha=0.3, linewidth=1.5)
    ax2.tick_params(axis='both', which='major', labelsize=20)
    # 1e6 표시 크기 키우기
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.2f}M' if x >= 1e6 else f'{x/1e3:.1f}K' if x >= 1e3 else f'{x:.0f}'))
    for label in ax2.get_yticklabels():
        label.set_fontsize(20)
        label.set_fontfamily('Times')
    
    # Phase 경계 표시
    ax2.axvline(x=9.81, color='black', linestyle=':', linewidth=3, alpha=0.8)
    ax2.axvline(x=42.00, color='black', linestyle=':', linewidth=3, alpha=0.8)
    ax2.text(9.81, ax2.get_ylim()[1]*0.95, '9.81h', fontsize=18, fontfamily='Times', 
             ha='center', va='bottom', weight='bold')
    ax2.text(42.00, ax2.get_ylim()[1]*0.95, '42.00h', fontsize=18, fontfamily='Times', 
             ha='center', va='bottom', weight='bold')
    
    plt.suptitle('QPS vs S_max Comparison Over Time (CV-based Phase Boundaries)', 
                 fontsize=28, fontfamily='Times', fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_path = Path("figs/qps_vs_smax_over_time.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    # Phase별 통계 출력
    print("\n📊 Phase별 통계:")
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        avg_qps = phase_df['qps'].mean()
        avg_smax = phase_df['s_max'].mean()
        accuracy = 100 * (1 - abs(avg_smax - avg_qps) / avg_qps)
        
        print(f"\n{phase.upper()} Phase:")
        print(f"  시간: {phase_df['time_hours'].min():.2f} - {phase_df['time_hours'].max():.2f}h")
        print(f"  평균 QPS: {avg_qps:.0f} ops/sec")
        print(f"  S_max: {avg_smax:.0f} ops/sec")
        print(f"  정확도: {accuracy:.1f}%")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

