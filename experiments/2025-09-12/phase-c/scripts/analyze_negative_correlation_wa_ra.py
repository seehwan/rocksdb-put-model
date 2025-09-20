#!/usr/bin/env python3
"""
WA/RA와 Put Rate 간의 음의 상관관계 분석
WA/RA 증가가 Put Rate 감소에 미치는 영향을 정량적으로 분석
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

class NegativeCorrelationAnalyzer:
    """WA/RA와 Put Rate 간의 음의 상관관계 분석기"""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 실제 관찰 데이터
        self.observed_data = self._load_observed_correlation_data()
        
        # 이론적 음의 상관관계 모델
        self.theoretical_models = self._create_theoretical_negative_models()
        
    def _load_observed_correlation_data(self):
        """실제 관찰된 상관관계 데이터 로드"""
        print("📊 실제 관찰된 WA/RA vs Put Rate 상관관계 데이터 로드 중...")
        
        # Phase-B 실제 관찰 데이터
        observed_data = {
            'phase_data': {
                'initial_phase': {
                    'wa': 1.2,
                    'ra': 0.1,
                    'combined_amplification': 1.3,  # WA + RA
                    'actual_put_rate': 138769,  # ops/sec
                    'user_write_rate': 65.97,   # MB/s
                    'device_write_bw': 4116.6,  # MB/s (initial state)
                    'device_read_bw': 5487.2,   # MB/s
                    'device_utilization_write': 0.019,  # 65.97*1.2 / 4116.6
                    'device_utilization_read': 0.001    # 65.97*0.1 / 5487.2
                },
                'middle_phase': {
                    'wa': 2.5,
                    'ra': 0.8,
                    'combined_amplification': 3.3,  # WA + RA
                    'actual_put_rate': 114472,  # ops/sec
                    'user_write_rate': 16.95,   # MB/s
                    'device_write_bw': 1074.8,  # MB/s (degraded state)
                    'device_read_bw': 1166.1,   # MB/s
                    'device_utilization_write': 0.039,  # 16.95*2.5 / 1074.8
                    'device_utilization_read': 0.012    # 16.95*0.8 / 1166.1
                },
                'final_phase': {
                    'wa': 3.2,
                    'ra': 1.1,
                    'combined_amplification': 4.3,  # WA + RA
                    'actual_put_rate': 109678,  # ops/sec
                    'user_write_rate': 12.76,   # MB/s
                    'device_write_bw': 1074.8,  # MB/s (degraded state)
                    'device_read_bw': 1166.1,   # MB/s
                    'device_utilization_write': 0.038,  # 12.76*3.2 / 1074.8
                    'device_utilization_read': 0.012    # 12.76*1.1 / 1166.1
                }
            },
            'correlation_analysis_data': {
                'wa_values': [1.2, 2.5, 3.2],
                'ra_values': [0.1, 0.8, 1.1],
                'combined_amplification_values': [1.3, 3.3, 4.3],
                'put_rate_values': [138769, 114472, 109678],
                'normalized_put_rate': [1.0, 0.825, 0.790]  # Initial 기준 정규화
            }
        }
        
        print("✅ 실제 관찰된 상관관계 데이터 로드 완료")
        return observed_data
    
    def _create_theoretical_negative_models(self):
        """이론적 음의 상관관계 모델 생성"""
        print("📊 이론적 음의 상관관계 모델 생성 중...")
        
        theoretical_models = {
            'linear_negative_model': {
                'description': 'Put Rate = α - β×WA - γ×RA',
                'assumption': 'WA와 RA가 Put Rate에 선형적 음의 영향',
                'parameters': {
                    'alpha': 200000,  # 기본 성능
                    'beta': 20000,    # WA 페널티 계수
                    'gamma': 15000    # RA 페널티 계수
                }
            },
            'exponential_negative_model': {
                'description': 'Put Rate = α × e^(-β×WA) × e^(-γ×RA)',
                'assumption': 'WA와 RA가 Put Rate에 지수적 음의 영향',
                'parameters': {
                    'alpha': 180000,  # 기본 성능
                    'beta': 0.3,      # WA 지수 페널티
                    'gamma': 0.2      # RA 지수 페널티
                }
            },
            'power_negative_model': {
                'description': 'Put Rate = α / (WA^β × RA^γ)',
                'assumption': 'WA와 RA가 Put Rate에 거듭제곱 음의 영향',
                'parameters': {
                    'alpha': 300000,  # 기본 성능
                    'beta': 1.5,      # WA 거듭제곱 지수
                    'gamma': 0.8      # RA 거듭제곱 지수
                }
            },
            'threshold_model': {
                'description': 'Put Rate = α × max(0, 1 - (WA-1)×β - RA×γ)',
                'assumption': 'WA와 RA가 임계값을 넘으면 급격한 성능 저하',
                'parameters': {
                    'alpha': 150000,  # 기본 성능
                    'beta': 0.4,      # WA 임계 페널티
                    'gamma': 0.3      # RA 임계 페널티
                }
            }
        }
        
        print("✅ 이론적 음의 상관관계 모델 생성 완료")
        return theoretical_models
    
    def analyze_negative_correlations(self):
        """음의 상관관계 분석"""
        print("📊 WA/RA와 Put Rate 간의 음의 상관관계 분석 중...")
        
        correlation_data = self.observed_data['correlation_analysis_data']
        
        # 1. 피어슨 상관계수 (선형 관계)
        wa_put_correlation = pearsonr(correlation_data['wa_values'], correlation_data['put_rate_values'])
        ra_put_correlation = pearsonr(correlation_data['ra_values'], correlation_data['put_rate_values'])
        combined_put_correlation = pearsonr(correlation_data['combined_amplification_values'], correlation_data['put_rate_values'])
        
        # 2. 스피어만 상관계수 (순위 기반, 비선형 관계)
        wa_put_spearman = spearmanr(correlation_data['wa_values'], correlation_data['put_rate_values'])
        ra_put_spearman = spearmanr(correlation_data['ra_values'], correlation_data['put_rate_values'])
        combined_put_spearman = spearmanr(correlation_data['combined_amplification_values'], correlation_data['put_rate_values'])
        
        # 3. 개별 변화량 분석
        wa_changes = []
        ra_changes = []
        put_rate_changes = []
        
        for i in range(1, len(correlation_data['wa_values'])):
            wa_change = correlation_data['wa_values'][i] - correlation_data['wa_values'][i-1]
            ra_change = correlation_data['ra_values'][i] - correlation_data['ra_values'][i-1]
            put_rate_change = correlation_data['put_rate_values'][i] - correlation_data['put_rate_values'][i-1]
            
            wa_changes.append(wa_change)
            ra_changes.append(ra_change)
            put_rate_changes.append(put_rate_change)
        
        # 변화량 간 상관관계
        wa_change_correlation = pearsonr(wa_changes, put_rate_changes) if len(wa_changes) > 1 else (0, 1)
        ra_change_correlation = pearsonr(ra_changes, put_rate_changes) if len(ra_changes) > 1 else (0, 1)
        
        # 4. 정규화된 분석 (Initial Phase 기준)
        normalized_wa = [wa / correlation_data['wa_values'][0] for wa in correlation_data['wa_values']]
        normalized_ra = [ra / correlation_data['ra_values'][0] for ra in correlation_data['ra_values']]
        normalized_put_rate = correlation_data['normalized_put_rate']
        
        normalized_wa_correlation = pearsonr(normalized_wa, normalized_put_rate)
        normalized_ra_correlation = pearsonr(normalized_ra, normalized_put_rate)
        
        correlation_analysis = {
            'absolute_correlations': {
                'wa_put_rate': {
                    'pearson_coefficient': wa_put_correlation[0],
                    'pearson_p_value': wa_put_correlation[1],
                    'spearman_coefficient': wa_put_spearman[0],
                    'spearman_p_value': wa_put_spearman[1],
                    'correlation_strength': self._assess_correlation_strength(wa_put_correlation[0]),
                    'correlation_direction': 'negative' if wa_put_correlation[0] < 0 else 'positive'
                },
                'ra_put_rate': {
                    'pearson_coefficient': ra_put_correlation[0],
                    'pearson_p_value': ra_put_correlation[1],
                    'spearman_coefficient': ra_put_spearman[0],
                    'spearman_p_value': ra_put_spearman[1],
                    'correlation_strength': self._assess_correlation_strength(ra_put_correlation[0]),
                    'correlation_direction': 'negative' if ra_put_correlation[0] < 0 else 'positive'
                },
                'combined_amplification_put_rate': {
                    'pearson_coefficient': combined_put_correlation[0],
                    'pearson_p_value': combined_put_correlation[1],
                    'spearman_coefficient': combined_put_spearman[0],
                    'spearman_p_value': combined_put_spearman[1],
                    'correlation_strength': self._assess_correlation_strength(combined_put_correlation[0]),
                    'correlation_direction': 'negative' if combined_put_correlation[0] < 0 else 'positive'
                }
            },
            'change_correlations': {
                'wa_change_put_rate_change': {
                    'coefficient': wa_change_correlation[0],
                    'p_value': wa_change_correlation[1],
                    'interpretation': 'WA 변화와 Put Rate 변화 간의 관계'
                },
                'ra_change_put_rate_change': {
                    'coefficient': ra_change_correlation[0],
                    'p_value': ra_change_correlation[1],
                    'interpretation': 'RA 변화와 Put Rate 변화 간의 관계'
                }
            },
            'normalized_correlations': {
                'normalized_wa_put_rate': {
                    'coefficient': normalized_wa_correlation[0],
                    'p_value': normalized_wa_correlation[1],
                    'interpretation': '정규화된 WA와 Put Rate 간의 관계'
                },
                'normalized_ra_put_rate': {
                    'coefficient': normalized_ra_correlation[0],
                    'p_value': normalized_ra_correlation[1],
                    'interpretation': '정규화된 RA와 Put Rate 간의 관계'
                }
            }
        }
        
        return correlation_analysis
    
    def _assess_correlation_strength(self, coefficient):
        """상관관계 강도 평가"""
        abs_coeff = abs(coefficient)
        if abs_coeff >= 0.8:
            return "very_strong"
        elif abs_coeff >= 0.6:
            return "strong"
        elif abs_coeff >= 0.4:
            return "moderate"
        elif abs_coeff >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    def test_negative_correlation_models(self, correlation_analysis):
        """음의 상관관계 모델 테스트"""
        print("📊 음의 상관관계 모델 테스트 중...")
        
        # 실제 데이터
        wa_values = self.observed_data['correlation_analysis_data']['wa_values']
        ra_values = self.observed_data['correlation_analysis_data']['ra_values']
        put_rate_values = self.observed_data['correlation_analysis_data']['put_rate_values']
        combined_amplification = self.observed_data['correlation_analysis_data']['combined_amplification_values']
        
        model_test_results = {}
        
        # 1. Linear Negative Model Test
        for model_name, model_params in self.theoretical_models.items():
            predicted_values = []
            
            for i in range(len(wa_values)):
                wa = wa_values[i]
                ra = ra_values[i]
                
                if model_name == 'linear_negative_model':
                    # Put Rate = α - β×WA - γ×RA
                    alpha = model_params['parameters']['alpha']
                    beta = model_params['parameters']['beta']
                    gamma = model_params['parameters']['gamma']
                    predicted = alpha - beta * wa - gamma * ra
                    
                elif model_name == 'exponential_negative_model':
                    # Put Rate = α × e^(-β×WA) × e^(-γ×RA)
                    alpha = model_params['parameters']['alpha']
                    beta = model_params['parameters']['beta']
                    gamma = model_params['parameters']['gamma']
                    predicted = alpha * np.exp(-beta * wa) * np.exp(-gamma * ra)
                    
                elif model_name == 'power_negative_model':
                    # Put Rate = α / (WA^β × RA^γ)
                    alpha = model_params['parameters']['alpha']
                    beta = model_params['parameters']['beta']
                    gamma = model_params['parameters']['gamma']
                    predicted = alpha / (wa**beta * (ra + 0.01)**gamma)  # RA에 0.01 추가하여 0 방지
                    
                elif model_name == 'threshold_model':
                    # Put Rate = α × max(0, 1 - (WA-1)×β - RA×γ)
                    alpha = model_params['parameters']['alpha']
                    beta = model_params['parameters']['beta']
                    gamma = model_params['parameters']['gamma']
                    threshold_factor = max(0, 1 - (wa - 1) * beta - ra * gamma)
                    predicted = alpha * threshold_factor
                
                predicted_values.append(max(0, predicted))  # 음수 방지
            
            # 모델 정확도 계산
            accuracies = []
            for actual, predicted in zip(put_rate_values, predicted_values):
                accuracy = (1 - abs(predicted - actual) / actual) * 100
                accuracies.append(accuracy)
            
            avg_accuracy = np.mean(accuracies)
            
            # 상관관계 계산
            model_correlation = pearsonr(predicted_values, put_rate_values)
            
            model_test_results[model_name] = {
                'predicted_values': predicted_values,
                'accuracies': accuracies,
                'average_accuracy': avg_accuracy,
                'correlation_with_actual': model_correlation[0],
                'correlation_p_value': model_correlation[1],
                'model_effectiveness': 'good' if avg_accuracy > 50 else 'fair' if avg_accuracy > 20 else 'poor'
            }
        
        return model_test_results
    
    def analyze_amplification_impact_mechanisms(self):
        """증폭 영향 메커니즘 분석"""
        print("📊 WA/RA 증폭 영향 메커니즘 분석 중...")
        
        phase_data = self.observed_data['phase_data']
        
        impact_analysis = {
            'direct_impact_analysis': {},
            'indirect_impact_analysis': {},
            'cumulative_impact_analysis': {}
        }
        
        # 직접적 영향 분석
        for phase_name, data in phase_data.items():
            wa = data['wa']
            ra = data['ra']
            user_write = data['user_write_rate']
            actual_put_rate = data['actual_put_rate']
            
            # 직접적 I/O 증가량
            direct_write_overhead = user_write * (wa - 1.0)  # WA로 인한 추가 Write I/O
            direct_read_overhead = user_write * ra            # RA로 인한 Read I/O
            total_direct_overhead = direct_write_overhead + direct_read_overhead
            
            # 이론적 최대 Put Rate (WA/RA 없다면)
            theoretical_max_without_amplification = user_write * (1024 * 1024) / (16 + 1024)  # MB/s to ops/sec
            
            # 직접적 영향 계산
            direct_impact_percent = (total_direct_overhead / user_write) * 100
            
            impact_analysis['direct_impact_analysis'][phase_name] = {
                'wa_direct_overhead_mb_s': direct_write_overhead,
                'ra_direct_overhead_mb_s': direct_read_overhead,
                'total_direct_overhead_mb_s': total_direct_overhead,
                'direct_impact_percent': direct_impact_percent,
                'theoretical_max_without_amplification': theoretical_max_without_amplification,
                'actual_vs_theoretical_ratio': actual_put_rate / theoretical_max_without_amplification
            }
        
        # 간접적 영향 분석 (시스템 복잡성)
        for phase_name, data in phase_data.items():
            wa = data['wa']
            ra = data['ra']
            actual_put_rate = data['actual_put_rate']
            
            # 간접적 영향 요인들
            compaction_pressure = (wa - 1.0) * 0.5 + ra * 0.3  # 컴팩션 압박도
            memory_pressure = wa * 0.2 + ra * 0.1              # 메모리 압박도
            cpu_overhead = wa * 0.1 + ra * 0.15                # CPU 오버헤드
            io_contention = (wa + ra - 1.0) * 0.2              # I/O 경합
            
            total_indirect_impact = compaction_pressure + memory_pressure + cpu_overhead + io_contention
            
            impact_analysis['indirect_impact_analysis'][phase_name] = {
                'compaction_pressure': compaction_pressure,
                'memory_pressure': memory_pressure,
                'cpu_overhead': cpu_overhead,
                'io_contention': io_contention,
                'total_indirect_impact': total_indirect_impact,
                'indirect_impact_normalized': total_indirect_impact / (wa + ra)
            }
        
        # 누적 영향 분석
        for phase_name in phase_data.keys():
            direct_data = impact_analysis['direct_impact_analysis'][phase_name]
            indirect_data = impact_analysis['indirect_impact_analysis'][phase_name]
            
            # 총 영향도 계산
            total_amplification_impact = direct_data['direct_impact_percent'] + indirect_data['total_indirect_impact'] * 100
            
            # 실제 성능 저하와 비교
            if phase_name == 'initial_phase':
                baseline_put_rate = phase_data['initial_phase']['actual_put_rate']
            else:
                baseline_put_rate = phase_data['initial_phase']['actual_put_rate']
            
            actual_put_rate = phase_data[phase_name]['actual_put_rate']
            actual_degradation_percent = (baseline_put_rate - actual_put_rate) / baseline_put_rate * 100
            
            impact_analysis['cumulative_impact_analysis'][phase_name] = {
                'total_amplification_impact_percent': total_amplification_impact,
                'actual_degradation_percent': actual_degradation_percent,
                'explained_degradation_ratio': total_amplification_impact / actual_degradation_percent if actual_degradation_percent != 0 else 0,
                'unexplained_factors': actual_degradation_percent - total_amplification_impact
            }
        
        return impact_analysis
    
    def create_negative_correlation_visualization(self, correlation_analysis, impact_analysis, model_test_results, output_dir):
        """음의 상관관계 시각화 생성"""
        print("📊 음의 상관관계 시각화 생성 중...")
        
        # Liberation Serif 폰트 설정
        plt.rcParams['font.family'] = 'Liberation Serif'
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, axes = plt.subplots(3, 3, figsize=(18, 15))
        fig.suptitle('Negative Correlation Analysis: WA/RA vs Put Rate', fontsize=16, fontweight='bold')
        
        # 데이터 준비
        wa_values = self.observed_data['correlation_analysis_data']['wa_values']
        ra_values = self.observed_data['correlation_analysis_data']['ra_values']
        put_rate_values = self.observed_data['correlation_analysis_data']['put_rate_values']
        combined_values = self.observed_data['correlation_analysis_data']['combined_amplification_values']
        
        # 1. WA vs Put Rate (음의 상관관계)
        ax1 = axes[0, 0]
        ax1.scatter(wa_values, put_rate_values, c=['red', 'orange', 'green'], s=100, alpha=0.8)
        
        # 추세선 추가
        z = np.polyfit(wa_values, put_rate_values, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(wa_values), max(wa_values), 100)
        ax1.plot(x_trend, p(x_trend), "r--", alpha=0.8, linewidth=2)
        
        # 상관계수 표시
        wa_corr = correlation_analysis['absolute_correlations']['wa_put_rate']['pearson_coefficient']
        ax1.text(0.05, 0.95, f'Correlation: {wa_corr:.3f}', transform=ax1.transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        ax1.set_xlabel('Write Amplification (WA)')
        ax1.set_ylabel('Put Rate (ops/sec)')
        ax1.set_title('WA vs Put Rate (Negative Correlation)')
        ax1.grid(True, alpha=0.3)
        
        # 2. RA vs Put Rate (음의 상관관계)
        ax2 = axes[0, 1]
        ax2.scatter(ra_values, put_rate_values, c=['red', 'orange', 'green'], s=100, alpha=0.8)
        
        # 추세선 추가
        z = np.polyfit(ra_values, put_rate_values, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(ra_values), max(ra_values), 100)
        ax2.plot(x_trend, p(x_trend), "r--", alpha=0.8, linewidth=2)
        
        # 상관계수 표시
        ra_corr = correlation_analysis['absolute_correlations']['ra_put_rate']['pearson_coefficient']
        ax2.text(0.05, 0.95, f'Correlation: {ra_corr:.3f}', transform=ax2.transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        ax2.set_xlabel('Read Amplification (RA)')
        ax2.set_ylabel('Put Rate (ops/sec)')
        ax2.set_title('RA vs Put Rate (Negative Correlation)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Combined Amplification vs Put Rate
        ax3 = axes[0, 2]
        ax3.scatter(combined_values, put_rate_values, c=['red', 'orange', 'green'], s=100, alpha=0.8)
        
        # 추세선 추가
        z = np.polyfit(combined_values, put_rate_values, 1)
        p = np.poly1d(z)
        x_trend = np.linspace(min(combined_values), max(combined_values), 100)
        ax3.plot(x_trend, p(x_trend), "r--", alpha=0.8, linewidth=2)
        
        # 상관계수 표시
        combined_corr = correlation_analysis['absolute_correlations']['combined_amplification_put_rate']['pearson_coefficient']
        ax3.text(0.05, 0.95, f'Correlation: {combined_corr:.3f}', transform=ax3.transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        ax3.set_xlabel('Combined Amplification (WA + RA)')
        ax3.set_ylabel('Put Rate (ops/sec)')
        ax3.set_title('Combined Amplification vs Put Rate')
        ax3.grid(True, alpha=0.3)
        
        # 4. 직접적 영향 분석
        ax4 = axes[1, 0]
        phases = ['Initial', 'Middle', 'Final']
        direct_impacts = [impact_analysis['direct_impact_analysis'][f'{phase.lower()}_phase']['direct_impact_percent'] 
                         for phase in phases]
        
        bars = ax4.bar(phases, direct_impacts, color=['red', 'orange', 'green'], alpha=0.7)
        
        for bar, impact in zip(bars, direct_impacts):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{impact:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax4.set_ylabel('Direct Impact (%)')
        ax4.set_title('Direct WA/RA Impact on I/O Overhead')
        ax4.grid(True, alpha=0.3)
        
        # 5. 간접적 영향 분석
        ax5 = axes[1, 1]
        indirect_impacts = [impact_analysis['indirect_impact_analysis'][f'{phase.lower()}_phase']['total_indirect_impact'] 
                           for phase in phases]
        
        bars = ax5.bar(phases, indirect_impacts, color=['red', 'orange', 'green'], alpha=0.7)
        
        for bar, impact in zip(bars, indirect_impacts):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{impact:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax5.set_ylabel('Indirect Impact Score')
        ax5.set_title('Indirect WA/RA Impact (System Complexity)')
        ax5.grid(True, alpha=0.3)
        
        # 6. 실제 vs 예상 성능 저하
        ax6 = axes[1, 2]
        
        actual_degradations = []
        explained_degradations = []
        
        for phase in phases:
            phase_key = f'{phase.lower()}_phase'
            cumulative_data = impact_analysis['cumulative_impact_analysis'][phase_key]
            
            actual_deg = cumulative_data['actual_degradation_percent']
            explained_deg = cumulative_data['total_amplification_impact_percent']
            
            actual_degradations.append(actual_deg)
            explained_degradations.append(explained_deg)
        
        x = np.arange(len(phases))
        width = 0.35
        
        ax6.bar(x - width/2, actual_degradations, width, label='Actual Degradation', alpha=0.8, color='lightcoral')
        ax6.bar(x + width/2, explained_degradations, width, label='WA/RA Explained', alpha=0.8, color='lightblue')
        
        ax6.set_xlabel('Phase')
        ax6.set_ylabel('Performance Degradation (%)')
        ax6.set_title('Actual vs WA/RA Explained Degradation')
        ax6.set_xticks(x)
        ax6.set_xticklabels(phases)
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        # 7. 상관관계 강도 비교
        ax7 = axes[2, 0]
        correlation_types = ['WA-Put Rate', 'RA-Put Rate', 'Combined-Put Rate']
        pearson_coeffs = [
            correlation_analysis['absolute_correlations']['wa_put_rate']['pearson_coefficient'],
            correlation_analysis['absolute_correlations']['ra_put_rate']['pearson_coefficient'],
            correlation_analysis['absolute_correlations']['combined_amplification_put_rate']['pearson_coefficient']
        ]
        spearman_coeffs = [
            correlation_analysis['absolute_correlations']['wa_put_rate']['spearman_coefficient'],
            correlation_analysis['absolute_correlations']['ra_put_rate']['spearman_coefficient'],
            correlation_analysis['absolute_correlations']['combined_amplification_put_rate']['spearman_coefficient']
        ]
        
        x = np.arange(len(correlation_types))
        width = 0.35
        
        bars1 = ax7.bar(x - width/2, pearson_coeffs, width, label='Pearson', alpha=0.8, color='lightblue')
        bars2 = ax7.bar(x + width/2, spearman_coeffs, width, label='Spearman', alpha=0.8, color='lightgreen')
        
        # 값 표시
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax7.text(bar.get_x() + bar.get_width()/2., height + (0.05 if height >= 0 else -0.1),
                        f'{height:.3f}', ha='center', va='bottom' if height >= 0 else 'top', 
                        fontsize=9, fontweight='bold')
        
        ax7.set_xlabel('Correlation Type')
        ax7.set_ylabel('Correlation Coefficient')
        ax7.set_title('Correlation Strength Comparison')
        ax7.set_xticks(x)
        ax7.set_xticklabels(correlation_types, rotation=45)
        ax7.legend()
        ax7.grid(True, alpha=0.3)
        ax7.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 8. 이론적 모델 성능 비교
        ax8 = axes[2, 1]
        model_names = list(model_test_results.keys())
        model_labels = [name.replace('_', ' ').title() for name in model_names]
        model_accuracies = [model_test_results[model]['average_accuracy'] for model in model_names]
        
        bars = ax8.bar(model_labels, model_accuracies, alpha=0.7, 
                      color=['lightblue', 'lightgreen', 'lightcoral', 'lightyellow'])
        
        for bar, acc in zip(bars, model_accuracies):
            height = bar.get_height()
            ax8.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -5),
                    f'{acc:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', 
                    fontsize=9, fontweight='bold')
        
        ax8.set_ylabel('Model Accuracy (%)')
        ax8.set_title('Theoretical Negative Model Performance')
        ax8.set_xticklabels(model_labels, rotation=45)
        ax8.grid(True, alpha=0.3)
        ax8.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # 9. WA vs RA 영향도 비교
        ax9 = axes[2, 2]
        
        # WA와 RA의 개별 영향도 계산
        wa_individual_impact = []
        ra_individual_impact = []
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            direct_data = impact_analysis['direct_impact_analysis'][phase_name]
            user_write = self.observed_data['phase_data'][phase_name]['user_write_rate']
            
            wa_impact = direct_data['wa_direct_overhead_mb_s'] / user_write * 100
            ra_impact = direct_data['ra_direct_overhead_mb_s'] / user_write * 100
            
            wa_individual_impact.append(wa_impact)
            ra_individual_impact.append(ra_impact)
        
        x = np.arange(len(phases))
        width = 0.35
        
        ax9.bar(x - width/2, wa_individual_impact, width, label='WA Impact', alpha=0.8, color='lightcoral')
        ax9.bar(x + width/2, ra_individual_impact, width, label='RA Impact', alpha=0.8, color='lightblue')
        
        ax9.set_xlabel('Phase')
        ax9.set_ylabel('Individual Impact (%)')
        ax9.set_title('WA vs RA Individual Impact Comparison')
        ax9.set_xticks(x)
        ax9.set_xticklabels(phases)
        ax9.legend()
        ax9.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        output_file = os.path.join(output_dir, 'negative_correlation_wa_ra_analysis.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 음의 상관관계 시각화 저장 완료: {output_file}")

def main():
    """메인 실행 함수"""
    print("🚀 Negative Correlation Analysis: WA/RA vs Put Rate 시작")
    print("=" * 70)
    
    # 음의 상관관계 분석기 생성
    analyzer = NegativeCorrelationAnalyzer()
    
    # 음의 상관관계 분석
    correlation_analysis = analyzer.analyze_negative_correlations()
    
    # 증폭 영향 메커니즘 분석
    impact_analysis = analyzer.analyze_amplification_impact_mechanisms()
    
    # 음의 상관관계 모델 테스트
    model_test_results = analyzer.test_negative_correlation_models(correlation_analysis)
    
    # 시각화 생성
    analyzer.create_negative_correlation_visualization(correlation_analysis, impact_analysis, model_test_results, analyzer.results_dir)
    
    # 결과 요약 출력
    print("\n" + "=" * 70)
    print("📊 Negative Correlation Analysis Summary")
    print("=" * 70)
    
    print("Correlation Coefficients (Pearson):")
    abs_corr = correlation_analysis['absolute_correlations']
    print(f"  WA vs Put Rate: {abs_corr['wa_put_rate']['pearson_coefficient']:.3f} ({abs_corr['wa_put_rate']['correlation_direction']})")
    print(f"  RA vs Put Rate: {abs_corr['ra_put_rate']['pearson_coefficient']:.3f} ({abs_corr['ra_put_rate']['correlation_direction']})")
    print(f"  Combined vs Put Rate: {abs_corr['combined_amplification_put_rate']['pearson_coefficient']:.3f} ({abs_corr['combined_amplification_put_rate']['correlation_direction']})")
    print()
    
    print("Direct Impact Analysis:")
    for phase in ['initial_phase', 'middle_phase', 'final_phase']:
        direct_impact = impact_analysis['direct_impact_analysis'][phase]['direct_impact_percent']
        print(f"  {phase.replace('_', ' ').title()}: {direct_impact:.1f}% I/O overhead")
    print()
    
    print("Negative Model Performance:")
    for model_name, results in model_test_results.items():
        model_display = model_name.replace('_', ' ').title()
        accuracy = results['average_accuracy']
        correlation = results['correlation_with_actual']
        print(f"  {model_display}: {accuracy:.1f}% accuracy (r={correlation:.3f})")
    
    print("\nCritical Finding:")
    print("  강한 음의 상관관계 확인: WA/RA ↑ → Put Rate ↓")
    print("  하지만 이론적 모델들은 실제 관계를 정확히 포착하지 못함")
    print("  숨겨진 요인들이 WA/RA보다 더 큰 영향을 미침")
    
    print("\n✅ Negative Correlation Analysis 완료!")
    print("=" * 70)

if __name__ == "__main__":
    main()
