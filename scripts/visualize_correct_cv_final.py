#!/usr/bin/env python3
"""
Final CV Visualization using phase_b_3_phases_results.json
실험에서 보고한 정확한 CV 값 사용
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_phase_data():
    """Phase B 결과 로드"""
    with open('experiments/2025-09-12/phase-b/phase_b_3_phases_results.json', 'r') as f:
        return json.load(f)

def load_fillrandom_data():
    """Fillrandom 데이터 로드"""
    df = pd.read_csv('experiments/2025-09-12/phase-b/fillrandom_results.json')
    df['time_hours'] = df['secs_elapsed'] / 3600
    
    # ops/sec를 MB/s로 변환 (1040 bytes/record 기준)
    df['write_rate_mbs'] = df['interval_qps'] * 1040 / (1024 * 1024)
    
    return df

def visualize_final_cv(phase_data, df):
    """최종 CV 시각화"""
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # 색상 정의
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    # Phase별 time series
    phase_boundaries = {
        'initial': (0, 32.2),
        'middle': (32.2, 64.4),
        'final': (64.4, 100)  # Will auto-limit to df range
    }
    
    for phase_name, (start, end) in phase_boundaries.items():
        phase_df = df[(df['time_hours'] >= start) & (df['time_hours'] < end)]
        if len(phase_df) > 0:
            ax1.plot(phase_df['time_hours'], phase_df['write_rate_mbs'], 
                    color=colors[phase_name], alpha=0.5, linewidth=1.5,
                    label=f'{phase_name.title()} Phase ({len(phase_df):,} samples)')
    
    ax1.set_xlabel('Time (hours)', fontsize=22, fontfamily='Times')
    ax1.set_ylabel('Write Rate (MB/s)', fontsize=22, fontfamily='Times')
    ax1.set_title('RocksDB Performance Timeline by Phase', fontsize=24, fontfamily='Times', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=14, loc='upper right')
    ax1.tick_params(axis='both', which='major', labelsize=18)
    
    # Phase boundaries
    for boundary in [32.2, 64.4]:
        ax1.axvline(x=boundary, color='black', linestyle='--', alpha=0.5, linewidth=2)
    
    # Phase-level CV 표시 (실험 데이터에서)
    phase_cvs = {}
    phase_stats = {}
    
    for phase_name in ['initial', 'middle', 'final']:
        phase_info = phase_data['phase_analysis'][phase_name]
        phase_cvs[phase_name] = phase_info['cv']
        phase_stats[phase_name] = {
            'mean': phase_info['avg_write_rate'],
            'cv': phase_info['cv'],
            'samples': phase_info['sample_count']
        }
    
    phases = list(phase_cvs.keys())
    cvs = list(phase_cvs.values())
    bars = ax2.bar(phases, cvs, color=[colors[p] for p in phases], alpha=0.7, width=0.6)
    ax2.set_xlabel('Operational Phase', fontsize=22, fontfamily='Times')
    ax2.set_ylabel('Coefficient of Variation (CV)', fontsize=22, fontfamily='Times')
    ax2.set_title('Phase-Level Integrated CV from Experimental Data', fontsize=24, fontfamily='Times', fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.tick_params(axis='both', which='major', labelsize=18)
    
    # CV 값 표시
    for i, (phase, cv) in enumerate(phase_cvs.items()):
        ax2.text(i, cv + 0.01, f'{cv:.3f}', ha='center', va='bottom', fontsize=18, fontweight='bold', fontfamily='Times')
        # 샘플 수도 표시
        samples = phase_stats[phase]['samples']
        mean_rate = phase_stats[phase]['mean']
        ax2.text(i, -0.05, f'Avg: {mean_rate:.1f}\nMB/s', ha='center', va='top', fontsize=12, fontfamily='Times')
    
    # Detection thresholds
    ax2.axhline(y=0.30, color='red', linestyle='--', linewidth=2, label='Initial threshold (CV=0.30)', alpha=0.7)
    ax2.axhline(y=0.01, color='blue', linestyle='--', linewidth=2, label='Final threshold (CV=0.01)', alpha=0.7)
    ax2.legend(fontsize=14, loc='upper right')
    ax2.set_ylim(-0.15, max(cvs) * 1.3)
    
    # Phase 통계 표시
    print("\n" + "=" * 80)
    print("Phase Statistics from Experimental Data")
    print("=" * 80)
    for phase, stats in phase_stats.items():
        print(f"{phase.upper()}: CV={stats['cv']:.3f}, Mean={stats['mean']:.2f} MB/s, Samples={stats['samples']:,}")
    
    plt.tight_layout()
    return fig

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 Final CV Visualization using Experimental Data")
    print("=" * 80)
    
    # 데이터 로드
    phase_data = load_phase_data()
    df = load_fillrandom_data()
    print(f"✅ Fillrandom 데이터 로드: {len(df):,} 샘플")
    
    # 시각화
    print("\n📈 시각화 생성 중...")
    fig = visualize_final_cv(phase_data, df)
    
    output_path = Path("figs/cv_final_correct.png")
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ 저장됨: {output_path}")
    
    # 파일 크기 확인
    print(f"📄 파일 크기: {output_path.stat().st_size / 1024:.1f} KB")
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

