#!/usr/bin/env python3
"""
RocksDB LOG 파일 분석 스크립트
시간대별 컴팩션 동작과 레벨별 FillRandom 성능 변화 분석
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

class RocksDBLogAnalyzer:
    def __init__(self, logs_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12/logs"):
        self.logs_dir = Path(logs_dir)
        self.results_dir = Path("/home/sslab/rocksdb-put-model/experiments/2025-09-12/results")
        self.data_dir = Path("/home/sslab/rocksdb-put-model/experiments/2025-09-12/data")
        
        # 결과 저장을 위한 디렉토리 생성
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 분석 결과 저장
        self.analysis_results = {
            "compaction_stats": {},
            "performance_stats": {},
            "level_stats": {},
            "stabilization_analysis": {}
        }
    
    def parse_log_file(self, log_file):
        """LOG 파일 파싱"""
        print(f"LOG 파일 파싱 중: {log_file}")
        
        # 로그 데이터 저장용 리스트
        compaction_logs = []
        performance_logs = []
        level_logs = []
        
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # 컴팩션 로그 파싱
                if "Compaction" in line:
                    compaction_data = self.parse_compaction_line(line)
                    if compaction_data:
                        compaction_logs.append(compaction_data)
                
                # 성능 로그 파싱
                if "fillrandom" in line.lower() or "ops/sec" in line:
                    perf_data = self.parse_performance_line(line)
                    if perf_data:
                        performance_logs.append(perf_data)
                
                # 레벨 통계 파싱
                if "Level" in line and ("files" in line or "size" in line):
                    level_data = self.parse_level_line(line)
                    if level_data:
                        level_logs.append(level_data)
        
        return {
            "compaction": compaction_logs,
            "performance": performance_logs,
            "levels": level_logs
        }
    
    def parse_compaction_line(self, line):
        """컴팩션 로그 라인 파싱"""
        try:
            # 시간 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})', line)
            if not time_match:
                return None
            
            timestamp = datetime.strptime(time_match.group(1), '%Y/%m/%d-%H:%M:%S')
            
            # 레벨 정보 추출
            level_match = re.search(r'Level-(\d+)', line)
            level = int(level_match.group(1)) if level_match else None
            
            # 파일 수 추출
            files_match = re.search(r'(\d+) files', line)
            files = int(files_match.group(1)) if files_match else 0
            
            # 크기 추출
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|GB|KB)', line)
            size = 0
            if size_match:
                size_val = float(size_match.group(1))
                unit = size_match.group(2)
                if unit == "GB":
                    size = size_val * 1024
                elif unit == "MB":
                    size = size_val
                elif unit == "KB":
                    size = size_val / 1024
            
            # 컴팩션 타입 추출
            comp_type = "unknown"
            if "flush" in line.lower():
                comp_type = "flush"
            elif "compaction" in line.lower():
                comp_type = "compaction"
            
            return {
                "timestamp": timestamp,
                "level": level,
                "files": files,
                "size_mb": size,
                "type": comp_type,
                "raw_line": line
            }
            
        except Exception as e:
            print(f"컴팩션 로그 파싱 오류: {e}")
            return None
    
    def parse_performance_line(self, line):
        """성능 로그 라인 파싱"""
        try:
            # 시간 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})', line)
            if not time_match:
                return None
            
            timestamp = datetime.strptime(time_match.group(1), '%Y/%m/%d-%H:%M:%S')
            
            # ops/sec 추출
            ops_match = re.search(r'(\d+(?:\.\d+)?)\s*ops/sec', line)
            ops_per_sec = float(ops_match.group(1)) if ops_match else 0
            
            # MiB/s 추출
            mbps_match = re.search(r'(\d+(?:\.\d+)?)\s*MiB/s', line)
            mbps = float(mbps_match.group(1)) if mbps_match else 0
            
            # 지연시간 추출 (평균, 95%, 99%)
            latency_avg_match = re.search(r'avg:\s*(\d+(?:\.\d+)?)', line)
            latency_avg = float(latency_avg_match.group(1)) if latency_avg_match else 0
            
            latency_95_match = re.search(r'p95:\s*(\d+(?:\.\d+)?)', line)
            latency_95 = float(latency_95_match.group(1)) if latency_95_match else 0
            
            latency_99_match = re.search(r'p99:\s*(\d+(?:\.\d+)?)', line)
            latency_99 = float(latency_99_match.group(1)) if latency_99_match else 0
            
            return {
                "timestamp": timestamp,
                "ops_per_sec": ops_per_sec,
                "mbps": mbps,
                "latency_avg": latency_avg,
                "latency_95": latency_95,
                "latency_99": latency_99,
                "raw_line": line
            }
            
        except Exception as e:
            print(f"성능 로그 파싱 오류: {e}")
            return None
    
    def parse_level_line(self, line):
        """레벨 통계 로그 라인 파싱"""
        try:
            # 시간 추출
            time_match = re.search(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})', line)
            if not time_match:
                return None
            
            timestamp = datetime.strptime(time_match.group(1), '%Y/%m/%d-%H:%M:%S')
            
            # 레벨 추출
            level_match = re.search(r'Level-(\d+)', line)
            level = int(level_match.group(1)) if level_match else None
            
            # 파일 수 추출
            files_match = re.search(r'(\d+)\s*files', line)
            files = int(files_match.group(1)) if files_match else 0
            
            # 크기 추출
            size_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|GB|KB)', line)
            size = 0
            if size_match:
                size_val = float(size_match.group(1))
                unit = size_match.group(2)
                if unit == "GB":
                    size = size_val * 1024
                elif unit == "MB":
                    size = size_val
                elif unit == "KB":
                    size = size_val / 1024
            
            return {
                "timestamp": timestamp,
                "level": level,
                "files": files,
                "size_mb": size,
                "raw_line": line
            }
            
        except Exception as e:
            print(f"레벨 로그 파싱 오류: {e}")
            return None
    
    def analyze_compaction_patterns(self, compaction_data):
        """컴팩션 패턴 분석"""
        print("컴팩션 패턴 분석 중...")
        
        if not compaction_data:
            return {}
        
        df = pd.DataFrame(compaction_data)
        
        # 레벨별 컴팩션 통계
        level_stats = {}
        for level in df['level'].dropna().unique():
            level_df = df[df['level'] == level]
            level_stats[f"level_{level}"] = {
                "total_compactions": len(level_df),
                "avg_files_per_compaction": level_df['files'].mean(),
                "avg_size_per_compaction": level_df['size_mb'].mean(),
                "compaction_frequency": len(level_df) / ((df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600) if len(df) > 0 else 0
            }
        
        # 시간대별 컴팩션 패턴
        df['hour'] = df['timestamp'].dt.hour
        hourly_patterns = df.groupby('hour').size().to_dict()
        
        # 컴팩션 타입별 통계
        type_stats = df.groupby('type').size().to_dict()
        
        return {
            "level_stats": level_stats,
            "hourly_patterns": hourly_patterns,
            "type_stats": type_stats,
            "total_compactions": len(df),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def analyze_performance_trends(self, performance_data):
        """성능 트렌드 분석"""
        print("성능 트렌드 분석 중...")
        
        if not performance_data:
            return {}
        
        df = pd.DataFrame(performance_data)
        
        # 시간별 성능 통계
        df['hour'] = df['timestamp'].dt.hour
        hourly_performance = df.groupby('hour').agg({
            'ops_per_sec': ['mean', 'std', 'min', 'max'],
            'mbps': ['mean', 'std', 'min', 'max'],
            'latency_avg': ['mean', 'std', 'min', 'max'],
            'latency_95': ['mean', 'std', 'min', 'max'],
            'latency_99': ['mean', 'std', 'min', 'max']
        }).to_dict()
        
        # 전체 성능 통계
        overall_stats = {
            "avg_ops_per_sec": df['ops_per_sec'].mean(),
            "std_ops_per_sec": df['ops_per_sec'].std(),
            "max_ops_per_sec": df['ops_per_sec'].max(),
            "min_ops_per_sec": df['ops_per_sec'].min(),
            "avg_mbps": df['mbps'].mean(),
            "std_mbps": df['mbps'].std(),
            "avg_latency_avg": df['latency_avg'].mean(),
            "avg_latency_95": df['latency_95'].mean(),
            "avg_latency_99": df['latency_99'].mean()
        }
        
        # 성능 안정성 분석
        stability_analysis = self.analyze_performance_stability(df)
        
        return {
            "hourly_performance": hourly_performance,
            "overall_stats": overall_stats,
            "stability_analysis": stability_analysis,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def analyze_performance_stability(self, df):
        """성능 안정성 분석"""
        # 시간 윈도우별 성능 변화 분석
        window_size = 3600  # 1시간 윈도우
        windows = []
        
        start_time = df['timestamp'].min()
        end_time = df['timestamp'].max()
        
        current_time = start_time
        while current_time < end_time:
            window_end = current_time + timedelta(seconds=window_size)
            window_df = df[(df['timestamp'] >= current_time) & (df['timestamp'] < window_end)]
            
            if len(window_df) > 0:
                windows.append({
                    "start_time": current_time,
                    "end_time": window_end,
                    "avg_ops_per_sec": window_df['ops_per_sec'].mean(),
                    "std_ops_per_sec": window_df['ops_per_sec'].std(),
                    "avg_mbps": window_df['mbps'].mean(),
                    "avg_latency_avg": window_df['latency_avg'].mean()
                })
            
            current_time = window_end
        
        # 안정화 지표 계산
        if len(windows) > 1:
            ops_values = [w['avg_ops_per_sec'] for w in windows]
            cv = np.std(ops_values) / np.mean(ops_values) if np.mean(ops_values) > 0 else float('inf')
            
            # 안정화 판단 (CV < 0.1이면 안정화된 것으로 판단)
            is_stable = cv < 0.1
            stabilization_time = None
            
            if is_stable:
                # 안정화 시점 찾기
                for i, window in enumerate(windows):
                    if i > 0:
                        recent_cv = np.std([w['avg_ops_per_sec'] for w in windows[i:]]) / np.mean([w['avg_ops_per_sec'] for w in windows[i:]])
                        if recent_cv < 0.1:
                            stabilization_time = window['start_time']
                            break
            
            return {
                "coefficient_of_variation": cv,
                "is_stable": is_stable,
                "stabilization_time": stabilization_time.isoformat() if stabilization_time else None,
                "stable_performance": ops_values[-1] if ops_values else 0,
                "windows": windows
            }
        
        return {"error": "Insufficient data for stability analysis"}
    
    def analyze_level_distribution(self, level_data):
        """레벨별 데이터 분포 분석"""
        print("레벨별 데이터 분포 분석 중...")
        
        if not level_data:
            return {}
        
        df = pd.DataFrame(level_data)
        
        # 최신 레벨 분포
        latest_timestamp = df['timestamp'].max()
        latest_data = df[df['timestamp'] == latest_timestamp]
        
        level_distribution = {}
        for _, row in latest_data.iterrows():
            if pd.notna(row['level']):
                level_distribution[f"level_{int(row['level'])}"] = {
                    "files": int(row['files']),
                    "size_mb": float(row['size_mb'])
                }
        
        # 시간별 레벨 변화
        hourly_levels = df.groupby(['timestamp', 'level']).agg({
            'files': 'sum',
            'size_mb': 'sum'
        }).reset_index()
        
        return {
            "latest_distribution": level_distribution,
            "hourly_changes": hourly_levels.to_dict('records'),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def create_visualizations(self, analysis_data):
        """시각화 생성"""
        print("시각화 생성 중...")
        
        # 컴팩션 패턴 시각화
        if 'compaction' in analysis_data and analysis_data['compaction']:
            self.plot_compaction_patterns(analysis_data['compaction'])
        
        # 성능 트렌드 시각화
        if 'performance' in analysis_data and analysis_data['performance']:
            self.plot_performance_trends(analysis_data['performance'])
        
        # 레벨 분포 시각화
        if 'levels' in analysis_data and analysis_data['levels']:
            self.plot_level_distribution(analysis_data['levels'])
    
    def plot_compaction_patterns(self, compaction_data):
        """컴팩션 패턴 시각화"""
        df = pd.DataFrame(compaction_data)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 레벨별 컴팩션 수
        level_counts = df['level'].value_counts().sort_index()
        axes[0, 0].bar(level_counts.index, level_counts.values)
        axes[0, 0].set_title('컴팩션 수 (레벨별)')
        axes[0, 0].set_xlabel('레벨')
        axes[0, 0].set_ylabel('컴팩션 수')
        
        # 시간별 컴팩션 패턴
        df['hour'] = df['timestamp'].dt.hour
        hourly_counts = df.groupby('hour').size()
        axes[0, 1].plot(hourly_counts.index, hourly_counts.values, marker='o')
        axes[0, 1].set_title('시간별 컴팩션 패턴')
        axes[0, 1].set_xlabel('시간 (시)')
        axes[0, 1].set_ylabel('컴팩션 수')
        
        # 레벨별 평균 파일 수
        level_files = df.groupby('level')['files'].mean()
        axes[1, 0].bar(level_files.index, level_files.values)
        axes[1, 0].set_title('레벨별 평균 파일 수')
        axes[1, 0].set_xlabel('레벨')
        axes[1, 0].set_ylabel('평균 파일 수')
        
        # 레벨별 평균 크기
        level_sizes = df.groupby('level')['size_mb'].mean()
        axes[1, 1].bar(level_sizes.index, level_sizes.values)
        axes[1, 1].set_title('레벨별 평균 크기 (MB)')
        axes[1, 1].set_xlabel('레벨')
        axes[1, 1].set_ylabel('평균 크기 (MB)')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'compaction_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_performance_trends(self, performance_data):
        """성능 트렌드 시각화"""
        df = pd.DataFrame(performance_data)
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 시간별 ops/sec
        axes[0, 0].plot(df['timestamp'], df['ops_per_sec'], alpha=0.7)
        axes[0, 0].set_title('시간별 처리량 (ops/sec)')
        axes[0, 0].set_xlabel('시간')
        axes[0, 0].set_ylabel('ops/sec')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 시간별 MiB/s
        axes[0, 1].plot(df['timestamp'], df['mbps'], alpha=0.7)
        axes[0, 1].set_title('시간별 처리량 (MiB/s)')
        axes[0, 1].set_xlabel('시간')
        axes[0, 1].set_ylabel('MiB/s')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 시간별 평균 지연시간
        axes[1, 0].plot(df['timestamp'], df['latency_avg'], alpha=0.7)
        axes[1, 0].set_title('시간별 평균 지연시간')
        axes[1, 0].set_xlabel('시간')
        axes[1, 0].set_ylabel('지연시간 (ms)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 95% 지연시간
        axes[1, 1].plot(df['timestamp'], df['latency_95'], alpha=0.7)
        axes[1, 1].set_title('시간별 95% 지연시간')
        axes[1, 1].set_xlabel('시간')
        axes[1, 1].set_ylabel('지연시간 (ms)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'performance_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_level_distribution(self, level_data):
        """레벨 분포 시각화"""
        df = pd.DataFrame(level_data)
        
        # 최신 레벨 분포
        latest_timestamp = df['timestamp'].max()
        latest_data = df[df['timestamp'] == latest_timestamp]
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # 레벨별 파일 수
        level_files = latest_data.groupby('level')['files'].sum()
        axes[0].bar(level_files.index, level_files.values)
        axes[0].set_title('레벨별 파일 수')
        axes[0].set_xlabel('레벨')
        axes[0].set_ylabel('파일 수')
        
        # 레벨별 크기
        level_sizes = latest_data.groupby('level')['size_mb'].sum()
        axes[1].bar(level_sizes.index, level_sizes.values)
        axes[1].set_title('레벨별 크기 (MB)')
        axes[1].set_xlabel('레벨')
        axes[1].set_ylabel('크기 (MB)')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'level_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def analyze_all_logs(self):
        """모든 로그 파일 분석"""
        print("=== 로그 파일 분석 시작 ===")
        
        # 로그 파일 찾기
        log_files = list(self.logs_dir.glob("LOG*"))
        
        if not log_files:
            print("로그 파일을 찾을 수 없습니다.")
            return
        
        # 모든 로그 파일 분석
        all_data = {
            "compaction": [],
            "performance": [],
            "levels": []
        }
        
        for log_file in log_files:
            print(f"분석 중: {log_file}")
            data = self.parse_log_file(log_file)
            
            if data:
                all_data["compaction"].extend(data["compaction"])
                all_data["performance"].extend(data["performance"])
                all_data["levels"].extend(data["levels"])
        
        # 분석 수행
        self.analysis_results["compaction_stats"] = self.analyze_compaction_patterns(all_data["compaction"])
        self.analysis_results["performance_stats"] = self.analyze_performance_trends(all_data["performance"])
        self.analysis_results["level_stats"] = self.analyze_level_distribution(all_data["levels"])
        
        # 시각화 생성
        self.create_visualizations(all_data)
        
        # 결과 저장
        with open(self.results_dir / "log_analysis_results.json", 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
        
        print("=== 로그 분석 완료 ===")
        print(f"분석 결과 저장: {self.results_dir / 'log_analysis_results.json'}")

def main():
    """메인 함수"""
    analyzer = RocksDBLogAnalyzer()
    analyzer.analyze_all_logs()

if __name__ == "__main__":
    main()
