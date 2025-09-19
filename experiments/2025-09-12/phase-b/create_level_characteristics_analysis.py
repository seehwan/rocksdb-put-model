#!/usr/bin/env python3
"""
Phase-B Level Characteristics Analysis
레벨별 특성 분석 시각화 생성 (글자 깨짐 수정)
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

def create_level_characteristics_analysis(stats_data, compaction_data):
    """레벨별 특성 분석 시각화 생성"""
    print("📊 레벨별 특성 분석 시각화 생성 중...")
    
    try:
        # 데이터프레임 생성
        stats_df = pd.DataFrame(stats_data)
        compaction_df = pd.DataFrame(compaction_data)
        
        if stats_df.empty or compaction_df.empty:
            print("❌ 데이터가 없습니다!")
            return
        
        # 시간 변환
        stats_df['datetime'] = pd.to_datetime(stats_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        
        # 시각화 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 레벨별 Compaction 빈도
        if not compaction_df.empty:
            level_counts = compaction_df['level'].value_counts().sort_index()
            colors = plt.cm.Set3(np.linspace(0, 1, len(level_counts)))
            
            bars = ax1.bar(range(len(level_counts)), level_counts.values, color=colors, alpha=0.8)
            ax1.set_title('Compaction Frequency by Level', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Level')
            ax1.set_ylabel('Compaction Count')
            ax1.set_xticks(range(len(level_counts)))
            ax1.set_xticklabels([f'Level {l}' for l in level_counts.index])
            ax1.grid(True, alpha=0.3)
            
            # 값 표시
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # 2. 시간별 레벨별 Compaction 패턴
        if not compaction_df.empty:
            compaction_df['hour'] = compaction_df['datetime'].dt.floor('H')
            hourly_level_compactions = compaction_df.groupby(['hour', 'level']).size().unstack(fill_value=0)
            
            if not hourly_level_compactions.empty:
                hourly_level_compactions.plot(kind='bar', stacked=True, ax=ax2, 
                                            color=plt.cm.Set3(np.linspace(0, 1, len(hourly_level_compactions.columns))))
                ax2.set_title('Hourly Compaction Pattern by Level', fontsize=14, fontweight='bold')
                ax2.set_xlabel('Hour')
                ax2.set_ylabel('Compaction Count')
                ax2.legend(title='Level', bbox_to_anchor=(1.05, 1), loc='upper left')
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
        
        # 3. 레벨별 Compaction 분포 (파이 차트)
        if not compaction_df.empty:
            level_counts = compaction_df['level'].value_counts().sort_index()
            colors = plt.cm.Set3(np.linspace(0, 1, len(level_counts)))
            
            wedges, texts, autotexts = ax3.pie(level_counts.values, 
                                             labels=[f'Level {l}' for l in level_counts.index], 
                                             autopct='%1.1f%%', 
                                             colors=colors,
                                             startangle=90)
            ax3.set_title('Compaction Distribution by Level', fontsize=14, fontweight='bold')
            
            # 텍스트 스타일 개선
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
        
        # 4. 성능 vs Compaction 상관관계
        if not stats_df.empty and not compaction_df.empty:
            # 시간별 성능 데이터
            stats_df['hour'] = stats_df['datetime'].dt.floor('H')
            hourly_performance = stats_df.groupby('hour')['write_rate'].mean()
            
            # 시간별 Compaction 데이터
            compaction_df['hour'] = compaction_df['datetime'].dt.floor('H')
            hourly_compactions = compaction_df.groupby('hour').size()
            
            # 공통 시간대만 선택
            common_hours = hourly_performance.index.intersection(hourly_compactions.index)
            if len(common_hours) > 0:
                performance_values = [hourly_performance[h] for h in common_hours]
                compaction_values = [hourly_compactions[h] for h in common_hours]
                
                scatter = ax4.scatter(compaction_values, performance_values, 
                                    c=range(len(common_hours)), cmap='viridis', 
                                    alpha=0.7, s=100)
                ax4.set_title('Performance vs Compaction Correlation', fontsize=14, fontweight='bold')
                ax4.set_xlabel('Compaction Count per Hour')
                ax4.set_ylabel('Write Rate (ops/sec)')
                ax4.grid(True, alpha=0.3)
                
                # 컬러바 추가
                cbar = plt.colorbar(scatter, ax=ax4)
                cbar.set_label('Time Progression')
        
        plt.tight_layout()
        plt.savefig('level_characteristics_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 레벨별 특성 분석 시각화 저장 완료: level_characteristics_analysis.png")
        
    except Exception as e:
        print(f"❌ 시각화 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 Phase-B Level Characteristics Analysis 시작...")
    
    # LOG 파일 찾기 (현재 디렉토리와 logs 디렉토리에서)
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
    
    # 레벨별 특성 분석 시각화 생성
    create_level_characteristics_analysis(stats_data, compaction_data)
    
    print("\n✅ Phase-B Level Characteristics Analysis 완료!")

if __name__ == "__main__":
    main()
