#!/usr/bin/env python3
"""
CV-Based Phase Detection
CV 값 변화를 분석하여 phase 구분 재설정
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def detect_phases_from_cv(df, cv_column='cv_rolling'):
    """
    CV 값 변화를 분석하여 phase 경계 자동 탐지
    """
    # NaN 제거
    valid_df = df[df[cv_column].notna()].copy()
    
    if len(valid_df) == 0:
        return df
    
    # CV 값을 시간에 따라 정렬
    valid_df = valid_df.sort_values('time_hours')
    
    # CV 변화율 계산
    cv_values = valid_df[cv_column].values
    time_values = valid_df['time_hours'].values
    
    # CV 변화 추세 분석
    window_size = 1000
    n_samples = len(cv_values)
    
    # CV 값의 분포 확인
    cv_percentile_25 = np.percentile(cv_values, 25)
    cv_percentile_75 = np.percentile(cv_values, 75)
    cv_median = np.median(cv_values)
    
    print(f"\n📊 CV 분포 통계:")
    print(f"  25% percentile: {cv_percentile_25:.6f}")
    print(f"  Median: {cv_median:.6f}")
    print(f"  75% percentile: {cv_percentile_75:.6f}")
    
    # Phase 경계 탐지: CV 변화가 급격한 지점 찾기
    # 각 timepoint에서 앞뒤 CV 차이 계산
    cv_changes = []
    for i in range(window_size, n_samples - window_size):
        before_mean = np.mean(cv_values[i-window_size:i])
        after_mean = np.mean(cv_values[i:i+window_size])
        change = abs(after_mean - before_mean)
        cv_changes.append({
            'time': time_values[i],
            'change': change
        })
    
    cv_changes_df = pd.DataFrame(cv_changes)
    
    # CV 변화가 큰 지점 찾기
    threshold = cv_changes_df['change'].quantile(0.95)  # 상위 5% 변화
    high_change_points = cv_changes_df[cv_changes_df['change'] > threshold]
    
    print(f"\n📊 CV 급격한 변화 지점:")
    if len(high_change_points) > 0:
        for idx, row in high_change_points.iterrows():
            print(f"  {row['time']:.2f} hours: change={row['change']:.6f}")
    else:
        print("  급격한 변화 지점 없음")
    
    # CV 기반 임계값으로 phase 구분
    # Method 1: CV 값의 terciles 사용
    cv_sorted = np.sort(cv_values)
    n = len(cv_sorted)
    tercile_1_idx = n // 3
    tercile_2_idx = 2 * n // 3
    
    threshold_low = cv_sorted[tercile_2_idx]  # 높은 CV
    threshold_mid = cv_sorted[tercile_1_idx]  # 낮은 CV
    
    print(f"\n📊 CV Tercile 기반 임계값:")
    print(f"  High CV threshold: {threshold_low:.6f} (상위 33%)")
    print(f"  Low CV threshold: {threshold_mid:.6f} (하위 33%)")
    
    # Phase 할당
    def assign_phase(cv_val):
        if pd.isna(cv_val):
            return 'unknown'
        elif cv_val >= threshold_low:
            return 'initial'  # 높은 변동성
        elif cv_val >= threshold_mid:
            return 'middle'   # 중간 변동성
        else:
            return 'final'    # 낮은 변동성
    
    df['phase_cv'] = df[cv_column].apply(assign_phase)
    
    return df, threshold_low, threshold_mid

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV-Based Phase Detection")
    print("=" * 80)
    
    # 1. 데이터 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['qps'] = df['interval_qps']
    
    print(f"✅ 데이터 로드: {len(df):,}개 샘플")
    
    # 2. Rolling CV 계산
    window = 1000
    df['mean_rolling'] = df['qps'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['qps'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    print(f"CV 통계:")
    print(f"  CV 범위: {df['cv_rolling'].min():.6f} ~ {df['cv_rolling'].max():.6f}")
    print(f"  CV 평균: {df['cv_rolling'].mean():.6f}")
    
    # 3. CV 기반 phase 탐지
    df, threshold_high, threshold_low = detect_phases_from_cv(df)
    
    # Phase별 통계
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통계 (CV 기반):")
    phase_info = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_cv'] == phase]
        if len(phase_df) > 0:
            cv_mean = phase_df['cv_rolling'].mean()
            cv_std = phase_df['cv_rolling'].std()
            
            # 통합 CV
            qps_mean = phase_df['qps'].mean()
            qps_std = phase_df['qps'].std()
            cv_integrated = qps_std / qps_mean if qps_mean > 0 else 0
            
            # 시간 범위
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
    
    # 4. 시각화
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. Rolling CV over Time (CV-based phase)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(df['time_hours'], df['cv_rolling'], color='#2C3E50', alpha=0.7, linewidth=1.5)
    
    for phase in ['initial', 'middle', 'final']:
        phase_mask = df['phase_cv'] == phase
        if phase_mask.any():
            ax1.scatter(df[phase_mask]['time_hours'], df[phase_mask]['cv_rolling'], 
                       color=colors[phase], alpha=0.3, s=1, label=f'{phase.title()} Phase')
    
    ax1.axhline(y=threshold_high, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.axhline(y=threshold_low, color='blue', linestyle='--', linewidth=2, alpha=0.7)
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('Rolling CV', fontsize=18, fontfamily='Times')
    ax1.set_title('CV-Based Phase Detection', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    
    # 2. CV 분포 히스토그램
    ax2 = fig.add_subplot(gs[0, 1])
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_cv'] == phase]
        if len(phase_df) > 0:
            ax2.hist(phase_df['cv_rolling'].dropna(), bins=50, alpha=0.6, 
                    label=f'{phase.title()} Phase', color=colors[phase], density=True)
    
    ax2.axvline(x=threshold_high, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax2.axvline(x=threshold_low, color='blue', linestyle='--', linewidth=2, alpha=0.7)
    
    ax2.set_xlabel('CV Value', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('Density', fontsize=18, fontfamily='Times')
    ax2.set_title('CV Distribution by Phase', fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # 3. QPS over Time
    ax3 = fig.add_subplot(gs[1, 0])
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_cv'] == phase]
        if len(phase_df) > 0:
            ax3.plot(phase_df['time_hours'], phase_df['qps'], 
                    color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase')
    
    ax3.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax3.set_ylabel('QPS (ops/sec)', fontsize=18, fontfamily='Times')
    ax3.set_title('QPS Over Time (CV-based Phases)', fontsize=20, fontfamily='Times', fontweight='bold')
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=16)
    ax3.set_yscale('log')
    
    # 4. Phase별 통합 CV 비교
    ax4 = fig.add_subplot(gs[1, 1])
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
    ax4.set_ylim(0, max(cvs) * 1.3)
    
    output_path = Path("figs/cv_based_phase_detection.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

