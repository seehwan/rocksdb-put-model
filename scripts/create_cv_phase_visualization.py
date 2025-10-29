#!/usr/bin/env python3
"""
Comprehensive CV Phase Detection Visualization
10h, 42h 기준과 동적 탐지 비교 시각화
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.patches as mpatches

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV Phase Detection Visualization")
    print("=" * 80)
    
    # 데이터 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['qps'] = df['interval_qps']
    
    # Rolling CV 계산
    window = 1000
    df['mean_rolling'] = df['qps'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['qps'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    # 1. Fixed boundaries (10h, 42h)
    df['phase_fixed'] = df['time_hours'].apply(
        lambda h: 'initial' if h < 10 else ('middle' if h < 42 else 'final')
    )
    
    df_valid = df[df['cv_rolling'].notna()].copy()
    df_valid['phase_fixed'] = df_valid['time_hours'].apply(
        lambda h: 'initial' if h < 10 else ('middle' if h < 42 else 'final')
    )
    
    df['phase_fixed'] = df['time_hours'].apply(
        lambda h: 'initial' if h < 10 else ('middle' if h < 42 else 'final')
    )
    
    # 2. Dynamic detection (9.81h, 14.50h)
    boundary_1_dynamic = 9.81
    boundary_2_dynamic = 14.50
    
    df['phase_dynamic'] = df['time_hours'].apply(
        lambda h: 'initial' if h < boundary_1_dynamic else ('middle' if h < boundary_2_dynamic else 'final')
    )
    df_valid['phase_dynamic'] = df_valid['time_hours'].apply(
        lambda h: 'initial' if h < boundary_1_dynamic else ('middle' if h < boundary_2_dynamic else 'final')
    )
    
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    # Phase별 통계
    print("\n📊 Fixed Boundaries (10h, 42h):")
    phase_fixed_stats = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_fixed'] == phase]
        cv_integrated = phase_df['qps'].std() / phase_df['qps'].mean()
        phase_fixed_stats[phase] = {
            'samples': len(phase_df),
            'cv_integrated': cv_integrated,
            'qps_mean': phase_df['qps'].mean(),
            'time_range': (phase_df['time_hours'].min(), phase_df['time_hours'].max())
        }
        print(f"  {phase}: {phase_df['time_hours'].min():.2f}-{phase_df['time_hours'].max():.2f}h, CV={cv_integrated:.3f}")
    
    print("\n📊 Dynamic Detection (9.81h, 14.50h):")
    phase_dynamic_stats = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_dynamic'] == phase]
        cv_integrated = phase_df['qps'].std() / phase_df['qps'].mean()
        phase_dynamic_stats[phase] = {
            'samples': len(phase_df),
            'cv_integrated': cv_integrated,
            'qps_mean': phase_df['qps'].mean(),
            'time_range': (phase_df['time_hours'].min(), phase_df['time_hours'].max())
        }
        print(f"  {phase}: {phase_df['time_hours'].min():.2f}-{phase_df['time_hours'].max():.2f}h, CV={cv_integrated:.3f}")
    
    # 시각화
    fig = plt.figure(figsize=(24, 18))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Row 1: CV over Time with Phase Boundaries
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.plot(df_valid['time_hours'], df_valid['cv_rolling'], color='#2C3E50', alpha=0.7, linewidth=2, label='Rolling CV')
    
    for phase in ['initial', 'middle', 'final']:
        phase_mask = (df_valid['phase_fixed'] == phase)
        if phase_mask.any():
            ax1.scatter(df_valid[phase_mask]['time_hours'], df_valid[phase_mask]['cv_rolling'], 
                       color=colors[phase], alpha=0.2, s=1)
    
    for boundary, label, color in [(10, '10h Boundary', 'red'), (42, '42h Boundary', 'blue')]:
        ax1.axvline(x=boundary, color=color, linestyle='--', linewidth=3, alpha=0.8, label=label)
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('Coefficient of Variation (CV)', fontsize=18, fontfamily='Times')
    ax1.set_title('Rolling CV Over Time with Phase Boundaries (10h, 42h)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # Row 1: Phase Statistics
    ax2 = fig.add_subplot(gs[0, 2])
    phases = ['initial', 'middle', 'final']
    cvs_fixed = [phase_fixed_stats[p]['cv_integrated'] for p in phases]
    cvs_dynamic = [phase_dynamic_stats[p]['cv_integrated'] for p in phases]
    
    x = np.arange(len(phases))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, cvs_fixed, width, label='Fixed (10h, 42h)', color='steelblue', alpha=0.7)
    bars2 = ax2.bar(x + width/2, cvs_dynamic, width, label='Dynamic (9.8h, 14.5h)', color='coral', alpha=0.7)
    
    for i, phase in enumerate(phases):
        height1 = cvs_fixed[i]
        height2 = cvs_dynamic[i]
        ax2.text(i - width/2, height1 + max(max(cvs_fixed), max(cvs_dynamic))*0.05, f'{height1:.3f}', 
                ha='center', va='bottom', fontsize=14, fontweight='bold', fontfamily='Times')
        ax2.text(i + width/2, height2 + max(max(cvs_fixed), max(cvs_dynamic))*0.05, f'{height2:.3f}', 
                ha='center', va='bottom', fontsize=14, fontweight='bold', fontfamily='Times')
    
    ax2.set_xlabel('Phase', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('Integrated CV', fontsize=18, fontfamily='Times')
    ax2.set_title('CV Comparison: Fixed vs Dynamic', fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([p.title() for p in phases])
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=16)
    ax2.set_ylim(0, max(max(cvs_fixed), max(cvs_dynamic)) * 1.3)
    
    # Row 2: QPS over Time
    ax3 = fig.add_subplot(gs[1, :2])
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_fixed'] == phase]
        ax3.plot(phase_df['time_hours'], phase_df['qps'], 
                color=colors[phase], alpha=0.6, linewidth=1.5, label=f'{phase.title()} Phase')
    
    for boundary in [10, 42]:
        ax3.axvline(x=boundary, color='black', linestyle='--', linewidth=2, alpha=0.7)
    
    ax3.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax3.set_ylabel('QPS (ops/sec)', fontsize=18, fontfamily='Times')
    ax3.set_title('QPS Over Time (Fixed Boundaries)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=16)
    ax3.set_yscale('log')
    
    # Row 2: Sample Counts
    ax4 = fig.add_subplot(gs[1, 2])
    samples_fixed = [phase_fixed_stats[p]['samples'] for p in phases]
    samples_dynamic = [phase_dynamic_stats[p]['samples'] for p in phases]
    
    bars1 = ax4.bar(x - width/2, samples_fixed, width, label='Fixed', color='steelblue', alpha=0.7)
    bars2 = ax4.bar(x + width/2, samples_dynamic, width, label='Dynamic', color='coral', alpha=0.7)
    
    ax4.set_xlabel('Phase', fontsize=18, fontfamily='Times')
    ax4.set_ylabel('Sample Count', fontsize=18, fontfamily='Times')
    ax4.set_title('Sample Count Comparison', fontsize=20, fontfamily='Times', fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([p.title() for p in phases])
    ax4.legend(fontsize=12)
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.tick_params(axis='both', which='major', labelsize=16)
    
    # Row 3: CV Distribution by Phase
    ax5 = fig.add_subplot(gs[2, :])
    for phase in ['initial', 'middle', 'final']:
        phase_df_fixed = df_valid[df_valid['phase_fixed'] == phase]
        if len(phase_df_fixed) > 0:
            ax5.hist(phase_df_fixed['cv_rolling'], bins=50, alpha=0.5, 
                    label=f'{phase.title()} Phase', color=colors[phase], density=True, histtype='step', linewidth=2)
    
    ax5.axvline(x=0.50, color='red', linestyle='--', linewidth=2, alpha=0.7, label='CV=0.50')
    
    ax5.set_xlabel('CV Value', fontsize=18, fontfamily='Times')
    ax5.set_ylabel('Density', fontsize=18, fontfamily='Times')
    ax5.set_title('CV Distribution by Phase (Fixed Boundaries)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax5.legend(fontsize=12)
    ax5.grid(True, alpha=0.3)
    ax5.tick_params(axis='both', which='major', labelsize=16)
    
    plt.suptitle('Comprehensive CV Phase Detection Analysis', fontsize=24, fontfamily='Times', fontweight='bold', y=0.995)
    
    output_path = Path("figs/comprehensive_cv_phase_detection.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    # Additional: Method Summary Visualization (Dynamic Detection)
    fig2, ax = plt.subplots(figsize=(14, 10))
    
    # Dynamic phase boundaries: 9.81h, 14.50h
    boundary_1 = 9.81
    boundary_2 = 14.50
    
    # Phase regions with proper colors
    ax.axvspan(0, boundary_1, color=colors['initial'], alpha=0.15, label='Initial Phase')
    ax.axvspan(boundary_1, boundary_2, color=colors['middle'], alpha=0.15, label='Middle Phase')
    ax.axvspan(boundary_2, df_valid['time_hours'].max(), color=colors['final'], alpha=0.15, label='Final Phase')
    
    # CV with annotations
    ax.plot(df_valid['time_hours'], df_valid['cv_rolling'], 
            color='#2C3E50', alpha=0.8, linewidth=3, label='Rolling CV (window=1000)')
    
    # Phase boundaries
    for boundary, y, label, color in [(boundary_1, 0.72, 'Initial→Middle\n(9.81h)', 'red'), 
                                        (boundary_2, 0.52, 'Middle→Final\n(14.50h)', 'blue')]:
        ax.axvline(x=boundary, color=color, linestyle='--', linewidth=4, alpha=0.9, zorder=10)
        ax.text(boundary, y, label, ha='center', va='bottom', fontsize=18, fontweight='bold', 
                fontfamily='Times', color=color, bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9))
    
    # Text annotations with improved positioning (based on actual CV values)
    ax.text(4.9, 0.65, 'Initial Phase\nCV = 0.714\nHigh Variability', ha='center', va='center', 
            fontsize=18, fontweight='bold', fontfamily='Times', 
            bbox=dict(boxstyle='round,pad=1', facecolor='white', alpha=0.95, edgecolor='#FF6B6B', linewidth=2))
    ax.text(12.16, 0.52, 'Middle Phase\nCV = 0.492\nModerate Variability', ha='center', va='center', 
            fontsize=18, fontweight='bold', fontfamily='Times', 
            bbox=dict(boxstyle='round,pad=1', facecolor='white', alpha=0.95, edgecolor='#4ECDC4', linewidth=2))
    ax.text(55.5, 0.50, 'Final Phase\nCV = 0.497\nLower Variability', ha='center', va='center', 
            fontsize=18, fontweight='bold', fontfamily='Times', 
            bbox=dict(boxstyle='round,pad=1', facecolor='white', alpha=0.95, edgecolor='#45B7D1', linewidth=2))
    
    ax.set_xlabel('Time (hours)', fontsize=24, fontfamily='Times')
    ax.set_ylabel('Coefficient of Variation (CV)', fontsize=24, fontfamily='Times')
    ax.set_title('Dynamic CV-Based Phase Detection Strategy', fontsize=28, fontfamily='Times', fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', which='major', labelsize=20)
    ax.set_xlim(0, 100)
    
    output_path2 = Path("figs/cv_phase_strategy.png")
    output_path2.parent.mkdir(exist_ok=True)
    fig2.savefig(output_path2, dpi=300, bbox_inches='tight')
    
    print(f"✅ 저장됨: {output_path2}")
    print(f"📄 파일 크기: {output_path2.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

