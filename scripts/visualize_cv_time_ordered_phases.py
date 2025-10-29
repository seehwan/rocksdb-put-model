#!/usr/bin/env python3
"""
CV-based Phase Detection with Time Ordering
CV 값 변화를 시간 순서대로 분석하여 phase 구분
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def detect_time_ordered_phases(df, cv_column='cv_rolling'):
    """
    CV 값 변화를 시간 순서대로 분석하여 phase 경계 탐지
    """
    # NaN 제거 및 시간 순 정렬
    valid_df = df[df[cv_column].notna()].copy()
    valid_df = valid_df.sort_values('time_hours')
    
    cv_values = valid_df[cv_column].values
    time_values = valid_df['time_hours'].values
    n_samples = len(cv_values)
    
    # CV 변화율 분석
    window_size = 2000  # 더 큰 window로 안정적인 변화 탐지
    
    print(f"📊 CV 변화 분석 (window={window_size})...")
    
    # 시간을 3등분하여 각 구간의 CV 특성 분석
    n_segments = 10  # 전체를 10 구간으로 나눠서 분석
    segment_size = n_samples // n_segments
    
    cv_by_segment = []
    for i in range(n_segments):
        start_idx = i * segment_size
        end_idx = (i + 1) * segment_size if i < n_segments - 1 else n_samples
        segment_cv = cv_values[start_idx:end_idx]
        mean_cv = np.mean(segment_cv)
        std_cv = np.std(segment_cv)
        time_mid = time_values[(start_idx + end_idx) // 2]
        
        cv_by_segment.append({
            'segment': i,
            'time': time_mid,
            'mean_cv': mean_cv,
            'std_cv': std_cv
        })
    
    cv_by_segment_df = pd.DataFrame(cv_by_segment)
    
    print(f"\n📊 구간별 CV 평균:")
    for _, row in cv_by_segment_df.iterrows():
        print(f"  구간 {row['segment']}: 시간={row['time']:.2f}h, CV={row['mean_cv']:.3f}")
    
    # CV가 높은 구간 찾기 (Initial phase)
    # CV가 중간인 구간 찾기 (Middle phase)
    # CV가 낮은 구간 찾기 (Final phase)
    
    # 방법: 각 구간의 평균 CV로 판단
    cv_means = cv_by_segment_df['mean_cv'].values
    
    # percentile 기반 임계값
    cv_high_threshold = np.percentile(cv_means, 66.7)  # 상위 1/3
    cv_low_threshold = np.percentile(cv_means, 33.3)    # 하위 1/3
    
    print(f"\n📊 CV 구간 임계값:")
    print(f"  High (상위 33%): {cv_high_threshold:.6f}")
    print(f"  Low (하위 33%): {cv_low_threshold:.6f}")
    
    # 각 구간을 phase로 분류
    segment_phases = {}
    for _, row in cv_by_segment_df.iterrows():
        cv_mean = row['mean_cv']
        if cv_mean >= cv_high_threshold:
            segment_phases[row['segment']] = 'initial'
        elif cv_mean >= cv_low_threshold:
            segment_phases[row['segment']] = 'middle'
        else:
            segment_phases[row['segment']] = 'final'
    
    # 시간에 따라 phase 할당
    def assign_phase_by_time(time_hours):
        for i, row in cv_by_segment_df.iterrows():
            if time_hours < row['time']:
                return segment_phases.get(row['segment'], 'middle')
        return 'final'  # 마지막 구간
    
    df['phase_time_cv'] = df['time_hours'].apply(assign_phase_by_time)
    
    return df

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV-based Phase Detection (Time-Ordered)")
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
    
    # CV 기반 시간 순서 phase 탐지
    df = detect_time_ordered_phases(df)
    
    # Phase별 통계
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통계 (시간 순서):")
    phase_info = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_time_cv'] == phase]
        if len(phase_df) > 0:
            cv_mean = phase_df['cv_rolling'].mean()
            cv_std = phase_df['cv_rolling'].std()
            
            qps_mean = phase_df['qps'].mean()
            qps_std = phase_df['qps'].std()
            cv_integrated = qps_std / qps_mean if qps_mean > 0 else 0
            
            time_min = phase_df['time_hours'].min()
            time_max = phase_df['time_hours'].max()
            
            phase_info[phase] = {
                'samples': len(phase_df),
                'cv_mean': cv_mean,
                'cv_integrated': cv_integrated,
                'qps_mean': qps_mean,
                'time_range': (time_min, time_max)
            }
            
            print(f"  {phase}:")
            print(f"    샘플: {len(phase_df):,}개")
            print(f"    시간: {time_min:.2f} ~ {time_max:.2f} hours")
            print(f"    Rolling CV: {cv_mean:.6f}")
            print(f"    통합 CV: {cv_integrated:.6f}")
            print(f"    QPS 평균: {qps_mean:.0f} ops/sec")
    
    # 시각화
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Rolling CV over Time with Phase Colors
    ax1.plot(df['time_hours'], df['cv_rolling'], color='#2C3E50', alpha=0.7, linewidth=1.5)
    
    for phase in ['initial', 'middle', 'final']:
        phase_mask = df['phase_time_cv'] == phase
        if phase_mask.any():
            ax1.scatter(df[phase_mask]['time_hours'], df[phase_mask]['cv_rolling'], 
                       color=colors[phase], alpha=0.3, s=1, label=f'{phase.title()} Phase')
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('Rolling CV', fontsize=18, fontfamily='Times')
    ax1.set_title('CV-Based Phase Detection (Time-Ordered)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # 2. CV Distribution by Phase
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_time_cv'] == phase]
        if len(phase_df) > 0:
            ax2.hist(phase_df['cv_rolling'].dropna(), bins=50, alpha=0.6, 
                    label=f'{phase.title()} Phase', color=colors[phase], density=True)
    
    ax2.set_xlabel('CV Value', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('Density', fontsize=18, fontfamily='Times')
    ax2.set_title('CV Distribution by Phase', fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # 3. QPS over Time
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_time_cv'] == phase]
        if len(phase_df) > 0:
            ax3.plot(phase_df['time_hours'], phase_df['qps'], 
                    color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
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
    
    output_path = Path("figs/cv_time_ordered_phases.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

