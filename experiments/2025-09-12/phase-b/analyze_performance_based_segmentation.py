#!/usr/bin/env python3
"""
성능 변화 기반 구간 분할 분석
LOG 데이터에서 성능 변화율을 분석하여 의미있는 구간으로 분할
"""

import os
import re
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import signal
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def parse_log_file(log_file):
    """LOG 파일 파싱"""
    print(f"📖 LOG 파일 파싱 중: {log_file}")
    
    stats_data = []
    current_timestamp = None
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 시간 정보 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            # Stats 로그 파싱
            if "Cumulative writes:" in line:
                stats_data.append(parse_stats_line(line, current_timestamp))
    
    print(f"✅ 파싱 완료: Stats {len(stats_data)}개")
    return stats_data

def parse_stats_line(line, timestamp):
    """Stats 라인 파싱"""
    try:
        # Cumulative writes: 1130K writes, 1130K keys, 72K commit groups, 15.5 writes per commit group, ingest: 1.10 GB, 280.18 MB/s
        write_match = re.search(r'Cumulative writes: (\d+[KM]?) writes', line)
        mbps_match = re.search(r'(\d+\.\d+) MB/s', line)
        
        if write_match and mbps_match:
            # K, M 단위 처리
            writes_str = write_match.group(1)
            if writes_str.endswith('K'):
                cumulative_writes = int(writes_str[:-1]) * 1000
            elif writes_str.endswith('M'):
                cumulative_writes = int(writes_str[:-1]) * 1000000
            else:
                cumulative_writes = int(writes_str)
            
            return {
                'timestamp': timestamp,
                'cumulative_writes': cumulative_writes,
                'write_rate': float(mbps_match.group(1))
            }
    except Exception:
        pass
    return None

def calculate_performance_metrics(stats_df):
    """성능 메트릭 계산"""
    print("📊 성능 메트릭 계산 중...")
    
    # 시간 정규화 (초 단위)
    stats_df['time_seconds'] = (stats_df['datetime'] - stats_df['datetime'].iloc[0]).dt.total_seconds()
    
    # 이동평균을 통한 노이즈 제거 (윈도우 크기: 100)
    window_size = 100
    stats_df['write_rate_smooth'] = stats_df['write_rate'].rolling(window=window_size, center=True).mean()
    
    # 성능 변화율 계산
    stats_df['performance_change_rate'] = stats_df['write_rate_smooth'].pct_change().fillna(0)
    
    # 성능 변화율의 절댓값 (변화 강도)
    stats_df['performance_change_abs'] = np.abs(stats_df['performance_change_rate'])
    
    # 성능 변화율의 이동평균 (추세 분석)
    stats_df['change_rate_trend'] = stats_df['performance_change_rate'].rolling(window=200, center=True).mean().fillna(0)
    
    # 성능 안정성 (변동계수)
    rolling_window = 500
    stats_df['performance_stability'] = stats_df['write_rate_smooth'].rolling(window=rolling_window).std() / stats_df['write_rate_smooth'].rolling(window=rolling_window).mean()
    stats_df['performance_stability'] = stats_df['performance_stability'].fillna(1.0)
    
    print("✅ 성능 메트릭 계산 완료")
    return stats_df

def detect_performance_transitions(stats_df):
    """성능 전환점 탐지"""
    print("📊 성능 전환점 탐지 중...")
    
    # 1. 성능 변화율 기반 전환점 탐지
    change_threshold = 0.02  # 2% 변화율 임계값
    significant_changes = stats_df[np.abs(stats_df['performance_change_rate']) > change_threshold].copy()
    
    # 2. 성능 수준 변화 탐지 (큰 폭 변화)
    performance_levels = []
    current_level = stats_df['write_rate_smooth'].iloc[0]
    level_threshold = 5.0  # 5 MB/s 차이
    
    for i, row in stats_df.iterrows():
        if abs(row['write_rate_smooth'] - current_level) > level_threshold:
            performance_levels.append(i)
            current_level = row['write_rate_smooth']
    
    # 3. 안정성 변화 탐지
    stability_threshold = 0.5  # 안정성 변화 임계값
    stability_changes = []
    
    for i in range(1, len(stats_df)):
        if i < len(stats_df) - 1:
            prev_stability = stats_df.iloc[i-1]['performance_stability']
            curr_stability = stats_df.iloc[i]['performance_stability']
            
            if not np.isnan(prev_stability) and not np.isnan(curr_stability):
                if abs(curr_stability - prev_stability) > stability_threshold:
                    stability_changes.append(i)
    
    # 4. 시계열 클러스터링을 통한 구간 분할
    # 성능 특성 벡터 생성
    features = ['write_rate_smooth', 'performance_change_abs', 'performance_stability']
    feature_data = stats_df[features].fillna(stats_df[features].mean())
    
    # 표준화
    scaler = StandardScaler()
    feature_data_scaled = scaler.fit_transform(feature_data)
    
    # K-means 클러스터링 (3개 클러스터)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    stats_df['cluster'] = kmeans.fit_predict(feature_data_scaled)
    
    # 클러스터 경계 찾기
    cluster_boundaries = []
    current_cluster = stats_df['cluster'].iloc[0]
    
    for i, cluster in enumerate(stats_df['cluster']):
        if cluster != current_cluster:
            cluster_boundaries.append(i)
            current_cluster = cluster
    
    print(f"✅ 성능 전환점 탐지 완료:")
    print(f"   - 큰 변화율 지점: {len(significant_changes)}개")
    print(f"   - 성능 수준 변화: {len(performance_levels)}개")
    print(f"   - 안정성 변화: {len(stability_changes)}개")
    print(f"   - 클러스터 경계: {len(cluster_boundaries)}개")
    
    return {
        'significant_changes': significant_changes,
        'performance_levels': performance_levels,
        'stability_changes': stability_changes,
        'cluster_boundaries': cluster_boundaries,
        'kmeans_model': kmeans,
        'scaler': scaler
    }

def determine_optimal_segmentation(stats_df, transitions):
    """최적 구간 분할 결정"""
    print("📊 최적 구간 분할 결정 중...")
    
    total_length = len(stats_df)
    
    # 방법 1: 성능 변화율 기반 분할
    method1_boundaries = []
    
    # 초기 구간: 빠른 성능 변화 구간 (높은 변화율)
    high_change_period = stats_df[stats_df['performance_change_abs'] > 0.01]  # 1% 이상 변화
    if len(high_change_period) > 0:
        initial_end = high_change_period.index[-1]
        method1_boundaries.append(initial_end)
    
    # 중기 구간: 안정화 진행 구간 (중간 안정성)
    remaining_data = stats_df.iloc[method1_boundaries[0]:] if method1_boundaries else stats_df
    stable_threshold = remaining_data['performance_stability'].quantile(0.3)  # 하위 30% 안정성
    stable_period = remaining_data[remaining_data['performance_stability'] < stable_threshold]
    
    if len(stable_period) > 0:
        middle_end = stable_period.index[-1]
        method1_boundaries.append(middle_end)
    
    # 방법 2: 클러스터 기반 분할
    method2_boundaries = transitions['cluster_boundaries'][:2]  # 처음 2개 경계만 사용
    
    # 방법 3: 성능 수준 기반 분할
    method3_boundaries = []
    
    # 성능 수준별 분할
    performance_quantiles = stats_df['write_rate_smooth'].quantile([0.33, 0.67])
    
    # 첫 번째 경계: 성능이 67% 분위수 아래로 떨어지는 지점
    high_to_mid = stats_df[stats_df['write_rate_smooth'] < performance_quantiles[0.67]].index
    if len(high_to_mid) > 0:
        method3_boundaries.append(high_to_mid[0])
    
    # 두 번째 경계: 성능이 33% 분위수 아래로 떨어지는 지점
    mid_to_low = stats_df[stats_df['write_rate_smooth'] < performance_quantiles[0.33]].index
    if len(mid_to_low) > 0:
        method3_boundaries.append(mid_to_low[0])
    
    # 최적 분할 선택 (여러 방법의 결과를 종합)
    all_boundaries = []
    if method1_boundaries:
        all_boundaries.extend(method1_boundaries)
    if method2_boundaries:
        all_boundaries.extend(method2_boundaries)
    if method3_boundaries:
        all_boundaries.extend(method3_boundaries)
    
    # 경계점들을 정렬하고 중복 제거
    all_boundaries = sorted(list(set(all_boundaries)))
    
    # 너무 가까운 경계점들 제거 (전체 길이의 10% 이내)
    min_distance = total_length * 0.1
    filtered_boundaries = []
    
    for boundary in all_boundaries:
        if not filtered_boundaries or boundary - filtered_boundaries[-1] > min_distance:
            filtered_boundaries.append(boundary)
    
    # 최대 2개의 경계점만 선택 (3구간)
    if len(filtered_boundaries) > 2:
        # 성능 변화가 가장 큰 지점들 선택
        boundary_scores = []
        for boundary in filtered_boundaries:
            if boundary > 0 and boundary < total_length - 1:
                before_perf = stats_df.iloc[max(0, boundary-50):boundary]['write_rate_smooth'].mean()
                after_perf = stats_df.iloc[boundary:min(total_length, boundary+50)]['write_rate_smooth'].mean()
                score = abs(before_perf - after_perf)
                boundary_scores.append((boundary, score))
        
        # 점수가 높은 상위 2개 선택
        boundary_scores.sort(key=lambda x: x[1], reverse=True)
        filtered_boundaries = sorted([bs[0] for bs in boundary_scores[:2]])
    
    # 최종 구간 정의
    if len(filtered_boundaries) >= 2:
        boundaries = filtered_boundaries[:2]
    elif len(filtered_boundaries) == 1:
        # 하나만 있으면 중간 지점에 하나 더 추가
        boundaries = [filtered_boundaries[0], int(total_length * 0.75)]
    else:
        # 경계를 찾지 못하면 기본 분할
        boundaries = [int(total_length * 0.4), int(total_length * 0.75)]
    
    # 구간 정의
    segments = {
        'initial': {
            'start_idx': 0,
            'end_idx': boundaries[0],
            'description': '빈 DB에서 빠르게 성능이 변하는 구간'
        },
        'middle': {
            'start_idx': boundaries[0],
            'end_idx': boundaries[1],
            'description': '컴팩션이 진행되며 안정화되어 가는 구간'
        },
        'final': {
            'start_idx': boundaries[1],
            'end_idx': total_length - 1,
            'description': '안정화 구간'
        }
    }
    
    print(f"✅ 최적 구간 분할 결정 완료:")
    for segment_name, segment_info in segments.items():
        start_time = stats_df.iloc[segment_info['start_idx']]['datetime']
        end_time = stats_df.iloc[segment_info['end_idx']]['datetime']
        duration = (end_time - start_time).total_seconds() / 3600
        print(f"   - {segment_name.title()} 구간: {segment_info['start_idx']} ~ {segment_info['end_idx']} ({duration:.1f}시간)")
        print(f"     설명: {segment_info['description']}")
    
    return segments

def analyze_segment_characteristics(stats_df, segments):
    """구간별 특성 분석"""
    print("📊 구간별 특성 분석 중...")
    
    segment_analysis = {}
    
    for segment_name, segment_info in segments.items():
        start_idx = segment_info['start_idx']
        end_idx = segment_info['end_idx']
        segment_data = stats_df.iloc[start_idx:end_idx+1]
        
        if len(segment_data) == 0:
            continue
            
        # 기본 통계
        basic_stats = {
            'duration_hours': (segment_data['datetime'].iloc[-1] - segment_data['datetime'].iloc[0]).total_seconds() / 3600,
            'sample_count': len(segment_data),
            'start_time': segment_data['datetime'].iloc[0],
            'end_time': segment_data['datetime'].iloc[-1],
            'start_idx': start_idx,
            'end_idx': end_idx
        }
        
        # 성능 통계
        performance_stats = {
            'avg_write_rate': segment_data['write_rate'].mean(),
            'max_write_rate': segment_data['write_rate'].max(),
            'min_write_rate': segment_data['write_rate'].min(),
            'std_write_rate': segment_data['write_rate'].std(),
            'cv': segment_data['write_rate'].std() / segment_data['write_rate'].mean() if segment_data['write_rate'].mean() > 0 else 0,
            'median_write_rate': segment_data['write_rate'].median(),
            'q25_write_rate': segment_data['write_rate'].quantile(0.25),
            'q75_write_rate': segment_data['write_rate'].quantile(0.75)
        }
        
        # 성능 변화 분석
        if len(segment_data) > 1:
            performance_trend = {
                'trend_slope': np.polyfit(range(len(segment_data)), segment_data['write_rate'], 1)[0],
                'trend_r2': np.corrcoef(range(len(segment_data)), segment_data['write_rate'])[0,1]**2 if len(segment_data) > 1 else 0,
                'performance_change': (segment_data['write_rate'].iloc[-1] - segment_data['write_rate'].iloc[0]) / segment_data['write_rate'].iloc[0] * 100 if segment_data['write_rate'].iloc[0] > 0 else 0,
                'avg_change_rate': segment_data['performance_change_rate'].mean(),
                'change_rate_volatility': segment_data['performance_change_rate'].std()
            }
        else:
            performance_trend = {
                'trend_slope': 0,
                'trend_r2': 0,
                'performance_change': 0,
                'avg_change_rate': 0,
                'change_rate_volatility': 0
            }
        
        # 구간별 특성 분류
        characteristics = classify_segment_characteristics(performance_stats, performance_trend)
        
        segment_analysis[segment_name] = {
            'basic_stats': basic_stats,
            'performance_stats': performance_stats,
            'performance_trend': performance_trend,
            'characteristics': characteristics,
            'description': segment_info['description']
        }
    
    print("✅ 구간별 특성 분석 완료")
    return segment_analysis

def classify_segment_characteristics(performance_stats, performance_trend):
    """구간별 특성 분류"""
    characteristics = {}
    
    # 성능 안정성
    if performance_stats['cv'] < 0.1:
        characteristics['stability'] = 'high'
    elif performance_stats['cv'] < 0.3:
        characteristics['stability'] = 'medium'
    else:
        characteristics['stability'] = 'low'
    
    # 성능 트렌드
    if performance_trend['trend_slope'] > 0.1:
        characteristics['trend'] = 'increasing'
    elif performance_trend['trend_slope'] < -0.1:
        characteristics['trend'] = 'decreasing'
    else:
        characteristics['trend'] = 'stable'
    
    # 성능 수준
    if performance_stats['avg_write_rate'] > 20:
        characteristics['performance_level'] = 'high'
    elif performance_stats['avg_write_rate'] > 15:
        characteristics['performance_level'] = 'medium'
    else:
        characteristics['performance_level'] = 'low'
    
    # 변화율 특성
    if abs(performance_trend['avg_change_rate']) > 0.01:
        characteristics['change_intensity'] = 'high'
    elif abs(performance_trend['avg_change_rate']) > 0.005:
        characteristics['change_intensity'] = 'medium'
    else:
        characteristics['change_intensity'] = 'low'
    
    return characteristics

def create_performance_segmentation_visualization(stats_df, segments, segment_analysis, transitions):
    """성능 기반 구간 분할 시각화"""
    print("📊 성능 기반 구간 분할 시각화 생성 중...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Performance-based Segmentation Analysis', fontsize=18, fontweight='bold')
    
    # 시간 정규화 (시간 단위)
    time_hours = stats_df['time_seconds'] / 3600
    
    # 구간별 색상
    colors = {'initial': '#FF6B6B', 'middle': '#4ECDC4', 'final': '#45B7D1'}
    
    # 1. 성능 추이와 구간 분할
    ax1.plot(time_hours, stats_df['write_rate'], alpha=0.3, color='gray', label='Raw Performance')
    ax1.plot(time_hours, stats_df['write_rate_smooth'], color='black', linewidth=2, label='Smoothed Performance')
    
    # 구간별 색칠
    for segment_name, segment_info in segments.items():
        start_idx = segment_info['start_idx']
        end_idx = segment_info['end_idx']
        segment_time = time_hours.iloc[start_idx:end_idx+1]
        segment_perf = stats_df['write_rate_smooth'].iloc[start_idx:end_idx+1]
        
        ax1.fill_between(segment_time, 0, segment_perf, alpha=0.3, color=colors[segment_name], 
                        label=f'{segment_name.title()} Phase')
    
    # 구간 경계선
    for segment_name, segment_info in segments.items():
        if segment_name != 'final':  # 마지막 구간 제외
            boundary_time = time_hours.iloc[segment_info['end_idx']]
            ax1.axvline(x=boundary_time, color='red', linestyle='--', alpha=0.7)
    
    ax1.set_xlabel('Time (hours)')
    ax1.set_ylabel('Write Rate (MB/s)')
    ax1.set_title('Performance-based Phase Segmentation')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 성능 변화율
    ax2.plot(time_hours, stats_df['performance_change_rate'], alpha=0.5, color='blue', label='Change Rate')
    ax2.plot(time_hours, stats_df['change_rate_trend'], color='darkblue', linewidth=2, label='Change Rate Trend')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.axhline(y=0.02, color='red', linestyle='--', alpha=0.5, label='Change Threshold')
    ax2.axhline(y=-0.02, color='red', linestyle='--', alpha=0.5)
    
    ax2.set_xlabel('Time (hours)')
    ax2.set_ylabel('Performance Change Rate')
    ax2.set_title('Performance Change Rate Analysis')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 구간별 특성 비교
    segment_names = list(segment_analysis.keys())
    avg_rates = [segment_analysis[seg]['performance_stats']['avg_write_rate'] for seg in segment_names]
    cv_values = [segment_analysis[seg]['performance_stats']['cv'] for seg in segment_names]
    change_rates = [abs(segment_analysis[seg]['performance_trend']['avg_change_rate']) for seg in segment_names]
    
    x = np.arange(len(segment_names))
    width = 0.25
    
    ax3_twin = ax3.twinx()
    
    bars1 = ax3.bar(x - width, avg_rates, width, label='Avg Performance (MB/s)', color='skyblue', alpha=0.8)
    bars2 = ax3_twin.bar(x, cv_values, width, label='CV', color='lightcoral', alpha=0.8)
    bars3 = ax3_twin.bar(x + width, change_rates, width, label='Avg Change Rate', color='lightgreen', alpha=0.8)
    
    ax3.set_xlabel('Phase')
    ax3.set_ylabel('Average Performance (MB/s)', color='blue')
    ax3_twin.set_ylabel('CV / Change Rate', color='red')
    ax3.set_title('Phase Characteristics Comparison')
    ax3.set_xticks(x)
    ax3.set_xticklabels([seg.title() for seg in segment_names])
    
    # 범례 통합
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax3.grid(True, alpha=0.3)
    
    # 4. 구간별 요약
    ax4.text(0.05, 0.95, 'Performance-based Segmentation Summary', fontsize=16, fontweight='bold', transform=ax4.transAxes)
    
    y_pos = 0.85
    for segment_name, analysis in segment_analysis.items():
        ax4.text(0.05, y_pos, f'{segment_name.title()} Phase:', fontsize=14, fontweight='bold', transform=ax4.transAxes, color=colors[segment_name])
        y_pos -= 0.05
        
        basic = analysis['basic_stats']
        perf = analysis['performance_stats']
        char = analysis['characteristics']
        
        ax4.text(0.05, y_pos, f'  Duration: {basic["duration_hours"]:.1f} hours ({basic["sample_count"]:,} samples)', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Avg Performance: {perf["avg_write_rate"]:.1f} MB/s (CV: {perf["cv"]:.3f})', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Characteristics: {char["stability"]} stability, {char["trend"]} trend', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.05, y_pos, f'  Description: {analysis["description"]}', fontsize=10, transform=ax4.transAxes, style='italic')
        y_pos -= 0.06
    
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    
    plt.tight_layout()
    plt.savefig('performance_based_segmentation_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ 성능 기반 구간 분할 시각화 완료")

def save_results(stats_df, segments, segment_analysis, transitions):
    """결과 저장"""
    print("💾 성능 기반 구간 분할 결과 저장 중...")
    
    # JSON 결과 저장
    results = {
        'segmentation_method': 'performance_based',
        'segments': segments,
        'segment_analysis': segment_analysis,
        'transition_points': {
            'cluster_boundaries': transitions['cluster_boundaries'],
            'performance_levels': transitions['performance_levels'],
            'stability_changes': transitions['stability_changes']
        },
        'analysis_time': datetime.now().isoformat()
    }
    
    with open('performance_based_segmentation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Markdown 보고서 생성
    with open('performance_based_segmentation_report.md', 'w') as f:
        f.write("# Performance-based Segmentation Analysis Report\n\n")
        f.write(f"## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n")
        f.write("This report presents the results of performance-based segmentation analysis using RocksDB LOG data.\n")
        f.write("Unlike time-based segmentation, this approach identifies phases based on actual performance change patterns.\n\n")
        
        f.write("## Segmentation Method\n")
        f.write("The segmentation is based on:\n")
        f.write("1. **Performance Change Rate Analysis**: Detecting significant performance transitions\n")
        f.write("2. **Performance Level Changes**: Identifying major performance drops\n")
        f.write("3. **Stability Analysis**: Detecting changes in performance variability\n")
        f.write("4. **Clustering Analysis**: Using K-means clustering on performance characteristics\n\n")
        
        f.write("## Phase Definitions\n")
        for segment_name, analysis in segment_analysis.items():
            f.write(f"### {segment_name.title()} Phase\n")
            f.write(f"**Description**: {analysis['description']}\n\n")
            
            basic = analysis['basic_stats']
            f.write(f"**Timing**:\n")
            f.write(f"- Start: {basic['start_time']}\n")
            f.write(f"- End: {basic['end_time']}\n")
            f.write(f"- Duration: {basic['duration_hours']:.1f} hours\n")
            f.write(f"- Sample Count: {basic['sample_count']:,}\n\n")
            
            perf = analysis['performance_stats']
            f.write(f"**Performance Statistics**:\n")
            f.write(f"- Average Rate: {perf['avg_write_rate']:.1f} MB/s\n")
            f.write(f"- Performance Range: {perf['min_write_rate']:.1f} - {perf['max_write_rate']:.1f} MB/s\n")
            f.write(f"- Standard Deviation: {perf['std_write_rate']:.1f} MB/s\n")
            f.write(f"- Coefficient of Variation: {perf['cv']:.3f}\n")
            f.write(f"- Median Rate: {perf['median_write_rate']:.1f} MB/s\n\n")
            
            trend = analysis['performance_trend']
            f.write(f"**Performance Trend**:\n")
            f.write(f"- Trend Slope: {trend['trend_slope']:.6f}\n")
            f.write(f"- R² Score: {trend['trend_r2']:.3f}\n")
            f.write(f"- Overall Change: {trend['performance_change']:.1f}%\n")
            f.write(f"- Average Change Rate: {trend['avg_change_rate']:.6f}\n")
            f.write(f"- Change Rate Volatility: {trend['change_rate_volatility']:.6f}\n\n")
            
            char = analysis['characteristics']
            f.write(f"**Phase Characteristics**:\n")
            f.write(f"- Stability: {char['stability']}\n")
            f.write(f"- Trend: {char['trend']}\n")
            f.write(f"- Performance Level: {char['performance_level']}\n")
            f.write(f"- Change Intensity: {char['change_intensity']}\n\n")
            
            f.write("---\n\n")
        
        f.write("## Key Insights\n\n")
        f.write("### Performance-based vs Time-based Segmentation\n")
        f.write("- **Performance-based**: Segments based on actual performance change patterns\n")
        f.write("- **Advantage**: More meaningful phase boundaries that reflect actual system behavior\n")
        f.write("- **Result**: Variable phase durations based on performance characteristics\n\n")
        
        f.write("### Phase Progression Pattern\n")
        for segment_name, analysis in segment_analysis.items():
            char = analysis['characteristics']
            perf = analysis['performance_stats']
            f.write(f"- **{segment_name.title()}**: {char['performance_level']} performance, {char['stability']} stability, {char['trend']} trend (Avg: {perf['avg_write_rate']:.1f} MB/s)\n")
        
        f.write(f"\n## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    print("✅ 성능 기반 구간 분할 결과 저장 완료")

def main():
    """메인 함수"""
    print("🚀 성능 변화 기반 구간 분할 분석 시작...")
    
    # LOG 파일 경로 설정
    main_log = "rocksdb_log_phase_b.log"
    
    if not os.path.exists(main_log):
        print("❌ LOG 파일을 찾을 수 없습니다!")
        return
    
    print(f"📖 메인 LOG 파일: {main_log}")
    
    # LOG 파일 분석
    stats_data = parse_log_file(main_log)
    
    if not stats_data:
        print("❌ Stats 데이터가 없습니다.")
        return
    
    # 데이터프레임 생성
    stats_df = pd.DataFrame([s for s in stats_data if s])
    stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'])
    stats_df = stats_df.sort_values('datetime').reset_index(drop=True)
    
    print(f"📊 총 데이터 포인트: {len(stats_df)}개")
    
    # 성능 메트릭 계산
    stats_df = calculate_performance_metrics(stats_df)
    
    # 성능 전환점 탐지
    transitions = detect_performance_transitions(stats_df)
    
    # 최적 구간 분할 결정
    segments = determine_optimal_segmentation(stats_df, transitions)
    
    # 구간별 특성 분석
    segment_analysis = analyze_segment_characteristics(stats_df, segments)
    
    # 결과 출력
    print("\n📊 성능 기반 구간 분할 결과:")
    for segment_name, analysis in segment_analysis.items():
        print(f"\n  {segment_name.title()} Phase:")
        basic = analysis['basic_stats']
        perf = analysis['performance_stats']
        char = analysis['characteristics']
        
        print(f"    기간: {basic['start_time']} ~ {basic['end_time']}")
        print(f"    지속시간: {basic['duration_hours']:.1f} 시간")
        print(f"    샘플 수: {basic['sample_count']:,}개")
        print(f"    평균 성능: {perf['avg_write_rate']:.1f} MB/s")
        print(f"    성능 범위: {perf['min_write_rate']:.1f} ~ {perf['max_write_rate']:.1f} MB/s")
        print(f"    변동계수: {perf['cv']:.3f}")
        print(f"    안정성: {char['stability']}")
        print(f"    트렌드: {char['trend']}")
        print(f"    성능 수준: {char['performance_level']}")
        print(f"    변화 강도: {char['change_intensity']}")
        print(f"    설명: {analysis['description']}")
    
    # 시각화 생성
    create_performance_segmentation_visualization(stats_df, segments, segment_analysis, transitions)
    
    # 결과 저장
    save_results(stats_df, segments, segment_analysis, transitions)
    
    print("\n✅ 성능 변화 기반 구간 분할 분석 완료!")
    print("📊 결과 파일: performance_based_segmentation_analysis.png, performance_based_segmentation_results.json, performance_based_segmentation_report.md")

if __name__ == "__main__":
    main()





