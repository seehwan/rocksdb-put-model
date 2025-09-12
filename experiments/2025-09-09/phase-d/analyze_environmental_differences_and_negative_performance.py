#!/usr/bin/env python3
"""
환경별 차이와 음수 성능 분석
장치 대역폭 차이와 음수 성능이 나오는 원인 분석
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

class EnvironmentalDifferenceAnalyzer:
    """환경별 차이와 음수 성능 분석 클래스"""
    
    def __init__(self):
        self.experiment_data = {}
        self.device_analysis = {}
        self.performance_analysis = {}
        self.load_actual_data()
        self.analyze_device_differences()
        self.analyze_negative_performance()
        self.identify_calculation_errors()
    
    def load_actual_data(self):
        """실제 실험 데이터 로드"""
        print("=== 실제 실험 데이터 로드 ===")
        
        # 실제 실험 데이터 (원본)
        self.experiment_data = {
            '2025-09-05': {
                'device': '/dev/nvme1n1p1',
                'device_bandwidth': 1556.0,  # MB/s
                'actual_throughput': 196.2,  # MB/s
                'actual_efficiency': 196.2 / 1556.0,  # 0.1261 (12.61%)
                'duration_hours': 17,
                'operations': 3.2e9,
                'workload': 'fillrandom'
            },
            '2025-09-08': {
                'device': '/dev/nvme1n1p1',
                'device_bandwidth': 1490.0,  # MB/s
                'actual_throughput': 157.5,  # MB/s
                'actual_efficiency': 157.5 / 1490.0,  # 0.1057 (10.57%)
                'duration_hours': 8,
                'operations': 3.2e9,
                'workload': 'fillrandom'
            },
            '2025-09-09': {
                'device': '/dev/nvme1n1p2',
                'device_bandwidth': 3005.8,  # MB/s
                'actual_throughput': 30.1,  # MB/s
                'actual_efficiency': 30.1 / 3005.8,  # 0.0100 (1.00%)
                'duration_hours': 36.5,
                'operations': 4e9,
                'workload': 'fillrandom'
            }
        }
        
        print("실제 실험 데이터:")
        for exp_date, exp_data in self.experiment_data.items():
            print(f"  {exp_date}:")
            print(f"    장치: {exp_data['device']}")
            print(f"    장치 대역폭: {exp_data['device_bandwidth']:.1f} MB/s")
            print(f"    실제 처리량: {exp_data['actual_throughput']:.1f} MB/s")
            print(f"    실제 효율성: {exp_data['actual_efficiency']:.4f} ({exp_data['actual_efficiency']*100:.2f}%)")
            print(f"    지속시간: {exp_data['duration_hours']:.1f}시간")
    
    def analyze_device_differences(self):
        """장치 차이 분석"""
        print("\n=== 장치 차이 분석 ===")
        
        # 장치별 분석
        device_analysis = {}
        
        for exp_date, exp_data in self.experiment_data.items():
            device = exp_data['device']
            bandwidth = exp_data['device_bandwidth']
            throughput = exp_data['actual_throughput']
            efficiency = exp_data['actual_efficiency']
            
            if device not in device_analysis:
                device_analysis[device] = {
                    'experiments': [],
                    'bandwidths': [],
                    'throughputs': [],
                    'efficiencies': []
                }
            
            device_analysis[device]['experiments'].append(exp_date)
            device_analysis[device]['bandwidths'].append(bandwidth)
            device_analysis[device]['throughputs'].append(throughput)
            device_analysis[device]['efficiencies'].append(efficiency)
        
        print("장치별 분석:")
        for device, analysis in device_analysis.items():
            print(f"\n{device}:")
            print(f"  실험들: {', '.join(analysis['experiments'])}")
            print(f"  대역폭들: {analysis['bandwidths']} MB/s")
            print(f"  처리량들: {analysis['throughputs']} MB/s")
            print(f"  효율성들: {[f'{eff:.4f} ({eff*100:.2f}%)' for eff in analysis['efficiencies']]}")
            
            # 장치별 통계
            if len(analysis['bandwidths']) > 1:
                bandwidth_std = np.std(analysis['bandwidths'])
                bandwidth_cv = bandwidth_std / np.mean(analysis['bandwidths'])
                print(f"  대역폭 변동계수: {bandwidth_cv:.4f}")
            
            if len(analysis['efficiencies']) > 1:
                efficiency_std = np.std(analysis['efficiencies'])
                efficiency_cv = efficiency_std / np.mean(analysis['efficiencies'])
                print(f"  효율성 변동계수: {efficiency_cv:.4f}")
        
        # 장치 간 차이 분석
        print(f"\n=== 장치 간 차이 분석 ===")
        
        devices = list(device_analysis.keys())
        if len(devices) >= 2:
            for i in range(len(devices)):
                for j in range(i+1, len(devices)):
                    device1 = devices[i]
                    device2 = devices[j]
                    
                    device1_bandwidth = np.mean(device_analysis[device1]['bandwidths'])
                    device2_bandwidth = np.mean(device_analysis[device2]['bandwidths'])
                    device1_efficiency = np.mean(device_analysis[device1]['efficiencies'])
                    device2_efficiency = np.mean(device_analysis[device2]['efficiencies'])
                    
                    bandwidth_ratio = device1_bandwidth / device2_bandwidth
                    efficiency_ratio = device1_efficiency / device2_efficiency
                    
                    print(f"{device1} vs {device2}:")
                    print(f"  대역폭 비율: {bandwidth_ratio:.2f}x")
                    print(f"  효율성 비율: {efficiency_ratio:.2f}x")
                    print(f"  대역폭 차이: {abs(device1_bandwidth - device2_bandwidth):.1f} MB/s")
                    print(f"  효율성 차이: {abs(device1_efficiency - device2_efficiency):.4f}")
        
        self.device_analysis = device_analysis
    
    def analyze_negative_performance(self):
        """음수 성능 분석"""
        print("\n=== 음수 성능 분석 ===")
        
        # v5 모델에서 음수 성능이 나온 계산 과정 재분석
        print("v5 모델에서 음수 성능이 나온 계산 과정:")
        
        for exp_date, exp_data in self.experiment_data.items():
            print(f"\n{exp_date} 실험:")
            
            actual_throughput = exp_data['actual_throughput']
            duration_hours = exp_data['duration_hours']
            
            # v5 모델의 단계별 가중치 (시간 기반)
            initial_time = 0.167  # 10분
            transitional_time = 0.833  # 50분
            
            if duration_hours <= initial_time:
                w_i = 1.0
                w_t = 0.0
                w_s = 0.0
            elif duration_hours <= 1.0:
                w_i = initial_time / duration_hours
                w_t = (duration_hours - initial_time) / duration_hours
                w_s = 0.0
            else:
                w_i = initial_time / duration_hours
                w_t = transitional_time / duration_hours
                w_s = (duration_hours - 1.0) / duration_hours
            
            print(f"  단계별 가중치:")
            print(f"    초기 단계: {w_i:.4f}")
            print(f"    전환 단계: {w_t:.4f}")
            print(f"    안정화 단계: {w_s:.4f}")
            
            # v5 모델의 단계별 성능
            initial_performance = 1853.0  # MB/s
            transitional_performance = 1280.5  # MB/s
            stable_performance = 20.2  # MB/s
            
            # 단계별 기여도 계산
            initial_contribution = initial_performance * w_i
            transitional_contribution = transitional_performance * w_t
            stable_contribution = stable_performance * w_s
            
            print(f"  단계별 기여도:")
            print(f"    초기 단계: {initial_performance:.1f} × {w_i:.4f} = {initial_contribution:.1f} MB/s")
            print(f"    전환 단계: {transitional_performance:.1f} × {w_t:.4f} = {transitional_contribution:.1f} MB/s")
            print(f"    안정화 단계: {stable_performance:.1f} × {w_s:.4f} = {stable_contribution:.1f} MB/s")
            
            # 예측 처리량
            predicted_throughput = initial_contribution + transitional_contribution + stable_contribution
            
            print(f"  예측 처리량: {predicted_throughput:.1f} MB/s")
            print(f"  실제 처리량: {actual_throughput:.1f} MB/s")
            
            # 안정화 구간 실제 성능 역산 (문제가 되는 부분)
            if w_s > 0:
                # actual = w_i * initial + w_t * transitional + w_s * stable
                # stable = (actual - w_i * initial - w_t * transitional) / w_s
                
                stable_actual = (actual_throughput - initial_contribution - transitional_contribution) / w_s
                
                print(f"  안정화 구간 실제 성능 역산:")
                print(f"    계산: ({actual_throughput:.1f} - {initial_contribution:.1f} - {transitional_contribution:.1f}) / {w_s:.4f}")
                print(f"    결과: {stable_actual:.1f} MB/s")
                
                if stable_actual < 0:
                    print(f"    ❌ 음수 성능 발생!")
                    print(f"    원인: 초기/전환 단계 기여도가 실제 처리량보다 큼")
                    print(f"    문제: 단계별 성능 모델이 부정확함")
    
    def identify_calculation_errors(self):
        """계산 오류 식별"""
        print("\n=== 계산 오류 식별 ===")
        
        calculation_errors = {
            'phase_performance_assumption': {
                'description': '단계별 성능 가정의 오류',
                'problem': '초기 단계 1,853 MB/s, 전환 단계 1,280.5 MB/s는 비현실적',
                'evidence': '실제 전체 성능이 30.1-196.2 MB/s인데 단계별 성능이 더 높음',
                'impact': 'Critical'
            },
            'phase_weight_calculation': {
                'description': '단계별 가중치 계산의 오류',
                'problem': '시간 기반 가중치만 사용하여 실제 성능 변화 무시',
                'evidence': '안정화 구간이 97.3% 비중이지만 실제로는 더 높은 성능',
                'impact': 'High'
            },
            'phase_separation_assumption': {
                'description': '단계 분리 가정의 오류',
                'problem': '전체 성능을 단계별로 분리할 수 있다고 가정',
                'evidence': '실제로는 단계별 성능을 직접 측정할 수 없음',
                'impact': 'Medium'
            },
            'negative_performance_calculation': {
                'description': '음수 성능 계산의 오류',
                'problem': '역산 계산에서 음수 성능이 나옴',
                'evidence': '초기/전환 단계 기여도가 실제 처리량보다 큼',
                'impact': 'Critical'
            }
        }
        
        print("계산 오류들:")
        for error_name, error_info in calculation_errors.items():
            print(f"\n{error_name}:")
            print(f"  설명: {error_info['description']}")
            print(f"  문제: {error_info['problem']}")
            print(f"  증거: {error_info['evidence']}")
            print(f"  영향도: {error_info['impact']}")
        
        # 실제 문제점 요약
        print(f"\n=== 실제 문제점 요약 ===")
        print("1. 단계별 성능 가정이 비현실적:")
        print("   - 초기 단계 1,853 MB/s (실제 전체 성능보다 9배 높음)")
        print("   - 전환 단계 1,280.5 MB/s (실제 전체 성능보다 6배 높음)")
        print("   - 안정화 단계 20.2 MB/s (고정값)")
        
        print("\n2. 시간 기반 가중치의 한계:")
        print("   - 실제 성능 변화 패턴 무시")
        print("   - 환경별 차이 반영 부족")
        print("   - 단순한 선형 가중치")
        
        print("\n3. 단계 분리 가정의 문제:")
        print("   - 전체 성능을 단계별로 분리할 수 없다고 가정")
        print("   - 실제로는 단계별 성능을 직접 측정할 수 없음")
        print("   - 역산 방법의 부정확성")
        
        print("\n4. 음수 성능 발생 원인:")
        print("   - 초기/전환 단계 기여도가 실제 처리량보다 큼")
        print("   - 단계별 성능 모델이 부정확함")
        print("   - 가정과 현실의 불일치")
    
    def propose_corrected_approach(self):
        """수정된 접근법 제안"""
        print("\n=== 수정된 접근법 제안 ===")
        
        corrected_approach = {
            'realistic_phase_performance': {
                'title': '현실적인 단계별 성능',
                'description': '실제 측정값에 기반한 단계별 성능',
                'method': '전체 성능을 기준으로 단계별 성능을 현실적으로 추정',
                'example': {
                    'initial_phase': '전체 성능의 1.5-2배 (30-60 MB/s)',
                    'transitional_phase': '전체 성능의 1.0-1.5배 (20-40 MB/s)',
                    'stable_phase': '전체 성능과 동일 (10-30 MB/s)'
                }
            },
            'environmental_aware_modeling': {
                'title': '환경 인식 모델링',
                'description': '환경별 차이를 반영한 모델링',
                'method': '장치별, 파티션별 성능 특성 고려',
                'example': {
                    'device_bandwidth_factor': '장치 대역폭에 비례한 성능',
                    'partition_factor': '파티션별 성능 차이',
                    'system_factor': '시스템 상태별 성능 차이'
                }
            },
            'empirical_phase_modeling': {
                'title': '경험적 단계 모델링',
                'description': '실제 측정값에 기반한 단계 모델링',
                'method': '이론적 가정보다는 실제 데이터 기반',
                'example': {
                    'measured_efficiency': '실제 측정된 효율성 사용',
                    'time_decay_factor': '시간에 따른 성능 저하 패턴',
                    'environmental_factor': '환경별 성능 차이'
                }
            }
        }
        
        print("수정된 접근법들:")
        for approach_name, approach_info in corrected_approach.items():
            print(f"\n{approach_name}:")
            print(f"  제목: {approach_info['title']}")
            print(f"  설명: {approach_info['description']}")
            print(f"  방법: {approach_info['method']}")
            print(f"  예시:")
            for key, value in approach_info['example'].items():
                print(f"    {key}: {value}")
    
    def save_analysis_results(self):
        """분석 결과 저장"""
        print("\n=== 분석 결과 저장 ===")
        
        analysis_results = {
            'analysis_info': {
                'title': 'Environmental Differences and Negative Performance Analysis',
                'date': '2025-09-09',
                'purpose': '환경별 차이와 음수 성능 발생 원인 분석'
            },
            'experiment_data': self.experiment_data,
            'device_analysis': self.device_analysis,
            'key_insights': [
                '장치 대역폭 차이의 실제 원인: 파티션 차이 (p1 vs p2)',
                '음수 성능 발생 원인: 단계별 성능 가정이 비현실적',
                '초기/전환 단계 성능이 실제 전체 성능보다 높게 설정됨',
                '시간 기반 가중치의 한계: 실제 성능 변화 패턴 무시',
                '단계 분리 가정의 문제: 전체 성능을 단계별로 분리 불가',
                '역산 계산의 오류: 가정과 현실의 불일치',
                '환경 인식 모델링 필요'
            ]
        }
        
        # JSON 파일로 저장
        output_file = Path("environmental_differences_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"분석 결과가 {output_file}에 저장되었습니다.")
        
        return analysis_results

def main():
    """메인 함수"""
    print("=== 환경별 차이와 음수 성능 분석 ===")
    
    # 분석기 생성
    analyzer = EnvironmentalDifferenceAnalyzer()
    
    # 수정된 접근법 제안
    analyzer.propose_corrected_approach()
    
    # 분석 결과 저장
    results = analyzer.save_analysis_results()
    
    print(f"\n=== 분석 완료 ===")
    print("핵심 발견사항:")
    print("1. 장치 대역폭 차이의 실제 원인: 파티션 차이 (p1 vs p2)")
    print("2. 음수 성능 발생 원인: 단계별 성능 가정이 비현실적")
    print("3. 초기/전환 단계 성능이 실제 전체 성능보다 높게 설정됨")
    print("4. 시간 기반 가중치의 한계: 실제 성능 변화 패턴 무시")
    print("5. 단계 분리 가정의 문제: 전체 성능을 단계별로 분리 불가")
    print("6. 역산 계산의 오류: 가정과 현실의 불일치")
    print("7. 환경 인식 모델링 필요")

if __name__ == "__main__":
    main()


