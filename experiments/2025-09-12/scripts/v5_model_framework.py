#!/usr/bin/env python3
"""
RocksDB Put Model v5 Framework
시간대별/레벨별 성능 변화를 반영한 향상된 모델
SSD 장치 상태 변화와 컴팩션 동작을 고려한 안정화 모델
"""

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import minimize
import json
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt

class RocksDBModelV5:
    """
    RocksDB Put Model v5
    - SSD 장치 상태 변화 고려
    - 시간대별 컴팩션 동작 반영
    - 레벨별 성능 변화 모델링
    - 안정화 가능성 및 안정적 Put 속도 예측
    """
    
    def __init__(self, config_file=None):
        self.model_config = self.load_default_config()
        if config_file:
            self.load_config(config_file)
        
        # 모델 파라미터
        self.device_performance = {}
        self.compaction_models = {}
        self.level_models = {}
        self.stabilization_model = None
        
        # v4 모델 기반 확장
        self.device_envelope = None
        self.dynamic_simulation = None
    
    def load_default_config(self):
        """기본 모델 설정 로드"""
        return {
            "model_version": "v5.0",
            "model_type": "enhanced_stabilization_model",
            "device_modeling": {
                "initialization_state": True,
                "degradation_tracking": True,
                "performance_interpolation": True
            },
            "compaction_modeling": {
                "time_dependent": True,
                "level_specific": True,
                "pattern_recognition": True
            },
            "stabilization_modeling": {
                "stability_detection": True,
                "steady_state_prediction": True,
                "performance_optimization": True
            },
            "performance_components": {
                "cache_miss": True,
                "system_overhead": True,
                "filesystem_impact": True,
                "device_degradation": True
            }
        }
    
    def load_config(self, config_file):
        """설정 파일 로드"""
        with open(config_file, 'r') as f:
            custom_config = json.load(f)
            self.model_config.update(custom_config)
    
    def initialize_device_model(self, device_data):
        """장치 모델 초기화"""
        print("장치 모델 초기화 중...")
        
        # 초기화 상태 성능
        initial_perf = device_data.get("initial", {})
        self.device_performance["initial"] = {
            "B_w": initial_perf.get("write_bandwidth_mbps", 0),
            "B_r": initial_perf.get("read_bandwidth_mbps", 0),
            "B_eff": (initial_perf.get("write_bandwidth_mbps", 0) + 
                     initial_perf.get("read_bandwidth_mbps", 0)) / 2
        }
        
        # 열화 상태 성능
        degraded_perf = device_data.get("degraded", {})
        self.device_performance["degraded"] = {
            "B_w": degraded_perf.get("write_bandwidth_mbps", 0),
            "B_r": degraded_perf.get("read_bandwidth_mbps", 0),
            "B_eff": (degraded_perf.get("write_bandwidth_mbps", 0) + 
                     degraded_perf.get("read_bandwidth_mbps", 0)) / 2
        }
        
        # 시간 의존적 성능 모델
        self.device_performance["time_dependent"] = self.create_time_dependent_model(device_data)
    
    def create_time_dependent_model(self, device_data):
        """시간 의존적 장치 성능 모델 생성"""
        # 시간에 따른 성능 저하 모델 (지수적 저하)
        initial_bw = self.device_performance["initial"]["B_w"]
        degraded_bw = self.device_performance["degraded"]["B_w"]
        
        # 저하율 계산 (시간 단위)
        degradation_rate = np.log(initial_bw / degraded_bw) / 36.0  # 36시간 기준
        
        def time_dependent_performance(t_hours):
            """시간에 따른 성능 계산"""
            if t_hours <= 0:
                return initial_bw
            else:
                return initial_bw * np.exp(-degradation_rate * t_hours)
        
        return time_dependent_performance
    
    def initialize_compaction_model(self, compaction_data):
        """컴팩션 모델 초기화"""
        print("컴팩션 모델 초기화 중...")
        
        # 레벨별 컴팩션 모델
        for level in range(4):  # L0, L1, L2, L3
            level_data = compaction_data.get(f"level_{level}", {})
            
            self.compaction_models[f"level_{level}"] = {
                "frequency": level_data.get("compaction_frequency", 0),
                "avg_files": level_data.get("avg_files_per_compaction", 0),
                "avg_size": level_data.get("avg_size_per_compaction", 0),
                "waf": self.calculate_waf_for_level(level),
                "io_intensity": self.calculate_io_intensity(level_data)
            }
        
        # 시간대별 컴팩션 패턴
        hourly_patterns = compaction_data.get("hourly_patterns", {})
        self.compaction_models["hourly_patterns"] = hourly_patterns
        
        # 컴팩션 타입별 모델
        type_stats = compaction_data.get("type_stats", {})
        self.compaction_models["type_stats"] = type_stats
    
    def calculate_waf_for_level(self, level):
        """레벨별 WAF 계산"""
        # 레벨별 WAF 추정 (실험 데이터 기반)
        waf_by_level = {
            0: 1.0,   # L0: flush only
            1: 2.0,   # L1: minimal WA
            2: 22.6,  # L2: major WA (09-09 실험 결과)
            3: 3.0    # L3: moderate WA
        }
        return waf_by_level.get(level, 1.0)
    
    def calculate_io_intensity(self, level_data):
        """레벨별 I/O 강도 계산"""
        frequency = level_data.get("compaction_frequency", 0)
        avg_size = level_data.get("avg_size_per_compaction", 0)
        
        # I/O 강도 = 컴팩션 빈도 × 평균 크기
        return frequency * avg_size
    
    def initialize_level_model(self, level_data):
        """레벨별 성능 모델 초기화"""
        print("레벨별 성능 모델 초기화 중...")
        
        # 최신 레벨 분포
        latest_dist = level_data.get("latest_distribution", {})
        
        for level_key, level_info in latest_dist.items():
            level_num = int(level_key.split("_")[1])
            
            self.level_models[level_key] = {
                "files": level_info.get("files", 0),
                "size_mb": level_info.get("size_mb", 0),
                "performance_factor": self.calculate_level_performance_factor(level_num),
                "compaction_overhead": self.calculate_compaction_overhead(level_num)
            }
        
        # 레벨별 성능 가중치 계산
        self.calculate_level_weights()
    
    def calculate_level_performance_factor(self, level):
        """레벨별 성능 인수 계산"""
        # 레벨이 높을수록 성능 저하 (09-09 실험 결과 기반)
        performance_factors = {
            0: 1.0,   # L0: 최고 성능
            1: 0.95,  # L1: 약간의 저하
            2: 0.30,  # L2: 주요 병목
            3: 0.80   # L3: 중간 성능
        }
        return performance_factors.get(level, 1.0)
    
    def calculate_compaction_overhead(self, level):
        """레벨별 컴팩션 오버헤드 계산"""
        # L2가 가장 높은 오버헤드 (09-09 실험 결과)
        overhead_by_level = {
            0: 0.05,  # L0: 낮은 오버헤드
            1: 0.10,  # L1: 중간 오버헤드
            2: 0.45,  # L2: 높은 오버헤드
            3: 0.20   # L3: 중간 오버헤드
        }
        return overhead_by_level.get(level, 0.10)
    
    def calculate_level_weights(self):
        """레벨별 가중치 계산"""
        total_weight = 0
        for level_key, level_info in self.level_models.items():
            weight = level_info["files"] * level_info["size_mb"]
            level_info["weight"] = weight
            total_weight += weight
        
        # 정규화
        for level_key, level_info in self.level_models.items():
            level_info["normalized_weight"] = level_info["weight"] / total_weight if total_weight > 0 else 0
    
    def initialize_stabilization_model(self, performance_data):
        """안정화 모델 초기화"""
        print("안정화 모델 초기화 중...")
        
        # 성능 안정성 분석
        stability_analysis = performance_data.get("stability_analysis", {})
        
        self.stabilization_model = {
            "is_stable": stability_analysis.get("is_stable", False),
            "stabilization_time": stability_analysis.get("stabilization_time"),
            "stable_performance": stability_analysis.get("stable_performance", 0),
            "coefficient_of_variation": stability_analysis.get("coefficient_of_variation", 0),
            "stability_threshold": 0.1,  # CV < 0.1이면 안정화
            "windows": stability_analysis.get("windows", [])
        }
        
        # 안정화 예측 모델
        self.create_stabilization_prediction_model()
    
    def create_stabilization_prediction_model(self):
        """안정화 예측 모델 생성"""
        windows = self.stabilization_model.get("windows", [])
        
        if len(windows) < 2:
            return
        
        # 시간 윈도우별 성능 데이터
        times = [i for i in range(len(windows))]
        performances = [w["avg_ops_per_sec"] for w in windows]
        
        # 지수적 수렴 모델 피팅
        def exponential_convergence(t, a, b, c):
            """지수적 수렴 모델: y = a + b * exp(-c * t)"""
            return a + b * np.exp(-c * t)
        
        # 최적화를 통한 파라미터 추정
        try:
            from scipy.optimize import curve_fit
            popt, _ = curve_fit(exponential_convergence, times, performances, maxfev=1000)
            
            self.stabilization_model["convergence_model"] = {
                "a": popt[0],  # 최종 수렴값
                "b": popt[1],  # 초기 편차
                "c": popt[2],  # 수렴 속도
                "model_func": lambda t: exponential_convergence(t, popt[0], popt[1], popt[2])
            }
            
        except Exception as e:
            print(f"안정화 모델 피팅 실패: {e}")
            self.stabilization_model["convergence_model"] = None
    
    def predict_put_rate(self, time_hours, key_distribution="uniform", num_threads=16):
        """Put 속도 예측"""
        # 1. 장치 성능 계산
        device_perf = self.device_performance["time_dependent"](time_hours)
        
        # 2. 레벨별 성능 계산
        level_performance = self.calculate_level_performance()
        
        # 3. 컴팩션 오버헤드 계산
        compaction_overhead = self.calculate_compaction_overhead(time_hours)
        
        # 4. 기본 Put 속도 계산
        base_put_rate = self.calculate_base_put_rate(device_perf, level_performance, num_threads)
        
        # 5. 분포별 조정
        distribution_factor = self.get_distribution_factor(key_distribution)
        
        # 6. 최종 Put 속도
        final_put_rate = base_put_rate * distribution_factor * (1 - compaction_overhead)
        
        return {
            "put_rate_ops_sec": final_put_rate,
            "put_rate_mbps": final_put_rate * 1024 / 1000000,  # 1KB value 가정
            "device_performance": device_perf,
            "level_performance": level_performance,
            "compaction_overhead": compaction_overhead,
            "distribution_factor": distribution_factor,
            "time_hours": time_hours
        }
    
    def calculate_level_performance(self):
        """레벨별 성능 계산"""
        total_performance = 0
        for level_key, level_info in self.level_models.items():
            weight = level_info.get("normalized_weight", 0)
            performance_factor = level_info.get("performance_factor", 1.0)
            total_performance += weight * performance_factor
        
        return total_performance
    
    def calculate_compaction_overhead(self, time_hours):
        """컴팩션 오버헤드 계산"""
        # 시간에 따른 컴팩션 오버헤드 (초기에는 높고, 시간이 지나면서 감소)
        base_overhead = 0.3  # 기본 오버헤드 30%
        decay_factor = np.exp(-time_hours / 24.0)  # 24시간 기준으로 감소
        
        return base_overhead * decay_factor
    
    def calculate_base_put_rate(self, device_perf, level_performance, num_threads):
        """기본 Put 속도 계산"""
        # 장치 성능과 레벨 성능을 고려한 기본 Put 속도
        base_rate = device_perf * level_performance * num_threads
        
        # 시스템 오버헤드 고려
        system_overhead = 0.1  # 10% 시스템 오버헤드
        
        return base_rate * (1 - system_overhead)
    
    def get_distribution_factor(self, distribution):
        """키 분포별 성능 인수"""
        distribution_factors = {
            "uniform": 1.0,
            "zipfian": 0.85  # Zipfian 분포는 약간의 성능 저하
        }
        return distribution_factors.get(distribution, 1.0)
    
    def predict_stabilization(self, max_time_hours=168):  # 7일
        """안정화 예측"""
        if not self.stabilization_model.get("convergence_model"):
            return {"error": "안정화 모델이 초기화되지 않았습니다"}
        
        model = self.stabilization_model["convergence_model"]
        model_func = model["model_func"]
        
        # 안정화 시간 예측 (CV < 0.1이 되는 시점)
        for t in range(max_time_hours):
            predicted_perf = model_func(t)
            
            # 안정화 판단 (간단한 휴리스틱)
            if t > 24:  # 최소 24시간 후부터 안정화 고려
                # 성능 변화율이 충분히 작아지면 안정화로 판단
                if t < max_time_hours - 1:
                    next_perf = model_func(t + 1)
                    change_rate = abs(next_perf - predicted_perf) / predicted_perf
                    
                    if change_rate < 0.05:  # 5% 이하 변화율
                        return {
                            "will_stabilize": True,
                            "stabilization_time_hours": t,
                            "stable_put_rate": predicted_perf,
                            "confidence": 0.8
                        }
        
        return {
            "will_stabilize": False,
            "reason": "예측 시간 내에 안정화되지 않음",
            "final_predicted_rate": model_func(max_time_hours - 1)
        }
    
    def optimize_parameters(self, experimental_data):
        """실험 데이터를 이용한 모델 파라미터 최적화"""
        print("모델 파라미터 최적화 중...")
        
        # 목적 함수: 예측값과 실제값의 차이 최소화
        def objective(params):
            # 파라미터 설정
            device_degradation_rate = params[0]
            level_performance_weights = params[1:5]
            compaction_overhead_base = params[5]
            
            # 모델 파라미터 업데이트
            self.update_model_parameters(device_degradation_rate, level_performance_weights, compaction_overhead_base)
            
            # 예측값과 실제값 비교
            total_error = 0
            for data_point in experimental_data:
                predicted = self.predict_put_rate(
                    data_point["time_hours"], 
                    data_point["distribution"], 
                    data_point["threads"]
                )
                actual = data_point["actual_put_rate"]
                
                error = abs(predicted["put_rate_ops_sec"] - actual) / actual
                total_error += error
            
            return total_error / len(experimental_data)
        
        # 초기 파라미터
        initial_params = [
            0.05,  # device_degradation_rate
            1.0, 0.95, 0.30, 0.80,  # level_performance_weights
            0.3   # compaction_overhead_base
        ]
        
        # 최적화 실행
        try:
            result = minimize(objective, initial_params, method='Nelder-Mead')
            
            if result.success:
                print(f"최적화 성공. 최종 오차: {result.fun:.4f}")
                return result.x
            else:
                print("최적화 실패")
                return initial_params
                
        except Exception as e:
            print(f"최적화 중 오류: {e}")
            return initial_params
    
    def update_model_parameters(self, degradation_rate, level_weights, overhead_base):
        """모델 파라미터 업데이트"""
        # 장치 성능 모델 업데이트
        if "time_dependent" in self.device_performance:
            old_func = self.device_performance["time_dependent"]
            initial_bw = self.device_performance["initial"]["B_w"]
            
            def new_time_dependent_performance(t_hours):
                if t_hours <= 0:
                    return initial_bw
                else:
                    return initial_bw * np.exp(-degradation_rate * t_hours)
            
            self.device_performance["time_dependent"] = new_time_dependent_performance
        
        # 레벨별 성능 가중치 업데이트
        for i, level_key in enumerate(["level_0", "level_1", "level_2", "level_3"]):
            if level_key in self.level_models:
                self.level_models[level_key]["performance_factor"] = level_weights[i]
        
        # 컴팩션 오버헤드 베이스 업데이트
        self.model_config["compaction_overhead_base"] = overhead_base
    
    def generate_model_report(self):
        """모델 보고서 생성"""
        report = {
            "model_version": self.model_config["model_version"],
            "model_type": self.model_config["model_type"],
            "device_performance": self.device_performance,
            "compaction_models": self.compaction_models,
            "level_models": self.level_models,
            "stabilization_model": self.stabilization_model,
            "model_parameters": {
                "device_degradation_enabled": self.model_config["device_modeling"]["degradation_tracking"],
                "time_dependent_compaction": self.model_config["compaction_modeling"]["time_dependent"],
                "level_specific_modeling": self.model_config["compaction_modeling"]["level_specific"],
                "stabilization_detection": self.model_config["stabilization_modeling"]["stability_detection"]
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def save_model(self, filepath):
        """모델 저장"""
        model_data = self.generate_model_report()
        
        with open(filepath, 'w') as f:
            json.dump(model_data, f, indent=2, default=str)
        
        print(f"모델 저장 완료: {filepath}")
    
    def load_model(self, filepath):
        """모델 로드"""
        with open(filepath, 'r') as f:
            model_data = json.load(f)
        
        self.device_performance = model_data.get("device_performance", {})
        self.compaction_models = model_data.get("compaction_models", {})
        self.level_models = model_data.get("level_models", {})
        self.stabilization_model = model_data.get("stabilization_model", {})
        
        print(f"모델 로드 완료: {filepath}")

def main():
    """메인 함수 - 모델 테스트"""
    model = RocksDBModelV5()
    
    # 테스트 데이터
    test_device_data = {
        "initial": {"write_bandwidth_mbps": 5000, "read_bandwidth_mbps": 7000},
        "degraded": {"write_bandwidth_mbps": 4200, "read_bandwidth_mbps": 6500}
    }
    
    test_compaction_data = {
        "level_0": {"compaction_frequency": 10, "avg_files_per_compaction": 4, "avg_size_per_compaction": 256},
        "level_1": {"compaction_frequency": 5, "avg_files_per_compaction": 10, "avg_size_per_compaction": 512},
        "level_2": {"compaction_frequency": 2, "avg_files_per_compaction": 100, "avg_size_per_compaction": 1024},
        "level_3": {"compaction_frequency": 1, "avg_files_per_compaction": 500, "avg_size_per_compaction": 2048},
        "hourly_patterns": {i: 5 for i in range(24)},
        "type_stats": {"flush": 100, "compaction": 50}
    }
    
    test_level_data = {
        "latest_distribution": {
            "level_0": {"files": 4, "size_mb": 256},
            "level_1": {"files": 10, "size_mb": 1024},
            "level_2": {"files": 100, "size_mb": 10240},
            "level_3": {"files": 500, "size_mb": 51200}
        }
    }
    
    test_performance_data = {
        "stability_analysis": {
            "is_stable": True,
            "stabilization_time": "2025-09-13T12:00:00",
            "stable_performance": 30000,
            "coefficient_of_variation": 0.05,
            "windows": [
                {"start_time": datetime.now() - timedelta(hours=24), "avg_ops_per_sec": 25000},
                {"start_time": datetime.now() - timedelta(hours=12), "avg_ops_per_sec": 28000},
                {"start_time": datetime.now(), "avg_ops_per_sec": 30000}
            ]
        }
    }
    
    # 모델 초기화
    model.initialize_device_model(test_device_data)
    model.initialize_compaction_model(test_compaction_data)
    model.initialize_level_model(test_level_data)
    model.initialize_stabilization_model(test_performance_data)
    
    # 예측 테스트
    prediction = model.predict_put_rate(time_hours=48, key_distribution="uniform", num_threads=16)
    print(f"48시간 후 예측 Put 속도: {prediction['put_rate_ops_sec']:.2f} ops/sec")
    
    # 안정화 예측
    stabilization = model.predict_stabilization()
    print(f"안정화 예측: {stabilization}")
    
    # 모델 저장
    model.save_model("v5_model_test.json")

if __name__ == "__main__":
    main()
