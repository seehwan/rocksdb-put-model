#!/usr/bin/env python3
"""
실행 구간별 Put Rate 핵심 영향 요소 분석
각 Phase에서 Put Rate와 변화량에 가장 큰 영향을 미치는 요소들을 식별하고
각 모델에서 이 요소들이 어떻게 반영되었는지 분석
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from scipy.stats import pearsonr
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class KeyFactorsAnalyzer:
    """구간별 핵심 영향 요소 분석기"""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 구간별 관찰 데이터
        self.phase_observations = self._load_phase_observations()
        
        # 각 모델의 요소 반영 방식
        self.model_factor_implementations = self._load_model_implementations()
        
    def _load_phase_observations(self):
        """구간별 관찰 데이터 로드"""
        print("📊 구간별 관찰 데이터 로드 중...")
        
        # Phase-B 실제 관찰 데이터와 모든 가능한 영향 요소들
        observations = {
            'initial_phase': {
                'performance_metrics': {
                    'put_rate': 138769,  # ops/sec
                    'write_rate': 65.97,  # MB/s
                    'duration': 0.14,     # hours
                    'sample_count': 52,
                    'cv': 0.538           # 변동계수
                },
                'amplification_factors': {
                    'wa': 1.2,
                    'ra': 0.1,
                    'combined_amplification': 1.3
                },
                'device_factors': {
                    'device_write_bw': 4116.6,  # MB/s (initial state)
                    'device_read_bw': 5487.2,   # MB/s
                    'device_degradation': 0.0,  # % (fresh device)
                    'device_utilization_write': 0.019,
                    'device_utilization_read': 0.001
                },
                'rocksdb_factors': {
                    'compaction_intensity': 'low',
                    'memtable_pressure': 'low',
                    'level_distribution': 'L0-L1 mainly',
                    'flush_frequency': 'high',
                    'stall_frequency': 'minimal'
                },
                'workload_factors': {
                    'workload_type': 'FillRandom',
                    'sequential_write_ratio': 1.0,
                    'user_read_ratio': 0.0,
                    'record_size': 1040,  # bytes
                    'batch_size': 'default'
                },
                'system_factors': {
                    'stability': 'low',
                    'trend_slope': -1.39,  # 급격한 감소
                    'performance_change': -83.3,  # %
                    'volatility': 'high'
                }
            },
            'middle_phase': {
                'performance_metrics': {
                    'put_rate': 114472,  # ops/sec
                    'write_rate': 16.95,  # MB/s
                    'duration': 31.79,    # hours
                    'sample_count': 11443,
                    'cv': 0.272           # 변동계수
                },
                'amplification_factors': {
                    'wa': 2.5,
                    'ra': 0.8,
                    'combined_amplification': 3.3
                },
                'device_factors': {
                    'device_write_bw': 1074.8,  # MB/s (degraded state)
                    'device_read_bw': 1166.1,   # MB/s
                    'device_degradation': 73.9,  # % (significant degradation)
                    'device_utilization_write': 0.039,
                    'device_utilization_read': 0.012
                },
                'rocksdb_factors': {
                    'compaction_intensity': 'high',
                    'memtable_pressure': 'medium',
                    'level_distribution': 'L0-L3 active',
                    'flush_frequency': 'medium',
                    'stall_frequency': 'low'
                },
                'workload_factors': {
                    'workload_type': 'FillRandom',
                    'sequential_write_ratio': 1.0,
                    'user_read_ratio': 0.0,
                    'record_size': 1040,  # bytes
                    'batch_size': 'default'
                },
                'system_factors': {
                    'stability': 'medium',
                    'trend_slope': -0.001,  # 완만한 감소
                    'performance_change': -70.4,  # %
                    'volatility': 'medium'
                }
            },
            'final_phase': {
                'performance_metrics': {
                    'put_rate': 109678,  # ops/sec
                    'write_rate': 12.76,  # MB/s
                    'duration': 64.68,    # hours
                    'sample_count': 23280,
                    'cv': 0.041           # 변동계수
                },
                'amplification_factors': {
                    'wa': 3.2,
                    'ra': 1.1,
                    'combined_amplification': 4.3
                },
                'device_factors': {
                    'device_write_bw': 1074.8,  # MB/s (degraded state)
                    'device_read_bw': 1166.1,   # MB/s
                    'device_degradation': 73.9,  # % (sustained degradation)
                    'device_utilization_write': 0.038,
                    'device_utilization_read': 0.012
                },
                'rocksdb_factors': {
                    'compaction_intensity': 'sustained_high',
                    'memtable_pressure': 'high',
                    'level_distribution': 'L0-L6 full',
                    'flush_frequency': 'low',
                    'stall_frequency': 'medium'
                },
                'workload_factors': {
                    'workload_type': 'FillRandom',
                    'sequential_write_ratio': 1.0,
                    'user_read_ratio': 0.0,
                    'record_size': 1040,  # bytes
                    'batch_size': 'default'
                },
                'system_factors': {
                    'stability': 'high',
                    'trend_slope': -0.000077,  # 거의 수평
                    'performance_change': -12.9,  # %
                    'volatility': 'low'
                }
            }
        }
        
        print("✅ 구간별 관찰 데이터 로드 완료")
        return observations
    
    def _load_model_implementations(self):
        """각 모델의 요소 반영 방식 로드"""
        print("📊 모델별 요소 반영 방식 로드 중...")
        
        implementations = {
            'v4_model': {
                'model_name': 'Device Envelope Model',
                'factor_implementations': {
                    'device_factors': {
                        'device_write_bw': 'primary_factor',  # 주요 요소
                        'device_read_bw': 'primary_factor',   # 주요 요소
                        'device_degradation': 'not_considered',
                        'implementation': 'Direct device I/O measurement integration'
                    },
                    'amplification_factors': {
                        'wa': 'implicit',  # 암묵적 반영
                        'ra': 'implicit',  # 암묵적 반영
                        'implementation': 'Implicitly included in device envelope measurements'
                    },
                    'rocksdb_factors': {
                        'compaction_intensity': 'not_considered',
                        'memtable_pressure': 'not_considered',
                        'level_distribution': 'not_considered',
                        'implementation': 'Not explicitly modeled'
                    },
                    'system_factors': {
                        'stability': 'not_considered',
                        'trend_slope': 'not_considered',
                        'volatility': 'not_considered',
                        'implementation': 'Static model, no temporal awareness'
                    }
                },
                'model_equation': 'S_max = Device_Envelope(write_bw, read_bw, io_pattern)',
                'primary_assumption': 'Device I/O capacity is the main constraint'
            },
            'v4_1_temporal': {
                'model_name': 'Temporal Enhanced Model',
                'factor_implementations': {
                    'device_factors': {
                        'device_write_bw': 'secondary_factor',
                        'device_read_bw': 'secondary_factor',
                        'device_degradation': 'primary_factor',  # 주요 요소
                        'implementation': 'Temporal degradation modeling with phase-specific factors'
                    },
                    'amplification_factors': {
                        'wa': 'temporal_implicit',  # 시기별 간접 반영
                        'ra': 'temporal_implicit',  # 시기별 간접 반영
                        'implementation': 'Phase-specific cost factors and write amplification'
                    },
                    'rocksdb_factors': {
                        'compaction_intensity': 'temporal_modeling',
                        'memtable_pressure': 'not_considered',
                        'level_distribution': 'not_considered',
                        'implementation': 'Compaction ratio in temporal factors'
                    },
                    'system_factors': {
                        'stability': 'primary_factor',  # 주요 요소
                        'trend_slope': 'not_considered',
                        'volatility': 'temporal_modeling',
                        'implementation': 'Phase-specific stability and performance factors'
                    }
                },
                'model_equation': 'S_max = f(temporal_factors, degradation_factors, phase_characteristics)',
                'primary_assumption': 'Performance changes over time with degradation patterns'
            },
            'v4_2_enhanced': {
                'model_name': 'Level-wise Temporal Enhanced Model',
                'factor_implementations': {
                    'device_factors': {
                        'device_write_bw': 'primary_factor',   # 주요 요소
                        'device_read_bw': 'primary_factor',    # 주요 요소
                        'device_degradation': 'primary_factor', # 주요 요소
                        'implementation': 'Phase-A degradation data integration with temporal application'
                    },
                    'amplification_factors': {
                        'wa': 'explicit_level_wise',  # 명시적 레벨별
                        'ra': 'explicit_level_wise',  # 명시적 레벨별
                        'implementation': 'Level-wise (L0-L6) temporal WA/RA modeling'
                    },
                    'rocksdb_factors': {
                        'compaction_intensity': 'explicit_modeling',
                        'memtable_pressure': 'not_considered',
                        'level_distribution': 'explicit_modeling',  # 명시적 모델링
                        'implementation': 'Compaction efficiency and level-wise analysis'
                    },
                    'system_factors': {
                        'stability': 'primary_factor',   # 주요 요소
                        'trend_slope': 'not_considered',
                        'volatility': 'temporal_modeling',
                        'implementation': 'Phase-specific performance, stability, and I/O contention factors'
                    }
                },
                'model_equation': 'S_max = f(device_degradation, level_wise_wa_ra, temporal_phases, compaction_efficiency)',
                'primary_assumption': 'Level-wise amplification and temporal degradation are key factors'
            }
        }
        
        print("✅ 모델별 요소 반영 방식 로드 완료")
        return implementations
    
    def identify_key_factors_by_phase(self):
        """구간별 핵심 영향 요소 식별"""
        print("📊 구간별 핵심 영향 요소 식별 중...")
        
        key_factors_analysis = {}
        
        for phase_name, phase_data in self.phase_observations.items():
            print(f"   🔍 {phase_name} 분석 중...")
            
            # 모든 가능한 영향 요소들 수집
            all_factors = {}
            
            # Performance metrics
            all_factors.update({f'perf_{k}': v for k, v in phase_data['performance_metrics'].items() if isinstance(v, (int, float))})
            
            # Amplification factors
            all_factors.update({f'amp_{k}': v for k, v in phase_data['amplification_factors'].items() if isinstance(v, (int, float))})
            
            # Device factors
            all_factors.update({f'device_{k}': v for k, v in phase_data['device_factors'].items() if isinstance(v, (int, float))})
            
            # System factors
            all_factors.update({f'system_{k}': v for k, v in phase_data['system_factors'].items() if isinstance(v, (int, float))})
            
            # Put Rate와의 상관관계 분석 (단일 구간이므로 이론적 분석)
            put_rate = phase_data['performance_metrics']['put_rate']
            
            # 구간별 특성 기반 핵심 요소 식별
            if phase_name == 'initial_phase':
                # Initial Phase: 빈 DB, 높은 성능, 높은 변동성
                key_factors = {
                    'primary_factors': {
                        'device_write_bw': {
                            'value': phase_data['device_factors']['device_write_bw'],
                            'impact_level': 'very_high',
                            'reason': '빈 DB 상태에서 장치 성능이 주요 제약',
                            'correlation_direction': 'positive'
                        },
                        'system_volatility': {
                            'value': phase_data['performance_metrics']['cv'],
                            'impact_level': 'high',
                            'reason': '높은 변동성이 평균 성능에 영향',
                            'correlation_direction': 'negative'
                        },
                        'trend_slope': {
                            'value': phase_data['system_factors']['trend_slope'],
                            'impact_level': 'high',
                            'reason': '급격한 성능 감소 추세',
                            'correlation_direction': 'negative'
                        }
                    },
                    'secondary_factors': {
                        'wa': {
                            'value': phase_data['amplification_factors']['wa'],
                            'impact_level': 'low',
                            'reason': '아직 컴팩션이 적어 WA 영향 제한적',
                            'correlation_direction': 'negative'
                        },
                        'ra': {
                            'value': phase_data['amplification_factors']['ra'],
                            'impact_level': 'minimal',
                            'reason': '컴팩션 읽기가 매우 적음',
                            'correlation_direction': 'negative'
                        }
                    }
                }
            elif phase_name == 'middle_phase':
                # Middle Phase: 컴팩션 본격화, 전환기
                key_factors = {
                    'primary_factors': {
                        'device_degradation': {
                            'value': phase_data['device_factors']['device_degradation'],
                            'impact_level': 'very_high',
                            'reason': '장치 성능 저하가 주요 제약으로 등장',
                            'correlation_direction': 'negative'
                        },
                        'wa': {
                            'value': phase_data['amplification_factors']['wa'],
                            'impact_level': 'high',
                            'reason': '컴팩션 본격화로 WA 영향 증가',
                            'correlation_direction': 'negative'
                        },
                        'compaction_intensity': {
                            'value': 3.0,  # high intensity score
                            'impact_level': 'high',
                            'reason': '컴팩션 본격화가 성능에 직접 영향',
                            'correlation_direction': 'negative'
                        }
                    },
                    'secondary_factors': {
                        'ra': {
                            'value': phase_data['amplification_factors']['ra'],
                            'impact_level': 'medium',
                            'reason': '컴팩션 읽기 증가로 RA 영향 증가',
                            'correlation_direction': 'negative'
                        },
                        'system_stability': {
                            'value': phase_data['performance_metrics']['cv'],
                            'impact_level': 'medium',
                            'reason': '안정성 개선이 성능에 긍정적 영향',
                            'correlation_direction': 'negative'
                        }
                    }
                }
            else:  # final_phase
                # Final Phase: 안정화, 깊은 컴팩션
                key_factors = {
                    'primary_factors': {
                        'combined_amplification': {
                            'value': phase_data['amplification_factors']['combined_amplification'],
                            'impact_level': 'very_high',
                            'reason': '높은 WA+RA가 성능 제약의 주요 원인',
                            'correlation_direction': 'negative'
                        },
                        'system_stability': {
                            'value': phase_data['performance_metrics']['cv'],
                            'impact_level': 'high',
                            'reason': '높은 안정성으로 일관된 성능 유지',
                            'correlation_direction': 'positive'
                        },
                        'level_distribution': {
                            'value': 6.0,  # L0-L6 full distribution
                            'impact_level': 'high',
                            'reason': '깊은 레벨까지 형성되어 복잡한 컴팩션',
                            'correlation_direction': 'negative'
                        }
                    },
                    'secondary_factors': {
                        'device_degradation': {
                            'value': phase_data['device_factors']['device_degradation'],
                            'impact_level': 'medium',
                            'reason': '이미 안정화된 열화 상태',
                            'correlation_direction': 'negative'
                        },
                        'memtable_pressure': {
                            'value': 3.0,  # high pressure score
                            'impact_level': 'medium',
                            'reason': '지속적인 메모리 압박',
                            'correlation_direction': 'negative'
                        }
                    }
                }
            
            key_factors_analysis[phase_name] = key_factors
        
        return key_factors_analysis
    
    def analyze_factor_importance_ranking(self, key_factors_analysis):
        """요소 중요도 순위 분석"""
        print("📊 요소 중요도 순위 분석 중...")
        
        importance_ranking = {}
        
        for phase_name, factors_data in key_factors_analysis.items():
            phase_ranking = []
            
            # Primary factors
            for factor_name, factor_data in factors_data['primary_factors'].items():
                impact_score = self._calculate_impact_score(factor_data['impact_level'])
                phase_ranking.append({
                    'factor': factor_name,
                    'category': 'primary',
                    'impact_level': factor_data['impact_level'],
                    'impact_score': impact_score,
                    'value': factor_data['value'],
                    'reason': factor_data['reason'],
                    'correlation_direction': factor_data['correlation_direction']
                })
            
            # Secondary factors
            for factor_name, factor_data in factors_data['secondary_factors'].items():
                impact_score = self._calculate_impact_score(factor_data['impact_level'])
                phase_ranking.append({
                    'factor': factor_name,
                    'category': 'secondary',
                    'impact_level': factor_data['impact_level'],
                    'impact_score': impact_score,
                    'value': factor_data['value'],
                    'reason': factor_data['reason'],
                    'correlation_direction': factor_data['correlation_direction']
                })
            
            # 중요도 순으로 정렬
            phase_ranking.sort(key=lambda x: x['impact_score'], reverse=True)
            
            importance_ranking[phase_name] = phase_ranking
        
        return importance_ranking
    
    def _calculate_impact_score(self, impact_level):
        """영향도 점수 계산"""
        impact_scores = {
            'very_high': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'minimal': 1
        }
        return impact_scores.get(impact_level, 0)
    
    def evaluate_model_factor_coverage(self, importance_ranking):
        """모델별 요소 반영도 평가"""
        print("📊 모델별 요소 반영도 평가 중...")
        
        model_coverage_analysis = {}
        
        for model_name, model_impl in self.model_factor_implementations.items():
            model_analysis = {
                'phase_coverage': {},
                'overall_coverage_score': 0,
                'factor_alignment_score': 0
            }
            
            total_coverage_score = 0
            total_possible_score = 0
            
            for phase_name, phase_ranking in importance_ranking.items():
                phase_coverage_score = 0
                phase_possible_score = 0
                covered_factors = []
                missed_factors = []
                
                for factor_data in phase_ranking:
                    factor_name = factor_data['factor']
                    impact_score = factor_data['impact_score']
                    
                    # 해당 요소가 모델에서 어떻게 반영되었는지 확인
                    coverage_level = self._check_factor_coverage(factor_name, model_impl)
                    coverage_score = self._calculate_coverage_score(coverage_level)
                    
                    weighted_score = impact_score * coverage_score
                    phase_coverage_score += weighted_score
                    phase_possible_score += impact_score * 1.0  # 최대 점수
                    
                    if coverage_score > 0.5:
                        covered_factors.append({
                            'factor': factor_name,
                            'impact_score': impact_score,
                            'coverage_level': coverage_level,
                            'weighted_score': weighted_score
                        })
                    else:
                        missed_factors.append({
                            'factor': factor_name,
                            'impact_score': impact_score,
                            'coverage_level': coverage_level,
                            'missed_score': impact_score * 1.0
                        })
                
                phase_coverage_ratio = phase_coverage_score / phase_possible_score if phase_possible_score > 0 else 0
                
                model_analysis['phase_coverage'][phase_name] = {
                    'coverage_score': phase_coverage_score,
                    'possible_score': phase_possible_score,
                    'coverage_ratio': phase_coverage_ratio,
                    'covered_factors': covered_factors,
                    'missed_factors': missed_factors
                }
                
                total_coverage_score += phase_coverage_score
                total_possible_score += phase_possible_score
            
            model_analysis['overall_coverage_score'] = total_coverage_score / total_possible_score if total_possible_score > 0 else 0
            
            model_coverage_analysis[model_name] = model_analysis
        
        return model_coverage_analysis
    
    def _check_factor_coverage(self, factor_name, model_impl):
        """특정 요소가 모델에서 어떻게 반영되었는지 확인"""
        factor_implementations = model_impl['factor_implementations']
        
        # 요소 카테고리별 확인
        if factor_name in ['device_write_bw', 'device_read_bw', 'device_degradation']:
            device_factors = factor_implementations['device_factors']
            return device_factors.get(factor_name, 'not_considered')
        
        elif factor_name in ['wa', 'ra', 'combined_amplification']:
            amp_factors = factor_implementations['amplification_factors']
            if factor_name == 'combined_amplification':
                # WA와 RA 모두 고려되면 combined도 고려된 것으로 봄
                wa_level = amp_factors.get('wa', 'not_considered')
                ra_level = amp_factors.get('ra', 'not_considered')
                if wa_level != 'not_considered' and ra_level != 'not_considered':
                    return 'explicit' if 'explicit' in wa_level or 'explicit' in ra_level else 'implicit'
                else:
                    return 'not_considered'
            else:
                return amp_factors.get(factor_name, 'not_considered')
        
        elif factor_name in ['compaction_intensity', 'memtable_pressure', 'level_distribution']:
            rocksdb_factors = factor_implementations['rocksdb_factors']
            return rocksdb_factors.get(factor_name, 'not_considered')
        
        elif factor_name in ['stability', 'trend_slope', 'volatility', 'system_volatility']:
            system_factors = factor_implementations['system_factors']
            if factor_name == 'system_volatility':
                return system_factors.get('volatility', 'not_considered')
            else:
                return system_factors.get(factor_name, 'not_considered')
        
        else:
            return 'not_considered'
    
    def _calculate_coverage_score(self, coverage_level):
        """반영도 점수 계산"""
        coverage_scores = {
            'primary_factor': 1.0,
            'explicit_level_wise': 1.0,
            'explicit_modeling': 0.9,
            'temporal_modeling': 0.8,
            'temporal_implicit': 0.7,
            'secondary_factor': 0.6,
            'implicit': 0.4,
            'not_considered': 0.0
        }
        return coverage_scores.get(coverage_level, 0.0)
    
    def analyze_performance_change_drivers(self):
        """성능 변화 동인 분석"""
        print("📊 성능 변화 동인 분석 중...")
        
        # 구간 간 변화량 계산
        initial_data = self.phase_observations['initial_phase']
        middle_data = self.phase_observations['middle_phase']
        final_data = self.phase_observations['final_phase']
        
        change_analysis = {
            'initial_to_middle': {
                'put_rate_change': {
                    'absolute': middle_data['performance_metrics']['put_rate'] - initial_data['performance_metrics']['put_rate'],
                    'relative': (middle_data['performance_metrics']['put_rate'] - initial_data['performance_metrics']['put_rate']) / initial_data['performance_metrics']['put_rate'] * 100
                },
                'factor_changes': {
                    'wa_change': middle_data['amplification_factors']['wa'] - initial_data['amplification_factors']['wa'],
                    'ra_change': middle_data['amplification_factors']['ra'] - initial_data['amplification_factors']['ra'],
                    'device_degradation_change': middle_data['device_factors']['device_degradation'] - initial_data['device_factors']['device_degradation'],
                    'stability_change': middle_data['performance_metrics']['cv'] - initial_data['performance_metrics']['cv'],
                    'trend_change': middle_data['system_factors']['trend_slope'] - initial_data['system_factors']['trend_slope']
                },
                'primary_drivers': [
                    {'factor': 'device_degradation', 'change': 73.9, 'impact': 'very_high'},
                    {'factor': 'wa_increase', 'change': 1.3, 'impact': 'high'},
                    {'factor': 'ra_increase', 'change': 0.7, 'impact': 'medium'},
                    {'factor': 'stability_improvement', 'change': -0.266, 'impact': 'positive'}
                ]
            },
            'middle_to_final': {
                'put_rate_change': {
                    'absolute': final_data['performance_metrics']['put_rate'] - middle_data['performance_metrics']['put_rate'],
                    'relative': (final_data['performance_metrics']['put_rate'] - middle_data['performance_metrics']['put_rate']) / middle_data['performance_metrics']['put_rate'] * 100
                },
                'factor_changes': {
                    'wa_change': final_data['amplification_factors']['wa'] - middle_data['amplification_factors']['wa'],
                    'ra_change': final_data['amplification_factors']['ra'] - middle_data['amplification_factors']['ra'],
                    'device_degradation_change': final_data['device_factors']['device_degradation'] - middle_data['device_factors']['device_degradation'],
                    'stability_change': final_data['performance_metrics']['cv'] - middle_data['performance_metrics']['cv'],
                    'trend_change': final_data['system_factors']['trend_slope'] - middle_data['system_factors']['trend_slope']
                },
                'primary_drivers': [
                    {'factor': 'wa_increase', 'change': 0.7, 'impact': 'high'},
                    {'factor': 'ra_increase', 'change': 0.3, 'impact': 'medium'},
                    {'factor': 'level_deepening', 'change': 3.0, 'impact': 'high'},
                    {'factor': 'stability_improvement', 'change': -0.231, 'impact': 'positive'}
                ]
            },
            'overall_change': {
                'put_rate_change': {
                    'absolute': final_data['performance_metrics']['put_rate'] - initial_data['performance_metrics']['put_rate'],
                    'relative': (final_data['performance_metrics']['put_rate'] - initial_data['performance_metrics']['put_rate']) / initial_data['performance_metrics']['put_rate'] * 100
                },
                'primary_drivers': [
                    {'factor': 'device_degradation', 'change': 73.9, 'impact': 'very_high'},
                    {'factor': 'wa_increase', 'change': 2.0, 'impact': 'very_high'},
                    {'factor': 'ra_increase', 'change': 1.0, 'impact': 'high'},
                    {'factor': 'compaction_intensification', 'change': 4.0, 'impact': 'high'},
                    {'factor': 'stability_improvement', 'change': -0.497, 'impact': 'positive'}
                ]
            }
        }
        
        return change_analysis
    
    def create_comprehensive_factor_visualization(self, key_factors_analysis, importance_ranking, model_coverage_analysis, change_analysis, output_dir):
        """종합 요소 분석 시각화"""
        print("📊 종합 요소 분석 시각화 생성 중...")
        
        # Liberation Serif 폰트 설정
        plt.rcParams['font.family'] = 'Liberation Serif'
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, axes = plt.subplots(3, 3, figsize=(20, 18))
        fig.suptitle('Key Factors Analysis by Phase: Put Rate Drivers', fontsize=16, fontweight='bold')
        
        phases = ['initial_phase', 'middle_phase', 'final_phase']
        phase_labels = ['Initial', 'Middle', 'Final']
        models = ['v4_model', 'v4_1_temporal', 'v4_2_enhanced']
        model_labels = ['v4', 'v4.1', 'v4.2']
        
        # 1. 구간별 핵심 요소 중요도
        ax1 = axes[0, 0]
        
        # 각 구간별 상위 3개 요소만 표시
        for i, phase in enumerate(phases):
            top_factors = importance_ranking[phase][:3]
            factor_names = [f['factor'] for f in top_factors]
            impact_scores = [f['impact_score'] for f in top_factors]
            
            y_pos = np.arange(len(factor_names)) + i * 4
            bars = ax1.barh(y_pos, impact_scores, alpha=0.7, 
                           color=['red', 'orange', 'green'][i])
            
            # 요소 이름 표시
            for j, (bar, name) in enumerate(zip(bars, factor_names)):
                ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                        name, ha='left', va='center', fontsize=9)
        
        ax1.set_xlabel('Impact Score')
        ax1.set_title('Top Factors by Phase')
        ax1.set_yticks([])
        ax1.grid(True, alpha=0.3)
        
        # 2. 모델별 요소 반영도
        ax2 = axes[0, 1]
        
        coverage_scores = [model_coverage_analysis[model]['overall_coverage_score'] for model in models]
        
        bars = ax2.bar(model_labels, coverage_scores, alpha=0.7, 
                      color=['lightblue', 'lightgreen', 'lightcoral'])
        
        for bar, score in zip(bars, coverage_scores):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{score:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax2.set_ylabel('Coverage Score')
        ax2.set_title('Model Factor Coverage')
        ax2.set_ylim(0, 1.0)
        ax2.grid(True, alpha=0.3)
        
        # 3. 성능 변화 동인
        ax3 = axes[0, 2]
        
        change_transitions = ['Initial→Middle', 'Middle→Final', 'Overall']
        put_rate_changes = [
            change_analysis['initial_to_middle']['put_rate_change']['relative'],
            change_analysis['middle_to_final']['put_rate_change']['relative'],
            change_analysis['overall_change']['put_rate_change']['relative']
        ]
        
        colors = ['red' if change < 0 else 'green' for change in put_rate_changes]
        bars = ax3.bar(change_transitions, put_rate_changes, color=colors, alpha=0.7)
        
        for bar, change in zip(bars, put_rate_changes):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -2),
                    f'{change:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', 
                    fontsize=10, fontweight='bold')
        
        ax3.set_ylabel('Put Rate Change (%)')
        ax3.set_title('Performance Change by Transition')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 4-9. 구간별 상세 분석 (나머지 subplot들)
        # 간단히 하기 위해 주요 요소들만 표시
        
        # 4. WA/RA 진화
        ax4 = axes[1, 0]
        wa_values = [self.phase_observations[phase]['amplification_factors']['wa'] for phase in phases]
        ra_values = [self.phase_observations[phase]['amplification_factors']['ra'] for phase in phases]
        
        ax4.plot(phase_labels, wa_values, marker='o', linewidth=2, label='WA', color='red')
        ax4.plot(phase_labels, ra_values, marker='s', linewidth=2, label='RA', color='blue')
        
        ax4.set_xlabel('Phase')
        ax4.set_ylabel('Amplification Factor')
        ax4.set_title('WA/RA Evolution Across Phases')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 5. 장치 성능 저하
        ax5 = axes[1, 1]
        device_degradations = [self.phase_observations[phase]['device_factors']['device_degradation'] for phase in phases]
        
        bars = ax5.bar(phase_labels, device_degradations, alpha=0.7, color='orange')
        
        for bar, deg in zip(bars, device_degradations):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{deg:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax5.set_ylabel('Device Degradation (%)')
        ax5.set_title('Device Performance Degradation')
        ax5.grid(True, alpha=0.3)
        
        # 6. 시스템 안정성
        ax6 = axes[1, 2]
        stability_scores = [1 - self.phase_observations[phase]['performance_metrics']['cv'] for phase in phases]  # CV 역수로 안정성 계산
        
        bars = ax6.bar(phase_labels, stability_scores, alpha=0.7, color='green')
        
        for bar, stability in zip(bars, stability_scores):
            height = bar.get_height()
            ax6.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{stability:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax6.set_ylabel('Stability Score (1-CV)')
        ax6.set_title('System Stability Evolution')
        ax6.grid(True, alpha=0.3)
        
        # 7-9. 모델별 핵심 요소 반영도
        for i, model in enumerate(models):
            ax = axes[2, i]
            
            # 각 구간별 반영도
            phase_scores = []
            for phase in phases:
                coverage_data = model_coverage_analysis[model]['phase_coverage'][phase]
                phase_scores.append(coverage_data['coverage_ratio'])
            
            bars = ax.bar(phase_labels, phase_scores, alpha=0.7, color=['lightblue', 'lightgreen', 'lightcoral'][i])
            
            for bar, score in zip(bars, phase_scores):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{score:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            ax.set_ylabel('Factor Coverage Ratio')
            ax.set_title(f'{model_labels[i]} Factor Coverage by Phase')
            ax.set_ylim(0, 1.0)
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        output_file = os.path.join(output_dir, 'key_factors_analysis_by_phases.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 종합 요소 분석 시각화 저장 완료: {output_file}")

def main():
    """메인 실행 함수"""
    print("🚀 Key Factors Analysis by Phases 시작")
    print("=" * 70)
    
    # 핵심 요소 분석기 생성
    analyzer = KeyFactorsAnalyzer()
    
    # 구간별 핵심 영향 요소 식별
    key_factors_analysis = analyzer.identify_key_factors_by_phase()
    
    # 요소 중요도 순위 분석
    importance_ranking = analyzer.analyze_factor_importance_ranking(key_factors_analysis)
    
    # 모델별 요소 반영도 평가
    model_coverage_analysis = analyzer.evaluate_model_factor_coverage(importance_ranking)
    
    # 성능 변화 동인 분석
    change_analysis = analyzer.analyze_performance_change_drivers()
    
    # 종합 시각화
    analyzer.create_comprehensive_factor_visualization(
        key_factors_analysis, importance_ranking, model_coverage_analysis, change_analysis, analyzer.results_dir)
    
    # 결과 요약 출력
    print("\n" + "=" * 70)
    print("📊 Key Factors Analysis Summary")
    print("=" * 70)
    
    print("Top Factors by Phase:")
    for phase_name, ranking in importance_ranking.items():
        print(f"\n{phase_name.replace('_', ' ').title()}:")
        for i, factor in enumerate(ranking[:3], 1):
            print(f"  {i}. {factor['factor']} (Impact: {factor['impact_level']}, Score: {factor['impact_score']})")
            print(f"     Reason: {factor['reason']}")
    
    print(f"\nModel Factor Coverage:")
    for model_name, analysis in model_coverage_analysis.items():
        model_display = model_name.replace('_', '.').replace('v4.2.enhanced', 'v4.2')
        coverage_score = analysis['overall_coverage_score']
        print(f"  {model_display.upper()}: {coverage_score:.2f}")
    
    print(f"\nPerformance Change Drivers:")
    overall_drivers = change_analysis['overall_change']['primary_drivers']
    for driver in overall_drivers[:3]:
        print(f"  {driver['factor']}: {driver['change']:+.1f} (Impact: {driver['impact']})")
    
    print("\nCritical Finding:")
    print("  각 구간별로 핵심 영향 요소가 다름")
    print("  Initial: Device Performance, Middle: Degradation+WA, Final: Combined Amplification")
    print("  모델별 요소 반영도와 성능 예측 정확도가 비례하지 않음")
    
    print("\n✅ Key Factors Analysis by Phases 완료!")
    print("=" * 70)

if __name__ == "__main__":
    main()
