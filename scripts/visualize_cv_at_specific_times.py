#!/usr/bin/env python3
"""
CV Analysis at Specific Time Points
15h, 42h 근처에서 CV 변화 분석 및 phase 구분
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV Analysis at Specific Times (15h, 42h)")
    print("=" * 80)
    
    # 데이터 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['qps'] = df['interval_qps']
    
    print(f"✅ 데이터 로드: {len(df):,}개 샘플")
    
    # Rolling CV 계산
    window = 1000
    df['mean_rolling'] = df['qps'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['qps'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    # df_valid 초기화
    df_valid = df[df['cv_rolling'].notna()].copy()
    
    # 10h, 42h 근처에서 CV 변화 분석
    print(f"\n📊 CV 변화 포인트 분석:")
    
    # 10h 근처 분석
    range_10 = df_valid[(df_valid['time_hours'] >= 5) & (df_valid['time_hours'] <= 15)]
    if len(range_10) > 0:
        cv_around_10 = range_10['cv_rolling']
        print(f"  Around 10h (5-15h):")
        print(f"    CV 평균: {cv_around_10.mean():.6f}")
        print(f"    CV 표준편차: {cv_around_10.std():.6f}")
    
    # 42h 근처 분석
    range_42 = df_valid[(df_valid['time_hours'] >= 37) & (df_valid['time_hours'] <= 47)]
    if len(range_42) > 0:
        cv_around_42 = range_42['cv_rolling']
        print(f"  Around 42h (37-47h):")
        print(f"    CV 평균: {cv_around_42.mean():.6f}")
        print(f"    CV 표준편차: {cv_around_42.std():.6f}")
    
    # 전체 구간별로 나누기 (10h, 42h 기준)
    df['phase'] = df['time_hours'].apply(
        lambda h: 'initial' if h < 10 else ('middle' if h < 42 else 'final')
    )
    
    # df_valid에도 phase 정보 복사
    df_valid = df[df['cv_rolling'].notna()].copy()
    df_valid['phase'] = df_valid['time_hours'].apply(
        lambda h: 'initial' if h < 10 else ('middle' if h < 42 else 'final')
    )
    
    # Phase별 통계
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통계 (10h, 42h 기준):")
    phase_info = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        cv_valid = phase_df['cv_rolling'].dropna()
        
        if len(cv_valid) > 0:
            # 통합 CV 계산
            qps_mean = phase_df['qps'].mean()
            qps_std = phase_df['qps'].std()
            cv_integrated = qps_std / qps_mean if qps_mean > 0 else 0
            
            # Rolling CV 통계
            cv_rolling_mean = cv_valid.mean()
            
            time_min = phase_df['time_hours'].min()
            time_max = phase_df['time_hours'].max()
            
            phase_info[phase] = {
                'samples': len(phase_df),
                'cv_rolling_mean': cv_rolling_mean,
                'cv_integrated': cv_integrated,
                'qps_mean': qps_mean,
                'time_range': (time_min, time_max)
            }
            
            print(f"  {phase}:")
            print(f"    시간: {time_min:.2f} ~ {time_max:.2f} hours")
            print(f"    샘플: {len(phase_df):,}개")
            print(f"    Rolling CV 평균: {cv_rolling_mean:.6f}")
            print(f"    통합 CV: {cv_integrated:.6f}")
            print(f"    QPS 평균: {qps_mean:.0f} ops/sec")
    
    # 시각화
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. CV over Time with Phase Boundaries
    ax1.plot(df_valid['time_hours'], df_valid['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=1.5, label='Rolling CV')
    
    # Phase별 색상 표시
    for phase in ['initial', 'middle', 'final']:
        phase_mask = (df_valid['phase'] == phase)
        if phase_mask.any():
            ax1.scatter(df_valid[phase_mask]['time_hours'], df_valid[phase_mask]['cv_rolling'], 
                       color=colors[phase], alpha=0.3, s=1, label=f'{phase.title()} Phase')
    
    # Phase boundaries
    for boundary, label in [(10, '10h (Initial→Middle)'), (42, '42h (Middle→Final)')]:
        ax1.axvline(x=boundary, color='black', linestyle='--', linewidth=3, alpha=0.7, label=label)
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('Rolling CV', fontsize=18, fontfamily='Times')
    ax1.set_title('CV Over Time (10h, 42h Boundaries)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # 2. CV Distribution by Phase
    for phase in ['initial', 'middle', 'final']:
        phase_df = df_valid[df_valid['phase'] == phase]
        if len(phase_df) > 0:
            ax2.hist(phase_df['cv_rolling'].dropna(), bins=50, alpha=0.6, 
                    label=f'{phase.title()} Phase', color=colors[phase], density=True)
    
    # 10h, 42h boundaries 표시
    for boundary, color in [(10, 'red'), (42, 'blue')]:
        if boundary == 10:
            phase_df = df_valid[df_valid['phase'] == 'initial']
        else:
            phase_df = df_valid[df_valid['phase'] == 'middle']
        if len(phase_df) > 0:
            cv_at_boundary = phase_df[(phase_df['time_hours'].abs() - boundary) <= 1]['cv_rolling']
            if len(cv_at_boundary) > 0:
                ax2.axvline(x=cv_at_boundary.mean(), color=color, linestyle='--', 
                           linewidth=2, label=f'{boundary}h Boundary', alpha=0.7)
    
    ax2.set_xlabel('CV Value', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('Density', fontsize=18, fontfamily='Times')
    ax2.set_title('CV Distribution by Phase', fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # 3. QPS over Time
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        ax3.plot(phase_df['time_hours'], phase_df['qps'], 
                color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
    for boundary in [10, 42]:
        ax3.axvline(x=boundary, color='black', linestyle='--', linewidth=2, alpha=0.7)
    
    ax3.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax3.set_ylabel('QPS (ops/sec)', fontsize=18, fontfamily='Times')
    ax3.set_title('QPS Over Time', fontsize=20, fontfamily='Times', fontweight='bold')
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=16)
    ax3.set_yscale('log')
    
    # 4. Phase별 통합 CV
    if phase_info:
        phases = list(phase_info.keys())
        cvs = [phase_info[p]['cv_integrated'] for p in phases]
        
        bars = ax4.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
        for i, phase in enumerate(phases):
            cv_val = cvs[i]
            ax4.text(i, cv_val + max(cvs)*0.05, f'{cv_val:.3f}', ha='center', va='bottom', 
                    fontsize=18, fontweight='bold', fontfamily='Times')
        
        ax4.set_xlabel('Phase', fontsize=18, fontfamily='Times')
        ax4.set_ylabel('Integrated CV', fontsize=18, fontfamily='Times')
        ax4.set_title('Phase-Level Integrated CV', fontsize=20, fontfamily='Times', fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.tick_params(axis='both', which='major', labelsize=16)
        if cvs:
            ax4.set_ylim(0, max(cvs) * 1.3)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_at_10h_42h.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

