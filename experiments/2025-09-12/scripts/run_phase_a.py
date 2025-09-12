#!/usr/bin/env python3
"""
Phase-A: Device Envelope 모델 구축
초기상태 장치 성능과 Phase-B 이후 열화된 상태에서의 장치 성능을 측정하여 Device Envelope 모델 구축
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
from scipy.interpolate import RegularGridInterpolator

class PhaseARunner:
    def __init__(self, base_dir="/home/sslab/rocksdb-put-model/experiments/2025-09-12"):
        self.base_dir = Path(base_dir)
        self.phase_dir = self.base_dir / "phase-a"
        self.data_dir = self.phase_dir / "data"
        self.results_dir = self.phase_dir / "results"
        
        # 디렉토리 생성
        for dir_path in [self.data_dir, self.results_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 로깅 설정
        self.setup_logging()
        
        # 실험 설정
        self.experiment_config = {
            "device_path": "/dev/nvme1n1",
            "mount_point": "/rocksdb",
            "fio_parameters": {
                "block_sizes": ["4k", "8k", "16k", "32k", "64k", "128k", "256k", "512k", "1m"],
                "queue_depths": [1, 2, 4, 8, 16, 32, 64],
                "num_jobs": [1, 2, 4, 8, 16],
                "read_write_ratios": [0.0, 0.25, 0.5, 0.75, 1.0]  # 0.0=write only, 1.0=read only
            },
            "test_duration": 300,  # 5분
            "warmup_duration": 60   # 1분 워밍업
        }
        
        # 결과 저장
        self.device_envelope = {
            "initial_state": {},
            "degraded_state": {},
            "interpolation_model": None,
            "degradation_model": None
        }
    
    def setup_logging(self):
        """로깅 설정"""
        log_file = self.phase_dir / f"phase_a_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Phase-A 로그 파일: {log_file}")
    
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
        self.run_command(f"sudo umount {self.experiment_config['device_path']}")
        time.sleep(2)
        
        # 2. 블록 디스카드 (완전 초기화)
        self.logger.info("SSD 블록 디스카드 중...")
        self.run_command(f"sudo blkdiscard {self.experiment_config['device_path']}")
        time.sleep(5)
        
        # 3. 파일시스템 재생성
        self.logger.info("F2FS 파일시스템 재생성 중...")
        self.run_command(f"sudo mkfs.f2fs {self.experiment_config['device_path']}")
        time.sleep(3)
        
        # 4. 마운트
        self.logger.info("SSD 마운트 중...")
        self.run_command(f"sudo mount {self.experiment_config['device_path']} {self.experiment_config['mount_point']}")
        time.sleep(2)
        
        # 5. 권한 설정
        self.run_command(f"sudo chown -R {os.getenv('USER')}:{os.getenv('USER')} {self.experiment_config['mount_point']}")
        
        self.logger.info("=== SSD 초기화 완료 ===")
    
    def run_fio_grid_benchmark(self, state="initial"):
        """fio 그리드 벤치마크 실행"""
        self.logger.info(f"=== {state} 상태 fio 그리드 벤치마크 시작 ===")
        
        config = self.experiment_config["fio_parameters"]
        results = []
        
        total_tests = (len(config["block_sizes"]) * len(config["queue_depths"]) * 
                      len(config["num_jobs"]) * len(config["read_write_ratios"]))
        current_test = 0
        
        for bs in config["block_sizes"]:
            for qd in config["queue_depths"]:
                for numjobs in config["num_jobs"]:
                    for rw_ratio in config["read_write_ratios"]:
                        current_test += 1
                        self.logger.info(f"테스트 진행: {current_test}/{total_tests} - {state} 상태")
                        
                        # fio 명령어 구성
                        fio_cmd = self.create_fio_command(bs, qd, numjobs, rw_ratio)
                        
                        # fio 실행
                        result = self.run_command(fio_cmd, timeout=self.experiment_config["test_duration"] + 60)
                        
                        if result:
                            # 결과 파싱
                            parsed_result = self.parse_fio_result(result, bs, qd, numjobs, rw_ratio, state)
                            if parsed_result:
                                results.append(parsed_result)
                        
                        # 테스트 간 간격
                        time.sleep(10)
        
        # 결과 저장
        self.device_envelope[f"{state}_state"] = {
            "raw_results": results,
            "grid_data": self.create_grid_data(results),
            "timestamp": datetime.now().isoformat()
        }
        
        # CSV 저장
        df = pd.DataFrame(results)
        csv_file = self.data_dir / f"fio_grid_{state}_results.csv"
        df.to_csv(csv_file, index=False)
        
        self.logger.info(f"=== {state} 상태 벤치마크 완료 ===")
        self.logger.info(f"결과 저장: {csv_file}")
        
        return results
    
    def create_fio_command(self, bs, qd, numjobs, rw_ratio):
        """fio 명령어 생성"""
        # rw 모드 결정
        if rw_ratio == 0.0:
            rw = "write"
        elif rw_ratio == 1.0:
            rw = "read"
        else:
            rw = "rw"
            rwmixread = int(rw_ratio * 100)
        
        # 기본 fio 명령어
        cmd_parts = [
            "fio",
            "--name=grid_test",
            f"--rw={rw}",
            f"--bs={bs}",
            f"--iodepth={qd}",
            f"--numjobs={numjobs}",
            f"--size=1g",
            f"--runtime={self.experiment_config['test_duration']}",
            "--time_based",
            "--direct=1",
            "--ioengine=libaio",
            "--output-format=json",
            "--output=/tmp/fio_result.json"
        ]
        
        # rw 모드인 경우 rwmixread 추가
        if rw == "rw":
            cmd_parts.append(f"--rwmixread={rwmixread}")
        
        return " ".join(cmd_parts)
    
    def parse_fio_result(self, result, bs, qd, numjobs, rw_ratio, state):
        """fio 결과 파싱"""
        try:
            # JSON 결과 로드
            with open('/tmp/fio_result.json', 'r') as f:
                fio_data = json.load(f)
            
            # 성능 지표 추출
            job = fio_data['jobs'][0]
            
            # 블록 크기를 KB로 변환
            bs_k = self.block_size_to_kb(bs)
            
            # 읽기/쓰기 성능 추출
            read_bw = job.get('read', {}).get('bw', 0)  # KiB/s
            write_bw = job.get('write', {}).get('bw', 0)  # KiB/s
            
            read_iops = job.get('read', {}).get('iops', 0)
            write_iops = job.get('write', {}).get('iops', 0)
            
            read_lat = job.get('read', {}).get('lat_ns', {}).get('mean', 0) / 1000  # μs
            write_lat = job.get('write', {}).get('lat_ns', {}).get('mean', 0) / 1000  # μs
            
            return {
                "state": state,
                "bs": bs,
                "bs_k": bs_k,
                "qd": qd,
                "numjobs": numjobs,
                "rw_ratio": rw_ratio,
                "read_bw_kibps": read_bw,
                "write_bw_kibps": write_bw,
                "read_bw_mbps": read_bw / 1024,
                "write_bw_mbps": write_bw / 1024,
                "read_iops": read_iops,
                "write_iops": write_iops,
                "read_lat_us": read_lat,
                "write_lat_us": write_lat,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"fio 결과 파싱 실패: {e}")
            return None
    
    def block_size_to_kb(self, bs):
        """블록 크기를 KB로 변환"""
        bs_lower = bs.lower()
        if bs_lower.endswith('k'):
            return int(bs_lower[:-1])
        elif bs_lower.endswith('m'):
            return int(bs_lower[:-1]) * 1024
        else:
            return int(bs_lower) // 1024
    
    def create_grid_data(self, results):
        """그리드 데이터 생성"""
        if not results:
            return {}
        
        df = pd.DataFrame(results)
        
        # 4D 그리드 생성
        bs_k_values = sorted(df['bs_k'].unique())
        qd_values = sorted(df['qd'].unique())
        numjobs_values = sorted(df['numjobs'].unique())
        rw_ratio_values = sorted(df['rw_ratio'].unique())
        
        # 읽기/쓰기 대역폭 그리드
        read_bw_grid = np.zeros((len(bs_k_values), len(qd_values), len(numjobs_values), len(rw_ratio_values)))
        write_bw_grid = np.zeros((len(bs_k_values), len(qd_values), len(numjobs_values), len(rw_ratio_values)))
        
        for _, row in df.iterrows():
            bs_idx = bs_k_values.index(row['bs_k'])
            qd_idx = qd_values.index(row['qd'])
            jobs_idx = numjobs_values.index(row['numjobs'])
            rw_idx = rw_ratio_values.index(row['rw_ratio'])
            
            read_bw_grid[bs_idx, qd_idx, jobs_idx, rw_idx] = row['read_bw_mbps']
            write_bw_grid[bs_idx, qd_idx, jobs_idx, rw_idx] = row['write_bw_mbps']
        
        return {
            "bs_k_values": bs_k_values,
            "qd_values": qd_values,
            "numjobs_values": numjobs_values,
            "rw_ratio_values": rw_ratio_values,
            "read_bw_grid": read_bw_grid.tolist(),
            "write_bw_grid": write_bw_grid.tolist()
        }
    
    def build_device_envelope_model(self):
        """Device Envelope 모델 구축"""
        self.logger.info("=== Device Envelope 모델 구축 시작 ===")
        
        initial_data = self.device_envelope.get("initial_state", {})
        degraded_data = self.device_envelope.get("degraded_state", {})
        
        if not initial_data or not degraded_data:
            self.logger.error("초기 상태 또는 열화 상태 데이터가 없습니다")
            return
        
        # 4D Grid Interpolation 모델 생성
        initial_grid = initial_data["grid_data"]
        degraded_grid = degraded_data["grid_data"]
        
        # RegularGridInterpolator 생성
        initial_read_interp = RegularGridInterpolator(
            (initial_grid["bs_k_values"], initial_grid["qd_values"], 
             initial_grid["numjobs_values"], initial_grid["rw_ratio_values"]),
            np.array(initial_grid["read_bw_grid"]),
            method='linear',
            bounds_error=False,
            fill_value=0
        )
        
        initial_write_interp = RegularGridInterpolator(
            (initial_grid["bs_k_values"], initial_grid["qd_values"], 
             initial_grid["numjobs_values"], initial_grid["rw_ratio_values"]),
            np.array(initial_grid["write_bw_grid"]),
            method='linear',
            bounds_error=False,
            fill_value=0
        )
        
        degraded_read_interp = RegularGridInterpolator(
            (degraded_grid["bs_k_values"], degraded_grid["qd_values"], 
             degraded_grid["numjobs_values"], degraded_grid["rw_ratio_values"]),
            np.array(degraded_grid["read_bw_grid"]),
            method='linear',
            bounds_error=False,
            fill_value=0
        )
        
        degraded_write_interp = RegularGridInterpolator(
            (degraded_grid["bs_k_values"], degraded_grid["qd_values"], 
             degraded_grid["numjobs_values"], degraded_grid["rw_ratio_values"]),
            np.array(degraded_grid["write_bw_grid"]),
            method='linear',
            bounds_error=False,
            fill_value=0
        )
        
        # 열화 모델 생성 (간단한 선형 보간)
        def time_dependent_interpolator(t_hours):
            """시간에 따른 성능 보간"""
            # t=0: 초기 상태, t=36: 열화 상태 (36시간 기준)
            if t_hours <= 0:
                return initial_read_interp, initial_write_interp
            elif t_hours >= 36:
                return degraded_read_interp, degraded_write_interp
            else:
                # 선형 보간
                alpha = t_hours / 36.0
                
                def interpolated_read(bs_k, qd, numjobs, rw_ratio):
                    initial_val = initial_read_interp([bs_k, qd, numjobs, rw_ratio])[0]
                    degraded_val = degraded_read_interp([bs_k, qd, numjobs, rw_ratio])[0]
                    return initial_val * (1 - alpha) + degraded_val * alpha
                
                def interpolated_write(bs_k, qd, numjobs, rw_ratio):
                    initial_val = initial_write_interp([bs_k, qd, numjobs, rw_ratio])[0]
                    degraded_val = degraded_write_interp([bs_k, qd, numjobs, rw_ratio])[0]
                    return initial_val * (1 - alpha) + degraded_val * alpha
                
                return interpolated_read, interpolated_write
        
        # 모델 저장
        self.device_envelope["interpolation_model"] = {
            "initial_read_interp": initial_read_interp,
            "initial_write_interp": initial_write_interp,
            "degraded_read_interp": degraded_read_interp,
            "degraded_write_interp": degraded_write_interp,
            "time_dependent_interpolator": time_dependent_interpolator
        }
        
        # 열화 분석
        self.analyze_degradation()
        
        self.logger.info("=== Device Envelope 모델 구축 완료 ===")
    
    def analyze_degradation(self):
        """열화 분석"""
        self.logger.info("=== 장치 열화 분석 시작 ===")
        
        initial_data = self.device_envelope["initial_state"]["raw_results"]
        degraded_data = self.device_envelope["degraded_state"]["raw_results"]
        
        # 평균 성능 계산
        initial_read_avg = np.mean([r["read_bw_mbps"] for r in initial_data])
        initial_write_avg = np.mean([r["write_bw_mbps"] for r in initial_data])
        degraded_read_avg = np.mean([r["read_bw_mbps"] for r in degraded_data])
        degraded_write_avg = np.mean([r["write_bw_mbps"] for r in degraded_data])
        
        # 열화율 계산
        read_degradation = (initial_read_avg - degraded_read_avg) / initial_read_avg * 100
        write_degradation = (initial_write_avg - degraded_write_avg) / initial_write_avg * 100
        
        degradation_analysis = {
            "initial_performance": {
                "read_avg_mbps": initial_read_avg,
                "write_avg_mbps": initial_write_avg
            },
            "degraded_performance": {
                "read_avg_mbps": degraded_read_avg,
                "write_avg_mbps": degraded_write_avg
            },
            "degradation_percent": {
                "read_degradation": read_degradation,
                "write_degradation": write_degradation
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        self.device_envelope["degradation_analysis"] = degradation_analysis
        
        self.logger.info(f"읽기 성능 열화: {read_degradation:.2f}%")
        self.logger.info(f"쓰기 성능 열화: {write_degradation:.2f}%")
        self.logger.info("=== 장치 열화 분석 완료 ===")
    
    def save_results(self):
        """결과 저장"""
        self.logger.info("=== Phase-A 결과 저장 시작 ===")
        
        # Device Envelope 모델 저장 (interpolator는 제외)
        model_data = {
            "initial_state": self.device_envelope["initial_state"],
            "degraded_state": self.device_envelope["degraded_state"],
            "degradation_analysis": self.device_envelope.get("degradation_analysis", {}),
            "experiment_config": self.experiment_config,
            "generated_at": datetime.now().isoformat()
        }
        
        # JSON 저장
        model_file = self.results_dir / "device_envelope_model.json"
        with open(model_file, 'w') as f:
            json.dump(model_data, f, indent=2, default=str)
        
        # 요약 보고서 생성
        self.generate_summary_report()
        
        self.logger.info(f"Device Envelope 모델 저장: {model_file}")
        self.logger.info("=== Phase-A 결과 저장 완료 ===")
    
    def generate_summary_report(self):
        """요약 보고서 생성"""
        report = {
            "phase": "Phase-A: Device Envelope 모델 구축",
            "objective": "초기상태와 열화상태 장치 성능 측정으로 Device Envelope 모델 구축",
            "experiment_summary": {
                "total_tests_initial": len(self.device_envelope.get("initial_state", {}).get("raw_results", [])),
                "total_tests_degraded": len(self.device_envelope.get("degraded_state", {}).get("raw_results", [])),
                "experiment_duration": "약 2-3시간 (각 상태별 그리드 벤치마크)"
            },
            "key_findings": []
        }
        
        # 주요 발견사항 추가
        if "degradation_analysis" in self.device_envelope:
            degradation = self.device_envelope["degradation_analysis"]["degradation_percent"]
            report["key_findings"].extend([
                f"읽기 성능 열화: {degradation['read_degradation']:.2f}%",
                f"쓰기 성능 열화: {degradation['write_degradation']:.2f}%",
                "4D Grid Interpolation 모델 구축 완료",
                "시간 의존적 성능 모델 구축 완료"
            ])
        
        # 보고서 저장
        report_file = self.results_dir / "phase_a_summary_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"요약 보고서 저장: {report_file}")
    
    def run_phase_a(self):
        """Phase-A 전체 실행"""
        self.logger.info("=== Phase-A 시작 ===")
        
        try:
            # 1. SSD 초기화
            self.initialize_ssd()
            
            # 2. 초기 상태 장치 성능 측정
            self.run_fio_grid_benchmark("initial")
            
            # 3. Phase-B 완료 대기 안내
            self.logger.info("=== Phase-B 실험을 진행하세요 ===")
            self.logger.info("Phase-B에서 FillRandom 실험을 완료한 후 다시 이 스크립트를 실행하여 열화 상태를 측정합니다.")
            
            # 사용자 입력 대기
            input("Phase-B 실험이 완료되었으면 Enter를 눌러 계속하세요...")
            
            # 4. 열화 상태 장치 성능 측정
            self.run_fio_grid_benchmark("degraded")
            
            # 5. Device Envelope 모델 구축
            self.build_device_envelope_model()
            
            # 6. 결과 저장
            self.save_results()
            
            self.logger.info("=== Phase-A 완료 ===")
            
        except Exception as e:
            self.logger.error(f"Phase-A 실행 중 오류: {e}")
            raise

def main():
    """메인 함수"""
    runner = PhaseARunner()
    runner.run_phase_a()

if __name__ == "__main__":
    main()
