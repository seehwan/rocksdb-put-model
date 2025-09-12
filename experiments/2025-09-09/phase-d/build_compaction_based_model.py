#!/usr/bin/env python3
"""
컴팩션 기반 정교한 모델 구축
RocksDB의 컴팩션 동작을 기반으로 한 성능 예측 모델
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

class CompactionBasedModel:
    """컴팩션 기반 모델 클래스"""
    
    def __init__(self):
        self.analysis_file = "compaction_performance_analysis.json"
        self.log_metrics_file = "fillrandom_log_based_model.json"
        self.compaction_data = {}
        self.log_metrics = {}
        self.model = {}
        self.load_data()
        self.build_model()
    
    def load_data(self):
        """분석 데이터 로드"""
        print("=== 컴팩션 기반 모델 데이터 로드 ===")
        
        # 컴팩션 성능 분석 데이터 로드
        if Path(self.analysis_file).exists():
            with open(self.analysis_file, 'r') as f:
                self.compaction_data = json.load(f)
                print("  ✅ 컴팩션 성능 분석 데이터 로드")
        
        # 로그 메트릭 데이터 로드
        if Path(self.log_metrics_file).exists():
            with open(self.log_metrics_file, 'r') as f:
                self.log_metrics = json.load(f)
                print("  ✅ 로그 메트릭 데이터 로드")
    
    def build_model(self):
        """컴팩션 기반 모델 구축"""
        print("\n=== 컴팩션 기반 모델 구축 ===")
        
        # 컴팩션 성능 패턴 추출
        performance_patterns = self.compaction_data['performance_patterns']
        compaction_model = self.compaction_data['compaction_model']
        
        # 실제 로그 메트릭 추출
        actual_performance = self.log_metrics['model_info']['actual_measurements']
        bottlenecks = self.log_metrics['log_metrics']['bottlenecks']
        
        # 컴팩션 기반 모델 정의
        self.model = {
            'name': 'RocksDB Compaction-Based Performance Model',
            'version': '1.0',
            'philosophy': 'RocksDB 컴팩션 동작을 기반으로 한 성능 예측',
            'formula': 'S_compaction = S_device × η_phase(compaction_state) × η_write_stall × η_compaction_overhead',
            'compaction_phases': {
                'initial_phase': {
                    'duration_minutes': 10,
                    'performance_factor': performance_patterns['initial_performance'] / performance_patterns['stable_performance'],
                    'characteristics': [
                        'MemTable 가득 참',
                        '첫 번째 Flush 발생',
                        'L0 레벨 생성',
                        'Write Stall 시작'
                    ],
                    'efficiency': 0.9  # 초기에는 높은 효율성
                },
                'transitional_phase': {
                    'duration_minutes': 50,
                    'performance_factor': performance_patterns['mid_performance'] / performance_patterns['stable_performance'],
                    'characteristics': [
                        '간헐적 Compaction 발생',
                        '성능 스파이크 패턴',
                        'L0 → L1 Compaction',
                        'Write Stall 간헐적 발생'
                    ],
                    'efficiency': 0.6  # 중간 효율성
                },
                'stable_phase': {
                    'duration_minutes': 'indefinite',
                    'performance_factor': 1.0,
                    'characteristics': [
                        '지속적 Compaction 오버헤드',
                        '높은 Write Amplification',
                        'Write Stall 지속',
                        'LSM-tree 안정화'
                    ],
                    'efficiency': 0.3  # 낮은 안정화 효율성
                }
            },
            'write_stall_model': {
                'stall_probability': bottlenecks['write_stall_percentage'] / 100.0,
                'stall_duration_seconds': 1258.3,  # P50 지연시간
                'stall_impact_factor': 0.2,  # Write Stall 시 80% 성능 저하
                'recovery_factor': 1.5  # 회복 후 50% 성능 향상
            },
            'compaction_overhead_model': {
                'base_compaction_overhead': 0.2,  # 20% 기본 오버헤드
                'cpu_compaction_ratio': bottlenecks['compaction_cpu_percentage'] / 100.0,
                'compaction_io_overhead': 0.4,  # 40% I/O 오버헤드
                'total_compaction_overhead': 0.6  # 60% 총 컴팩션 오버헤드
            },
            'cache_impact_model': {
                'cache_miss_rate': bottlenecks['cache_miss_rate'] / 100.0,
                'cache_miss_impact': 0.1,  # Cache Miss 시 90% 성능 저하
                'block_cache_efficiency': 0.01  # 1% 효율성
            },
            'write_amplification_model': {
                'waf_factor': bottlenecks['write_amplification'],
                'waf_efficiency_impact': 1.0 / bottlenecks['write_amplification'],  # WAF 역비례
                'additional_write_overhead': (bottlenecks['write_amplification'] - 1.0) * 0.5
            }
        }
        
        print(f"모델명: {self.model['name']}")
        print(f"컴팩션 단계: {len(self.model['compaction_phases'])}개")
        print(f"Write Stall 확률: {self.model['write_stall_model']['stall_probability']*100:.1f}%")
        print(f"컴팩션 오버헤드: {self.model['compaction_overhead_model']['total_compaction_overhead']*100:.0f}%")
    
    def predict_compaction_based(self, device_bandwidth, elapsed_minutes=0, read_ratio=0.0):
        """컴팩션 기반 예측"""
        print(f"\n=== 컴팩션 기반 모델 예측 ===")
        print(f"입력 파라미터:")
        print(f"  장치 대역폭: {device_bandwidth:.1f} MB/s")
        print(f"  경과 시간: {elapsed_minutes:.1f} 분")
        print(f"  읽기 비율: {read_ratio:.1%}")
        
        # 1. Envelope 대역폭 계산
        if read_ratio <= 0:
            envelope_bandwidth = device_bandwidth
        elif read_ratio >= 1:
            envelope_bandwidth = device_bandwidth * 0.6
        else:
            envelope_bandwidth = device_bandwidth * (1 - read_ratio * 0.4)
        
        print(f"  Envelope 대역폭: {envelope_bandwidth:.1f} MB/s")
        
        # 2. 컴팩션 단계 결정
        compaction_phase = self.determine_compaction_phase(elapsed_minutes)
        phase_info = self.model['compaction_phases'][compaction_phase]
        
        print(f"  컴팩션 단계: {compaction_phase}")
        print(f"    - 성능 인수: {phase_info['performance_factor']:.2f}")
        print(f"    - 효율성: {phase_info['efficiency']:.2f}")
        
        # 3. Write Stall 영향 계산
        write_stall_model = self.model['write_stall_model']
        stall_probability = write_stall_model['stall_probability']
        stall_impact = write_stall_model['stall_impact_factor']
        
        # Write Stall이 발생하지 않을 확률
        no_stall_probability = 1.0 - stall_probability
        write_stall_efficiency = (no_stall_probability * 1.0) + (stall_probability * stall_impact)
        
        print(f"  Write Stall 효율성: {write_stall_efficiency:.3f}")
        print(f"    - Stall 확률: {stall_probability*100:.1f}%")
        print(f"    - Stall 영향: {stall_impact:.2f}")
        
        # 4. 컴팩션 오버헤드 계산
        compaction_model = self.model['compaction_overhead_model']
        compaction_overhead = compaction_model['total_compaction_overhead']
        compaction_efficiency = 1.0 - compaction_overhead
        
        print(f"  컴팩션 효율성: {compaction_efficiency:.3f}")
        print(f"    - 컴팩션 오버헤드: {compaction_overhead*100:.0f}%")
        
        # 5. Cache 영향 계산
        cache_model = self.model['cache_impact_model']
        cache_efficiency = cache_model['block_cache_efficiency']
        
        print(f"  Cache 효율성: {cache_efficiency:.3f}")
        print(f"    - Cache Miss Rate: {cache_model['cache_miss_rate']*100:.1f}%")
        
        # 6. Write Amplification 영향 계산
        waf_model = self.model['write_amplification_model']
        waf_efficiency = waf_model['waf_efficiency_impact']
        
        print(f"  WAF 효율성: {waf_efficiency:.3f}")
        print(f"    - WAF: {waf_model['waf_factor']:.2f}")
        
        # 7. 전체 효율성 계산
        total_efficiency = (
            phase_info['efficiency'] *
            write_stall_efficiency *
            compaction_efficiency *
            cache_efficiency *
            waf_efficiency
        )
        
        print(f"  총 효율성: {total_efficiency:.4f}")
        
        # 8. 예측 처리량 계산
        predicted_throughput = envelope_bandwidth * total_efficiency
        
        print(f"  예측 처리량: {predicted_throughput:.2f} MB/s")
        
        return {
            'predicted': predicted_throughput,
            'compaction_phase': compaction_phase,
            'components': {
                'envelope_bandwidth': envelope_bandwidth,
                'phase_efficiency': phase_info['efficiency'],
                'write_stall_efficiency': write_stall_efficiency,
                'compaction_efficiency': compaction_efficiency,
                'cache_efficiency': cache_efficiency,
                'waf_efficiency': waf_efficiency,
                'total_efficiency': total_efficiency
            },
            'phase_info': phase_info
        }
    
    def determine_compaction_phase(self, elapsed_minutes):
        """컴팩션 단계 결정"""
        if elapsed_minutes <= 10:
            return 'initial_phase'
        elif elapsed_minutes <= 60:
            return 'transitional_phase'
        else:
            return 'stable_phase'
    
    def validate_compaction_model(self):
        """컴팩션 모델 검증"""
        print("\n=== 컴팩션 모델 검증 ===")
        
        # 실제 측정값
        actual_throughput = self.log_metrics['model_info']['actual_measurements']['throughput_mb_s']
        device_bandwidth = self.log_metrics['model_info']['performance_characteristics']['device_bandwidth']
        
        # 다양한 시간 지점에서 예측
        validation_results = {}
        time_points = [5, 30, 120, 360, 720, 1440]  # 5분, 30분, 2시간, 6시간, 12시간, 24시간
        
        for minutes in time_points:
            prediction = self.predict_compaction_based(device_bandwidth, minutes)
            predicted_throughput = prediction['predicted']
            
            error_rate = abs(predicted_throughput - actual_throughput) / actual_throughput
            
            validation_results[f'{minutes}_minutes'] = {
                'predicted': predicted_throughput,
                'actual': actual_throughput,
                'error_rate': error_rate,
                'compaction_phase': prediction['compaction_phase'],
                'components': prediction['components']
            }
            
            print(f"  {minutes}분: {predicted_throughput:.2f} MB/s (오류율: {error_rate:.3f})")
        
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
    
    def explain_compaction_behavior(self):
        """컴팩션 동작 설명"""
        print("\n=== RocksDB 컴팩션 동작과 성능 패턴 설명 ===")
        
        print("1. 초기 성능 급격한 저하 (0-10분):")
        print("   원인:")
        print("   - MemTable이 가득 차면서 첫 번째 Flush 발생")
        print("   - L0 레벨이 생성되면서 Write Stall 시작")
        print("   - 컴팩션 스레드가 시작되면서 I/O 경합 발생")
        print(f"   - 성능 인수: {self.model['compaction_phases']['initial_phase']['performance_factor']:.2f}x")
        
        print("\n2. 중간 스파이크 패턴 (10-60분):")
        print("   원인:")
        print("   - L0 → L1 컴팩션 완료 후 일시적 성능 회복")
        print("   - 새로운 MemTable로 전환되면서 Write Stall 일시 해소")
        print("   - 컴팩션 간격 동안 정상적인 쓰기 성능 회복")
        print(f"   - 성능 인수: {self.model['compaction_phases']['transitional_phase']['performance_factor']:.2f}x")
        
        print("\n3. 낮은 성능으로 안정화 (60분 이후):")
        print("   원인:")
        print("   - 지속적인 컴팩션 오버헤드 (60% CPU 사용)")
        print("   - 높은 Write Amplification (1.64x)")
        print("   - Write Stall 지속 (81.8% 확률)")
        print("   - Cache Miss 지속 (100%)")
        print("   - LSM-tree 구조의 본질적 특성")
        
        print("\n4. 컴팩션의 핵심 메커니즘:")
        print("   - L0 레벨이 가득 차면 L1으로 컴팩션")
        print("   - 컴팩션 중에는 쓰기 성능 급격히 저하")
        print("   - 컴팩션 완료 후 일시적 성능 회복")
        print("   - 시간이 지날수록 더 많은 레벨에서 컴팩션 발생")
        
        print("\n5. Write Stall의 역할:")
        print(f"   - Stall 확률: {self.model['write_stall_model']['stall_probability']*100:.1f}%")
        print("   - L0 레벨이 가득 찰 때 쓰기 중단")
        print("   - 컴팩션 완료까지 대기")
        print("   - 성능 저하의 주요 원인")
    
    def save_compaction_model(self, validation_results):
        """컴팩션 모델 저장"""
        print("\n=== 컴팩션 모델 저장 ===")
        
        final_model = {
            'model_info': self.model,
            'validation_results': validation_results,
            'compaction_analysis': self.compaction_data,
            'log_metrics': self.log_metrics,
            'model_insights': {
                'key_insights': [
                    'RocksDB 성능은 컴팩션 단계에 따라 크게 변동',
                    'Write Stall이 성능 저하의 주요 원인 (81.8%)',
                    '컴팩션 오버헤드가 지속적 성능 저하 원인 (60%)',
                    'Cache Miss로 인한 추가 성능 저하 (100%)',
                    'Write Amplification으로 인한 쓰기 부하 증가 (1.64x)'
                ],
                'performance_phases': {
                    'initial': 'MemTable Flush + L0 Compaction 시작',
                    'transitional': '간헐적 Compaction + 스파이크',
                    'stable': '지속적 Compaction 오버헤드'
                },
                'bottleneck_ranking': [
                    'Write Stall (81.8% 확률)',
                    'Compaction CPU (271.7% 사용)',
                    'Cache Miss (100% 확률)',
                    'Write Amplification (1.64x)'
                ]
            }
        }
        
        # JSON 파일로 저장
        output_file = Path("compaction_based_model.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_model, f, indent=2, ensure_ascii=False)
        
        print(f"컴팩션 기반 모델이 {output_file}에 저장되었습니다.")
        
        return final_model

def main():
    """메인 함수"""
    print("=== RocksDB 컴팩션 기반 정교한 모델 ===")
    
    # 컴팩션 기반 모델 생성
    compaction_model = CompactionBasedModel()
    
    # 컴팩션 동작 설명
    compaction_model.explain_compaction_behavior()
    
    # 컴팩션 모델 검증
    validation_results = compaction_model.validate_compaction_model()
    
    # 컴팩션 모델 저장
    final_model = compaction_model.save_compaction_model(validation_results)
    
    print(f"\n=== 컴팩션 기반 모델 완료 ===")
    print("주요 특징:")
    print("1. RocksDB 컴팩션 동작 기반")
    print("2. 시간별 성능 단계 모델링")
    print("3. Write Stall 영향 정량화")
    print("4. 컴팩션 오버헤드 고려")
    print("5. 실제 로그 데이터 검증")

if __name__ == "__main__":
    main()


