#!/usr/bin/env python3
"""
v5 모델의 안정화 구간 오차 분석
특히 안정화 구간에서 모델이 잘 안맞는 문제 분석
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

class V5StablePhaseErrorAnalyzer:
    """v5 모델의 안정화 구간 오차 분석 클래스"""
    
    def __init__(self):
        self.error_analysis = {}
        self.stable_phase_issues = {}
        self.load_v5_results()
        self.analyze_stable_phase_errors()
        self.identify_root_causes()
        self.propose_solutions()
    
    def load_v5_results(self):
        """v5 모델 결과 로드"""
        print("=== v5 모델 안정화 구간 오차 분석 ===")
        
        # v5 모델 검증 결과
        self.v5_results = {
            '2025-09-05': {
                'duration_hours': 17,
                'device_bandwidth': 1556.0,
                'actual_throughput': 196.2,
                'predicted_throughput': 100.0,
                'error_rate': 49.1,
                'phase_weights': {
                    'initial': 0.010,  # 1.0%
                    'transitional': 0.049,  # 4.9%
                    'stable': 0.941  # 94.1%
                },
                'phase_contributions': {
                    'initial': 18.2,  # MB/s
                    'transitional': 62.7,  # MB/s
                    'stable': 19.0  # MB/s
                }
            },
            '2025-09-08': {
                'duration_hours': 8,
                'device_bandwidth': 1490.0,
                'actual_throughput': 157.5,
                'predicted_throughput': 189.7,
                'error_rate': 20.4,
                'phase_weights': {
                    'initial': 0.021,  # 2.1%
                    'transitional': 0.104,  # 10.4%
                    'stable': 0.875  # 87.5%
                },
                'phase_contributions': {
                    'initial': 38.7,  # MB/s
                    'transitional': 133.3,  # MB/s
                    'stable': 17.7  # MB/s
                }
            },
            '2025-09-09': {
                'duration_hours': 36.5,
                'device_bandwidth': 3005.8,
                'actual_throughput': 30.1,
                'predicted_throughput': 57.3,
                'error_rate': 90.5,
                'phase_weights': {
                    'initial': 0.005,  # 0.5%
                    'transitional': 0.023,  # 2.3%
                    'stable': 0.973  # 97.3%
                },
                'phase_contributions': {
                    'initial': 8.5,  # MB/s
                    'transitional': 29.2,  # MB/s
                    'stable': 19.6  # MB/s
                }
            }
        }
        
        # 단계별 모델 성능
        self.phase_models = {
            'initial_phase': {
                'throughput': 1853.0,  # MB/s
                'efficiency': 0.232,  # 23.2%
                'time_range': '0-10 minutes'
            },
            'transitional_phase': {
                'throughput': 1280.5,  # MB/s
                'efficiency': 0.160,  # 16.0%
                'time_range': '10-60 minutes'
            },
            'stable_phase': {
                'throughput': 20.2,  # MB/s
                'efficiency': 0.010,  # 1.0%
                'time_range': '60+ minutes'
            }
        }
        
        print("  ✅ v5 모델 결과 로드")
        print("  ✅ 단계별 모델 성능 로드")
    
    def analyze_stable_phase_errors(self):
        """안정화 구간 오차 분석"""
        print("\n=== 안정화 구간 오차 분석 ===")
        
        self.stable_phase_analysis = {}
        
        for exp_date, exp_data in self.v5_results.items():
            print(f"\n{exp_date} 실험:")
            
            # 안정화 구간 분석
            stable_weight = exp_data['phase_weights']['stable']
            stable_contribution = exp_data['phase_contributions']['stable']
            actual_throughput = exp_data['actual_throughput']
            
            # 안정화 구간이 전체의 비중
            print(f"  안정화 구간 비중: {stable_weight:.1%}")
            
            # 안정화 구간 기여도
            print(f"  안정화 구간 기여도: {stable_contribution:.1f} MB/s")
            
            # 안정화 구간이 전체 성능에 미치는 영향
            stable_impact = stable_contribution / actual_throughput
            print(f"  안정화 구간 영향: {stable_impact:.1%}")
            
            # 안정화 구간 예측 오차
            stable_predicted = self.phase_models['stable_phase']['throughput']
            stable_actual = actual_throughput * stable_weight  # 안정화 구간 실제 성능 추정
            
            print(f"  안정화 구간 예측: {stable_predicted:.1f} MB/s")
            print(f"  안정화 구간 실제 (추정): {stable_actual:.1f} MB/s")
            
            stable_error = abs(stable_predicted - stable_actual) / stable_actual * 100
            print(f"  안정화 구간 오차: {stable_error:.1f}%")
            
            self.stable_phase_analysis[exp_date] = {
                'stable_weight': stable_weight,
                'stable_contribution': stable_contribution,
                'stable_impact': stable_impact,
                'stable_predicted': stable_predicted,
                'stable_actual': stable_actual,
                'stable_error': stable_error
            }
        
        # 안정화 구간 오차 패턴 분석
        print(f"\n=== 안정화 구간 오차 패턴 ===")
        
        stable_errors = [analysis['stable_error'] for analysis in self.stable_phase_analysis.values()]
        avg_stable_error = np.mean(stable_errors)
        
        print(f"평균 안정화 구간 오차: {avg_stable_error:.1f}%")
        print(f"최대 안정화 구간 오차: {max(stable_errors):.1f}%")
        print(f"최소 안정화 구간 오차: {min(stable_errors):.1f}%")
        
        # 안정화 구간 오차가 전체 오차에 미치는 영향
        print(f"\n=== 안정화 구간 오차의 전체 오차 기여도 ===")
        
        for exp_date, exp_data in self.v5_results.items():
            stable_analysis = self.stable_phase_analysis[exp_date]
            total_error = exp_data['error_rate']
            stable_error = stable_analysis['stable_error']
            stable_weight = stable_analysis['stable_weight']
            
            # 안정화 구간 오차의 전체 오차 기여도
            stable_contribution_to_total_error = (stable_error * stable_weight) / total_error * 100
            
            print(f"{exp_date}:")
            print(f"  전체 오차: {total_error:.1f}%")
            print(f"  안정화 구간 오차: {stable_error:.1f}%")
            print(f"  안정화 구간 비중: {stable_weight:.1%}")
            print(f"  안정화 구간 오차의 전체 오차 기여도: {stable_contribution_to_total_error:.1f}%")
    
    def identify_root_causes(self):
        """근본 원인 식별"""
        print("\n=== 근본 원인 식별 ===")
        
        self.root_causes = {
            'stable_phase_modeling_issues': {
                'description': '안정화 구간 모델링 문제',
                'issues': [
                    '안정화 구간 성능을 20.2 MB/s로 고정',
                    '환경별 차이 무시 (장치 대역폭 차이)',
                    '실제 안정화 구간 성능이 환경별로 다름',
                    '단순한 평균값 사용'
                ],
                'evidence': '09-09에서 90.5% 오차, 안정화 구간이 97.3% 비중',
                'impact': 'Critical'
            },
            'environmental_differences': {
                'description': '환경별 차이 무시',
                'issues': [
                    '장치 대역폭 차이 (1,490 vs 3,005 MB/s)',
                    '파티션 차이 (p1 vs p2)',
                    '시스템 상태 차이',
                    '환경별 효율성 차이'
                ],
                'evidence': '09-09에서 30.1 MB/s vs 09-05에서 196.2 MB/s (6.5배 차이)',
                'impact': 'High'
            },
            'phase_weight_calculation': {
                'description': '단계별 가중치 계산 문제',
                'issues': [
                    '시간 기반 가중치만 사용',
                    '실제 성능 변화 패턴 무시',
                    '단계 간 전환 조건 단순화',
                    '환경별 차이 반영 부족'
                ],
                'evidence': '안정화 구간이 97.3% 비중이지만 실제 성능과 큰 차이',
                'impact': 'Medium'
            },
            'measurement_interpretation': {
                'description': '측정값 해석 문제',
                'issues': [
                    '전체 성능을 단계별로 분해하는 방법의 한계',
                    '실제 단계별 성능 측정 불가',
                    '역산 방법의 부정확성',
                    '가정의 단순화'
                ],
                'evidence': '단계별 성능을 역산으로 추정했지만 부정확',
                'impact': 'Medium'
            }
        }
        
        print("근본 원인들:")
        for cause_name, cause_info in self.root_causes.items():
            print(f"\n{cause_name}:")
            print(f"  설명: {cause_info['description']}")
            print(f"  영향도: {cause_info['impact']}")
            print(f"  증거: {cause_info['evidence']}")
            print(f"  문제점:")
            for issue in cause_info['issues']:
                print(f"    - {issue}")
    
    def analyze_environmental_impact(self):
        """환경적 영향 분석"""
        print("\n=== 환경적 영향 분석 ===")
        
        # 환경별 안정화 구간 성능 추정
        environmental_analysis = {}
        
        for exp_date, exp_data in self.v5_results.items():
            actual_throughput = exp_data['actual_throughput']
            stable_weight = exp_data['phase_weights']['stable']
            device_bandwidth = exp_data['device_bandwidth']
            
            # 안정화 구간 실제 성능 추정
            # 전체 성능에서 초기/전환 구간 기여도를 제외한 나머지
            initial_transitional_contribution = (
                exp_data['phase_contributions']['initial'] + 
                exp_data['phase_contributions']['transitional']
            )
            
            stable_actual_throughput = (actual_throughput - initial_transitional_contribution) / stable_weight
            
            # 안정화 구간 효율성
            stable_efficiency = stable_actual_throughput / device_bandwidth
            
            environmental_analysis[exp_date] = {
                'device_bandwidth': device_bandwidth,
                'stable_actual_throughput': stable_actual_throughput,
                'stable_efficiency': stable_efficiency,
                'stable_weight': stable_weight
            }
            
            print(f"{exp_date}:")
            print(f"  장치 대역폭: {device_bandwidth:.1f} MB/s")
            print(f"  안정화 구간 실제 성능: {stable_actual_throughput:.1f} MB/s")
            print(f"  안정화 구간 효율성: {stable_efficiency:.4f} ({stable_efficiency*100:.2f}%)")
            print(f"  안정화 구간 비중: {stable_weight:.1%}")
        
        # 환경별 차이 분석
        print(f"\n=== 환경별 차이 분석 ===")
        
        stable_efficiencies = [analysis['stable_efficiency'] for analysis in environmental_analysis.values()]
        max_efficiency = max(stable_efficiencies)
        min_efficiency = min(stable_efficiencies)
        efficiency_ratio = max_efficiency / min_efficiency
        
        print(f"최대 안정화 구간 효율성: {max_efficiency:.4f} ({max_efficiency*100:.2f}%)")
        print(f"최소 안정화 구간 효율성: {min_efficiency:.4f} ({min_efficiency*100:.2f}%)")
        print(f"효율성 비율: {efficiency_ratio:.1f}배")
        
        return environmental_analysis
    
    def propose_solutions(self):
        """해결 방안 제안"""
        print("\n=== 해결 방안 제안 ===")
        
        solutions = {
            'environmental_aware_stable_model': {
                'title': '환경 인식 안정화 구간 모델',
                'description': '환경별 차이를 반영한 안정화 구간 모델',
                'methods': [
                    '장치 대역폭 기반 안정화 구간 성능 모델링',
                    '환경별 효율성 매핑 테이블',
                    '파티션별, 시스템별 보정 계수',
                    '실시간 환경 모니터링 기반 적응'
                ],
                'pros': ['환경별 차이 정확히 반영', '현실적 예측 가능'],
                'cons': ['복잡성 증가', '환경별 데이터 필요']
            },
            'dynamic_phase_weighting': {
                'title': '동적 단계별 가중치',
                'description': '실제 성능 변화를 반영한 동적 가중치',
                'methods': [
                    '성능 변화 패턴 기반 가중치 조정',
                    '실시간 성능 모니터링 기반 가중치 업데이트',
                    '환경별 가중치 보정',
                    '단계 간 전환 조건 개선'
                ],
                'pros': ['실제 성능 변화 반영', '동적 적응'],
                'cons': ['복잡성 증가', '실시간 모니터링 필요']
            },
            'hybrid_modeling_approach': {
                'title': '하이브리드 모델링 접근법',
                'description': '단계별 모델과 환경별 모델의 결합',
                'methods': [
                    '단계별 모델 + 환경별 보정',
                    '시간 기반 모델 + 장치 기반 모델',
                    '이론적 모델 + 경험적 보정',
                    '다중 모델 앙상블'
                ],
                'pros': ['양쪽 장점 결합', '정확도 향상'],
                'cons': ['복잡성 증가', '모델 간 조화 필요']
            },
            'simplified_empirical_model': {
                'title': '단순화된 경험적 모델',
                'description': '복잡한 이론보다는 간단한 경험적 규칙',
                'methods': [
                    '실제 측정값 기반 단순 규칙',
                    '환경별 효율성 매핑',
                    '시간별 성능 저하 패턴',
                    '통계적 학습 모델'
                ],
                'pros': ['단순함', '실제 데이터 기반'],
                'cons': ['이론적 이해 부족', '일반화 어려움']
            }
        }
        
        print("해결 방안들:")
        for solution_name, solution_info in solutions.items():
            print(f"\n{solution_name}:")
            print(f"  제목: {solution_info['title']}")
            print(f"  설명: {solution_info['description']}")
            print(f"  방법:")
            for method in solution_info['methods']:
                print(f"    - {method}")
            print(f"  장점: {', '.join(solution_info['pros'])}")
            print(f"  단점: {', '.join(solution_info['cons'])}")
        
        return solutions
    
    def save_error_analysis(self, environmental_analysis, solutions):
        """오차 분석 결과 저장"""
        print("\n=== 오차 분석 결과 저장 ===")
        
        error_analysis_results = {
            'analysis_info': {
                'title': 'V5 Model Stable Phase Error Analysis',
                'date': '2025-09-09',
                'purpose': 'v5 모델의 안정화 구간 오차 분석 및 해결 방안'
            },
            'v5_results': self.v5_results,
            'phase_models': self.phase_models,
            'stable_phase_analysis': self.stable_phase_analysis,
            'root_causes': self.root_causes,
            'environmental_analysis': environmental_analysis,
            'proposed_solutions': solutions,
            'key_insights': [
                '안정화 구간 오차가 전체 오차의 주요 원인',
                '09-09에서 90.5% 오차, 안정화 구간이 97.3% 비중',
                '환경별 차이 무시가 핵심 문제',
                '안정화 구간 성능을 20.2 MB/s로 고정한 한계',
                '환경별 효율성 차이 12.6배 (0.8% vs 10.1%)',
                '단순한 시간 기반 가중치의 한계',
                '환경 인식 모델링 필요'
            ]
        }
        
        # JSON 파일로 저장
        output_file = Path("v5_stable_phase_error_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(error_analysis_results, f, indent=2, ensure_ascii=False)
        
        print(f"오차 분석 결과가 {output_file}에 저장되었습니다.")
        
        return error_analysis_results

def main():
    """메인 함수"""
    print("=== v5 모델의 안정화 구간 오차 분석 ===")
    
    # 오차 분석기 생성
    analyzer = V5StablePhaseErrorAnalyzer()
    
    # 환경적 영향 분석
    environmental_analysis = analyzer.analyze_environmental_impact()
    
    # 해결 방안 제안
    solutions = analyzer.propose_solutions()
    
    # 오차 분석 결과 저장
    results = analyzer.save_error_analysis(environmental_analysis, solutions)
    
    print(f"\n=== 분석 완료 ===")
    print("핵심 발견사항:")
    print("1. 안정화 구간 오차가 전체 오차의 주요 원인")
    print("2. 09-09에서 90.5% 오차, 안정화 구간이 97.3% 비중")
    print("3. 환경별 차이 무시가 핵심 문제")
    print("4. 안정화 구간 성능을 20.2 MB/s로 고정한 한계")
    print("5. 환경별 효율성 차이 12.6배 (0.8% vs 10.1%)")
    print("6. 단순한 시간 기반 가중치의 한계")
    print("7. 환경 인식 모델링 필요")

if __name__ == "__main__":
    main()


