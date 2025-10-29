#!/usr/bin/env python3
"""
CV from fillrandom_results.json
fillrandom_results.json 기반 CV 계산 및 phase 구분
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV from fillrandom_results.json")
    print("=" * 80)
    
    # 1. fillrandom_results.json 로드
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    print(f"✅ 데이터 로드: {len(df):,}개 샘플")
    print(f"   시간 범위: {df['time_hours'].min():.2f} ~ {df['time_hours'].max():.2f} hours")
    
    # 2. interval_qps 그대로 사용 (ops/sec)
    df['qps'] = df['interval_qps']
    
    # 3. Rolling CV 계산
    window = 1000
    print(f"\n📊 Rolling CV 계산 중 (window={window})...")
    
    df['mean_rolling'] = df['qps'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['qps'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    valid_samples = df['cv_rolling'].notna().sum()
    print(f"CV 통계:")
    print(f"  유효 샘플: {valid_samples:,}개")
    print(f"  CV 최소: {df['cv_rolling'].min():.6f}")
    print(f"  CV 최대: {df['cv_rolling'].max():.6f}")
    print(f"  CV 평균: {df['cv_rolling'].mean():.6f}")
    
    # 4. Phase 구분 (CV 기반)
    print(f"\n📊 Phase 구분 (CV 기반)...")
    
    # CV 통계를 기반으로 임계값 결정
    cv_mean = df['cv_rolling'].mean()
    cv_std = df['cv_rolling'].std()
    
    # 초기: CV > mean + std, 중간: mean-std < CV <= mean+std, 최종: CV <= mean-std
    threshold_high = cv_mean + cv_std
    threshold_low = cv_mean - cv_std
    
    print(f"  CV 통계: mean={cv_mean:.6f}, std={cv_std:.6f}")
    print(f"  임계값: 높음={threshold_high:.3f}, 낮음={threshold_low:.3f}")
    
    def detect_phase(cv_val):
        if pd.isna(cv_val):
            return 'unknown'
        elif cv_val > threshold_high:
            return 'initial'
        elif cv_val > threshold_low:
            return 'middle'
        else:
            return 'final'
    
    df['phase_cv'] = df['cv_rolling'].apply(detect_phase)
    
    # Time-based phase (참고용)
    total_hours = df['time_hours'].max()
    df['phase_time'] = df['time_hours'].apply(
        lambda h: 'initial' if h < total_hours/3 else ('middle' if h < total_hours*2/3 else 'final')
    )
    
    # Phase별 통계
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    print(f"\n📊 Phase별 통계 (CV 기반):")
    phase_cvs = {}
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_cv'] == phase]
        if len(phase_df) > 0:
            cv_mean_phase = phase_df['cv_rolling'].mean()
            cv_std_phase = phase_df['cv_rolling'].std()
            
            # QPS 통계
            qps_mean = phase_df['qps'].mean()
            qps_std = phase_df['qps'].std()
            cv_integrated = qps_std / qps_mean if qps_mean > 0 else 0
            
            phase_cvs[phase] = cv_integrated
            print(f"  {phase}:")
            print(f"    샘플 수: {len(phase_df):,}")
            print(f"    Rolling CV 평균: {cv_mean_phase:.6f}")
            print(f"    통합 CV: {cv_integrated:.6f}")
            print(f"    QPS 평균: {qps_mean:.0f} ops/sec")
    
    # 5. 시각화
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Rolling CV over time
    ax1.plot(df['time_hours'], df['cv_rolling'], 
            color='#2C3E50', alpha=0.7, linewidth=1.5, label=f'Rolling CV (window={window})')
    
    # CV 기반 phase 색상
    for phase in ['initial', 'middle', 'final']:
        phase_mask = df['phase_cv'] == phase
        if phase_mask.any():
            ax1.scatter(df[phase_mask]['time_hours'], df[phase_mask]['cv_rolling'], 
                       color=colors[phase], alpha=0.3, s=1, label=f'{phase.title()} Phase (CV-based)')
    
    ax1.axhline(y=threshold_high, color='red', linestyle='--', linewidth=2, 
                label=f'Threshold High ({threshold_high:.3f})', alpha=0.7)
    ax1.axhline(y=threshold_low, color='blue', linestyle='--', linewidth=2, 
                label=f'Threshold Low ({threshold_low:.3f})', alpha=0.7)
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Rolling CV', fontsize=22, fontfamily='Times')
    ax1.set_title('Rolling CV Over Time (CV-based Phase Detection)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.legend(fontsize=12, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # 2. Time-based phase 비교
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_time'] == phase]
        ax2.plot(phase_df['time_hours'], phase_df['cv_rolling'], 
                color=colors[phase], alpha=0.7, linewidth=1, label=f'{phase.title()} Phase')
    
    for boundary in [total_hours/3, total_hours*2/3]:
        ax2.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    ax2.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Rolling CV', fontsize=22, fontfamily='Times')
    ax2.set_title('Rolling CV Over Time (Time-based Phase)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    # 3. QPS over time
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase_cv'] == phase]
        if len(phase_df) > 0:
            ax3.plot(phase_df['time_hours'], phase_df['qps'], 
                    color=colors[phase], alpha=0.5, linewidth=1, label=f'{phase.title()} Phase (CV-based)')
    
    ax3.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax3.set_ylabel('QPS (ops/sec)', fontsize=22, fontfamily='Times')
    ax3.set_title('QPS Over Time (CV-based Phase Detection)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax3.legend(fontsize=12)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=18)
    ax3.set_yscale('log')
    
    # 4. Phase별 통합 CV 비교
    phases = list(phase_cvs.keys())
    cvs = [phase_cvs[p] for p in phases]
    
    bars = ax4.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        ax4.text(i, cv + max(cvs)*0.05, f'{cv:.3f}', ha='center', va='bottom', 
                fontsize=18, fontweight='bold', fontfamily='Times')
    
    ax4.set_xlabel('Phase', fontsize=22, fontfamily='Times')
    ax4.set_ylabel('Integrated CV (std/mean)', fontsize=22, fontfamily='Times')
    ax4.set_title('Phase-Level Integrated CV (QPS-based)', fontsize=24, fontfamily='Times', fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.tick_params(axis='both', which='major', labelsize=18)
    ax4.set_ylim(0, max(cvs) * 1.3)
    
    plt.tight_layout()
    
    output_path = Path("figs/cv_from_fillrandom.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"\n✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")
    print("\n📊 그래프 설명:")
    print("  1. Rolling CV over Time (CV 기반 phase 구분)")
    print("  2. Rolling CV over Time (시간 기반 phase 비교)")
    print("  3. QPS over Time (CV 기반 phase 구분)")
    print("  4. Phase별 통합 CV")

if __name__ == "__main__":
    main()

