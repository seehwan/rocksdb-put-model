#!/usr/bin/env python3
"""
2025-09-12 향상된 실험 실행 스크립트
SSD 장치 상태 변화와 시간대별 컴팩션 동작을 관찰하여 RocksDB 안정화 가능성 및 안정적 Put 속도 구하기
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

class EnhancedExperimentRunner:
    def __init__(self, base_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12"):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.data_dir = self.base_dir / "data"
        self.results_dir = self.base_dir / "results"
        self.scripts_dir = self.base_dir / "scripts"
        
        # 디렉토리 생성
        for dir_path in [self.logs_dir, self.data_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # 실험 설정
        self.experiment_config = {
            "num_keys": 1000000000,  # 10억 키
            "value_size": 1024,      # 1KB
            "key_size": 16,          # 16 bytes
            "threads": 16,           # 16 threads
            "db_path": "/rocksdb/data",
            "distributions": ["uniform", "zipfian"],
            "zipfian_alpha": 0.99,
            "monitor_interval": 3600,  # 1시간 간격
            "experiment_duration": 7 * 24 * 3600  # 7일
        }
        
        # 실험 결과 저장
        self.experiment_results = {
            "start_time": None,
            "end_time": None,
            "device_performance": {},
            "rocksdb_performance": {},
            "compaction_stats": {},
            "stabilization_analysis": {}
        }
    
    def setup_logging(self):
        """로깅 설정"""
        log_file = self.logs_dir / f"experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"실험 로그 파일: {log_file}")
    
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
    
    def initialize_ssd(self):
        """SSD 완전 초기화"""
        self.logger.info("=== SSD 완전 초기화 시작 ===")
        
        # 1. 언마운트
        self.logger.info("SSD 언마운트 중...")
        self.run_command("sudo umount /dev/nvme0n1p1")
        
        # 2. 블록 디스카드 (완전 초기화)
        self.logger.info("SSD 블록 디스카드 중...")
        self.run_command("sudo blkdiscard /dev/nvme0n1p1")
        
        # 3. 파일시스템 재생성
        self.logger.info("F2FS 파일시스템 재생성 중...")
        self.run_command("sudo mkfs.f2fs /dev/nvme0n1p1")
        
        # 4. 마운트
        self.logger.info("SSD 마운트 중...")
        self.run_command("sudo mount /dev/nvme0n1p1 /rocksdb")
        
        self.logger.info("=== SSD 초기화 완료 ===")
    
    def measure_device_performance(self, phase="initial"):
        """장치 성능 측정"""
        self.logger.info(f"=== {phase} 장치 성능 측정 시작 ===")
        
        # 쓰기 성능 측정
        write_cmd = """
        fio --name=write_test \
            --rw=write \
            --bs=4k \
            --size=10g \
            --numjobs=16 \
            --direct=1 \
            --ioengine=libaio \
            --runtime=300 \
            --time_based \
            --output-format=json \
            --output=/tmp/write_perf.json
        """
        
        # 읽기 성능 측정
        read_cmd = """
        fio --name=read_test \
            --rw=read \
            --bs=4k \
            --size=10g \
            --numjobs=16 \
            --direct=1 \
            --ioengine=libaio \
            --runtime=300 \
            --time_based \
            --output-format=json \
            --output=/tmp/read_perf.json
        """
        
        # 성능 측정 실행
        self.run_command(write_cmd)
        self.run_command(read_cmd)
        
        # 결과 파싱 및 저장
        try:
            with open('/tmp/write_perf.json', 'r') as f:
                write_perf = json.load(f)
            
            with open('/tmp/read_perf.json', 'r') as f:
                read_perf = json.load(f)
            
            # 성능 지표 추출
            write_bw = write_perf['jobs'][0]['write']['bw']  # KiB/s
            read_bw = read_perf['jobs'][0]['read']['bw']     # KiB/s
            
            device_perf = {
                "write_bandwidth_kibps": write_bw,
                "write_bandwidth_mbps": write_bw / 1024,
                "read_bandwidth_kibps": read_bw,
                "read_bandwidth_mbps": read_bw / 1024,
                "timestamp": datetime.now().isoformat()
            }
            
            self.experiment_results["device_performance"][phase] = device_perf
            
            # 결과 저장
            with open(self.data_dir / f"device_performance_{phase}.json", 'w') as f:
                json.dump(device_perf, f, indent=2)
            
            self.logger.info(f"{phase} 장치 성능 측정 완료: {device_perf}")
            
        except Exception as e:
            self.logger.error(f"장치 성능 측정 결과 파싱 실패: {e}")
    
    def run_fillrandom_experiment(self, distribution="uniform"):
        """FillRandom 실험 실행"""
        self.logger.info(f"=== FillRandom 실험 시작 (분포: {distribution}) ===")
        
        # db_bench 명령어 구성
        cmd_parts = [
            "./db_bench",
            f"--benchmarks=fillrandom",
            f"--db={self.experiment_config['db_path']}",
            f"--num={self.experiment_config['num_keys']}",
            f"--value_size={self.experiment_config['value_size']}",
            f"--key_size={self.experiment_config['key_size']}",
            f"--threads={self.experiment_config['threads']}",
            f"--distribution={distribution}",
            "--stats_interval=1000000",
            "--stats_interval_seconds=60",
            "--report_interval_seconds=60",
            "--histogram=true"
        ]
        
        if distribution == "zipfian":
            cmd_parts.append(f"--zipfian_alpha={self.experiment_config['zipfian_alpha']}")
        
        command = " ".join(cmd_parts)
        
        # 실험 시작 시간 기록
        start_time = datetime.now()
        self.experiment_results["start_time"] = start_time.isoformat()
        
        # 실험 실행
        self.logger.info(f"FillRandom 실험 명령어: {command}")
        result = self.run_command(command, timeout=self.experiment_config["experiment_duration"])
        
        # 실험 종료 시간 기록
        end_time = datetime.now()
        self.experiment_results["end_time"] = end_time.isoformat()
        
        if result:
            # 결과 저장
            with open(self.logs_dir / f"fillrandom_{distribution}_output.log", 'w') as f:
                f.write(result)
            
            self.logger.info(f"FillRandom 실험 완료 (분포: {distribution})")
            return True
        else:
            self.logger.error(f"FillRandom 실험 실패 (분포: {distribution})")
            return False
    
    def copy_log_files(self):
        """LOG 파일을 실험 디렉토리로 복사"""
        self.logger.info("=== LOG 파일 복사 시작 ===")
        
        db_path = Path(self.experiment_config["db_path"])
        
        # 메인 LOG 파일 복사
        main_log = db_path / "LOG"
        if main_log.exists():
            self.run_command(f"cp {main_log} {self.logs_dir}/")
            self.logger.info(f"메인 LOG 파일 복사: {main_log}")
        
        # 롤링된 LOG 파일들 복사
        log_files = list(db_path.glob("LOG.old.*"))
        for log_file in log_files:
            self.run_command(f"cp {log_file} {self.logs_dir}/")
            self.logger.info(f"롤링 LOG 파일 복사: {log_file}")
        
        self.logger.info("=== LOG 파일 복사 완료 ===")
    
    def wait_for_compaction_completion(self):
        """컴팩션 완료 대기"""
        self.logger.info("=== 컴팩션 완료 대기 시작 ===")
        
        max_wait_time = 24 * 3600  # 최대 24시간 대기
        check_interval = 300       # 5분 간격 체크
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            # 컴팩션 상태 확인
            cmd = f"./db_bench --benchmarks=compact --db={self.experiment_config['db_path']}"
            result = self.run_command(cmd)
            
            if result and "Compaction" in result:
                self.logger.info("컴팩션 진행 중...")
                time.sleep(check_interval)
                elapsed_time += check_interval
            else:
                self.logger.info("컴팩션 완료!")
                break
        
        if elapsed_time >= max_wait_time:
            self.logger.warning("컴팩션 완료 대기 시간 초과")
        
        self.logger.info("=== 컴팩션 완료 대기 종료 ===")
    
    def analyze_logs(self):
        """로그 파일 분석"""
        self.logger.info("=== 로그 파일 분석 시작 ===")
        
        # 로그 분석 스크립트 실행
        analysis_script = self.scripts_dir / "analyze_logs.py"
        if analysis_script.exists():
            self.run_command(f"python3 {analysis_script}")
        else:
            self.logger.warning("로그 분석 스크립트를 찾을 수 없습니다")
        
        self.logger.info("=== 로그 파일 분석 완료 ===")
    
    def generate_final_report(self):
        """최종 보고서 생성"""
        self.logger.info("=== 최종 보고서 생성 시작 ===")
        
        # 실험 결과 저장
        with open(self.results_dir / "experiment_results.json", 'w') as f:
            json.dump(self.experiment_results, f, indent=2)
        
        # 보고서 생성 스크립트 실행
        report_script = self.scripts_dir / "generate_report.py"
        if report_script.exists():
            self.run_command(f"python3 {report_script}")
        else:
            self.logger.warning("보고서 생성 스크립트를 찾을 수 없습니다")
        
        self.logger.info("=== 최종 보고서 생성 완료 ===")
    
    def run_experiment(self):
        """전체 실험 실행"""
        self.logger.info("=== 2025-09-12 향상된 실험 시작 ===")
        
        try:
            # 1. SSD 초기화
            self.initialize_ssd()
            
            # 2. 초기 장치 성능 측정
            self.measure_device_performance("initial")
            
            # 3. Uniform Random FillRandom 실험
            self.run_fillrandom_experiment("uniform")
            
            # 4. 중간 장치 성능 측정
            self.measure_device_performance("middle")
            
            # 5. Zipfian Random FillRandom 실험
            self.run_fillrandom_experiment("zipfian")
            
            # 6. 최종 장치 성능 측정
            self.measure_device_performance("final")
            
            # 7. LOG 파일 복사
            self.copy_log_files()
            
            # 8. 컴팩션 완료 대기
            self.wait_for_compaction_completion()
            
            # 9. 로그 분석
            self.analyze_logs()
            
            # 10. 최종 보고서 생성
            self.generate_final_report()
            
            self.logger.info("=== 실험 완료 ===")
            
        except Exception as e:
            self.logger.error(f"실험 실행 중 오류 발생: {e}")
            raise

def main():
    """메인 함수"""
    runner = EnhancedExperimentRunner()
    runner.run_experiment()

if __name__ == "__main__":
    main()
