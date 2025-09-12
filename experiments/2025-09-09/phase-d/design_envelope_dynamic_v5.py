#!/usr/bin/env python3
"""
Envelope + 동적 모델을 고려한 v5 모델 개선
장치 envelope 모델과 RocksDB 동적 모델을 통합한 개선된 v5 모델을 설계합니다.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

class DeviceEnvelopeModel:
    """장치 Envelope 모델 클래스"""
    
    def __init__(self):
        self.envelope_data = {}
        self.load_envelope_data()
    
    def load_envelope_data(self):
        """장치 envelope 데이터를 로드합니다."""
        print("=== 장치 Envelope 데이터 로드 ===")
        
        # 다양한 읽기/쓰기 비율의 fio 데이터
        envelope_files = {
            '0_read': 'result_0_1_1_1024.json',      # 순수 쓰기
            '25_read': 'result_25_4_2_64.json',      # 25% 읽기
            '50_read': 'result_50_4_2_64.json',      # 50% 읽기  
            '75_read': 'result_75_4_2_64.json',      # 75% 읽기
            '100_read': 'result_100_1_1_1024.json',  # 순수 읽기
        }
        
        device_dir = Path("../phase-a/device_envelope_results")
        
        for test_name, filename in envelope_files.items():
            file_path = device_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.envelope_data[test_name] = data
                    print(f"  ✅ {test_name}: {filename}")
            else:
                print(f"  ❌ {test_name}: {filename} 없음")
    
    def analyze_envelope_characteristics(self):
        """장치 envelope 특성을 분석합니다."""
        print("\n=== 장치 Envelope 특성 분석 ===")
        
        envelope_chars = {}
        
        for test_name, data in self.envelope_data.items():
            job = data['jobs'][0]
            
            # 읽기/쓰기 비율 추출
            read_ratio = int(test_name.split('_')[0]) / 100.0 if test_name != '0_read' else 0.0
            
            # 성능 데이터 추출
            read_bw = job['read']['bw'] / 1024 if job['read']['bw'] > 0 else 0  # KB/s to MB/s
            write_bw = job['write']['bw'] / 1024 if job['write']['bw'] > 0 else 0  # KB/s to MB/s
            total_bw = read_bw + write_bw
            
            envelope_chars[test_name] = {
                'read_ratio': read_ratio,
                'read_bandwidth': read_bw,
                'write_bandwidth': write_bw,
                'total_bandwidth': total_bw,
                'read_iops': job['read']['iops'],
                'write_iops': job['write']['iops'],
                'total_iops': job['read']['iops'] + job['write']['iops']
            }
            
            print(f"{test_name}:")
            print(f"  읽기 비율: {read_ratio:.1%}")
            print(f"  읽기 대역폭: {read_bw:.1f} MB/s")
            print(f"  쓰기 대역폭: {write_bw:.1f} MB/s")
            print(f"  총 대역폭: {total_bw:.1f} MB/s")
        
        return envelope_chars
    
    def build_envelope_function(self, envelope_chars):
        """장치 envelope 함수를 구축합니다."""
        print("\n=== 장치 Envelope 함수 구축 ===")
        
        # 읽기 비율별 총 대역폭 데이터
        read_ratios = []
        total_bandwidths = []
        
        for test_name, chars in envelope_chars.items():
            read_ratios.append(chars['read_ratio'])
            total_bandwidths.append(chars['total_bandwidth'])
        
        # 데이터 정렬
        sorted_data = sorted(zip(read_ratios, total_bandwidths))
        read_ratios_sorted = [x[0] for x in sorted_data]
        total_bandwidths_sorted = [x[1] for x in sorted_data]
        
        print("읽기 비율별 총 대역폭:")
        for ratio, bw in sorted_data:
            print(f"  {ratio:.1%} 읽기: {bw:.1f} MB/s")
        
        # Envelope 함수 정의 (선형 보간)
        def envelope_function(read_ratio):
            """읽기 비율에 따른 총 대역폭 함수"""
            if read_ratio <= read_ratios_sorted[0]:
                return total_bandwidths_sorted[0]
            elif read_ratio >= read_ratios_sorted[-1]:
                return total_bandwidths_sorted[-1]
            else:
                # 선형 보간
                for i in range(len(read_ratios_sorted) - 1):
                    if read_ratios_sorted[i] <= read_ratio <= read_ratios_sorted[i + 1]:
                        x1, y1 = read_ratios_sorted[i], total_bandwidths_sorted[i]
                        x2, y2 = read_ratios_sorted[i + 1], total_bandwidths_sorted[i + 1]
                        return y1 + (y2 - y1) * (read_ratio - x1) / (x2 - x1)
        
        return envelope_function

class RocksDBDynamicModel:
    """RocksDB 동적 모델 클래스"""
    
    def __init__(self):
        self.dynamic_factors = {}
        self.load_dynamic_data()
    
    def load_dynamic_data(self):
        """동적 모델 데이터를 로드합니다."""
        print("\n=== RocksDB 동적 모델 데이터 로드 ===")
        
        # FillRandom 로그 분석 결과
        self.dynamic_factors = {
            'write_stall_ratio': 0.818,      # Write Stall 비율
            'compaction_io_ratio': 0.314,    # Compaction I/O 비율
            'cache_miss_ratio': 1.0,         # Cache Miss 비율
            'flush_ratio': 0.155,            # Flush 비율
            'compaction_frequency': 'high',  # Compaction 빈도
            'waf': 2.39,                     # Write Amplification Factor
            'key_distribution': 'random',    # 키 분포 패턴
            'access_pattern': 'random'       # 접근 패턴
        }
        
        print("동적 모델 요인들:")
        for factor, value in self.dynamic_factors.items():
            print(f"  {factor}: {value}")
    
    def calculate_dynamic_efficiency(self, workload_type):
        """동적 효율성을 계산합니다."""
        print(f"\n=== {workload_type} 동적 효율성 계산 ===")
        
        # 기본 동적 요인들
        base_factors = self.dynamic_factors.copy()
        
        # 워크로드별 특성 조정
        if workload_type == 'fillrandom':
            # FillRandom 특성
            dynamic_efficiency = {
                'cache_efficiency': 0.0,      # 100% cache miss
                'stall_efficiency': 1.0 - base_factors['write_stall_ratio'],  # 18.2%
                'compaction_efficiency': 1.0 - base_factors['compaction_io_ratio'],  # 68.6%
                'flush_efficiency': 1.0 - base_factors['flush_ratio'],  # 84.5%
                'waf_efficiency': 1.0 / base_factors['waf']  # WAF 역효과
            }
        elif workload_type == 'overwrite':
            # Overwrite 특성 (추정)
            dynamic_efficiency = {
                'cache_efficiency': 0.0,      # 여전히 높은 cache miss
                'stall_efficiency': 0.368,    # Write Stall 63.2% → 36.8% 효율
                'compaction_efficiency': 0.749,  # Compaction I/O 25.1% → 74.9% 효율
                'flush_efficiency': 0.635,    # Flush 36.5% → 63.5% 효율
                'waf_efficiency': 0.8         # 더 낮은 WAF
            }
        else:
            # 기본값
            dynamic_efficiency = {
                'cache_efficiency': 0.5,
                'stall_efficiency': 0.5,
                'compaction_efficiency': 0.5,
                'flush_efficiency': 0.5,
                'waf_efficiency': 0.5
            }
        
        # 전체 동적 효율성 계산 (가중 평균)
        weights = {
            'cache_efficiency': 0.3,    # 캐시가 가장 중요
            'stall_efficiency': 0.25,   # Write Stall 중요
            'compaction_efficiency': 0.25,  # Compaction 중요
            'flush_efficiency': 0.1,    # Flush 상대적 중요
            'waf_efficiency': 0.1       # WAF 상대적 중요
        }
        
        total_dynamic_efficiency = sum(
            dynamic_efficiency[factor] * weights[factor] 
            for factor in dynamic_efficiency.keys()
        )
        
        print(f"{workload_type} 동적 효율성 구성:")
        for factor, efficiency in dynamic_efficiency.items():
            weight = weights[factor]
            print(f"  {factor}: {efficiency:.3f} (가중치: {weight:.2f})")
        
        print(f"  총 동적 효율성: {total_dynamic_efficiency:.3f}")
        
        return dynamic_efficiency, total_dynamic_efficiency

class EnvelopeDynamicV5Model:
    """Envelope + 동적 모델을 통합한 v5 모델"""
    
    def __init__(self):
        self.envelope_model = DeviceEnvelopeModel()
        self.dynamic_model = RocksDBDynamicModel()
        self.envelope_function = None
        self.integrated_model = {}
    
    def integrate_models(self):
        """Envelope 모델과 동적 모델을 통합합니다."""
        print("\n=== Envelope + 동적 모델 통합 ===")
        
        # 1. 장치 Envelope 특성 분석
        envelope_chars = self.envelope_model.analyze_envelope_characteristics()
        self.envelope_function = self.envelope_model.build_envelope_function(envelope_chars)
        
        # 2. 통합 v5 모델 설계
        integrated_formula = """
        S_v5 = S_envelope(read_ratio) × η_workload × η_dynamic × η_system
        
        여기서:
        - S_envelope(read_ratio): 읽기 비율에 따른 장치 envelope 대역폭
        - η_workload: 워크로드별 기본 효율성
        - η_dynamic: RocksDB 동적 요인들 (Stall, Compaction, Cache, WAF)
        - η_system: 시스템 오버헤드
        """
        
        print("통합 v5 모델 공식:")
        print(integrated_formula)
        
        self.integrated_model = {
            'name': 'RocksDB Put Model v5 - Envelope + Dynamic Integration',
            'version': '5.1',
            'formula': 'S_v5 = S_envelope(read_ratio) × η_workload × η_dynamic × η_system',
            'components': {
                'envelope_function': self.envelope_function,
                'workload_efficiency': {
                    'fillrandom': 0.02,
                    'overwrite': 0.05
                },
                'system_overhead': 0.1
            }
        }
        
        return self.integrated_model
    
    def calculate_integrated_predictions(self):
        """통합 모델 예측값을 계산합니다."""
        print("\n=== 통합 모델 예측값 계산 ===")
        
        predictions = {}
        
        for workload in ['fillrandom', 'overwrite']:
            print(f"\n{workload.upper()} 예측:")
            
            # 1. 읽기 비율 추정
            if workload == 'fillrandom':
                read_ratio = 0.0  # 순수 쓰기 워크로드
            elif workload == 'overwrite':
                read_ratio = 0.1  # 약간의 읽기 (업데이트를 위한 기존 값 읽기)
            else:
                read_ratio = 0.0
            
            # 2. Envelope 대역폭 계산
            envelope_bandwidth = self.envelope_function(read_ratio)
            print(f"  Envelope 대역폭 ({read_ratio:.1%} 읽기): {envelope_bandwidth:.1f} MB/s")
            
            # 3. 워크로드 효율성
            workload_eta = self.integrated_model['components']['workload_efficiency'][workload]
            print(f"  워크로드 효율성: {workload_eta:.3f}")
            
            # 4. 동적 효율성 계산
            dynamic_factors, total_dynamic_eta = self.dynamic_model.calculate_dynamic_efficiency(workload)
            print(f"  동적 효율성: {total_dynamic_eta:.3f}")
            
            # 5. 시스템 오버헤드
            system_eta = 1.0 - self.integrated_model['components']['system_overhead']
            print(f"  시스템 효율성: {system_eta:.3f}")
            
            # 6. 최종 예측값 계산
            predicted_throughput = envelope_bandwidth * workload_eta * total_dynamic_eta * system_eta
            
            # 7. 실제값과 비교
            actual_values = {'fillrandom': 30.1, 'overwrite': 74.4}
            actual = actual_values[workload]
            error_rate = abs(predicted_throughput - actual) / actual if actual > 0 else 1.0
            
            predictions[workload] = {
                'predicted': predicted_throughput,
                'actual': actual,
                'error_rate': error_rate,
                'components': {
                    'envelope_bandwidth': envelope_bandwidth,
                    'read_ratio': read_ratio,
                    'workload_eta': workload_eta,
                    'dynamic_eta': total_dynamic_eta,
                    'system_eta': system_eta,
                    'total_efficiency': workload_eta * total_dynamic_eta * system_eta
                }
            }
            
            print(f"  예측 처리량: {predicted_throughput:.2f} MB/s")
            print(f"  실제 처리량: {actual} MB/s")
            print(f"  오류율: {error_rate:.3f} ({error_rate*100:.1f}%)")
        
        return predictions
    
    def analyze_model_improvements(self, predictions):
        """모델 개선사항을 분석합니다."""
        print("\n=== 모델 개선사항 분석 ===")
        
        print("Envelope + 동적 모델의 개선사항:")
        print("1. 장치 Envelope 모델 통합:")
        print("   - 읽기/쓰기 비율에 따른 실제 장치 성능 반영")
        print("   - fio 측정값 기반 정확한 대역폭 계산")
        print("   - 혼합 워크로드에서의 성능 특성 고려")
        
        print("\n2. RocksDB 동적 모델 통합:")
        print("   - Write Stall, Compaction, Cache Miss 등 실제 병목 반영")
        print("   - WAF(Write Amplification Factor) 고려")
        print("   - 워크로드별 동적 특성 차별화")
        
        print("\n3. 통합 모델의 장점:")
        print("   - 장치 특성과 RocksDB 특성을 모두 고려")
        print("   - 실제 운영 환경과 유사한 조건 반영")
        print("   - 워크로드별 세밀한 차별화")
        
        # 전체 정확도 계산
        total_error = sum(pred['error_rate'] for pred in predictions.values()) / len(predictions)
        overall_accuracy = 'Excellent' if total_error < 0.1 else 'Good' if total_error < 0.2 else 'Poor'
        
        print(f"\n통합 모델 정확도:")
        print(f"  평균 오류율: {total_error:.3f} ({total_error*100:.1f}%)")
        print(f"  전체 정확도: {overall_accuracy}")
        
        return {
            'total_error_rate': total_error,
            'overall_accuracy': overall_accuracy,
            'improvements': [
                '장치 Envelope 모델 통합',
                'RocksDB 동적 모델 통합',
                '워크로드별 세밀한 차별화',
                '실제 운영 환경 반영'
            ]
        }
    
    def save_integrated_model(self, predictions, analysis):
        """통합 모델을 저장합니다."""
        print("\n=== 통합 모델 저장 ===")
        
        final_model = {
            'model_info': self.integrated_model,
            'predictions': predictions,
            'analysis': analysis,
            'envelope_characteristics': self.envelope_model.analyze_envelope_characteristics(),
            'dynamic_factors': self.dynamic_model.dynamic_factors
        }
        
        # 함수 객체 제거 (JSON 직렬화를 위해)
        if 'components' in final_model['model_info']:
            if 'envelope_function' in final_model['model_info']['components']:
                del final_model['model_info']['components']['envelope_function']
        
        # JSON 파일로 저장
        output_file = Path("v5_envelope_dynamic_integrated.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_model, f, indent=2, ensure_ascii=False)
        
        print(f"통합 모델이 {output_file}에 저장되었습니다.")
        
        return final_model

def main():
    """메인 함수"""
    print("=== Envelope + 동적 모델을 고려한 v5 모델 개선 ===")
    
    # 통합 v5 모델 생성
    integrated_v5 = EnvelopeDynamicV5Model()
    
    # 모델 통합
    integrated_model = integrated_v5.integrate_models()
    
    # 통합 예측값 계산
    predictions = integrated_v5.calculate_integrated_predictions()
    
    # 모델 개선사항 분석
    analysis = integrated_v5.analyze_model_improvements(predictions)
    
    # 통합 모델 저장
    final_model = integrated_v5.save_integrated_model(predictions, analysis)
    
    print(f"\n=== Envelope + 동적 모델 통합 완료 ===")
    print("주요 개선사항:")
    print("1. 장치 Envelope 모델: 읽기/쓰기 비율에 따른 실제 장치 성능")
    print("2. RocksDB 동적 모델: Write Stall, Compaction, Cache Miss 등 실제 병목")
    print("3. 워크로드별 세밀한 차별화")
    print("4. 실제 운영 환경과 유사한 조건 반영")

if __name__ == "__main__":
    main()
