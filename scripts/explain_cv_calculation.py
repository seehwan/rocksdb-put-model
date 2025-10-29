#!/usr/bin/env python3
"""
CV (Coefficient of Variation) 설명 및 계산 방법
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def demonstrate_cv_calculation():
    """CV 계산 방법 시연"""
    
    print("=" * 80)
    print("📊 CV (Coefficient of Variation) 설명")
    print("=" * 80)
    
    # 예시 데이터
    print("\n1️⃣ 예시: QPS 데이터")
    qps_example = np.array([120000, 150000, 90000, 130000, 110000, 140000, 95000, 125000])
    
    mean = np.mean(qps_example)
    std = np.std(qps_example)
    cv = std / mean
    
    print(f"   데이터: {qps_example}")
    print(f"   평균 (μ): {mean:.0f} ops/sec")
    print(f"   표준편차 (σ): {std:.0f} ops/sec")
    print(f"   CV = σ / μ = {std:.0f} / {mean:.0f} = {cv:.3f}")
    print(f"   해석: {('높은 변동성 (불안정)' if cv > 0.5 else '낮은 변동성 (안정)' if cv < 0.3 else '중간 변동성 (보통)')}")
    
    # 실제 fillrandom 데이터로 설명
    print("\n2️⃣ 실제 데이터: fillrandom_results.json")
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['qps'] = df['interval_qps']
    
    # 전체 데이터 CV
    overall_mean = df['qps'].mean()
    overall_std = df['qps'].std()
    overall_cv = overall_std / overall_mean
    
    print(f"   전체 데이터:")
    print(f"     평균: {overall_mean:.0f} ops/sec")
    print(f"     표준편차: {overall_std:.0f} ops/sec")
    print(f"     CV: {overall_cv:.3f}")
    
    # Phase별 CV
    df['time_hours'] = df['secs_elapsed'] / 3600
    df['phase'] = df['time_hours'].apply(
        lambda h: 'initial' if h < 10 else ('middle' if h < 42 else 'final')
    )
    
    print(f"\n3️⃣ Phase별 CV (통합 CV):")
    for phase in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase]
        mean = phase_df['qps'].mean()
        std = phase_df['qps'].std()
        cv = std / mean
        print(f"   {phase}:")
        print(f"     평균: {mean:.0f} ops/sec")
        print(f"     표준편차: {std:.0f} ops/sec")
        print(f"     CV = {std:.0f} / {mean:.0f} = {cv:.3f}")
    
    # Rolling CV 설명
    print(f"\n4️⃣ Rolling CV 계산 방법:")
    window = 1000
    df['mean_rolling'] = df['qps'].rolling(window=window, min_periods=window).mean()
    df['std_rolling'] = df['qps'].rolling(window=window, min_periods=window).std()
    df['cv_rolling'] = df['std_rolling'] / df['mean_rolling']
    
    print(f"   Rolling window: {window} 샘플")
    print(f"   각 시간점에서:")
    print(f"     - 최근 {window}개 샘플의 평균 계산")
    print(f"     - 최근 {window}개 샘플의 표준편차 계산")
    print(f"     - CV = 표준편차 / 평균")
    print(f"   → 시간에 따른 CV 변화를 추적 가능")
    
    # 첫 번째 유효 CV 값 예시
    first_valid_idx = df['cv_rolling'].first_valid_index()
    if first_valid_idx is not None:
        window_qps = df['qps'].iloc[first_valid_idx-window+1:first_valid_idx+1]
        window_mean = window_qps.mean()
        window_std = window_qps.std()
        window_cv = window_std / window_mean
        
        print(f"\n   예시 (첫 유효 CV값):")
        print(f"     최근 {window}개 샘플: {window_qps.tolist()[:5]}... {window_qps.tolist()[-5:]}")
        print(f"     평균: {window_mean:.0f}")
        print(f"     표준편차: {window_std:.0f}")
        print(f"     CV: {window_cv:.3f}")
    
    # 시각화
    print(f"\n5️⃣ 시각화 생성 중...")
    
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. QPS over Time with Rolling Statistics
    ax1 = fig.add_subplot(gs[0, :])
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    ax1_twin = ax1.twinx()
    
    # QPS
    ax1.plot(df['time_hours'], df['qps'], color='steelblue', alpha=0.7, linewidth=1, label='QPS')
    
    # Rolling Mean
    ax1.plot(df['time_hours'], df['mean_rolling'], color='green', alpha=0.8, linewidth=2, label='Rolling Mean (window=1000)')
    ax1.fill_between(df['time_hours'], 
                     df['mean_rolling'] - df['std_rolling'], 
                     df['mean_rolling'] + df['std_rolling'], 
                     color='green', alpha=0.2, label='±1 Std Dev')
    
    # Rolling CV
    ax1_twin.plot(df['time_hours'], df['cv_rolling'], color='red', alpha=0.8, linewidth=2, label='Rolling CV')
    
    ax1.set_xlabel('Time (hours)', fontsize=18, fontfamily='Times')
    ax1.set_ylabel('QPS (ops/sec)', fontsize=18, fontfamily='Times', color='steelblue')
    ax1_twin.set_ylabel('CV Value', fontsize=18, fontfamily='Times', color='red')
    ax1.set_title('QPS, Rolling Mean/Std, and CV Over Time', fontsize=20, fontfamily='Times', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='steelblue', labelsize=14)
    ax1_twin.tick_params(axis='y', labelcolor='red', labelsize=14)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=16)
    ax1.set_yscale('log')
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=12)
    
    # 2. CV Distribution
    ax2 = fig.add_subplot(gs[1, 0])
    valid_cv = df['cv_rolling'].dropna()
    ax2.hist(valid_cv, bins=50, color='steelblue', alpha=0.7, edgecolor='black', linewidth=1)
    ax2.axvline(x=valid_cv.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {valid_cv.mean():.3f}')
    ax2.axvline(x=valid_cv.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {valid_cv.median():.3f}')
    
    ax2.set_xlabel('CV Value', fontsize=18, fontfamily='Times')
    ax2.set_ylabel('Frequency', fontsize=18, fontfamily='Times')
    ax2.set_title('CV Distribution', fontsize=20, fontfamily='Times', fontweight='bold')
    ax2.legend(fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=16)
    
    # 3. CV Formula Explanation
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')
    
    explanation_text = """
CV (Coefficient of Variation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 정의:
   CV = 표준편차(σ) / 평균(μ)

📈 의미:
   • CV는 데이터의 상대적 변동성을 측정
   • 단위가 다른 데이터를 비교 가능
   • CV가 낮을수록 안정적

🔢 계산:
   CV = std(QPS) / mean(QPS)

📊 해석:
   • CV < 0.3: 매우 안정적 (Low variability)
   • 0.3 < CV < 0.5: 보통 (Moderate variability)  
   • CV > 0.5: 불안정 (High variability)

🎯 실제 데이터:
   • Initial Phase: CV ≈ 0.71 (High)
   • Middle Phase:  CV ≈ 0.52 (Moderate)
   • Final Phase:   CV ≈ 0.47 (Low)
    """
    
    ax3.text(0.05, 0.95, explanation_text, transform=ax3.transAxes,
            fontsize=14, verticalalignment='top', horizontalalignment='left',
            fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    output_path = Path("figs/cv_explanation.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"✅ 저장됨: {output_path}")
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    demonstrate_cv_calculation()

