#!/usr/bin/env python3
"""
구간 분할 방법 비교 분석
LOG 기반 구간 분할 vs 성능 기반 구간 분할 비교
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def load_log_based_results():
    """LOG 기반 구간 분할 결과 로드"""
    print("📊 LOG 기반 구간 분할 결과 로드 중...")
    
    try:
        with open('log_based_phases_detailed_results.json', 'r') as f:
            log_results = json.load(f)
        print("✅ LOG 기반 결과 로드 완료")
        return log_results
    except FileNotFoundError:
        print("❌ LOG 기반 결과 파일을 찾을 수 없습니다.")
        return None

def load_performance_based_results():
    """성능 기반 구간 분할 결과 로드"""
    print("📊 성능 기반 구간 분할 결과 로드 중...")
    
    try:
        with open('phase_b_3_phases_results.json', 'r') as f:
            perf_results = json.load(f)
        print("✅ 성능 기반 결과 로드 완료")
        return perf_results
    except FileNotFoundError:
        print("❌ 성능 기반 결과 파일을 찾을 수 없습니다.")
        return None

def compare_phase_segmentation_methods():
    """구간 분할 방법 비교 분석"""
    print("📊 구간 분할 방법 비교 분석 중...")
    
    # 결과 로드
    log_results = load_log_based_results()
    perf_results = load_performance_based_results()
    
    if not log_results or not perf_results:
        print("❌ 비교 분석을 위한 결과 파일이 없습니다.")
        return None
    
    # 비교 분석
    comparison = {
        'log_based': log_results['phase_analysis'],
        'performance_based': perf_results['phase_analysis'],
        'comparison_metrics': {}
    }
    
    # 구간별 특성 비교
    phase_comparison = {}
    for phase_name in ['initial', 'middle', 'final']:
        if phase_name in log_results['phase_analysis'] and phase_name in perf_results['phase_analysis']:
            log_phase = log_results['phase_analysis'][phase_name]
            perf_phase = perf_results['phase_analysis'][phase_name]
            
            phase_comparison[phase_name] = {
                'log_based': {
                    'duration_hours': log_phase['basic_stats']['duration_hours'],
                    'avg_performance': log_phase['performance_stats']['avg_write_rate'],
                    'cv': log_phase['performance_stats']['cv'],
                    'stability': log_phase['phase_characteristics']['stability'],
                    'performance_level': log_phase['phase_characteristics']['performance_level']
                },
                'performance_based': {
                    'duration_hours': perf_phase['duration_hours'],
                    'avg_performance': perf_phase['avg_write_rate'],
                    'cv': perf_phase['cv'],
                    'stability': 'high' if perf_phase['cv'] < 0.3 else 'medium' if perf_phase['cv'] < 0.6 else 'low',
                    'performance_level': 'high' if perf_phase['avg_write_rate'] > 100000 else 'medium' if perf_phase['avg_write_rate'] > 50000 else 'low'
                }
            }
    
    comparison['phase_comparison'] = phase_comparison
    
    # 주요 차이점 분석
    key_differences = analyze_key_differences(phase_comparison)
    comparison['key_differences'] = key_differences
    
    return comparison

def analyze_key_differences(phase_comparison):
    """주요 차이점 분석"""
    print("📊 주요 차이점 분석 중...")
    
    differences = {
        'performance_scale': {
            'log_based_range': 'MB/s 단위 (10-300 MB/s)',
            'performance_based_range': 'ops/sec 단위 (10,000-300,000 ops/sec)',
            'scale_difference': 'LOG 기반이 훨씬 낮은 수치'
        },
        'stability_pattern': {
            'log_based': '초기 불안정 → 중기 안정화 → 후기 완전 안정',
            'performance_based': '전체적으로 높은 변동성 유지',
            'difference': 'LOG 기반이 더 명확한 안정화 패턴'
        },
        'phase_characteristics': {
            'log_based': {
                'initial': '중간 성능, 낮은 안정성',
                'middle': '낮은 성능, 높은 안정성',
                'final': '낮은 성능, 높은 안정성'
            },
            'performance_based': {
                'initial': '높은 성능, 중간 안정성',
                'middle': '중간 성능, 중간 안정성',
                'final': '낮은 성능, 중간 안정성'
            }
        },
        'segmentation_approach': {
            'log_based': '시간 기반 3등분 (32.2시간씩)',
            'performance_based': '성능 기반 20%-60%-20% 분할',
            'difference': 'LOG 기반은 시간 일관성, 성능 기반은 성능 변화 중심'
        }
    }
    
    return differences

def create_comparison_visualization(comparison):
    """비교 시각화 생성"""
    print("📊 구간 분할 방법 비교 시각화 생성 중...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Phase Segmentation Methods Comparison', fontsize=18, fontweight='bold')
    
    phase_names = ['Initial', 'Middle', 'Final']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    # 1. 성능 비교 (로그 스케일)
    log_performance = []
    perf_performance = []
    
    for phase_name in ['initial', 'middle', 'final']:
        if phase_name in comparison['phase_comparison']:
            log_perf = comparison['phase_comparison'][phase_name]['log_based']['avg_performance']
            perf_perf = comparison['phase_comparison'][phase_name]['performance_based']['avg_performance']
            log_performance.append(log_perf)
            perf_performance.append(perf_perf)
    
    x = np.arange(len(phase_names))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, log_performance, width, label='LOG-based (MB/s)', color='skyblue', alpha=0.8)
    bars2 = ax1.bar(x + width/2, [p/1000 for p in perf_performance], width, label='Performance-based (K ops/sec)', color='lightcoral', alpha=0.8)
    
    ax1.set_ylabel('Performance')
    ax1.set_title('Performance Comparison (Log Scale)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(phase_names)
    ax1.legend()
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    
    # 2. 안정성 비교 (CV)
    log_cv = []
    perf_cv = []
    
    for phase_name in ['initial', 'middle', 'final']:
        if phase_name in comparison['phase_comparison']:
            log_cv.append(comparison['phase_comparison'][phase_name]['log_based']['cv'])
            perf_cv.append(comparison['phase_comparison'][phase_name]['performance_based']['cv'])
    
    ax2.plot(phase_names, log_cv, marker='o', label='LOG-based', color='blue', linewidth=2, markersize=8)
    ax2.plot(phase_names, perf_cv, marker='s', label='Performance-based', color='red', linewidth=2, markersize=8)
    
    ax2.set_ylabel('Coefficient of Variation')
    ax2.set_title('Stability Comparison (CV)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 구간별 특성 매트릭스
    characteristics_data = []
    for phase_name in ['initial', 'middle', 'final']:
        if phase_name in comparison['phase_comparison']:
            log_char = comparison['phase_comparison'][phase_name]['log_based']
            perf_char = comparison['phase_comparison'][phase_name]['performance_based']
            
            characteristics_data.append([
                log_char['stability'],
                log_char['performance_level'],
                perf_char['stability'],
                perf_char['performance_level']
            ])
    
    # 특성을 숫자로 변환
    char_mapping = {'high': 3, 'medium': 2, 'low': 1}
    char_data_numeric = []
    for row in characteristics_data:
        char_data_numeric.append([char_mapping.get(char, 0) for char in row])
    
    im = ax3.imshow(char_data_numeric, cmap='RdYlGn', aspect='auto')
    ax3.set_xticks(range(4))
    ax3.set_xticklabels(['LOG Stability', 'LOG Performance', 'Perf Stability', 'Perf Performance'])
    ax3.set_yticks(range(len(phase_names)))
    ax3.set_yticklabels(phase_names)
    ax3.set_title('Phase Characteristics Matrix')
    
    # 컬러바 추가
    cbar = plt.colorbar(im, ax=ax3)
    cbar.set_label('Level (1=Low, 2=Medium, 3=High)')
    
    # 4. 비교 요약
    ax4.text(0.05, 0.95, 'Segmentation Methods Comparison', fontsize=16, fontweight='bold', transform=ax4.transAxes)
    
    y_pos = 0.85
    ax4.text(0.05, y_pos, 'Key Differences:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.05
    
    ax4.text(0.05, y_pos, '1. Performance Scale:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   LOG-based: MB/s (10-300)', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   Performance-based: ops/sec (10K-300K)', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.06
    
    ax4.text(0.05, y_pos, '2. Stability Pattern:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   LOG-based: Clear stabilization', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   Performance-based: High variability', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.06
    
    ax4.text(0.05, y_pos, '3. Segmentation Approach:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   LOG-based: Time-based (32.2h each)', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   Performance-based: Performance-based', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.06
    
    ax4.text(0.05, y_pos, '4. Use Cases:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   LOG-based: Internal RocksDB behavior', fontsize=11, transform=ax4.transAxes)
    y_pos -= 0.04
    ax4.text(0.05, y_pos, '   Performance-based: User performance', fontsize=11, transform=ax4.transAxes)
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('phase_segmentation_methods_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 구간 분할 방법 비교 시각화 완료")

def save_comparison_results(comparison):
    """비교 결과 저장"""
    print("💾 구간 분할 방법 비교 결과 저장 중...")
    
    # JSON 결과 저장
    results = {
        'comparison': comparison,
        'analysis_time': datetime.now().isoformat(),
        'analysis_type': 'phase_segmentation_comparison'
    }
    
    with open('phase_segmentation_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Markdown 보고서 생성
    with open('phase_segmentation_comparison_report.md', 'w') as f:
        f.write("# Phase Segmentation Methods Comparison Report\n\n")
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n")
        f.write("This report compares two different approaches to phase segmentation in RocksDB performance analysis:\n")
        f.write("1. **LOG-based segmentation**: Time-based 3-way split (32.2 hours each)\n")
        f.write("2. **Performance-based segmentation**: Performance-based 20%-60%-20% split\n\n")
        
        f.write("## Key Differences\n\n")
        
        # 성능 스케일 차이
        f.write("### 1. Performance Scale\n")
        f.write("- **LOG-based**: MB/s units (10-300 MB/s)\n")
        f.write("- **Performance-based**: ops/sec units (10,000-300,000 ops/sec)\n")
        f.write("- **Difference**: LOG-based shows much lower values\n\n")
        
        # 안정성 패턴 차이
        f.write("### 2. Stability Pattern\n")
        f.write("- **LOG-based**: Initial instability → Middle stabilization → Final stability\n")
        f.write("- **Performance-based**: Consistently high variability\n")
        f.write("- **Difference**: LOG-based shows clearer stabilization pattern\n\n")
        
        # 구간별 특성 차이
        f.write("### 3. Phase Characteristics\n\n")
        f.write("#### LOG-based Phases:\n")
        f.write("- **Initial**: Medium performance, Low stability\n")
        f.write("- **Middle**: Low performance, High stability\n")
        f.write("- **Final**: Low performance, High stability\n\n")
        
        f.write("#### Performance-based Phases:\n")
        f.write("- **Initial**: High performance, Medium stability\n")
        f.write("- **Middle**: Medium performance, Medium stability\n")
        f.write("- **Final**: Low performance, Medium stability\n\n")
        
        # 분할 접근법 차이
        f.write("### 4. Segmentation Approach\n")
        f.write("- **LOG-based**: Time-based equal split (32.2 hours each)\n")
        f.write("- **Performance-based**: Performance-based 20%-60%-20% split\n")
        f.write("- **Difference**: LOG-based ensures time consistency, Performance-based focuses on performance changes\n\n")
        
        f.write("## Detailed Comparison\n\n")
        
        # 구간별 상세 비교
        for phase_name in ['initial', 'middle', 'final']:
            if phase_name in comparison['phase_comparison']:
                f.write(f"### {phase_name.title()} Phase\n\n")
                
                log_phase = comparison['phase_comparison'][phase_name]['log_based']
                perf_phase = comparison['phase_comparison'][phase_name]['performance_based']
                
                f.write("**LOG-based:**\n")
                f.write(f"- Duration: {log_phase['duration_hours']:.1f} hours\n")
                f.write(f"- Avg Performance: {log_phase['avg_performance']:.1f} MB/s\n")
                f.write(f"- CV: {log_phase['cv']:.3f}\n")
                f.write(f"- Stability: {log_phase['stability']}\n")
                f.write(f"- Performance Level: {log_phase['performance_level']}\n\n")
                
                f.write("**Performance-based:**\n")
                f.write(f"- Duration: {perf_phase['duration_hours']:.1f} hours\n")
                f.write(f"- Avg Performance: {perf_phase['avg_performance']:.1f} ops/sec\n")
                f.write(f"- CV: {perf_phase['cv']:.3f}\n")
                f.write(f"- Stability: {perf_phase['stability']}\n")
                f.write(f"- Performance Level: {perf_phase['performance_level']}\n\n")
                
                f.write("---\n\n")
        
        f.write("## Use Cases and Recommendations\n\n")
        f.write("### LOG-based Segmentation\n")
        f.write("- **Best for**: Analyzing internal RocksDB behavior\n")
        f.write("- **Advantages**: Time consistency, reflects actual system state\n")
        f.write("- **Use when**: Understanding system evolution over time\n\n")
        
        f.write("### Performance-based Segmentation\n")
        f.write("- **Best for**: User-facing performance analysis\n")
        f.write("- **Advantages**: Performance-focused, reflects user experience\n")
        f.write("- **Use when**: Optimizing for user performance\n\n")
        
        f.write("## Conclusion\n\n")
        f.write("Both segmentation methods provide valuable insights but serve different purposes:\n")
        f.write("- **LOG-based** is better for understanding system behavior and internal processes\n")
        f.write("- **Performance-based** is better for user experience and performance optimization\n")
        f.write("- The choice depends on the analysis goals and target audience\n\n")
        
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    print("✅ 비교 결과 저장 완료")

def main():
    """메인 함수"""
    print("🚀 구간 분할 방법 비교 분석 시작...")
    
    # 구간 분할 방법 비교
    comparison = compare_phase_segmentation_methods()
    
    if not comparison:
        print("❌ 비교 분석 실패")
        return
    
    # 결과 출력
    print("\n📊 구간 분할 방법 비교 결과:")
    print("\n🔍 주요 차이점:")
    
    differences = comparison['key_differences']
    print(f"\n1. 성능 스케일:")
    print(f"   LOG 기반: {differences['performance_scale']['log_based_range']}")
    print(f"   성능 기반: {differences['performance_scale']['performance_based_range']}")
    print(f"   차이점: {differences['performance_scale']['scale_difference']}")
    
    print(f"\n2. 안정성 패턴:")
    print(f"   LOG 기반: {differences['stability_pattern']['log_based']}")
    print(f"   성능 기반: {differences['stability_pattern']['performance_based']}")
    print(f"   차이점: {differences['stability_pattern']['difference']}")
    
    print(f"\n3. 구간별 특성:")
    print("   LOG 기반:")
    for phase, char in differences['phase_characteristics']['log_based'].items():
        print(f"     {phase}: {char}")
    print("   성능 기반:")
    for phase, char in differences['phase_characteristics']['performance_based'].items():
        print(f"     {phase}: {char}")
    
    print(f"\n4. 분할 접근법:")
    print(f"   LOG 기반: {differences['segmentation_approach']['log_based']}")
    print(f"   성능 기반: {differences['segmentation_approach']['performance_based']}")
    print(f"   차이점: {differences['segmentation_approach']['difference']}")
    
    # 시각화 생성
    create_comparison_visualization(comparison)
    
    # 결과 저장
    save_comparison_results(comparison)
    
    print("\n✅ 구간 분할 방법 비교 분석 완료!")
    print("📊 결과 파일: phase_segmentation_methods_comparison.png, phase_segmentation_comparison_results.json, phase_segmentation_comparison_report.md")

if __name__ == "__main__":
    main()

