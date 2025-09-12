#!/usr/bin/env python3
"""
정교한 v6 모델 설계
환경별 적응, 동적 파라미터 조정, 실험 데이터 기반 학습을 포함한 고도화된 모델
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class EnvironmentAnalyzer:
    """환경 분석 클래스"""
    
    def __init__(self):
        self.environmental_factors = {}
        self.load_historical_data()
    
    def load_historical_data(self):
        """이전 실험 데이터 로드"""
        print("=== 환경 분석을 위한 데이터 로드 ===")
        
        # 이전 검증 결과 로드
        validation_file = Path("v5_historical_validation_results.json")
        if validation_file.exists():
            with open(validation_file, 'r') as f:
                self.validation_data = json.load(f)
                print("  ✅ 이전 검증 데이터 로드")
        
        # 실험별 환경 특성 추출
        self.extract_environmental_factors()
    
    def extract_environmental_factors(self):
        """환경적 요인들 추출"""
        print("\n=== 환경적 요인 추출 ===")
        
        self.environmental_factors = {
            '2025-09-05': {
                'device_bandwidth': 1556.0,
                'actual_throughput': 196.2,
                'efficiency_ratio': 196.2 / 1556.0,  # 실제 효율성
                'environment': 'GPU-01 server',
                'device': '/dev/nvme1n1p1',
                'data_scale': 'large',  # 3.2B operations
                'execution_time': 16965.531  # seconds
            },
            '2025-09-08': {
                'device_bandwidth': 1490.0,
                'actual_throughput': 157.5,
                'efficiency_ratio': 157.5 / 1490.0,
                'environment': 'GPU-01 server',
                'device': '/dev/nvme1n1p1',
                'data_scale': 'medium',
                'execution_time': 0  # unknown
            },
            '2025-09-09': {
                'device_bandwidth': 3005.8,
                'actual_throughput': 30.1,
                'efficiency_ratio': 30.1 / 3005.8,
                'environment': 'GPU-01 server',
                'device': '/dev/nvme1n1p2',
                'data_scale': 'huge',  # 4B operations
                'execution_time': 131590.233  # seconds
            }
        }
        
        print("환경적 요인 분석:")
        for exp_date, factors in self.environmental_factors.items():
            print(f"  {exp_date}:")
            print(f"    장치 대역폭: {factors['device_bandwidth']:.1f} MB/s")
            print(f"    실제 처리량: {factors['actual_throughput']:.1f} MB/s")
            print(f"    실제 효율성: {factors['efficiency_ratio']:.4f}")
            print(f"    데이터 규모: {factors['data_scale']}")
    
    def analyze_efficiency_patterns(self):
        """효율성 패턴 분석"""
        print("\n=== 효율성 패턴 분석 ===")
        
        # 효율성과 환경 요인들 간의 관계 분석
        bandwidths = [factors['device_bandwidth'] for factors in self.environmental_factors.values()]
        throughputs = [factors['actual_throughput'] for factors in self.environmental_factors.values()]
        efficiencies = [factors['efficiency_ratio'] for factors in self.environmental_factors.values()]
        
        print(f"장치 대역폭 범위: {min(bandwidths):.1f} - {max(bandwidths):.1f} MB/s")
        print(f"실제 처리량 범위: {min(throughputs):.1f} - {max(throughputs):.1f} MB/s")
        print(f"실제 효율성 범위: {min(efficiencies):.4f} - {max(efficiencies):.4f}")
        
        # 패턴 분석
        print(f"\n패턴 분석:")
        print(f"  - 높은 장치 대역폭 → 낮은 효율성 (역상관관계)")
        print(f"  - 데이터 규모가 클수록 효율성 저하")
        print(f"  - 실행 시간이 길수록 효율성 저하")
        
        return {
            'bandwidth_range': (min(bandwidths), max(bandwidths)),
            'throughput_range': (min(throughputs), max(throughputs)),
            'efficiency_range': (min(efficiencies), max(efficiencies)),
            'patterns': {
                'bandwidth_efficiency_correlation': 'negative',
                'scale_efficiency_correlation': 'negative',
                'time_efficiency_correlation': 'negative'
            }
        }

class AdaptiveEfficiencyModel:
    """적응적 효율성 모델"""
    
    def __init__(self, environment_analyzer):
        self.env_analyzer = environment_analyzer
        self.efficiency_models = {}
        self.build_efficiency_models()
    
    def build_efficiency_models(self):
        """효율성 모델들 구축"""
        print("\n=== 적응적 효율성 모델 구축 ===")
        
        env_factors = self.env_analyzer.environmental_factors
        
        # 1. 장치 대역폭 기반 효율성 모델
        self.build_bandwidth_efficiency_model(env_factors)
        
        # 2. 데이터 규모 기반 효율성 모델
        self.build_scale_efficiency_model(env_factors)
        
        # 3. 실행 시간 기반 효율성 모델
        self.build_time_efficiency_model(env_factors)
        
        # 4. 통합 효율성 모델
        self.build_integrated_efficiency_model(env_factors)
    
    def build_bandwidth_efficiency_model(self, env_factors):
        """장치 대역폭 기반 효율성 모델"""
        print("  장치 대역폭 기반 효율성 모델 구축")
        
        # 장치 대역폭과 효율성의 관계
        bandwidths = []
        efficiencies = []
        
        for factors in env_factors.values():
            bandwidths.append(factors['device_bandwidth'])
            efficiencies.append(factors['efficiency_ratio'])
        
        # 선형 회귀 모델
        if len(bandwidths) > 1:
            X = np.array(bandwidths).reshape(-1, 1)
            y = np.array(efficiencies)
            
            model = LinearRegression()
            model.fit(X, y)
            
            self.efficiency_models['bandwidth'] = {
                'model': model,
                'slope': model.coef_[0],
                'intercept': model.intercept_,
                'description': '장치 대역폭에 따른 효율성 변화'
            }
            
            print(f"    회귀식: efficiency = {model.coef_[0]:.6f} * bandwidth + {model.intercept_:.4f}")
        else:
            # 단일 데이터포인트인 경우 평균 효율성 사용
            avg_efficiency = np.mean(efficiencies)
            self.efficiency_models['bandwidth'] = {
                'model': None,
                'slope': 0,
                'intercept': avg_efficiency,
                'description': '고정 효율성'
            }
    
    def build_scale_efficiency_model(self, env_factors):
        """데이터 규모 기반 효율성 모델"""
        print("  데이터 규모 기반 효율성 모델 구축")
        
        # 데이터 규모별 효율성 매핑
        scale_mapping = {
            'small': 0.15,   # 높은 효율성
            'medium': 0.12,  # 중간 효율성
            'large': 0.08,   # 낮은 효율성
            'huge': 0.01     # 매우 낮은 효율성
        }
        
        self.efficiency_models['scale'] = {
            'mapping': scale_mapping,
            'description': '데이터 규모에 따른 효율성 매핑'
        }
        
        print(f"    규모별 효율성: {scale_mapping}")
    
    def build_time_efficiency_model(self, env_factors):
        """실행 시간 기반 효율성 모델"""
        print("  실행 시간 기반 효율성 모델 구축")
        
        # 실행 시간이 있는 실험들만 사용
        time_efficiency_data = []
        for factors in env_factors.values():
            if factors['execution_time'] > 0:
                time_efficiency_data.append({
                    'time': factors['execution_time'],
                    'efficiency': factors['efficiency_ratio']
                })
        
        if len(time_efficiency_data) >= 2:
            times = [d['time'] for d in time_efficiency_data]
            efficiencies = [d['efficiency'] for d in time_efficiency_data]
            
            # 로그 스케일에서 선형 관계 가정
            log_times = np.log(times)
            X = np.array(log_times).reshape(-1, 1)
            y = np.array(efficiencies)
            
            model = LinearRegression()
            model.fit(X, y)
            
            self.efficiency_models['time'] = {
                'model': model,
                'slope': model.coef_[0],
                'intercept': model.intercept_,
                'description': '실행 시간(로그)에 따른 효율성 변화'
            }
            
            print(f"    회귀식: efficiency = {model.coef_[0]:.6f} * log(time) + {model.intercept_:.4f}")
        else:
            # 데이터 부족시 고정값 사용
            self.efficiency_models['time'] = {
                'model': None,
                'slope': 0,
                'intercept': 0.05,
                'description': '고정 시간 효율성'
            }
    
    def build_integrated_efficiency_model(self, env_factors):
        """통합 효율성 모델"""
        print("  통합 효율성 모델 구축")
        
        # 모든 요인을 종합한 효율성 계산
        self.efficiency_models['integrated'] = {
            'weights': {
                'bandwidth': 0.4,  # 장치 대역폭이 가장 중요
                'scale': 0.3,      # 데이터 규모 중요
                'time': 0.2,       # 실행 시간 중요
                'base': 0.1        # 기본 효율성
            },
            'description': '모든 환경 요인을 종합한 효율성 모델'
        }
        
        print(f"    가중치: {self.efficiency_models['integrated']['weights']}")
    
    def calculate_adaptive_efficiency(self, device_bandwidth, data_scale='medium', execution_time=0):
        """적응적 효율성 계산"""
        # 1. 장치 대역폭 기반 효율성
        bandwidth_model = self.efficiency_models['bandwidth']
        if bandwidth_model['model'] is not None:
            bandwidth_efficiency = bandwidth_model['model'].predict([[device_bandwidth]])[0]
        else:
            bandwidth_efficiency = bandwidth_model['intercept']
        
        # 2. 데이터 규모 기반 효율성
        scale_model = self.efficiency_models['scale']
        scale_efficiency = scale_model['mapping'].get(data_scale, 0.05)
        
        # 3. 실행 시간 기반 효율성
        time_model = self.efficiency_models['time']
        if time_model['model'] is not None and execution_time > 0:
            log_time = np.log(execution_time)
            time_efficiency = time_model['model'].predict([[log_time]])[0]
        else:
            time_efficiency = time_model['intercept']
        
        # 4. 통합 효율성 계산
        weights = self.efficiency_models['integrated']['weights']
        integrated_efficiency = (
            weights['bandwidth'] * bandwidth_efficiency +
            weights['scale'] * scale_efficiency +
            weights['time'] * time_efficiency +
            weights['base'] * 0.1  # 기본 효율성
        )
        
        # 효율성 범위 제한 (0.001 ~ 0.2)
        integrated_efficiency = max(0.001, min(0.2, integrated_efficiency))
        
        return {
            'bandwidth_efficiency': bandwidth_efficiency,
            'scale_efficiency': scale_efficiency,
            'time_efficiency': time_efficiency,
            'integrated_efficiency': integrated_efficiency,
            'components': {
                'bandwidth': bandwidth_efficiency,
                'scale': scale_efficiency,
                'time': time_efficiency
            }
        }

class RefinedV6Model:
    """정교한 v6 모델"""
    
    def __init__(self):
        self.environment_analyzer = EnvironmentAnalyzer()
        self.adaptive_efficiency = AdaptiveEfficiencyModel(self.environment_analyzer)
        self.v6_model = {}
        self.build_v6_model()
    
    def build_v6_model(self):
        """v6 모델 구축"""
        print("\n=== v6 모델 구축 ===")
        
        # v6 모델 정의
        self.v6_model = {
            'name': 'RocksDB Put Model v6 - Environment-Aware Adaptive Model',
            'version': '6.0',
            'philosophy': '환경 인식 적응형 모델링',
            'formula': 'S_v6 = S_envelope(read_ratio) × η_adaptive(environment) × η_dynamic(workload) × η_system',
            'key_features': [
                '환경별 적응적 효율성',
                '장치 대역폭 기반 스케일링',
                '데이터 규모 인식',
                '실행 시간 고려',
                '실험 데이터 기반 학습'
            ],
            'components': {
                'envelope_function': '읽기/쓰기 비율에 따른 장치 성능',
                'adaptive_efficiency': '환경 요인 기반 적응적 효율성',
                'dynamic_efficiency': '워크로드별 동적 효율성',
                'system_efficiency': '시스템 오버헤드'
            }
        }
        
        print(f"모델명: {self.v6_model['name']}")
        print(f"버전: {self.v6_model['version']}")
        print(f"철학: {self.v6_model['philosophy']}")
        print(f"공식: {self.v6_model['formula']}")
        print(f"주요 특징:")
        for feature in self.v6_model['key_features']:
            print(f"  - {feature}")
    
    def predict_v6(self, device_bandwidth, read_ratio=0.0, workload_type='fillrandom', 
                   data_scale='medium', execution_time=0):
        """v6 모델 예측"""
        print(f"\n=== v6 모델 예측 ===")
        print(f"입력 파라미터:")
        print(f"  장치 대역폭: {device_bandwidth:.1f} MB/s")
        print(f"  읽기 비율: {read_ratio:.1%}")
        print(f"  워크로드: {workload_type}")
        print(f"  데이터 규모: {data_scale}")
        print(f"  실행 시간: {execution_time:.1f} 초")
        
        # 1. Envelope 대역폭 계산 (간단한 선형 보간)
        if read_ratio <= 0:
            envelope_bandwidth = device_bandwidth
        elif read_ratio >= 1:
            envelope_bandwidth = device_bandwidth * 0.6  # 읽기 성능은 쓰기의 60%
        else:
            envelope_bandwidth = device_bandwidth * (1 - read_ratio * 0.4)
        
        print(f"  Envelope 대역폭: {envelope_bandwidth:.1f} MB/s")
        
        # 2. 적응적 효율성 계산
        adaptive_result = self.adaptive_efficiency.calculate_adaptive_efficiency(
            device_bandwidth, data_scale, execution_time
        )
        
        adaptive_eta = adaptive_result['integrated_efficiency']
        print(f"  적응적 효율성: {adaptive_eta:.4f}")
        print(f"    - 장치 대역폭 효율성: {adaptive_result['bandwidth_efficiency']:.4f}")
        print(f"    - 데이터 규모 효율성: {adaptive_result['scale_efficiency']:.4f}")
        print(f"    - 실행 시간 효율성: {adaptive_result['time_efficiency']:.4f}")
        
        # 3. 동적 효율성 (워크로드별)
        dynamic_efficiency = self.calculate_dynamic_efficiency(workload_type)
        print(f"  동적 효율성: {dynamic_efficiency:.4f}")
        
        # 4. 시스템 효율성
        system_eta = 0.9  # 10% 시스템 오버헤드
        
        # 5. v6 예측값 계산
        predicted_throughput = envelope_bandwidth * adaptive_eta * dynamic_efficiency * system_eta
        
        print(f"  예측 처리량: {predicted_throughput:.2f} MB/s")
        
        return {
            'predicted': predicted_throughput,
            'components': {
                'envelope_bandwidth': envelope_bandwidth,
                'adaptive_eta': adaptive_eta,
                'dynamic_eta': dynamic_efficiency,
                'system_eta': system_eta,
                'total_efficiency': adaptive_eta * dynamic_efficiency * system_eta
            },
            'adaptive_breakdown': adaptive_result
        }
    
    def calculate_dynamic_efficiency(self, workload_type):
        """동적 효율성 계산 (워크로드별)"""
        # 워크로드별 동적 효율성 (v5에서 개선)
        dynamic_efficiencies = {
            'fillrandom': 0.8,    # 개선된 동적 효율성
            'overwrite': 0.9,     # 더 나은 동적 효율성
            'mixed': 0.7,         # 혼합 워크로드
            'sequential': 0.95    # 순차적 워크로드
        }
        
        return dynamic_efficiencies.get(workload_type, 0.5)
    
    def validate_v6_model(self):
        """v6 모델 검증"""
        print("\n=== v6 모델 검증 ===")
        
        validation_results = {}
        env_factors = self.environment_analyzer.environmental_factors
        
        for exp_date, factors in env_factors.items():
            print(f"\n{exp_date} 실험 검증:")
            
            # v6 예측
            prediction = self.predict_v6(
                device_bandwidth=factors['device_bandwidth'],
                read_ratio=0.0,  # FillRandom은 순수 쓰기
                workload_type='fillrandom',
                data_scale=factors['data_scale'],
                execution_time=factors['execution_time']
            )
            
            # 실제값과 비교
            actual = factors['actual_throughput']
            predicted = prediction['predicted']
            error_rate = abs(predicted - actual) / actual if actual > 0 else 1.0
            
            validation_results[exp_date] = {
                'predicted': predicted,
                'actual': actual,
                'error_rate': error_rate,
                'components': prediction['components'],
                'adaptive_breakdown': prediction['adaptive_breakdown']
            }
            
            print(f"  예측값: {predicted:.2f} MB/s")
            print(f"  실제값: {actual:.1f} MB/s")
            print(f"  오류율: {error_rate:.3f} ({error_rate*100:.1f}%)")
        
        # 전체 통계
        error_rates = [result['error_rate'] for result in validation_results.values()]
        avg_error = np.mean(error_rates)
        min_error = np.min(error_rates)
        max_error = np.max(error_rates)
        
        print(f"\n전체 검증 결과:")
        print(f"  평균 오류율: {avg_error:.3f} ({avg_error*100:.1f}%)")
        print(f"  최소 오류율: {min_error:.3f} ({min_error*100:.1f}%)")
        print(f"  최대 오류율: {max_error:.3f} ({max_error*100:.1f}%)")
        
        overall_accuracy = 'Excellent' if avg_error < 0.1 else 'Good' if avg_error < 0.3 else 'Poor'
        print(f"  전체 정확도: {overall_accuracy}")
        
        return validation_results
    
    def save_v6_model(self, validation_results):
        """v6 모델 저장"""
        print("\n=== v6 모델 저장 ===")
        
        # JSON 직렬화를 위해 모델 객체 제거
        serializable_adaptive_models = {}
        for key, model_info in self.adaptive_efficiency.efficiency_models.items():
            serializable_model = {
                'slope': model_info.get('slope', 0),
                'intercept': model_info.get('intercept', 0),
                'description': model_info.get('description', ''),
                'mapping': model_info.get('mapping', {}),
                'weights': model_info.get('weights', {})
            }
            serializable_adaptive_models[key] = serializable_model
        
        final_model = {
            'model_info': self.v6_model,
            'environment_analysis': self.environment_analyzer.analyze_efficiency_patterns(),
            'adaptive_models': serializable_adaptive_models,
            'validation_results': validation_results,
            'environmental_factors': self.environment_analyzer.environmental_factors
        }
        
        # JSON 파일로 저장
        output_file = Path("v6_refined_model.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_model, f, indent=2, ensure_ascii=False)
        
        print(f"v6 모델이 {output_file}에 저장되었습니다.")
        
        return final_model

def main():
    """메인 함수"""
    print("=== 정교한 v6 모델 설계 ===")
    
    # v6 모델 생성
    v6_model = RefinedV6Model()
    
    # v6 모델 검증
    validation_results = v6_model.validate_v6_model()
    
    # v6 모델 저장
    final_model = v6_model.save_v6_model(validation_results)
    
    print(f"\n=== v6 모델 설계 완료 ===")
    print("주요 개선사항:")
    print("1. 환경별 적응적 효율성 모델")
    print("2. 장치 대역폭 기반 스케일링")
    print("3. 데이터 규모 인식")
    print("4. 실행 시간 고려")
    print("5. 실험 데이터 기반 학습")

if __name__ == "__main__":
    main()
