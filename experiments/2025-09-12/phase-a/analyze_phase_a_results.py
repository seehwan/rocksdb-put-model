#!/usr/bin/env python3
"""
Phase-A 결과 분석 및 시각화 스크립트
- 초기 상태와 열화 상태 성능 비교
- Device Envelope 모델 시각화
- 성능 열화 패턴 분석
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import seaborn as sns

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def load_phase_a_results():
    """Phase-A 결과 파일들을 로드합니다."""
    data_dir = Path("data")
    
    results = {}
    
    # 초기 상태 결과
    initial_file = data_dir / "initial_state_results.json"
    if initial_file.exists():
        with open(initial_file, 'r') as f:
            results['initial'] = json.load(f)
    else:
        print(f"경고: {initial_file} 파일을 찾을 수 없습니다.")
    
    # 열화 상태 결과
    degraded_file = data_dir / "degraded_state_results.json"
    if degraded_file.exists():
        with open(degraded_file, 'r') as f:
            results['degraded'] = json.load(f)
    else:
        print(f"경고: {degraded_file} 파일을 찾을 수 없습니다.")
    
    # Device Envelope 모델
    model_file = data_dir / "device_envelope_model.json"
    if model_file.exists():
        with open(model_file, 'r') as f:
            results['model'] = json.load(f)
    else:
        print(f"경고: {model_file} 파일을 찾을 수 없습니다.")
    
    return results

def create_performance_comparison_chart(results):
    """성능 비교 차트를 생성합니다."""
    if 'initial' not in results or 'degraded' not in results:
        print("초기 상태 또는 열화 상태 결과가 없어 차트를 생성할 수 없습니다.")
        return
    
    # 테스트 유형별 데이터 추출
    test_types = ['sequential_write', 'random_write', 'sequential_read', 'random_read', 'mixed_rw']
    test_labels = ['Seq Write', 'Rand Write', 'Seq Read', 'Rand Read', 'Mixed R/W']
    
    initial_bandwidths = []
    degraded_bandwidths = []
    
    for test_type in test_types:
        initial_bw = results['initial']['tests'][test_type]['bandwidth_mib_s']
        degraded_bw = results['degraded']['tests'][test_type]['bandwidth_mib_s']
        initial_bandwidths.append(initial_bw)
        degraded_bandwidths.append(degraded_bw)
    
    # 차트 생성
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. 대역폭 비교
    x = np.arange(len(test_labels))
    width = 0.35
    
    ax1.bar(x - width/2, initial_bandwidths, width, label='초기 상태', color='lightblue', alpha=0.8)
    ax1.bar(x + width/2, degraded_bandwidths, width, label='열화 상태', color='lightcoral', alpha=0.8)
    
    ax1.set_xlabel('테스트 유형')
    ax1.set_ylabel('대역폭 (MiB/s)')
    ax1.set_title('초기 상태 vs 열화 상태 성능 비교')
    ax1.set_xticks(x)
    ax1.set_xticklabels(test_labels, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 열화율 계산 및 표시
    degradations = []
    for i in range(len(initial_bandwidths)):
        degradation = ((initial_bandwidths[i] - degraded_bandwidths[i]) / initial_bandwidths[i]) * 100
        degradations.append(degradation)
    
    bars = ax2.bar(test_labels, degradations, color='orange', alpha=0.7)
    ax2.set_xlabel('테스트 유형')
    ax2.set_ylabel('성능 열화율 (%)')
    ax2.set_title('테스트별 성능 열화율')
    ax2.grid(True, alpha=0.3)
    
    # 열화율 값을 막대 위에 표시
    for bar, degradation in zip(bars, degradations):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{degradation:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('data/performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_degradation_timeline(results):
    """열화 타임라인 차트를 생성합니다."""
    if 'model' not in results:
        print("Device Envelope 모델이 없어 타임라인 차트를 생성할 수 없습니다.")
        return
    
    # 시간축 생성 (0: 초기 상태, 1: 열화 상태)
    time_points = [0, 1]
    time_labels = ['초기 상태\n(완전 초기화)', '열화 상태\n(Phase-B 후)']
    
    # 각 테스트 유형별 성능 추이
    test_types = ['sequential_write', 'random_write', 'sequential_read', 'random_read', 'mixed_rw']
    test_labels = ['Seq Write', 'Rand Write', 'Seq Read', 'Rand Read', 'Mixed R/W']
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, (test_type, test_label) in enumerate(zip(test_types, test_labels)):
        initial_bw = results['initial']['tests'][test_type]['bandwidth_mib_s']
        degraded_bw = results['degraded']['tests'][test_type]['bandwidth_mib_s']
        
        ax.plot(time_points, [initial_bw, degraded_bw], 
               marker='o', linewidth=2, markersize=8, 
               label=test_label, color=colors[i])
        
        # 각 점에 값 표시
        ax.annotate(f'{initial_bw:.0f} MiB/s', 
                   (0, initial_bw), textcoords="offset points", 
                   xytext=(0,10), ha='center')
        ax.annotate(f'{degraded_bw:.0f} MiB/s', 
                   (1, degraded_bw), textcoords="offset points", 
                   xytext=(0,10), ha='center')
    
    ax.set_xlabel('장치 상태')
    ax.set_ylabel('대역폭 (MiB/s)')
    ax.set_title('장치 성능 열화 타임라인')
    ax.set_xticks(time_points)
    ax.set_xticklabels(time_labels)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('data/degradation_timeline.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_io_pattern_analysis(results):
    """I/O 패턴 분석 차트를 생성합니다."""
    if 'initial' not in results or 'degraded' not in results:
        print("초기 상태 또는 열화 상태 결과가 없어 I/O 패턴 분석을 할 수 없습니다.")
        return
    
    # IOPS 데이터 추출
    test_types = ['sequential_write', 'random_write', 'sequential_read', 'random_read', 'mixed_rw']
    test_labels = ['Seq Write', 'Rand Write', 'Seq Read', 'Rand Read', 'Mixed R/W']
    
    initial_iops = []
    degraded_iops = []
    
    for test_type in test_types:
        initial_iops_val = results['initial']['tests'][test_type]['iops']
        degraded_iops_val = results['degraded']['tests'][test_type]['iops']
        initial_iops.append(initial_iops_val)
        degraded_iops.append(degraded_iops_val)
    
    # 레이턴시 데이터 추출
    initial_lat_mean = []
    degraded_lat_mean = []
    
    for test_type in test_types:
        initial_lat = results['initial']['tests'][test_type]['latency_mean_us']
        degraded_lat = results['degraded']['tests'][test_type]['latency_mean_us']
        initial_lat_mean.append(initial_lat)
        degraded_lat_mean.append(degraded_lat)
    
    # 2x2 서브플롯 생성
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. IOPS 비교
    x = np.arange(len(test_labels))
    width = 0.35
    
    ax1.bar(x - width/2, initial_iops, width, label='초기 상태', color='lightblue', alpha=0.8)
    ax1.bar(x + width/2, degraded_iops, width, label='열화 상태', color='lightcoral', alpha=0.8)
    ax1.set_xlabel('테스트 유형')
    ax1.set_ylabel('IOPS')
    ax1.set_title('IOPS 비교')
    ax1.set_xticks(x)
    ax1.set_xticklabels(test_labels, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 레이턴시 비교
    ax2.bar(x - width/2, initial_lat_mean, width, label='초기 상태', color='lightgreen', alpha=0.8)
    ax2.bar(x + width/2, degraded_lat_mean, width, label='열화 상태', color='salmon', alpha=0.8)
    ax2.set_xlabel('테스트 유형')
    ax2.set_ylabel('평균 레이턴시 (μs)')
    ax2.set_title('평균 레이턴시 비교')
    ax2.set_xticks(x)
    ax2.set_xticklabels(test_labels, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. IOPS 열화율
    iops_degradations = []
    for i in range(len(initial_iops)):
        degradation = ((initial_iops[i] - degraded_iops[i]) / initial_iops[i]) * 100
        iops_degradations.append(degradation)
    
    bars1 = ax3.bar(test_labels, iops_degradations, color='orange', alpha=0.7)
    ax3.set_xlabel('테스트 유형')
    ax3.set_ylabel('IOPS 열화율 (%)')
    ax3.set_title('IOPS 열화율')
    ax3.grid(True, alpha=0.3)
    
    for bar, degradation in zip(bars1, iops_degradations):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{degradation:.1f}%', ha='center', va='bottom')
    
    # 4. 레이턴시 증가율
    lat_increases = []
    for i in range(len(initial_lat_mean)):
        increase = ((degraded_lat_mean[i] - initial_lat_mean[i]) / initial_lat_mean[i]) * 100
        lat_increases.append(increase)
    
    bars2 = ax4.bar(test_labels, lat_increases, color='red', alpha=0.7)
    ax4.set_xlabel('테스트 유형')
    ax4.set_ylabel('레이턴시 증가율 (%)')
    ax4.set_title('평균 레이턴시 증가율')
    ax4.grid(True, alpha=0.3)
    
    for bar, increase in zip(bars2, lat_increases):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{increase:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig('data/io_pattern_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_analysis_report(results):
    """분석 보고서를 생성합니다."""
    report_file = Path("data/phase_a_analysis_report.md")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Phase-A 분석 보고서\n\n")
        f.write(f"**생성일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if 'model' in results:
            f.write("## Device Envelope 모델 요약\n\n")
            model = results['model']
            
            f.write("### 성능 열화 분석\n\n")
            f.write("| 테스트 유형 | 열화율 (%) |\n")
            f.write("|-------------|------------|\n")
            
            degradation = model['degradation_analysis']
            test_types = [
                ('sequential_write', 'Sequential Write'),
                ('random_write', 'Random Write'),
                ('sequential_read', 'Sequential Read'),
                ('random_read', 'Random Read'),
                ('mixed_rw', 'Mixed R/W')
            ]
            
            for test_key, test_name in test_types:
                degradation_key = f"{test_key}_degradation_percent"
                if degradation_key in degradation:
                    f.write(f"| {test_name} | {degradation[degradation_key]:.2f} |\n")
            
            f.write(f"\n### 전체 요약\n\n")
            f.write(f"- **평균 Write 열화율**: {degradation.get('avg_write_degradation_percent', 0):.2f}%\n")
            f.write(f"- **평균 Read 열화율**: {degradation.get('avg_read_degradation_percent', 0):.2f}%\n")
            f.write(f"- **가장 큰 열화**: {max([v for k, v in degradation.items() if 'degradation_percent' in k]):.2f}%\n")
            f.write(f"- **가장 작은 열화**: {min([v for k, v in degradation.items() if 'degradation_percent' in k]):.2f}%\n")
        
        f.write("\n## 생성된 차트\n\n")
        f.write("1. **performance_comparison.png**: 초기 상태 vs 열화 상태 성능 비교\n")
        f.write("2. **degradation_timeline.png**: 장치 성능 열화 타임라인\n")
        f.write("3. **io_pattern_analysis.png**: I/O 패턴 분석 (IOPS, 레이턴시)\n\n")
        
        f.write("## 결론\n\n")
        if 'model' in results:
            degradation = results['model']['degradation_analysis']
            avg_write_degradation = degradation.get('avg_write_degradation_percent', 0)
            
            if avg_write_degradation > 10:
                f.write(f"⚠️ **주의**: 평균 Write 성능이 {avg_write_degradation:.1f}% 열화되었습니다. 이는 FillRandom 성능에 영향을 줄 수 있습니다.\n\n")
            elif avg_write_degradation > 5:
                f.write(f"ℹ️ **정보**: 평균 Write 성능이 {avg_write_degradation:.1f}% 열화되었습니다. 모델에서 이를 고려해야 합니다.\n\n")
            else:
                f.write(f"✅ **양호**: 평균 Write 성능 열화가 {avg_write_degradation:.1f}%로 미미합니다.\n\n")
            
            f.write("### 권장사항\n\n")
            f.write("1. **모델 파라미터 조정**: Device Envelope 모델을 사용하여 시간에 따른 성능 변화를 반영\n")
            f.write("2. **FillRandom 성능 예측**: Random Write 열화율을 고려한 FillRandom 성능 예측\n")
            f.write("3. **컴팩션 성능 고려**: Sequential Read/Write 열화율을 고려한 컴팩션 성능 예측\n\n")
    
    print(f"분석 보고서가 생성되었습니다: {report_file}")

def main():
    """메인 함수"""
    print("=== Phase-A 결과 분석 시작 ===")
    
    # 결과 로드
    results = load_phase_a_results()
    
    if not results:
        print("분석할 결과 파일이 없습니다.")
        return
    
    print("결과 파일 로드 완료:")
    for key in results.keys():
        print(f"  - {key} 상태 결과")
    
    # 차트 생성
    print("\n차트 생성 중...")
    
    # data 디렉토리 생성
    Path("data").mkdir(exist_ok=True)
    
    create_performance_comparison_chart(results)
    print("  ✓ 성능 비교 차트 생성 완료")
    
    create_degradation_timeline(results)
    print("  ✓ 열화 타임라인 차트 생성 완료")
    
    create_io_pattern_analysis(results)
    print("  ✓ I/O 패턴 분석 차트 생성 완료")
    
    # 분석 보고서 생성
    print("\n분석 보고서 생성 중...")
    generate_analysis_report(results)
    print("  ✓ 분석 보고서 생성 완료")
    
    print("\n=== Phase-A 결과 분석 완료 ===")
    print("생성된 파일:")
    print("  - data/performance_comparison.png")
    print("  - data/degradation_timeline.png")
    print("  - data/io_pattern_analysis.png")
    print("  - data/phase_a_analysis_report.md")

if __name__ == "__main__":
    main()
