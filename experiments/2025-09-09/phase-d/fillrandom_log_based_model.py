#!/usr/bin/env python3
"""
FillRandom 로그 데이터 기반 정교한 모델
실제 FillRandom 로그에서 추출한 성능 지표와 병목 현상을 기반으로 한 모델
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import re

class FillRandomLogAnalyzer:
    """FillRandom 로그 분석 클래스"""
    
    def __init__(self):
        self.log_file = "/home/sslab/rocksdb-put-model/experiments/2025-09-09/phase-b/phase_b_final_results/fillrandom_results.txt"
        self.log_metrics = {}
        self.analyze_logs()
    
    def analyze_logs(self):
        """FillRandom 로그 분석"""
        print("=== FillRandom 로그 분석 ===")
        
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # 1. 전체 성능 지표 추출
        self.extract_performance_metrics(log_content)
        
        # 2. 병목 현상 분석
        self.analyze_bottlenecks(log_content)
        
        # 3. 시간별 성능 변화 분석
        self.analyze_temporal_performance(log_content)
        
        print("로그 분석 완료")
    
    def extract_performance_metrics(self, log_content):
        """전체 성능 지표 추출"""
        print("  전체 성능 지표 추출")
        
        # 최종 성능 지표
        final_perf_match = re.search(
            r'fillrandom\s*:\s*(\d+\.\d+)\s+micros/op\s+(\d+)\s+ops/sec\s+(\d+\.\d+)\s+seconds\s+(\d+)\s+operations;\s*(\d+\.\d+)\s+MB/s',
            log_content
        )
        
        if final_perf_match:
            self.log_metrics['performance'] = {
                'micros_per_op': float(final_perf_match.group(1)),
                'ops_per_sec': int(final_perf_match.group(2)),
                'total_seconds': float(final_perf_match.group(3)),
                'total_operations': int(final_perf_match.group(4)),
                'throughput_mb_s': float(final_perf_match.group(5))
            }
            
            print(f"    처리량: {self.log_metrics['performance']['throughput_mb_s']} MB/s")
            print(f"    OPS: {self.log_metrics['performance']['ops_per_sec']:,} ops/sec")
            print(f"    지연시간: {self.log_metrics['performance']['micros_per_op']:.1f} μs/op")
            print(f"    총 실행시간: {self.log_metrics['performance']['total_seconds']:.1f} 초")
    
    def analyze_bottlenecks(self, log_content):
        """병목 현상 분석"""
        print("  병목 현상 분석")
        
        # Write Stall 분석
        write_stall_match = re.search(
            r'rocksdb\.db\.write\.stall.*?COUNT\s*:\s*(\d+).*?SUM\s*:\s*(\d+)',
            log_content
        )
        
        if write_stall_match:
            stall_count = int(write_stall_match.group(1))
            stall_sum = int(write_stall_match.group(2))
            stall_percentage = (stall_sum / (self.log_metrics['performance']['total_seconds'] * 1_000_000)) * 100
            
            self.log_metrics['bottlenecks'] = {
                'write_stall_count': stall_count,
                'write_stall_sum_micros': stall_sum,
                'write_stall_percentage': stall_percentage
            }
            
            print(f"    Write Stall: {stall_percentage:.1f}%")
        
        # Compaction 분석
        compaction_time_match = re.search(
            r'rocksdb\.compaction\.total\.time\.cpu_micros\s+COUNT\s*:\s*(\d+)',
            log_content
        )
        
        if compaction_time_match:
            compaction_cpu_time = int(compaction_time_match.group(1))
            compaction_percentage = (compaction_cpu_time / (self.log_metrics['performance']['total_seconds'] * 1_000_000)) * 100
            
            self.log_metrics['bottlenecks']['compaction_cpu_percentage'] = compaction_percentage
            print(f"    Compaction CPU: {compaction_percentage:.1f}%")
        
        # Cache Miss 분석
        cache_miss_match = re.search(
            r'rocksdb\.block\.cache\.miss\s+COUNT\s*:\s*(\d+)',
            log_content
        )
        cache_hit_match = re.search(
            r'rocksdb\.block\.cache\.hit\s+COUNT\s*:\s*(\d+)',
            log_content
        )
        
        if cache_miss_match and cache_hit_match:
            cache_misses = int(cache_miss_match.group(1))
            cache_hits = int(cache_hit_match.group(1))
            total_cache_requests = cache_misses + cache_hits
            
            if total_cache_requests > 0:
                cache_miss_rate = (cache_misses / total_cache_requests) * 100
                self.log_metrics['bottlenecks']['cache_miss_rate'] = cache_miss_rate
                print(f"    Cache Miss Rate: {cache_miss_rate:.1f}%")
        
        # Key Drop 분석 (Write Amplification 지표)
        key_drop_match = re.search(
            r'rocksdb\.compaction\.key\.drop\.new\s+COUNT\s*:\s*(\d+)',
            log_content
        )
        
        if key_drop_match:
            keys_dropped = int(key_drop_match.group(1))
            total_operations = self.log_metrics['performance']['total_operations']
            write_amplification = (total_operations + keys_dropped) / total_operations
            
            self.log_metrics['bottlenecks']['write_amplification'] = write_amplification
            print(f"    Write Amplification: {write_amplification:.2f}")
    
    def analyze_temporal_performance(self, log_content):
        """시간별 성능 변화 분석"""
        print("  시간별 성능 변화 분석")
        
        # 스레드별 시간별 성능 추출
        thread_performance = {}
        
        # 정규식으로 시간별 성능 데이터 추출
        time_pattern = r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2})\s+\.\.\.\s+thread\s+(\d+):\s+\((\d+),(\d+)\)\s+ops\s+and\s+\(([^,]+),([^)]+)\)\s+ops/second'
        
        matches = re.findall(time_pattern, log_content)
        
        if matches:
            temporal_data = []
            for match in matches:
                timestamp, thread_id, current_ops, total_ops, current_rate, avg_rate = match
                temporal_data.append({
                    'timestamp': timestamp,
                    'thread_id': int(thread_id),
                    'current_ops': int(current_ops),
                    'total_ops': int(total_ops),
                    'current_rate': float(current_rate),
                    'avg_rate': float(avg_rate)
                })
            
            self.log_metrics['temporal_performance'] = temporal_data
            
            # 시간별 성능 변화 분석
            if temporal_data:
                rates = [d['current_rate'] for d in temporal_data]
                avg_rates = [d['avg_rate'] for d in temporal_data]
                
                self.log_metrics['performance_analysis'] = {
                    'current_rate_std': np.std(rates),
                    'avg_rate_std': np.std(avg_rates),
                    'performance_variance': np.var(avg_rates),
                    'total_samples': len(temporal_data)
                }
                
                print(f"    시간별 성능 샘플 수: {len(temporal_data)}")
                print(f"    성능 변동성: {np.std(avg_rates):.1f} ops/sec")
    
    def get_log_metrics(self):
        """로그 메트릭 반환"""
        return self.log_metrics

class FillRandomLogBasedModel:
    """FillRandom 로그 기반 모델"""
    
    def __init__(self):
        self.log_analyzer = FillRandomLogAnalyzer()
        self.log_metrics = self.log_analyzer.get_log_metrics()
        self.model = {}
        self.build_model()
    
    def build_model(self):
        """로그 기반 모델 구축"""
        print("\n=== FillRandom 로그 기반 모델 구축 ===")
        
        performance = self.log_metrics['performance']
        bottlenecks = self.log_metrics.get('bottlenecks', {})
        
        # 실제 측정된 효율성 계산
        device_bandwidth = 3005.8  # 현재 실험의 fio 측정값
        actual_efficiency = performance['throughput_mb_s'] / device_bandwidth
        
        # 병목별 효율성 분석
        bottleneck_analysis = self.analyze_bottleneck_impact(bottlenecks)
        
        self.model = {
            'name': 'FillRandom Log-Based Model',
            'version': '1.0',
            'philosophy': '실제 FillRandom 로그 데이터 기반 모델링',
            'formula': 'S_log = S_device × η_log_based(measured_efficiency) × η_bottleneck_aware × η_temporal',
            'actual_measurements': {
                'throughput_mb_s': performance['throughput_mb_s'],
                'ops_per_sec': performance['ops_per_sec'],
                'micros_per_op': performance['micros_per_op'],
                'total_seconds': performance['total_seconds'],
                'actual_efficiency': actual_efficiency
            },
            'bottleneck_analysis': bottleneck_analysis,
            'performance_characteristics': {
                'device_bandwidth': device_bandwidth,
                'efficiency_ratio': actual_efficiency,
                'bottleneck_severity': self.calculate_bottleneck_severity(bottlenecks)
            }
        }
        
        print(f"모델명: {self.model['name']}")
        print(f"실제 측정 효율성: {actual_efficiency:.4f}")
        print(f"병목 심각도: {self.model['performance_characteristics']['bottleneck_severity']}")
    
    def analyze_bottleneck_impact(self, bottlenecks):
        """병목 현상 영향 분석"""
        print("  병목 현상 영향 분석")
        
        bottleneck_impact = {}
        
        # Write Stall 영향
        if 'write_stall_percentage' in bottlenecks:
            stall_pct = bottlenecks['write_stall_percentage']
            # Write Stall이 높을수록 효율성 저하 (선형 관계 가정)
            stall_efficiency = max(0.1, 1.0 - (stall_pct / 100.0))
            bottleneck_impact['write_stall_efficiency'] = stall_efficiency
            print(f"    Write Stall 효율성: {stall_efficiency:.3f} ({stall_pct:.1f}% stall)")
        
        # Cache Miss 영향
        if 'cache_miss_rate' in bottlenecks:
            cache_miss_rate = bottlenecks['cache_miss_rate']
            # Cache Miss가 높을수록 효율성 저하
            cache_efficiency = max(0.01, 1.0 - (cache_miss_rate / 100.0))
            bottleneck_impact['cache_efficiency'] = cache_efficiency
            print(f"    Cache 효율성: {cache_efficiency:.3f} ({cache_miss_rate:.1f}% miss)")
        
        # Compaction 영향
        if 'compaction_cpu_percentage' in bottlenecks:
            compaction_pct = bottlenecks['compaction_cpu_percentage']
            # Compaction이 높을수록 효율성 저하
            compaction_efficiency = max(0.2, 1.0 - (compaction_pct / 100.0))
            bottleneck_impact['compaction_efficiency'] = compaction_efficiency
            print(f"    Compaction 효율성: {compaction_efficiency:.3f} ({compaction_pct:.1f}% CPU)")
        
        # Write Amplification 영향
        if 'write_amplification' in bottlenecks:
            waf = bottlenecks['write_amplification']
            # WAF가 높을수록 효율성 저하 (로그 스케일)
            waf_efficiency = max(0.1, 1.0 / np.log(waf + 1))
            bottleneck_impact['waf_efficiency'] = waf_efficiency
            print(f"    WAF 효율성: {waf_efficiency:.3f} (WAF: {waf:.2f})")
        
        return bottleneck_impact
    
    def calculate_bottleneck_severity(self, bottlenecks):
        """병목 심각도 계산"""
        severity_score = 0
        
        if 'write_stall_percentage' in bottlenecks:
            severity_score += bottlenecks['write_stall_percentage'] * 0.3
        
        if 'cache_miss_rate' in bottlenecks:
            severity_score += bottlenecks['cache_miss_rate'] * 0.2
        
        if 'compaction_cpu_percentage' in bottlenecks:
            severity_score += bottlenecks['compaction_cpu_percentage'] * 0.3
        
        if 'write_amplification' in bottlenecks:
            severity_score += (bottlenecks['write_amplification'] - 1) * 100 * 0.2
        
        if severity_score < 20:
            return "Low"
        elif severity_score < 50:
            return "Medium"
        elif severity_score < 80:
            return "High"
        else:
            return "Critical"
    
    def predict_log_based(self, device_bandwidth, read_ratio=0.0, workload_type='fillrandom'):
        """로그 기반 예측"""
        print(f"\n=== 로그 기반 모델 예측 ===")
        print(f"입력 파라미터:")
        print(f"  장치 대역폭: {device_bandwidth:.1f} MB/s")
        print(f"  읽기 비율: {read_ratio:.1%}")
        print(f"  워크로드: {workload_type}")
        
        # 1. Envelope 대역폭 계산
        if read_ratio <= 0:
            envelope_bandwidth = device_bandwidth
        elif read_ratio >= 1:
            envelope_bandwidth = device_bandwidth * 0.6
        else:
            envelope_bandwidth = device_bandwidth * (1 - read_ratio * 0.4)
        
        print(f"  Envelope 대역폭: {envelope_bandwidth:.1f} MB/s")
        
        # 2. 실제 측정된 효율성 사용
        actual_efficiency = self.model['actual_measurements']['actual_efficiency']
        print(f"  실제 측정 효율성: {actual_efficiency:.4f}")
        
        # 3. 병목 인식 효율성 조정
        bottleneck_analysis = self.model['bottleneck_analysis']
        if bottleneck_analysis:
            # 병목별 효율성의 가중 평균
            bottleneck_efficiency = np.mean(list(bottleneck_analysis.values()))
            print(f"  병목 인식 효율성: {bottleneck_efficiency:.4f}")
        else:
            bottleneck_efficiency = actual_efficiency
        
        # 4. 시간적 변동성 고려
        temporal_efficiency = 0.95  # 기본값 (5% 변동성)
        if 'performance_analysis' in self.log_metrics:
            variance = self.log_metrics['performance_analysis']['performance_variance']
            # 변동성이 클수록 효율성 저하
            temporal_efficiency = max(0.8, 1.0 - (variance / 1_000_000))  # 정규화
        
        print(f"  시간적 효율성: {temporal_efficiency:.4f}")
        
        # 5. 로그 기반 예측값 계산
        predicted_throughput = envelope_bandwidth * actual_efficiency * bottleneck_efficiency * temporal_efficiency
        
        print(f"  예측 처리량: {predicted_throughput:.2f} MB/s")
        
        return {
            'predicted': predicted_throughput,
            'components': {
                'envelope_bandwidth': envelope_bandwidth,
                'actual_efficiency': actual_efficiency,
                'bottleneck_efficiency': bottleneck_efficiency,
                'temporal_efficiency': temporal_efficiency,
                'total_efficiency': actual_efficiency * bottleneck_efficiency * temporal_efficiency
            },
            'bottleneck_breakdown': bottleneck_analysis
        }
    
    def validate_log_model(self):
        """로그 기반 모델 검증"""
        print("\n=== 로그 기반 모델 검증 ===")
        
        # 현재 실험 데이터로 검증
        actual_throughput = self.model['actual_measurements']['throughput_mb_s']
        device_bandwidth = self.model['performance_characteristics']['device_bandwidth']
        
        # 예측
        prediction = self.predict_log_based(device_bandwidth)
        predicted_throughput = prediction['predicted']
        
        # 오류율 계산
        error_rate = abs(predicted_throughput - actual_throughput) / actual_throughput
        
        print(f"\n검증 결과:")
        print(f"  예측값: {predicted_throughput:.2f} MB/s")
        print(f"  실제값: {actual_throughput:.1f} MB/s")
        print(f"  오류율: {error_rate:.3f} ({error_rate*100:.1f}%)")
        
        accuracy = 'Excellent' if error_rate < 0.1 else 'Good' if error_rate < 0.3 else 'Poor'
        print(f"  정확도: {accuracy}")
        
        return {
            'predicted': predicted_throughput,
            'actual': actual_throughput,
            'error_rate': error_rate,
            'accuracy': accuracy,
            'components': prediction['components']
        }
    
    def save_log_model(self, validation_result):
        """로그 기반 모델 저장"""
        print("\n=== 로그 기반 모델 저장 ===")
        
        final_model = {
            'model_info': self.model,
            'log_metrics': self.log_metrics,
            'validation_result': validation_result,
            'model_insights': {
                'actual_efficiency': self.model['actual_measurements']['actual_efficiency'],
                'bottleneck_severity': self.model['performance_characteristics']['bottleneck_severity'],
                'key_bottlenecks': list(self.model['bottleneck_analysis'].keys()),
                'performance_characteristics': self.model['performance_characteristics']
            }
        }
        
        # JSON 파일로 저장
        output_file = Path("fillrandom_log_based_model.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_model, f, indent=2, ensure_ascii=False)
        
        print(f"로그 기반 모델이 {output_file}에 저장되었습니다.")
        
        return final_model

def main():
    """메인 함수"""
    print("=== FillRandom 로그 기반 정교한 모델 ===")
    
    # 로그 기반 모델 생성
    log_model = FillRandomLogBasedModel()
    
    # 로그 기반 모델 검증
    validation_result = log_model.validate_log_model()
    
    # 로그 기반 모델 저장
    final_model = log_model.save_log_model(validation_result)
    
    print(f"\n=== FillRandom 로그 기반 모델 완료 ===")
    print("주요 특징:")
    print("1. 실제 FillRandom 로그 데이터 기반")
    print("2. 병목 현상 정확한 분석")
    print("3. 시간별 성능 변화 고려")
    print("4. 측정된 실제 효율성 사용")
    print("5. 장치 특성과 워크로드 특성 통합")

if __name__ == "__main__":
    main()


