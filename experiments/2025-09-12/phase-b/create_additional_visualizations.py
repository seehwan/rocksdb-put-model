#!/usr/bin/env python3
"""
Phase-B 추가 시각화 생성
- compaction_io_analysis.png
- time_series_analysis.png
- phase_b_performance_trend.png
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

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def parse_log_file(log_file):
    """LOG 파일 파싱"""
    print(f"📖 LOG 파일 파싱 중: {log_file}")
    
    stats_data = []
    compaction_data = []
    current_timestamp = None
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 시간 정보 추출 (DUMPING STATS 라인 바로 위)
            if "------- DUMPING STATS -------" in line:
                # 이전 라인에서 시간 정보 추출
                continue
            
            # 시간 정보가 있는 라인에서 timestamp 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            # Stats 로그 파싱 (시간 정보와 함께)
            if "Cumulative writes:" in line:
                stats_data.append(parse_stats_line(line, current_timestamp))
            
            # Compaction 로그 파싱
            elif "Compaction start" in line or "Compaction finished" in line:
                compaction_data.append(parse_compaction_line(line))
    
    print(f"✅ 파싱 완료: Stats {len(stats_data)}개, Compaction {len(compaction_data)}개")
    return stats_data, compaction_data

def parse_stats_line(line, timestamp):
    """Stats 라인 파싱"""
    try:
        # write_rate 추출
        write_rate_match = re.search(r'write_rate:(\d+(?:\.\d+)?)', line)
        write_rate = float(write_rate_match.group(1)) if write_rate_match else 0
        
        # cumulative_writes 추출
        cum_writes_match = re.search(r'Cumulative writes:(\d+)', line)
        cum_writes = int(cum_writes_match.group(1)) if cum_writes_match else 0
        
        return {
            'timestamp': timestamp,
            'write_rate': write_rate,
            'cumulative_writes': cum_writes
        }
    except Exception as e:
        return None

def parse_compaction_line(line):
    """Compaction 라인 파싱"""
    try:
        # level 추출
        level_match = re.search(r'level:(\d+)', line)
        level = int(level_match.group(1)) if level_match else -1
        
        # timestamp 추출
        timestamp_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        return {
            'timestamp': timestamp,
            'level': level
        }
    except Exception as e:
        return None

def create_compaction_io_analysis(stats_data, compaction_data):
    """Compaction I/O 분석 시각화 생성"""
    print("📊 Compaction I/O 분석 시각화 생성 중...")
    
    try:
        # 데이터프레임 생성
        stats_df = pd.DataFrame([d for d in stats_data if d is not None])
        compaction_df = pd.DataFrame([d for d in compaction_data if d is not None])
        
        if stats_df.empty or compaction_df.empty:
            print("❌ 데이터가 없습니다!")
            return
        
        # 시간 변환
        stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        
        # 시각화 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Compaction I/O 강도 분석
        compaction_df['hour'] = compaction_df['datetime'].dt.floor('h')
        hourly_compactions = compaction_df.groupby('hour').size()
        
        ax1.plot(hourly_compactions.index, hourly_compactions.values, 'b-', linewidth=2, marker='o')
        ax1.set_title('Compaction I/O Intensity Over Time', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Compaction Count per Hour')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. 레벨별 I/O 분포
        level_counts = compaction_df['level'].value_counts().sort_index()
        colors = plt.cm.Set3(np.linspace(0, 1, len(level_counts)))
        
        bars = ax2.bar(range(len(level_counts)), level_counts.values, color=colors, alpha=0.8)
        ax2.set_title('I/O Distribution by Level', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Level')
        ax2.set_ylabel('I/O Count')
        ax2.set_xticks(range(len(level_counts)))
        ax2.set_xticklabels([f'Level {l}' for l in level_counts.index])
        ax2.grid(True, alpha=0.3)
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # 3. 성능 vs Compaction 상관관계
        stats_df['hour'] = stats_df['datetime'].dt.floor('h')
        hourly_performance = stats_df.groupby('hour')['write_rate'].mean()
        
        # 공통 시간대만 선택
        common_hours = hourly_performance.index.intersection(hourly_compactions.index)
        if len(common_hours) > 0:
            performance_values = [hourly_performance[h] for h in common_hours]
            compaction_values = [hourly_compactions[h] for h in common_hours]
            
            scatter = ax3.scatter(compaction_values, performance_values, 
                                c=range(len(common_hours)), cmap='viridis', 
                                alpha=0.7, s=100)
            ax3.set_title('Performance vs Compaction Correlation', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Compaction Count per Hour')
            ax3.set_ylabel('Write Rate (ops/sec)')
            ax3.grid(True, alpha=0.3)
            
            # 컬러바 추가
            cbar = plt.colorbar(scatter, ax=ax3)
            cbar.set_label('Time Progression')
        
        # 4. I/O 패턴 히트맵
        compaction_df['day'] = compaction_df['datetime'].dt.date
        compaction_df['hour'] = compaction_df['datetime'].dt.hour
        
        pivot_data = compaction_df.groupby(['day', 'hour']).size().unstack(fill_value=0)
        if not pivot_data.empty:
            im = ax4.imshow(pivot_data.values, cmap='YlOrRd', aspect='auto')
            ax4.set_title('I/O Pattern Heatmap', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Hour of Day')
            ax4.set_ylabel('Day')
            ax4.set_xticks(range(0, 24, 4))
            ax4.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 4)])
            
            # 컬러바 추가
            cbar = plt.colorbar(im, ax=ax4)
            cbar.set_label('I/O Count')
        
        plt.tight_layout()
        plt.savefig('compaction_io_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Compaction I/O 분석 시각화 저장 완료: compaction_io_analysis.png")
        
    except Exception as e:
        print(f"❌ 시각화 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def create_time_series_analysis(stats_data, compaction_data):
    """시계열 분석 시각화 생성"""
    print("📊 시계열 분석 시각화 생성 중...")
    
    try:
        # 데이터프레임 생성
        stats_df = pd.DataFrame([d for d in stats_data if d is not None])
        compaction_df = pd.DataFrame([d for d in compaction_data if d is not None])
        
        if stats_df.empty or compaction_df.empty:
            print("❌ 데이터가 없습니다!")
            return
        
        # 시간 변환
        stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        
        # 시각화 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 성능 시계열
        ax1.plot(stats_df['datetime'], stats_df['write_rate'], 'b-', linewidth=2, alpha=0.7)
        ax1.set_title('Write Rate Time Series', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Write Rate (ops/sec)')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 이동평균 추가
        stats_df['ma_10'] = stats_df['write_rate'].rolling(window=10).mean()
        ax1.plot(stats_df['datetime'], stats_df['ma_10'], 'r--', alpha=0.8, linewidth=2, label='10-point MA')
        ax1.legend()
        
        # 2. 누적 쓰기 시계열
        ax2.plot(stats_df['datetime'], stats_df['cumulative_writes'], 'g-', linewidth=2)
        ax2.set_title('Cumulative Writes Time Series', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Cumulative Writes')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Compaction 시계열
        compaction_df['hour'] = compaction_df['datetime'].dt.floor('h')
        hourly_compactions = compaction_df.groupby('hour').size()
        
        ax3.plot(hourly_compactions.index, hourly_compactions.values, 'orange', linewidth=2, marker='o')
        ax3.set_title('Compaction Frequency Time Series', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('Compaction Count per Hour')
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)
        
        # 4. 성능 분포 히스토그램
        ax4.hist(stats_df['write_rate'], bins=50, alpha=0.7, color='purple', edgecolor='black')
        ax4.set_title('Write Rate Distribution', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Write Rate (ops/sec)')
        ax4.set_ylabel('Frequency')
        ax4.grid(True, alpha=0.3)
        
        # 통계 정보 추가
        mean_rate = stats_df['write_rate'].mean()
        std_rate = stats_df['write_rate'].std()
        ax4.axvline(mean_rate, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_rate:.1f}')
        ax4.axvline(mean_rate + std_rate, color='orange', linestyle='--', linewidth=2, label=f'+1σ: {mean_rate + std_rate:.1f}')
        ax4.axvline(mean_rate - std_rate, color='orange', linestyle='--', linewidth=2, label=f'-1σ: {mean_rate - std_rate:.1f}')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig('time_series_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 시계열 분석 시각화 저장 완료: time_series_analysis.png")
        
    except Exception as e:
        print(f"❌ 시각화 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def create_performance_trend_analysis(stats_data, compaction_data):
    """성능 트렌드 분석 시각화 생성"""
    print("📊 성능 트렌드 분석 시각화 생성 중...")
    
    try:
        # 데이터프레임 생성
        stats_df = pd.DataFrame([d for d in stats_data if d is not None])
        
        if stats_df.empty:
            print("❌ 데이터가 없습니다!")
            return
        
        # 시간 변환
        stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        
        # 시각화 생성
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # 1. 성능 트렌드
        ax1.plot(stats_df['datetime'], stats_df['write_rate'], 'b-', linewidth=2, alpha=0.7, label='Write Rate')
        ax1.set_title('Performance Trend Analysis', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Write Rate (ops/sec)')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 이동평균 추가
        stats_df['ma_5'] = stats_df['write_rate'].rolling(window=5).mean()
        stats_df['ma_20'] = stats_df['write_rate'].rolling(window=20).mean()
        ax1.plot(stats_df['datetime'], stats_df['ma_5'], 'r--', alpha=0.8, linewidth=2, label='5-point MA')
        ax1.plot(stats_df['datetime'], stats_df['ma_20'], 'g--', alpha=0.8, linewidth=2, label='20-point MA')
        ax1.legend()
        
        # 2. 성능 변화율
        stats_df['rate_change'] = stats_df['write_rate'].pct_change() * 100
        ax2.plot(stats_df['datetime'], stats_df['rate_change'], 'purple', linewidth=2, alpha=0.7)
        ax2.set_title('Performance Change Rate', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Change Rate (%)')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig('phase_b_performance_trend.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 성능 트렌드 분석 시각화 저장 완료: phase_b_performance_trend.png")
        
    except Exception as e:
        print(f"❌ 시각화 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 Phase-B 추가 시각화 생성 시작...")
    
    # LOG 파일 찾기
    log_files = list(Path('.').glob('LOG*')) + list(Path('logs').glob('LOG*'))
    
    if not log_files:
        print("❌ LOG 파일을 찾을 수 없습니다!")
        print("Phase-B 실행 후 LOG 파일이 생성되었는지 확인하세요.")
        return
    
    # 가장 큰 LOG 파일 선택 (메인 로그)
    main_log = max(log_files, key=lambda f: f.stat().st_size)
    print(f"📖 메인 LOG 파일: {main_log}")
    
    # LOG 파일 분석
    stats_data, compaction_data = parse_log_file(main_log)
    
    if not stats_data or not compaction_data:
        print("❌ 분석할 데이터가 없습니다!")
        return
    
    # 추가 시각화 생성
    create_compaction_io_analysis(stats_data, compaction_data)
    create_time_series_analysis(stats_data, compaction_data)
    create_performance_trend_analysis(stats_data, compaction_data)
    
    print("\n✅ Phase-B 추가 시각화 생성 완료!")

if __name__ == "__main__":
    main()


