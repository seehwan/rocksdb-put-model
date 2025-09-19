#!/usr/bin/env python3
"""
Phase-B 분석 스크립트
FillRandom LOG 파일 분석 및 시간별 성능 변화 시각화
"""

import json
import re
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from datetime import datetime
import numpy as np

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

def parse_log_file(log_file):
    """LOG 파일 파싱"""
    print(f"📖 LOG 파일 분석 중: {log_file}")
    
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
    
    return stats_data, compaction_data

def parse_stats_line(line, timestamp=None):
    """Stats 라인 파싱"""
    try:
        # Cumulative writes 추출 (K 단위 처리)
        writes_match = re.search(r'Cumulative writes: (\d+)K writes', line)
        if writes_match:
            writes = int(writes_match.group(1)) * 1000  # K를 1000으로 변환
        else:
            writes_match = re.search(r'Cumulative writes: (\d+) writes', line)
            writes = int(writes_match.group(1)) if writes_match else 0
        
        # Write rate 추출 (MB/s 단위)
        rate_match = re.search(r'(\d+\.?\d*) MB/s', line)
        write_rate = float(rate_match.group(1)) if rate_match else 0
        
        # Ingest 추출 (GB 단위)
        ingest_match = re.search(r'ingest: (\d+\.?\d*) GB', line)
        ingest_gb = float(ingest_match.group(1)) if ingest_match else 0
        
        return {
            'timestamp': timestamp,
            'cumulative_writes': writes,
            'write_rate': write_rate,
            'ingest_gb': ingest_gb
        }
    except Exception as e:
        print(f"Stats 라인 파싱 오류: {e}")
        return None

def parse_compaction_line(line):
    """Compaction 라인 파싱"""
    try:
        # 시간 추출 (마이크로초 포함)
        time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
        timestamp = time_match.group(1) if time_match else None
        
        # Compaction 타입 추출
        compaction_type = "start" if "Compaction start" in line else "finish"
        
        # 레벨 정보 추출
        level_match = re.search(r'level-(\d+)', line)
        level = int(level_match.group(1)) if level_match else -1
        
        return {
            'timestamp': timestamp,
            'type': compaction_type,
            'level': level
        }
    except Exception as e:
        print(f"Compaction 라인 파싱 오류: {e}")
        return None

def analyze_performance_trends(stats_data):
    """성능 트렌드 분석"""
    print("\n=== 📊 성능 트렌드 분석 ===")
    
    if not stats_data:
        print("❌ Stats 데이터가 없습니다!")
        return None
    
    # 데이터프레임 생성
    df = pd.DataFrame([d for d in stats_data if d is not None])
    
    if df.empty:
        print("❌ 유효한 Stats 데이터가 없습니다!")
        return None
    
    # 시간 변환 (마이크로초 포함)
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    
    # 성능 분석
    initial_rate = df['write_rate'].iloc[0] if len(df) > 0 else 0
    final_rate = df['write_rate'].iloc[-1] if len(df) > 0 else 0
    max_rate = df['write_rate'].max()
    min_rate = df['write_rate'].min()
    
    print(f"📈 성능 지표:")
    print(f"  초기 Put Rate: {initial_rate:.0f} ops/sec")
    print(f"  최대 Put Rate: {max_rate:.0f} ops/sec")
    print(f"  최소 Put Rate: {min_rate:.0f} ops/sec")
    print(f"  최종 Put Rate: {final_rate:.0f} ops/sec")
    print(f"  성능 저하율: {((initial_rate - final_rate) / initial_rate * 100):.1f}%")
    
    # 안정화 분석
    last_10_percent = df.tail(int(len(df) * 0.1))
    if len(last_10_percent) > 1:
        stability_std = last_10_percent['write_rate'].std()
        stability_mean = last_10_percent['write_rate'].mean()
        stability_cv = stability_std / stability_mean * 100 if stability_mean > 0 else 0
        
        print(f"  안정화 구간 변동계수: {stability_cv:.1f}%")
        if stability_cv < 10:
            print("  ✅ 안정화 달성")
        else:
            print("  ⚠️ 안정화 미달성")
    
    return df

def analyze_compaction_patterns(compaction_data):
    """Compaction 패턴 분석"""
    print("\n=== 📊 Compaction 패턴 분석 ===")
    
    if not compaction_data:
        print("❌ Compaction 데이터가 없습니다!")
        return None
    
    # 데이터프레임 생성
    df = pd.DataFrame([d for d in compaction_data if d is not None])
    
    if df.empty:
        print("❌ 유효한 Compaction 데이터가 없습니다!")
        return None
    
    # 시간 변환 (마이크로초 포함)
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    
    # 레벨별 Compaction 통계
    level_stats = df.groupby('level').size()
    print(f"📈 레벨별 Compaction 횟수:")
    for level, count in level_stats.items():
        print(f"  Level {level}: {count}회")
    
    # 시간별 Compaction 빈도
    df['hour'] = df['datetime'].dt.floor('H')
    hourly_compactions = df.groupby('hour').size()
    
    print(f"📈 시간별 Compaction 빈도:")
    for hour, count in hourly_compactions.items():
        print(f"  {hour.strftime('%H:%M')}: {count}회")
    
    return df

def create_visualizations(stats_df, compaction_df):
    """시각화 생성"""
    print("\n=== 📊 시각화 생성 ===")
    
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Put Rate 시간별 변화
        if stats_df is not None and not stats_df.empty:
            ax1.plot(stats_df['datetime'], stats_df['write_rate'], 'b-', linewidth=2)
            ax1.set_title('Put Rate Over Time', fontsize=14, fontweight='bold')
            ax1.set_xlabel('Time')
            ax1.set_ylabel('Put Rate (ops/sec)')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # 이동평균 추가
            stats_df['ma_10'] = stats_df['write_rate'].rolling(window=10).mean()
            ax1.plot(stats_df['datetime'], stats_df['ma_10'], 'r--', alpha=0.7, label='10-point MA')
            ax1.legend()
        
        # 2. Cumulative Writes
        if stats_df is not None and not stats_df.empty:
            ax2.plot(stats_df['datetime'], stats_df['cumulative_writes'], 'g-', linewidth=2)
            ax2.set_title('Cumulative Writes Over Time', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Cumulative Writes')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Compaction 빈도
        if compaction_df is not None and not compaction_df.empty:
            compaction_df['hour'] = compaction_df['datetime'].dt.floor('H')
            hourly_compactions = compaction_df.groupby('hour').size()
            
            ax3.bar(range(len(hourly_compactions)), hourly_compactions.values, color='orange', alpha=0.7)
            ax3.set_title('Compaction Frequency by Hour', fontsize=14, fontweight='bold')
            ax3.set_xlabel('Hour')
            ax3.set_ylabel('Compaction Count')
            ax3.set_xticks(range(len(hourly_compactions)))
            ax3.set_xticklabels([h.strftime('%H:%M') for h in hourly_compactions.index], rotation=45)
            ax3.grid(True, alpha=0.3)
        
        # 4. 레벨별 Compaction 분포
        if compaction_df is not None and not compaction_df.empty:
            level_counts = compaction_df['level'].value_counts().sort_index()
            colors = plt.cm.Set3(np.linspace(0, 1, len(level_counts)))
            
            wedges, texts, autotexts = ax4.pie(level_counts.values, labels=[f'Level {l}' for l in level_counts.index], 
                                               autopct='%1.1f%%', colors=colors)
            ax4.set_title('Compaction Distribution by Level', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('phase_b_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ 시각화 저장 완료: phase_b_analysis.png")
        
    except Exception as e:
        print(f"❌ 시각화 생성 실패: {e}")

def generate_summary_report(stats_df, compaction_df):
    """종합 요약 보고서 생성"""
    print("\n=== 📋 종합 요약 보고서 생성 ===")
    
    summary = {
        "experiment_type": "Phase-B FillRandom Analysis",
        "analysis_date": datetime.now().isoformat(),
        "performance_summary": {},
        "compaction_summary": {},
        "stability_analysis": {}
    }
    
    if stats_df is not None and not stats_df.empty:
        summary["performance_summary"] = {
            "initial_put_rate": float(stats_df['write_rate'].iloc[0]),
            "final_put_rate": float(stats_df['write_rate'].iloc[-1]),
            "max_put_rate": float(stats_df['write_rate'].max()),
            "min_put_rate": float(stats_df['write_rate'].min()),
            "performance_degradation_percent": float(((stats_df['write_rate'].iloc[0] - stats_df['write_rate'].iloc[-1]) / stats_df['write_rate'].iloc[0] * 100)),
            "total_writes": int(stats_df['cumulative_writes'].iloc[-1]),
            "experiment_duration_minutes": float((stats_df['datetime'].iloc[-1] - stats_df['datetime'].iloc[0]).total_seconds() / 60)
        }
        
        # 안정화 분석
        last_10_percent = stats_df.tail(int(len(stats_df) * 0.1))
        if len(last_10_percent) > 1:
            stability_std = last_10_percent['write_rate'].std()
            stability_mean = last_10_percent['write_rate'].mean()
            stability_cv = stability_std / stability_mean * 100 if stability_mean > 0 else 0
            
            summary["stability_analysis"] = {
                "stability_coefficient_of_variation": float(stability_cv),
                "is_stable": stability_cv < 10,
                "final_stability_mean": float(stability_mean),
                "final_stability_std": float(stability_std)
            }
    
    if compaction_df is not None and not compaction_df.empty:
        level_counts = compaction_df['level'].value_counts().to_dict()
        summary["compaction_summary"] = {
            "total_compactions": len(compaction_df),
            "compactions_by_level": {f"level_{k}": v for k, v in level_counts.items()},
            "most_active_level": int(compaction_df['level'].mode().iloc[0]) if len(compaction_df['level'].mode()) > 0 else -1
        }
    
    # 요약 저장
    # JSON 저장 (numpy 타입 변환)
    def convert_numpy_types(obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    
    # 재귀적으로 numpy 타입 변환
    def clean_dict(d):
        if isinstance(d, dict):
            return {k: clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [clean_dict(item) for item in d]
        else:
            return convert_numpy_types(d)
    
    summary_clean = clean_dict(summary)
    
    with open('phase_b_summary.json', 'w') as f:
        json.dump(summary_clean, f, indent=2)
    
    print("✅ 종합 요약 보고서 저장: phase_b_summary.json")
    
    # 콘솔에 요약 출력
    if stats_df is not None and not stats_df.empty:
        print("\n🎯 **Phase-B FillRandom 분석 요약**")
        print(f"📅 분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n📊 성능 요약:")
        print(f"  초기 Put Rate: {stats_df['write_rate'].iloc[0]:.0f} ops/sec")
        print(f"  최종 Put Rate: {stats_df['write_rate'].iloc[-1]:.0f} ops/sec")
        print(f"  성능 저하율: {((stats_df['write_rate'].iloc[0] - stats_df['write_rate'].iloc[-1]) / stats_df['write_rate'].iloc[0] * 100):.1f}%")
        print(f"  총 Write 수: {stats_df['cumulative_writes'].iloc[-1]:,}")
        print(f"  실험 지속시간: {(stats_df['datetime'].iloc[-1] - stats_df['datetime'].iloc[0]).total_seconds() / 60:.1f}분")
        
        if 'stability_analysis' in summary and summary['stability_analysis']:
            stability = summary['stability_analysis']
            print(f"\n🔍 안정화 분석:")
            print(f"  변동계수: {stability['stability_coefficient_of_variation']:.1f}%")
            print(f"  안정화 달성: {'✅ 예' if stability['is_stable'] else '❌ 아니오'}")

def main():
    """메인 함수"""
    print("🚀 Phase-B FillRandom 분석 시작...")
    
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
    
    # 성능 트렌드 분석
    stats_df = analyze_performance_trends(stats_data)
    
    # Compaction 패턴 분석
    compaction_df = analyze_compaction_patterns(compaction_data)
    
    # 시각화 생성
    create_visualizations(stats_df, compaction_df)
    
    # 종합 요약 보고서 생성
    generate_summary_report(stats_df, compaction_df)
    
    print("\n✅ Phase-B FillRandom 분석 완료!")

if __name__ == "__main__":
    main()
