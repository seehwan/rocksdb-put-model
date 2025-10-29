#!/usr/bin/env python3
"""
RocksDB LOG 파일에서 CV 값 계산
"""

import re
import pandas as pd
from pathlib import Path
from datetime import datetime

def parse_log_file(log_file_path):
    """LOG 파일 파싱하여 시간별 write rate 추출"""
    print(f"📖 LOG 파일 파싱 중: {log_file_path}")
    
    data = []
    current_timestamp = None
    
    with open(log_file_path, 'r') as f:
        for line in f:
            # 시간 정보 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if time_match:
                current_timestamp = time_match.group(1)
            
            # Cumulative writes 라인 찾기
            if "Cumulative writes:" in line and "MB/s" in line:
                try:
                    # MB/s 추출
                    mbps_match = re.search(r'(\d+\.\d+) MB/s', line)
                    if mbps_match and current_timestamp:
                        mbps = float(mbps_match.group(1))
                        data.append({
                            'timestamp': current_timestamp,
                            'write_rate_mbs': mbps
                        })
                except Exception as e:
                    continue
    
    print(f"✅ 파싱 완료: {len(data):,}개 샘플")
    return data

def calculate_phase_cvs(df):
    """Phase별 CV 계산"""
    
    # 시간 변환
    df['datetime'] = pd.to_datetime(df['timestamp'], format='%Y/%m/%d-%H:%M:%S.%f')
    
    # 시작 시간 기준으로 시간 계산
    start_time = df['datetime'].min()
    df['hours'] = (df['datetime'] - start_time).dt.total_seconds() / 3600
    
    # Phase 구분 (시간 기반 3-way split)
    def get_phase(hours, total_hours):
        if hours < total_hours / 3:
            return 'initial'
        elif hours < total_hours * 2 / 3:
            return 'middle'
        else:
            return 'final'
    
    total_hours = df['hours'].max()
    df['phase'] = df['hours'].apply(lambda h: get_phase(h, total_hours))
    
    # Phase별 CV 계산
    phase_cvs = {}
    phase_stats = {}
    
    for phase_name in ['initial', 'middle', 'final']:
        phase_df = df[df['phase'] == phase_name]
        if len(phase_df) > 0:
            mean = phase_df['write_rate_mbs'].mean()
            std = phase_df['write_rate_mbs'].std()
            cv = std / mean
            phase_cvs[phase_name] = cv
            phase_stats[phase_name] = {
                'mean': mean,
                'std': std,
                'cv': cv,
                'samples': len(phase_df),
                'duration_hours': phase_df['hours'].max() - phase_df['hours'].min()
            }
    
    return df, phase_cvs, phase_stats

def main():
    """메인 함수"""
    print("=" * 80)
    print("📊 CV 계산 from RocksDB LOG")
    print("=" * 80)
    
    # LOG 파일 경로
    log_file = Path("experiments/2025-09-12/rocksdb_log_phase_b.log")
    
    if not log_file.exists():
        print(f"❌ LOG 파일 없음: {log_file}")
        return
    
    # 파일 크기 확인
    file_size_mb = log_file.stat().st_size / (1024 * 1024)
    print(f"📄 파일 크기: {file_size_mb:.1f} MB")
    
    # LOG 파일 파싱
    data = parse_log_file(log_file)
    
    if len(data) == 0:
        print("❌ 데이터 없음")
        return
    
    # 데이터프레임 생성
    df = pd.DataFrame(data)
    
    # Phase별 CV 계산
    print("\n📊 Phase별 CV 계산 중...")
    df, phase_cvs, phase_stats = calculate_phase_cvs(df)
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("Phase별 CV 결과")
    print("=" * 80)
    
    for phase_name in ['initial', 'middle', 'final']:
        if phase_name in phase_stats:
            stats = phase_stats[phase_name]
            print(f"\n{phase_name.upper()} Phase:")
            print(f"  CV: {stats['cv']:.6f}")
            print(f"  Mean: {stats['mean']:.2f} MB/s")
            print(f"  Std: {stats['std']:.2f} MB/s")
            print(f"  Samples: {stats['samples']:,}")
            print(f"  Duration: {stats['duration_hours']:.1f} hours")
    
    print("\n✅ 완료!")

if __name__ == "__main__":
    main()

