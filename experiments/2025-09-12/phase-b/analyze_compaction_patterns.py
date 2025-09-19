#!/usr/bin/env python3
"""
Compaction 패턴 상세 분석
실제 compaction이 어떤 레벨에서 어떤 레벨로 일어나는지 분석
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
    
    compaction_data = []
    current_timestamp = None
    
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 시간 정보 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            # Compaction 로그 파싱 (더 상세한 정보 추출)
            if "Compaction start" in line:
                compaction_data.append(parse_compaction_start_line(line, current_timestamp))
            elif "Compaction finished" in line:
                compaction_data.append(parse_compaction_finish_line(line, current_timestamp))
    
    print(f"✅ 파싱 완료: Compaction {len(compaction_data)}개")
    return compaction_data

def parse_compaction_start_line(line, timestamp):
    """Compaction start 라인 파싱"""
    try:
        # Base level 추출
        base_level_match = re.search(r'Base level (\d+)', line)
        base_level = int(base_level_match.group(1)) if base_level_match else -1
        
        # Input files 추출
        inputs_match = re.search(r'inputs: \[([^\]]+)\]', line)
        input_files = inputs_match.group(1) if inputs_match else ""
        
        # Output files 추출 (있는 경우)
        outputs_match = re.search(r'\[([^\]]+)\]', line)
        output_files = outputs_match.group(1) if outputs_match else ""
        
        # Compaction 타입 추출
        compaction_type = "unknown"
        if "Level-0" in line:
            compaction_type = "Level-0"
        elif "Level-1" in line:
            compaction_type = "Level-1"
        elif "Level-2" in line:
            compaction_type = "Level-2"
        elif "Level-3" in line:
            compaction_type = "Level-3"
        elif "Level-4" in line:
            compaction_type = "Level-4"
        
        return {
            'timestamp': timestamp,
            'type': 'start',
            'base_level': base_level,
            'input_files': input_files,
            'output_files': output_files,
            'compaction_type': compaction_type
        }
    except Exception as e:
        return None

def parse_compaction_finish_line(line, timestamp):
    """Compaction finish 라인 파싱"""
    try:
        # Base level 추출
        base_level_match = re.search(r'Base level (\d+)', line)
        base_level = int(base_level_match.group(1)) if base_level_match else -1
        
        return {
            'timestamp': timestamp,
            'type': 'finished',
            'base_level': base_level,
            'input_files': "",
            'output_files': "",
            'compaction_type': "unknown"
        }
    except Exception as e:
        return None

def analyze_compaction_patterns(compaction_data):
    """Compaction 패턴 상세 분석"""
    print("📊 Compaction 패턴 상세 분석 중...")
    
    try:
        # 데이터프레임 생성
        compaction_df = pd.DataFrame([d for d in compaction_data if d is not None])
        
        if compaction_df.empty:
            print("❌ 데이터가 없습니다!")
            return
        
        # 시간 변환
        compaction_df['datetime'] = pd.to_datetime(compaction_df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
        compaction_df['hour'] = compaction_df['datetime'].dt.floor('h')
        
        # 시각화 생성
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        
        # 1. Base Level별 Compaction 분포
        base_level_counts = compaction_df['base_level'].value_counts().sort_index()
        colors = plt.cm.Set3(np.linspace(0, 1, len(base_level_counts)))
        
        bars = ax1.bar(range(len(base_level_counts)), base_level_counts.values, color=colors, alpha=0.8)
        ax1.set_title('Compaction Distribution by Base Level', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Base Level')
        ax1.set_ylabel('Compaction Count')
        ax1.set_xticks(range(len(base_level_counts)))
        ax1.set_xticklabels([f'Level {l}' for l in base_level_counts.index])
        ax1.grid(True, alpha=0.3)
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # 2. 시간별 Base Level별 Compaction 히트맵
        hourly_base_level = compaction_df.groupby(['hour', 'base_level']).size().unstack(fill_value=0)
        
        if not hourly_base_level.empty:
            # 레벨 순서 정렬
            level_order = sorted([col for col in hourly_base_level.columns if col != -1])
            hourly_base_level_sorted = hourly_base_level[level_order]
            
            im = ax2.imshow(hourly_base_level_sorted.T.values, cmap='YlOrRd', aspect='auto')
            ax2.set_title('Hourly Compaction Heatmap by Base Level', fontsize=16, fontweight='bold')
            ax2.set_xlabel('Time (Hours)')
            ax2.set_ylabel('Base Level')
            ax2.set_yticks(range(len(level_order)))
            ax2.set_yticklabels([f'Level {l}' for l in level_order])
            
            # 시간 축 레이블 (24시간마다)
            time_labels = hourly_base_level_sorted.index[::24]
            time_positions = range(0, len(hourly_base_level_sorted), 24)
            ax2.set_xticks(time_positions)
            ax2.set_xticklabels([t.strftime('%m/%d %H:%M') for t in time_labels], rotation=45)
            
            # 컬러바 추가
            cbar = plt.colorbar(im, ax=ax2)
            cbar.set_label('Compaction Count')
        
        # 3. Base Level별 Compaction 분포 (파이 차트)
        wedges, texts, autotexts = ax3.pie(base_level_counts.values, labels=[f'Level {l}' for l in base_level_counts.index], 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        ax3.set_title('Compaction Distribution by Base Level', fontsize=16, fontweight='bold')
        
        # 통계 정보 추가
        stats_text = f"""
        Total Compactions: {base_level_counts.sum():,}
        Analysis Period: {len(hourly_base_level)} hours
        Most Active Base Level: Level {base_level_counts.idxmax()}
        """
        ax3.text(1.3, 0.5, stats_text, transform=ax3.transAxes, fontsize=10,
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 4. 시간별 Compaction 빈도
        hourly_compaction = compaction_df.groupby('hour').size()
        
        ax4.plot(hourly_compaction.index, hourly_compaction.values, 'b-', linewidth=2, marker='o')
        ax4.set_title('Hourly Compaction Frequency', fontsize=16, fontweight='bold')
        ax4.set_xlabel('Time')
        ax4.set_ylabel('Compaction Count per Hour')
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45)
        
        # 이동평균 추가
        hourly_compaction_ma = hourly_compaction.rolling(window=5).mean()
        ax4.plot(hourly_compaction_ma.index, hourly_compaction_ma.values, 'r--', alpha=0.8, linewidth=2, label='5-hour MA')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig('compaction_patterns_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Compaction 패턴 상세 분석 시각화 저장 완료: compaction_patterns_analysis.png")
        
        # 상세 분석 결과 출력
        print("\n📊 Compaction 패턴 상세 분석 결과:")
        print(f"  분석 기간: {len(hourly_base_level)} 시간")
        print(f"  총 Compaction: {base_level_counts.sum():,}회")
        print(f"  Base Level별 Compaction:")
        for level, count in base_level_counts.items():
            level_name = f'Level {level}'
            percentage = (count / base_level_counts.sum()) * 100
            print(f"    {level_name}: {count:,}회 ({percentage:.1f}%)")
        
        # 시간대별 분석
        print(f"\n  시간대별 Compaction 패턴:")
        peak_hour = hourly_compaction.idxmax()
        min_hour = hourly_compaction.idxmin()
        print(f"    최대 Compaction 시간: {peak_hour.strftime('%Y-%m-%d %H:%M')} ({hourly_compaction.max():,}회)")
        print(f"    최소 Compaction 시간: {min_hour.strftime('%Y-%m-%d %H:%M')} ({hourly_compaction.min():,}회)")
        print(f"    평균 Compaction 량: {hourly_compaction.mean():.1f}회/시간")
        
        # Base Level별 상세 분석
        print(f"\n  Base Level별 상세 분석:")
        for level in sorted(base_level_counts.index):
            level_data = compaction_df[compaction_df['base_level'] == level]
            if not level_data.empty:
                start_count = len(level_data[level_data['type'] == 'start'])
                finish_count = len(level_data[level_data['type'] == 'finished'])
                print(f"    Level {level}: Start {start_count}회, Finish {finish_count}회")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("🚀 Compaction 패턴 상세 분석 시작...")
    
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
    compaction_data = parse_log_file(main_log)
    
    if not compaction_data:
        print("❌ 분석할 데이터가 없습니다!")
        return
    
    # Compaction 패턴 상세 분석
    analyze_compaction_patterns(compaction_data)
    
    print("\n✅ Compaction 패턴 상세 분석 완료!")

if __name__ == "__main__":
    main()


