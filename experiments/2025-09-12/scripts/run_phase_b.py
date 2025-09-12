#!/usr/bin/env python3
"""
Phase-B: FillRandom 성능 분석 및 컴팩션 모니터링
LOG 파일을 저장하고, 시간에 따라 FillRandom 성능과 레벨별 컴팩션량을 분석할 수 있도록 충분한 로그를 사용하고, 시각화를 포함
"""

import os
import sys
import json
import time
import subprocess
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class PhaseBRunner:
    def __init__(self, base_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12"):
        self.base_dir = Path(base_dir)
        self.phase_dir = self.base_dir / "phase-b"
        self.data_dir = self.phase_dir / "data"
        self.results_dir = self.phase_dir / "results"
        self.logs_dir = self.base_dir / "logs"
        
        # 디렉토리 생성
        for dir_path in [self.data_dir, self.results_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # 실험 설정
        self.experiment_config = {
            "db_path": "/rocksdb/data",
            "num_keys": 1000000000,  # 10억 키
            "value_size": 1024,      # 1KB
            "key_size": 16,          # 16 bytes
            "threads": 16,           # 16 threads
            "distributions": ["uniform", "zipfian"],
            "zipfian_alpha": 0.99,
            "log_interval": 60,      # 1분 간격 로깅
            "stats_interval": 1000000,  # 100만 작업마다 통계
            "experiment_duration": 48 * 3600  # 48시간
        }
        
        # 실험 결과 저장
        self.experiment_results = {
            "start_time": None,
            "end_time": None,
            "uniform_results": {},
            "zipfian_results": {},
            "compaction_stats": {},
            "performance_trends": {}
        }
    
    def setup_logging(self):
        """로깅 설정"""
        log_file = self.phase_dir / f"phase_b_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Phase-B 로그 파일: {log_file}")
    
    def run_command(self, command, timeout=None):
        """명령어 실행"""
        try:
            self.logger.info(f"명령어 실행: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            if result.returncode == 0:
                self.logger.info("명령어 실행 성공")
                return result.stdout
            else:
                self.logger.error(f"명령어 실행 실패: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"명령어 실행 시간 초과: {command}")
            return None
        except Exception as e:
            self.logger.error(f"명령어 실행 중 오류: {e}")
            return None
    
    def setup_rocksdb_logging(self):
        """RocksDB 로깅 설정"""
        self.logger.info("=== RocksDB 로깅 설정 ===")
        
        # 로그 디렉토리 정리
        log_path = Path(self.experiment_config["db_path"])
        if log_path.exists():
            # 기존 LOG 파일 백업
            for log_file in log_path.glob("LOG*"):
                backup_name = f"{log_file.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(log_file, self.logs_dir / backup_name)
                self.logger.info(f"기존 로그 백업: {backup_name}")
        
        self.logger.info("RocksDB 로깅 설정 완료")
    
    def run_fillrandom_experiment(self, distribution="uniform"):
        """FillRandom 실험 실행"""
        self.logger.info(f"=== FillRandom 실험 시작 (분포: {distribution}) ===")
        
        # 실험 시작 시간 기록
        start_time = datetime.now()
        self.experiment_results["start_time"] = start_time.isoformat()
        
        # db_bench 명령어 구성
        cmd_parts = [
            "./db_bench",
            "--benchmarks=fillrandom",
            f"--db={self.experiment_config['db_path']}",
            f"--num={self.experiment_config['num_keys']}",
            f"--value_size={self.experiment_config['value_size']}",
            f"--key_size={self.experiment_config['key_size']}",
            f"--threads={self.experiment_config['threads']}",
            f"--distribution={distribution}",
            "--stats_interval=1000000",
            "--stats_interval_seconds=60",
            "--report_interval_seconds=60",
            "--histogram=true",
            "--compaction_measurement=1",
            "--compaction_style=0",  # Level compaction
            "--level0_file_num_compaction_trigger=4",
            "--max_bytes_for_level_base=268435456",  # 256MB
            "--max_bytes_for_level_multiplier=10",
            "--max_background_compactions=4",
            "--max_background_flushes=2",
            "--log_file_time_to_roll=3600",  # 1시간마다 로그 롤링
            "--max_log_file_size=10485760",  # 10MB
            "--log_level=INFO"
        ]
        
        if distribution == "zipfian":
            cmd_parts.append(f"--zipfian_alpha={self.experiment_config['zipfian_alpha']}")
        
        command = " ".join(cmd_parts)
        
        # 실험 실행
        self.logger.info(f"FillRandom 실험 명령어: {command}")
        
        # 실험 결과를 파일로 저장
        output_file = self.data_dir / f"fillrandom_{distribution}_output.log"
        
        try:
            with open(output_file, 'w') as f:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 실시간 출력 및 저장
                for line in process.stdout:
                    print(line.strip())  # 실시간 출력
                    f.write(line)  # 파일 저장
                    f.flush()
                
                process.wait()
                
                if process.returncode == 0:
                    self.logger.info(f"FillRandom 실험 완료 (분포: {distribution})")
                    result = True
                else:
                    self.logger.error(f"FillRandom 실험 실패 (분포: {distribution})")
                    result = False
                    
        except Exception as e:
            self.logger.error(f"FillRandom 실험 실행 중 오류: {e}")
            result = False
        
        # 실험 종료 시간 기록
        end_time = datetime.now()
        self.experiment_results["end_time"] = end_time.isoformat()
        
        return result
    
    def copy_log_files(self):
        """LOG 파일을 실험 디렉토리로 복사"""
        self.logger.info("=== LOG 파일 복사 시작 ===")
        
        db_path = Path(self.experiment_config["db_path"])
        
        # 메인 LOG 파일 복사
        main_log = db_path / "LOG"
        if main_log.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_file = self.logs_dir / f"LOG_{timestamp}"
            shutil.copy2(main_log, dest_file)
            self.logger.info(f"메인 LOG 파일 복사: {dest_file}")
        
        # 롤링된 LOG 파일들 복사
        log_files = list(db_path.glob("LOG.old.*"))
        for log_file in log_files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_file = self.logs_dir / f"{log_file.name}_{timestamp}"
            shutil.copy2(log_file, dest_file)
            self.logger.info(f"롤링 LOG 파일 복사: {dest_file}")
        
        self.logger.info("=== LOG 파일 복사 완료 ===")
    
    def analyze_performance_trends(self):
        """성능 트렌드 분석"""
        self.logger.info("=== 성능 트렌드 분석 시작 ===")
        
        # db_bench 출력 파일 분석
        uniform_file = self.data_dir / "fillrandom_uniform_output.log"
        zipfian_file = self.data_dir / "fillrandom_zipfian_output.log"
        
        uniform_data = self.parse_db_bench_output(uniform_file, "uniform")
        zipfian_data = self.parse_db_bench_output(zipfian_file, "zipfian")
        
        self.experiment_results["uniform_results"] = uniform_data
        self.experiment_results["zipfian_results"] = zipfian_data
        
        # 성능 트렌드 분석
        self.analyze_performance_stability(uniform_data, "uniform")
        self.analyze_performance_stability(zipfian_data, "zipfian")
        
        self.logger.info("=== 성능 트렌드 분석 완료 ===")
    
    def parse_db_bench_output(self, output_file, distribution):
        """db_bench 출력 파일 파싱"""
        if not output_file.exists():
            self.logger.warning(f"출력 파일이 없습니다: {output_file}")
            return {}
        
        performance_data = []
        
        with open(output_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # 성능 통계 라인 파싱
                if "fillrandom" in line and "ops/sec" in line:
                    try:
                        # 시간 추출
                        if "[" in line and "]" in line:
                            time_part = line[line.find("[")+1:line.find("]")]
                            timestamp = datetime.strptime(time_part, "%Y/%m/%d-%H:%M:%S")
                        else:
                            timestamp = datetime.now()
                        
                        # ops/sec 추출
                        ops_match = line.split("ops/sec")[0].split()[-1]
                        ops_per_sec = float(ops_match)
                        
                        # MiB/s 추출
                        mbps_match = None
                        if "MiB/s" in line:
                            mbps_part = line.split("MiB/s")[0]
                            mbps_match = mbps_part.split()[-1]
                            mbps = float(mbps_match)
                        else:
                            mbps = 0
                        
                        # 지연시간 추출
                        latency_avg = 0
                        latency_95 = 0
                        latency_99 = 0
                        
                        if "avg:" in line:
                            avg_match = line.split("avg:")[1].split()[0]
                            latency_avg = float(avg_match)
                        
                        if "p95:" in line:
                            p95_match = line.split("p95:")[1].split()[0]
                            latency_95 = float(p95_match)
                        
                        if "p99:" in line:
                            p99_match = line.split("p99:")[1].split()[0]
                            latency_99 = float(p99_match)
                        
                        performance_data.append({
                            "timestamp": timestamp,
                            "distribution": distribution,
                            "ops_per_sec": ops_per_sec,
                            "mbps": mbps,
                            "latency_avg": latency_avg,
                            "latency_95": latency_95,
                            "latency_99": latency_99
                        })
                        
                    except Exception as e:
                        self.logger.warning(f"성능 데이터 파싱 실패: {line} - {e}")
                        continue
        
        return {
            "raw_data": performance_data,
            "total_measurements": len(performance_data),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def analyze_performance_stability(self, data, distribution):
        """성능 안정성 분석"""
        if not data or "raw_data" not in data:
            return
        
        raw_data = data["raw_data"]
        if len(raw_data) < 2:
            return
        
        df = pd.DataFrame(raw_data)
        
        # 시간 윈도우별 성능 분석
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
                    "avg_latency_avg": window_df['latency_avg'].mean(),
                    "sample_count": len(window_df)
                })
            
            current_time = window_end
        
        # 안정화 분석
        if len(windows) > 1:
            ops_values = [w['avg_ops_per_sec'] for w in windows]
            cv = np.std(ops_values) / np.mean(ops_values) if np.mean(ops_values) > 0 else float('inf')
            
            # 안정화 판단
            is_stable = cv < 0.1
            stabilization_time = None
            
            if is_stable:
                # 안정화 시점 찾기
                for i, window in enumerate(windows):
                    if i > 0:
                        recent_windows = windows[i:]
                        recent_ops = [w['avg_ops_per_sec'] for w in recent_windows]
                        recent_cv = np.std(recent_ops) / np.mean(recent_ops)
                        if recent_cv < 0.1:
                            stabilization_time = window['start_time']
                            break
            
            stability_analysis = {
                "coefficient_of_variation": cv,
                "is_stable": is_stable,
                "stabilization_time": stabilization_time.isoformat() if stabilization_time else None,
                "stable_performance": ops_values[-1] if ops_values else 0,
                "windows": windows
            }
            
            data["stability_analysis"] = stability_analysis
    
    def analyze_compaction_stats(self):
        """컴팩션 통계 분석"""
        self.logger.info("=== 컴팩션 통계 분석 시작 ===")
        
        # LOG 파일들 분석
        log_files = list(self.logs_dir.glob("LOG*"))
        
        compaction_data = []
        level_stats = {}
        
        for log_file in log_files:
            self.logger.info(f"LOG 파일 분석 중: {log_file}")
            
            with open(log_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # 컴팩션 로그 파싱
                    if "Compaction" in line:
                        compaction_info = self.parse_compaction_line(line)
                        if compaction_info:
                            compaction_data.append(compaction_info)
                    
                    # 레벨 통계 파싱
                    if "Level" in line and ("files" in line or "size" in line):
                        level_info = self.parse_level_line(line)
                        if level_info:
                            level_key = f"level_{level_info['level']}"
                            if level_key not in level_stats:
                                level_stats[level_key] = []
                            level_stats[level_key].append(level_info)
        
        # 컴팩션 통계 계산
        compaction_stats = self.calculate_compaction_stats(compaction_data)
        
        self.experiment_results["compaction_stats"] = {
            "raw_compaction_data": compaction_data,
            "level_stats": level_stats,
            "compaction_summary": compaction_stats,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        self.logger.info("=== 컴팩션 통계 분석 완료 ===")
    
    def parse_compaction_line(self, line):
        """컴팩션 로그 라인 파싱"""
        try:
            # 시간 추출
            if "[" in line and "]" in line:
                time_part = line[line.find("[")+1:line.find("]")]
                timestamp = datetime.strptime(time_part, "%Y/%m/%d-%H:%M:%S")
            else:
                timestamp = datetime.now()
            
            # 레벨 정보 추출
            level_match = None
            if "Level-" in line:
                level_part = line.split("Level-")[1].split()[0]
                level_match = int(level_part)
            
            # 파일 수 추출
            files_match = None
            if " files" in line:
                files_part = line.split(" files")[0].split()[-1]
                files_match = int(files_part)
            
            # 크기 추출
            size_match = None
            size_unit = None
            if " MB" in line:
                size_part = line.split(" MB")[0].split()[-1]
                size_match = float(size_part)
                size_unit = "MB"
            elif " GB" in line:
                size_part = line.split(" GB")[0].split()[-1]
                size_match = float(size_part)
                size_unit = "GB"
            
            return {
                "timestamp": timestamp,
                "level": level_match,
                "files": files_match,
                "size": size_match,
                "size_unit": size_unit,
                "raw_line": line
            }
            
        except Exception as e:
            self.logger.warning(f"컴팩션 로그 파싱 실패: {line} - {e}")
            return None
    
    def parse_level_line(self, line):
        """레벨 통계 로그 라인 파싱"""
        try:
            # 시간 추출
            if "[" in line and "]" in line:
                time_part = line[line.find("[")+1:line.find("]")]
                timestamp = datetime.strptime(time_part, "%Y/%m/%d-%H:%M:%S")
            else:
                timestamp = datetime.now()
            
            # 레벨 추출
            level_match = None
            if "Level-" in line:
                level_part = line.split("Level-")[1].split()[0]
                level_match = int(level_part)
            
            # 파일 수 추출
            files_match = None
            if " files" in line:
                files_part = line.split(" files")[0].split()[-1]
                files_match = int(files_part)
            
            # 크기 추출
            size_match = None
            if " MB" in line:
                size_part = line.split(" MB")[0].split()[-1]
                size_match = float(size_part)
            elif " GB" in line:
                size_part = line.split(" GB")[0].split()[-1]
                size_match = float(size_part) * 1024  # GB to MB
            
            return {
                "timestamp": timestamp,
                "level": level_match,
                "files": files_match,
                "size_mb": size_match,
                "raw_line": line
            }
            
        except Exception as e:
            self.logger.warning(f"레벨 로그 파싱 실패: {line} - {e}")
            return None
    
    def calculate_compaction_stats(self, compaction_data):
        """컴팩션 통계 계산"""
        if not compaction_data:
            return {}
        
        df = pd.DataFrame(compaction_data)
        
        # 레벨별 컴팩션 통계
        level_stats = {}
        for level in df['level'].dropna().unique():
            level_df = df[df['level'] == level]
            level_stats[f"level_{int(level)}"] = {
                "total_compactions": len(level_df),
                "avg_files_per_compaction": level_df['files'].mean() if 'files' in level_df.columns else 0,
                "avg_size_per_compaction": level_df['size'].mean() if 'size' in level_df.columns else 0
            }
        
        # 시간대별 컴팩션 패턴
        df['hour'] = df['timestamp'].dt.hour
        hourly_patterns = df.groupby('hour').size().to_dict()
        
        return {
            "level_stats": level_stats,
            "hourly_patterns": hourly_patterns,
            "total_compactions": len(df),
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def create_visualizations(self):
        """시각화 생성"""
        self.logger.info("=== 시각화 생성 시작 ===")
        
        # 1. 성능 트렌드 시각화
        self.plot_performance_trends()
        
        # 2. 컴팩션 패턴 시각화
        self.plot_compaction_patterns()
        
        # 3. 안정화 분석 시각화
        self.plot_stabilization_analysis()
        
        self.logger.info("=== 시각화 생성 완료 ===")
    
    def plot_performance_trends(self):
        """성능 트렌드 시각화"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Uniform 분포 성능
        uniform_data = self.experiment_results.get("uniform_results", {})
        if uniform_data and "raw_data" in uniform_data:
            uniform_df = pd.DataFrame(uniform_data["raw_data"])
            
            axes[0, 0].plot(uniform_df['timestamp'], uniform_df['ops_per_sec'], alpha=0.7)
            axes[0, 0].set_title('Uniform 분포 - 처리량 (ops/sec)')
            axes[0, 0].set_ylabel('ops/sec')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            axes[0, 1].plot(uniform_df['timestamp'], uniform_df['mbps'], alpha=0.7)
            axes[0, 1].set_title('Uniform 분포 - 대역폭 (MiB/s)')
            axes[0, 1].set_ylabel('MiB/s')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Zipfian 분포 성능
        zipfian_data = self.experiment_results.get("zipfian_results", {})
        if zipfian_data and "raw_data" in zipfian_data:
            zipfian_df = pd.DataFrame(zipfian_data["raw_data"])
            
            axes[1, 0].plot(zipfian_df['timestamp'], zipfian_df['ops_per_sec'], alpha=0.7, color='orange')
            axes[1, 0].set_title('Zipfian 분포 - 처리량 (ops/sec)')
            axes[1, 0].set_ylabel('ops/sec')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            axes[1, 1].plot(zipfian_df['timestamp'], zipfian_df['mbps'], alpha=0.7, color='orange')
            axes[1, 1].set_title('Zipfian 분포 - 대역폭 (MiB/s)')
            axes[1, 1].set_ylabel('MiB/s')
            axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'performance_trends.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_compaction_patterns(self):
        """컴팩션 패턴 시각화"""
        compaction_stats = self.experiment_results.get("compaction_stats", {})
        if not compaction_stats:
            return
        
        level_stats = compaction_stats.get("compaction_summary", {}).get("level_stats", {})
        hourly_patterns = compaction_stats.get("compaction_summary", {}).get("hourly_patterns", {})
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 레벨별 컴팩션 수
        if level_stats:
            levels = []
            compactions = []
            
            for level_key, stats in level_stats.items():
                level_num = level_key.split("_")[1]
                levels.append(f"L{level_num}")
                compactions.append(stats.get("total_compactions", 0))
            
            bars = ax1.bar(levels, compactions, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
            ax1.set_title('레벨별 컴팩션 수')
            ax1.set_xlabel('레벨')
            ax1.set_ylabel('컴팩션 수')
            ax1.grid(True, alpha=0.3)
            
            # 값 표시
            for bar, value in zip(bars, compactions):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(compactions)*0.01,
                        str(value), ha='center', va='bottom')
        
        # 시간대별 컴팩션 패턴
        if hourly_patterns:
            hours = list(range(24))
            counts = [hourly_patterns.get(h, 0) for h in hours]
            
            ax2.plot(hours, counts, marker='o', linewidth=2, markersize=6)
            ax2.set_title('시간대별 컴팩션 패턴')
            ax2.set_xlabel('시간 (시)')
            ax2.set_ylabel('컴팩션 수')
            ax2.grid(True, alpha=0.3)
            ax2.set_xticks(range(0, 24, 2))
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'compaction_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_stabilization_analysis(self):
        """안정화 분석 시각화"""
        uniform_data = self.experiment_results.get("uniform_results", {})
        zipfian_data = self.experiment_results.get("zipfian_results", {})
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Uniform 분포 안정화 분석
        if uniform_data and "stability_analysis" in uniform_data:
            stability = uniform_data["stability_analysis"]
            windows = stability.get("windows", [])
            
            if windows:
                times = [i for i in range(len(windows))]
                performances = [w["avg_ops_per_sec"] for w in windows]
                
                axes[0, 0].plot(times, performances, marker='o', linewidth=2)
                axes[0, 0].set_title(f'Uniform 분포 - 안정화 분석 (CV: {stability["coefficient_of_variation"]:.3f})')
                axes[0, 0].set_xlabel('시간 윈도우')
                axes[0, 0].set_ylabel('평균 처리량 (ops/sec)')
                axes[0, 0].grid(True, alpha=0.3)
                
                if stability.get("is_stable"):
                    axes[0, 0].axhline(y=stability["stable_performance"], color='red', linestyle='--', alpha=0.7, label='안정화 성능')
                    axes[0, 0].legend()
        
        # Zipfian 분포 안정화 분석
        if zipfian_data and "stability_analysis" in zipfian_data:
            stability = zipfian_data["stability_analysis"]
            windows = stability.get("windows", [])
            
            if windows:
                times = [i for i in range(len(windows))]
                performances = [w["avg_ops_per_sec"] for w in windows]
                
                axes[0, 1].plot(times, performances, marker='o', linewidth=2, color='orange')
                axes[0, 1].set_title(f'Zipfian 분포 - 안정화 분석 (CV: {stability["coefficient_of_variation"]:.3f})')
                axes[0, 1].set_xlabel('시간 윈도우')
                axes[0, 1].set_ylabel('평균 처리량 (ops/sec)')
                axes[0, 1].grid(True, alpha=0.3)
                
                if stability.get("is_stable"):
                    axes[0, 1].axhline(y=stability["stable_performance"], color='red', linestyle='--', alpha=0.7, label='안정화 성능')
                    axes[0, 1].legend()
        
        # 안정화 요약
        uniform_stable = uniform_data.get("stability_analysis", {}).get("is_stable", False)
        zipfian_stable = zipfian_data.get("stability_analysis", {}).get("is_stable", False)
        
        stable_data = [uniform_stable, zipfian_stable]
        stable_labels = ['Uniform', 'Zipfian']
        colors = ['green' if stable else 'red' for stable in stable_data]
        
        axes[1, 0].bar(stable_labels, [1 if stable else 0 for stable in stable_data], color=colors, alpha=0.7)
        axes[1, 0].set_title('안정화 달성 여부')
        axes[1, 0].set_ylabel('안정화 (1=달성, 0=미달성)')
        axes[1, 0].set_ylim(0, 1.2)
        
        # 안정적 성능 비교
        uniform_perf = uniform_data.get("stability_analysis", {}).get("stable_performance", 0)
        zipfian_perf = zipfian_data.get("stability_analysis", {}).get("stable_performance", 0)
        
        perf_data = [uniform_perf/1000, zipfian_perf/1000]  # K ops/sec로 변환
        axes[1, 1].bar(stable_labels, perf_data, color=['blue', 'orange'], alpha=0.7)
        axes[1, 1].set_title('안정적 성능 비교')
        axes[1, 1].set_ylabel('안정적 처리량 (K ops/sec)')
        
        plt.tight_layout()
        plt.savefig(self.results_dir / 'stabilization_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self):
        """결과 저장"""
        self.logger.info("=== Phase-B 결과 저장 시작 ===")
        
        # 실험 결과 저장
        results_file = self.results_dir / "phase_b_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.experiment_results, f, indent=2, default=str)
        
        # 요약 보고서 생성
        self.generate_summary_report()
        
        self.logger.info(f"Phase-B 결과 저장: {results_file}")
        self.logger.info("=== Phase-B 결과 저장 완료 ===")
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        report = {
            "phase": "Phase-B: FillRandom 성능 분석 및 컴팩션 모니터링",
            "objective": "LOG 파일 저장 및 시간별 FillRandom 성능/레벨별 컴팩션 분석",
            "experiment_summary": {
                "start_time": self.experiment_results["start_time"],
                "end_time": self.experiment_results["end_time"],
                "experiment_duration": self.calculate_experiment_duration(),
                "distributions_tested": self.experiment_config["distributions"]
            },
            "key_findings": []
        }
        
        # 주요 발견사항 추가
        uniform_data = self.experiment_results.get("uniform_results", {})
        zipfian_data = self.experiment_results.get("zipfian_results", {})
        
        if uniform_data and "stability_analysis" in uniform_data:
            stability = uniform_data["stability_analysis"]
            if stability.get("is_stable"):
                report["key_findings"].append(f"Uniform 분포: 안정화 달성 (안정 성능: {stability['stable_performance']:.0f} ops/sec)")
            else:
                report["key_findings"].append("Uniform 분포: 안정화 미달성")
        
        if zipfian_data and "stability_analysis" in zipfian_data:
            stability = zipfian_data["stability_analysis"]
            if stability.get("is_stable"):
                report["key_findings"].append(f"Zipfian 분포: 안정화 달성 (안정 성능: {stability['stable_performance']:.0f} ops/sec)")
            else:
                report["key_findings"].append("Zipfian 분포: 안정화 미달성")
        
        # 컴팩션 발견사항
        compaction_stats = self.experiment_results.get("compaction_stats", {})
        if compaction_stats:
            total_compactions = compaction_stats.get("compaction_summary", {}).get("total_compactions", 0)
            report["key_findings"].append(f"총 컴팩션 수: {total_compactions}")
        
        # 보고서 저장
        report_file = self.results_dir / "phase_b_summary_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"요약 보고서 저장: {report_file}")
    
    def calculate_experiment_duration(self):
        """실험 지속 시간 계산"""
        if self.experiment_results["start_time"] and self.experiment_results["end_time"]:
            start = datetime.fromisoformat(self.experiment_results["start_time"])
            end = datetime.fromisoformat(self.experiment_results["end_time"])
            duration = (end - start).total_seconds() / 3600  # 시간 단위
            return duration
        return 0
    
    def run_phase_b(self):
        """Phase-B 전체 실행"""
        self.logger.info("=== Phase-B 시작 ===")
        
        try:
            # 1. RocksDB 로깅 설정
            self.setup_rocksdb_logging()
            
            # 2. Uniform Random FillRandom 실험
            self.run_fillrandom_experiment("uniform")
            
            # 3. Zipfian Random FillRandom 실험
            self.run_fillrandom_experiment("zipfian")
            
            # 4. LOG 파일 복사
            self.copy_log_files()
            
            # 5. 성능 트렌드 분석
            self.analyze_performance_trends()
            
            # 6. 컴팩션 통계 분석
            self.analyze_compaction_stats()
            
            # 7. 시각화 생성
            self.create_visualizations()
            
            # 8. 결과 저장
            self.save_results()
            
            self.logger.info("=== Phase-B 완료 ===")
            
        except Exception as e:
            self.logger.error(f"Phase-B 실행 중 오류: {e}")
            raise

def main():
    """메인 함수"""
    runner = PhaseBRunner()
    runner.run_phase_b()

if __name__ == "__main__":
    main()
