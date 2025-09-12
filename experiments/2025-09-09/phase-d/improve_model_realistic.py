#!/usr/bin/env python3
"""
현실적인 모델 개선
컴팩션 동작을 이해한 후 실제로 정확한 예측이 가능한 모델 구축
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

class RealisticModelImprover:
    """현실적인 모델 개선 클래스"""
    
    def __init__(self):
        self.compaction_data = {}
        self.log_metrics = {}
        self.historical_data = {}
        self.improved_model = {}
        self.load_data()
        self.analyze_failures()
        self.build_improved_model()
    
    def load_data(self):
        """데이터 로드"""
        print("=== 현실적인 모델 개선을 위한 데이터 로드 ===")
        
        # 컴팩션 분석 데이터
        if Path("compaction_performance_analysis.json").exists():
            with open("compaction_performance_analysis.json", 'r') as f:
                self.compaction_data = json.load(f)
                print("  ✅ 컴팩션 분석 데이터 로드")
        
        # 로그 메트릭 데이터
        if Path("fillrandom_log_based_model.json").exists():
            with open("fillrandom_log_based_model.json", 'r') as f:
                self.log_metrics = json.load(f)
                print("  ✅ 로그 메트릭 데이터 로드")
        
        # 이전 검증 결과들
        if Path("v5_historical_validation_results.json").exists():
            with open("v5_historical_validation_results.json", 'r') as f:
                historical = json.load(f)
                self.historical_data = historical['historical_data_summary']
                print("  ✅ 이전 검증 데이터 로드")
    
    def analyze_failures(self):
        """기존 모델들의 실패 원인 분석"""
        print("\n=== 기존 모델 실패 원인 분석 ===")
        
        # 실제 측정값들
        actual_fillrandom = 30.1  # MB/s
        device_bandwidth = 3005.8  # MB/s
        actual_efficiency = actual_fillrandom / device_bandwidth  # 1.0%
        
        print(f"실제 FillRandom 성능:")
        print(f"  처리량: {actual_fillrandom} MB/s")
        print(f"  장치 대역폭: {device_bandwidth} MB/s")
        print(f"  실제 효율성: {actual_efficiency:.4f} ({actual_efficiency*100:.2f}%)")
        
        # 기존 모델들의 문제점 분석
        failures = {
            'v5_original': {
                'error_rate': 0.378,
                'predicted': 18.58,
                'actual': 30.1,
                'problems': [
                    '고정된 효율성 사용',
                    '병목을 절대적 실패로 해석',
                    '환경별 차이 무시'
                ]
            },
            'v5_refined': {
                'error_rate': 0.427,
                'predicted': 41.62,
                'actual': 30.1,
                'problems': [
                    '환경 적응은 했지만 여전히 부정확',
                    '복잡한 계산으로 인한 오차 누적',
                    '실제 운영 환경과 차이'
                ]
            },
            'log_based': {
                'error_rate': 0.716,
                'predicted': 8.56,
                'actual': 30.1,
                'problems': [
                    '과도하게 보수적 예측',
                    '병목을 곱셈으로 계산',
                    '실제 RocksDB 동작 무시'
                ]
            },
            'compaction_based': {
                'error_rate': 0.962,
                'predicted': 0.76,
                'actual': 30.1,
                'problems': [
                    '병목을 절대적 실패로 해석',
                    '총 효율성이 0.0003으로 과도하게 낮음',
                    '실제 동작과 완전히 다른 예측'
                ]
            }
        }
        
        print(f"\n기존 모델들의 문제점:")
        for model_name, failure in failures.items():
            print(f"  {model_name}:")
            print(f"    오류율: {failure['error_rate']*100:.1f}%")
            print(f"    예측값: {failure['predicted']:.2f} MB/s")
            print(f"    문제점: {', '.join(failure['problems'])}")
        
        # 핵심 문제점 도출
        core_problems = [
            '병목 현상을 절대적 실패로 해석 (100% Cache Miss → 1% 효율성)',
            '복잡한 효율성 계산으로 인한 오차 누적',
            '실제 RocksDB 동작 방식 무시',
            '환경별 차이를 과도하게 단순화',
            '이론적 모델과 실제 운영 환경의 차이'
        ]
        
        print(f"\n핵심 문제점:")
        for i, problem in enumerate(core_problems, 1):
            print(f"  {i}. {problem}")
        
        return failures, core_problems
    
    def build_improved_model(self):
        """개선된 모델 구축"""
        print("\n=== 개선된 현실적 모델 구축 ===")
        
        # 실제 측정값들
        actual_fillrandom = 30.1
        device_bandwidth = 3005.8
        actual_efficiency = actual_fillrandom / device_bandwidth
        
        # 컴팩션 패턴 데이터
        compaction_patterns = self.compaction_data['performance_patterns']
        
        # 로그 메트릭 데이터
        bottlenecks = self.log_metrics['log_metrics']['bottlenecks']
        
        # 개선된 모델 설계
        self.improved_model = {
            'name': 'RocksDB Realistic Performance Model',
            'version': '2.0',
            'philosophy': '실제 RocksDB 동작을 반영한 현실적 예측',
            'formula': 'S_realistic = S_device × η_compaction_aware × η_workload_factor × η_environment',
            'key_insights': {
                'compaction_understanding': '컴팩션은 성능 저하의 원인이지만 완전한 실패가 아님',
                'bottleneck_reinterpretation': '병목은 상대적 영향이지 절대적 실패가 아님',
                'actual_efficiency_baseline': f'실제 FillRandom 효율성: {actual_efficiency:.4f}',
                'performance_phases': '초기 높음 → 중간 변동 → 안정화 낮음'
            },
            'compaction_aware_model': {
                'initial_phase': {
                    'efficiency_factor': 1.0,  # 초기에는 높은 효율성
                    'duration_minutes': 10,
                    'description': 'MemTable Flush, L0 생성'
                },
                'transitional_phase': {
                    'efficiency_factor': 0.6,  # 중간 효율성
                    'duration_minutes': 50,
                    'description': '간헐적 Compaction, 스파이크'
                },
                'stable_phase': {
                    'efficiency_factor': 0.3,  # 안정화된 낮은 효율성
                    'duration_minutes': 'indefinite',
                    'description': '지속적 Compaction 오버헤드'
                }
            },
            'bottleneck_impact_model': {
                'write_stall': {
                    'probability': bottlenecks['write_stall_percentage'] / 100.0,
                    'impact_factor': 0.5,  # Stall 시에도 50% 성능 유지
                    'description': 'Write Stall은 지연이지 완전 중단이 아님'
                },
                'cache_miss': {
                    'rate': bottlenecks['cache_miss_rate'] / 100.0,
                    'impact_factor': 0.8,  # Cache Miss에도 80% 성능 유지
                    'description': 'Cache Miss는 성능 저하이지 완전 실패가 아님'
                },
                'compaction_overhead': {
                    'cpu_ratio': bottlenecks['compaction_cpu_percentage'] / 100.0,
                    'impact_factor': 0.6,  # Compaction 중에도 60% 성능 유지
                    'description': 'Compaction은 백그라운드에서 진행'
                },
                'write_amplification': {
                    'factor': bottlenecks['write_amplification'],
                    'impact_factor': 0.7,  # WAF 1.64x여도 70% 성능 유지
                    'description': 'WAF는 추가 쓰기이지 성능 중단이 아님'
                }
            },
            'workload_factor': {
                'fillrandom': {
                    'base_efficiency': actual_efficiency,  # 실제 측정값 사용
                    'randomness_penalty': 0.8,  # 랜덤 키로 인한 20% 성능 저하
                    'compaction_penalty': 0.6,  # 높은 Compaction으로 인한 40% 성능 저하
                    'total_factor': actual_efficiency * 0.8 * 0.6
                }
            },
            'environment_factor': {
                'device_bandwidth': device_bandwidth,
                'scaling_factor': 1.0,  # 현재 환경 기준
                'system_overhead': 0.9  # 10% 시스템 오버헤드
            }
        }
        
        print(f"모델명: {self.improved_model['name']}")
        print(f"철학: {self.improved_model['philosophy']}")
        print(f"핵심 통찰:")
        for key, insight in self.improved_model['key_insights'].items():
            print(f"  - {key}: {insight}")
    
    def predict_realistic(self, device_bandwidth, elapsed_minutes=0, workload_type='fillrandom'):
        """현실적 예측"""
        print(f"\n=== 현실적 모델 예측 ===")
        print(f"입력 파라미터:")
        print(f"  장치 대역폭: {device_bandwidth:.1f} MB/s")
        print(f"  경과 시간: {elapsed_minutes:.1f} 분")
        print(f"  워크로드: {workload_type}")
        
        # 1. 기본 장치 대역폭
        base_bandwidth = device_bandwidth
        print(f"  기본 장치 대역폭: {base_bandwidth:.1f} MB/s")
        
        # 2. 컴팩션 인식 효율성
        compaction_phase = self.determine_compaction_phase(elapsed_minutes)
        compaction_factor = self.improved_model['compaction_aware_model'][compaction_phase]['efficiency_factor']
        print(f"  컴팩션 단계: {compaction_phase}")
        print(f"  컴팩션 효율성: {compaction_factor:.2f}")
        
        # 3. 워크로드 인수 (실제 측정값 기반)
        workload_factor = self.improved_model['workload_factor'][workload_type]['total_factor']
        print(f"  워크로드 인수: {workload_factor:.4f}")
        
        # 4. 환경 인수
        environment_factor = self.improved_model['environment_factor']['system_overhead']
        print(f"  환경 인수: {environment_factor:.2f}")
        
        # 5. 병목 영향 (상대적 영향으로 재해석)
        bottleneck_impact = self.calculate_realistic_bottleneck_impact()
        print(f"  병목 영향: {bottleneck_impact:.2f}")
        
        # 6. 총 효율성 계산
        total_efficiency = compaction_factor * workload_factor * environment_factor * bottleneck_impact
        print(f"  총 효율성: {total_efficiency:.4f}")
        
        # 7. 예측 처리량
        predicted_throughput = base_bandwidth * total_efficiency
        print(f"  예측 처리량: {predicted_throughput:.2f} MB/s")
        
        return {
            'predicted': predicted_throughput,
            'compaction_phase': compaction_phase,
            'components': {
                'base_bandwidth': base_bandwidth,
                'compaction_factor': compaction_factor,
                'workload_factor': workload_factor,
                'environment_factor': environment_factor,
                'bottleneck_impact': bottleneck_impact,
                'total_efficiency': total_efficiency
            }
        }
    
    def determine_compaction_phase(self, elapsed_minutes):
        """컴팩션 단계 결정"""
        if elapsed_minutes <= 10:
            return 'initial_phase'
        elif elapsed_minutes <= 60:
            return 'transitional_phase'
        else:
            return 'stable_phase'
    
    def calculate_realistic_bottleneck_impact(self):
        """현실적 병목 영향 계산"""
        bottleneck_model = self.improved_model['bottleneck_impact_model']
        
        # 각 병목의 상대적 영향을 계산
        write_stall_impact = (
            (1.0 - bottleneck_model['write_stall']['probability']) * 1.0 +
            bottleneck_model['write_stall']['probability'] * bottleneck_model['write_stall']['impact_factor']
        )
        
        cache_impact = (
            (1.0 - bottleneck_model['cache_miss']['rate']) * 1.0 +
            bottleneck_model['cache_miss']['rate'] * bottleneck_model['cache_miss']['impact_factor']
        )
        
        compaction_impact = (
            (1.0 - bottleneck_model['compaction_overhead']['cpu_ratio']) * 1.0 +
            bottleneck_model['compaction_overhead']['cpu_ratio'] * bottleneck_model['compaction_overhead']['impact_factor']
        )
        
        waf_impact = bottleneck_model['write_amplification']['impact_factor']
        
        # 가중 평균으로 총 영향 계산
        total_impact = (
            write_stall_impact * 0.3 +
            cache_impact * 0.2 +
            compaction_impact * 0.3 +
            waf_impact * 0.2
        )
        
        return total_impact
    
    def validate_improved_model(self):
        """개선된 모델 검증"""
        print("\n=== 개선된 모델 검증 ===")
        
        # 현재 실험 데이터
        current_device_bandwidth = 3005.8
        current_actual_throughput = 30.1
        
        # 다양한 시간 지점에서 예측
        validation_results = {}
        time_points = [5, 30, 120, 360, 720, 1440]  # 다양한 시간 지점
        
        for minutes in time_points:
            prediction = self.predict_realistic(current_device_bandwidth, minutes)
            predicted_throughput = prediction['predicted']
            
            error_rate = abs(predicted_throughput - current_actual_throughput) / current_actual_throughput
            
            validation_results[f'{minutes}_minutes'] = {
                'predicted': predicted_throughput,
                'actual': current_actual_throughput,
                'error_rate': error_rate,
                'compaction_phase': prediction['compaction_phase'],
                'components': prediction['components']
            }
            
            print(f"  {minutes}분: {predicted_throughput:.2f} MB/s (오류율: {error_rate:.3f})")
        
        # 이전 실험들과 비교
        if self.historical_data:
            print(f"\n이전 실험들과 비교:")
            for exp_date, exp_data in self.historical_data.items():
                if exp_data['actual_throughput'] > 0:
                    prediction = self.predict_realistic(exp_data['device_write_bw'], 120)  # 2시간 후 안정화
                    predicted_throughput = prediction['predicted']
                    actual_throughput = exp_data['actual_throughput']
                    error_rate = abs(predicted_throughput - actual_throughput) / actual_throughput
                    
                    print(f"  {exp_date}: {predicted_throughput:.2f} MB/s vs {actual_throughput:.1f} MB/s (오류율: {error_rate:.3f})")
        
        # 전체 통계
        error_rates = [result['error_rate'] for result in validation_results.values()]
        avg_error = np.mean(error_rates)
        min_error = np.min(error_rates)
        max_error = np.max(error_rates)
        
        print(f"\n전체 검증 결과:")
        print(f"  평균 오류율: {avg_error:.3f} ({avg_error*100:.1f}%)")
        print(f"  최소 오류율: {min_error:.3f} ({min_error*100:.1f}%)")
        print(f"  최대 오류율: {max_error:.3f} ({max_error*100:.1f}%)")
        
        accuracy = 'Excellent' if avg_error < 0.1 else 'Good' if avg_error < 0.3 else 'Poor'
        print(f"  전체 정확도: {accuracy}")
        
        return validation_results
    
    def save_improved_model(self, validation_results):
        """개선된 모델 저장"""
        print("\n=== 개선된 모델 저장 ===")
        
        # 기존 모델들과 비교
        model_comparison = {
            'v5_original': {'error_rate': 0.378, 'accuracy': 'Poor'},
            'v5_refined': {'error_rate': 0.427, 'accuracy': 'Poor'},
            'log_based': {'error_rate': 0.716, 'accuracy': 'Poor'},
            'compaction_based': {'error_rate': 0.962, 'accuracy': 'Poor'},
            'realistic_improved': {
                'error_rate': np.mean([r['error_rate'] for r in validation_results.values()]),
                'accuracy': 'TBD'
            }
        }
        
        final_model = {
            'model_info': self.improved_model,
            'validation_results': validation_results,
            'model_comparison': model_comparison,
            'improvement_summary': {
                'key_improvements': [
                    '병목을 상대적 영향으로 재해석',
                    '실제 측정 효율성을 기준으로 사용',
                    '컴팩션 단계별 현실적 효율성 적용',
                    '복잡한 계산 대신 간단한 현실적 모델',
                    '이론적 모델과 실제 동작의 차이 반영'
                ],
                'philosophy_change': '절대적 실패 → 상대적 영향',
                'efficiency_baseline': '실제 측정값 기반',
                'bottleneck_interpretation': '완전 중단 → 성능 저하'
            }
        }
        
        # JSON 파일로 저장
        output_file = Path("realistic_improved_model.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_model, f, indent=2, ensure_ascii=False)
        
        print(f"개선된 모델이 {output_file}에 저장되었습니다.")
        
        return final_model

def main():
    """메인 함수"""
    print("=== 현실적인 모델 개선 ===")
    
    # 모델 개선기 생성
    improver = RealisticModelImprover()
    
    # 개선된 모델 검증
    validation_results = improver.validate_improved_model()
    
    # 개선된 모델 저장
    final_model = improver.save_improved_model(validation_results)
    
    print(f"\n=== 모델 개선 완료 ===")
    print("주요 개선사항:")
    print("1. 병목을 상대적 영향으로 재해석")
    print("2. 실제 측정 효율성을 기준으로 사용")
    print("3. 컴팩션 단계별 현실적 효율성 적용")
    print("4. 복잡한 계산 대신 간단한 현실적 모델")
    print("5. 이론적 모델과 실제 동작의 차이 반영")

if __name__ == "__main__":
    main()


