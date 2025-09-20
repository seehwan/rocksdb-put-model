#!/usr/bin/env python3
"""
V4.1 Temporal Model with Phase-A Degradation Integration
시기별 디바이스 열화 모델을 반영한 v4.1 Temporal 모델 분석
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class V4_1_TemporalWithDegradationAnalyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-A 실제 열화 데이터
        self.phase_a_data = self._load_phase_a_degradation_data()
        
        # v4.1 Temporal 모델 예측 결과
        self.v4_1_temporal_predictions = {}
        self.results = {}
        
        print("🚀 V4.1 Temporal Model with Phase-A Degradation Integration 시작")
        print("=" * 60)
    
    def _load_phase_a_degradation_data(self):
        """Phase-A 실제 열화 데이터 로드"""
        print("📊 Phase-A 열화 데이터 로드 중...")
        
        # Phase-A 데이터 파일 경로
        initial_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/initial_state_results.json'
        degraded_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/degraded_state_results_fixed.json'
        
        phase_a_data = {
            'initial': {'write_bw': 0, 'read_bw': 0},  # 초기 상태 (완전 초기화)
            'degraded': {'write_bw': 1074.8, 'read_bw': 1166.1}  # 열화 상태 (Phase-B 후)
        }
        
        try:
            if os.path.exists(initial_file):
                with open(initial_file, 'r') as f:
                    initial_data = json.load(f)
                    phase_a_data['initial'] = {
                        'write_bw': initial_data['summary']['max_write_bandwidth_mib_s'],
                        'read_bw': initial_data['summary']['max_read_bandwidth_mib_s']
                    }
            
            if os.path.exists(degraded_file):
                with open(degraded_file, 'r') as f:
                    degraded_data = json.load(f)
                    phase_a_data['degraded'] = {
                        'write_bw': degraded_data['summary']['max_write_bandwidth_mib_s'],
                        'read_bw': degraded_data['summary']['max_read_bandwidth_mib_s']
                    }
            
            print(f"✅ Phase-A 열화 데이터 로드 완료:")
            print(f"   - 초기 상태: Write {phase_a_data['initial']['write_bw']:.1f} MB/s, Read {phase_a_data['initial']['read_bw']:.1f} MB/s")
            print(f"   - 열화 상태: Write {phase_a_data['degraded']['write_bw']:.1f} MB/s, Read {phase_a_data['degraded']['read_bw']:.1f} MB/s")
            
        except Exception as e:
            print(f"⚠️ Phase-A 데이터 로드 실패, 기본값 사용: {e}")
        
        return phase_a_data
    
    def _calculate_temporal_degradation_factors(self):
        """시기별 열화 인자 계산"""
        print("📊 시기별 열화 인자 계산 중...")
        
        # Phase-A 실제 데이터 기반 열화 패턴
        initial_perf = self.phase_a_data['initial']
        degraded_perf = self.phase_a_data['degraded']
        
        # 시기별 열화 모델링
        degradation_factors = {
            'initial_phase': {
                'base_performance': {
                    'write_bw': max(100, initial_perf['write_bw']),  # 최소 100 MB/s
                    'read_bw': max(100, initial_perf['read_bw'])
                },
                'degradation_factor': 0.0,  # 초기: 열화 없음
                'io_intensity': 0.8,        # 높은 I/O 강도
                'stability': 0.2,            # 낮은 안정성
                'performance_factor': 0.3    # 낮은 성능 인자
            },
            'middle_phase': {
                'base_performance': {
                    'write_bw': (initial_perf['write_bw'] + degraded_perf['write_bw']) / 2,
                    'read_bw': (initial_perf['read_bw'] + degraded_perf['read_bw']) / 2
                },
                'degradation_factor': 0.3,   # 중기: 30% 열화
                'io_intensity': 0.6,         # 중간 I/O 강도
                'stability': 0.5,            # 중간 안정성
                'performance_factor': 0.6    # 중간 성능 인자
            },
            'final_phase': {
                'base_performance': {
                    'write_bw': degraded_perf['write_bw'],  # 실제 측정값
                    'read_bw': degraded_perf['read_bw']
                },
                'degradation_factor': 0.6,   # 후기: 60% 열화
                'io_intensity': 0.4,         # 낮은 I/O 강도
                'stability': 0.8,            # 높은 안정성
                'performance_factor': 0.9    # 높은 성능 인자
            }
        }
        
        return degradation_factors
    
    def _analyze_device_envelope_with_degradation(self, temporal_analysis):
        """Phase-A 열화 데이터를 반영한 Device Envelope 모델 분석"""
        print("📊 Phase-A 열화 데이터 반영 Device Envelope 모델 분석 중...")
        
        degradation_factors = self._calculate_temporal_degradation_factors()
        device_envelope_temporal = {}
        
        for phase_name, phase_model in temporal_analysis.get('phase_models', {}).items():
            characteristics = phase_model['characteristics']
            degradation_data = degradation_factors[phase_name]
            
            # 기본 성능 (Phase-A 실제 데이터 기반)
            base_perf = degradation_data['base_performance']
            
            # 시기별 열화 인자
            degradation_factor = degradation_data['degradation_factor']
            io_intensity = degradation_data['io_intensity']
            stability = degradation_data['stability']
            performance_factor = degradation_data['performance_factor']
            
            # I/O 경합도 계산
            io_contention = 1.0 - (io_intensity * 0.3)  # 최대 30% 감소
            
            # 안정성에 따른 대역폭 조정
            stability_factor = 1.0 + (stability * 0.1)  # 최대 10% 증가
            
            # 열화를 고려한 성능 조정
            adjusted_write_bw = (base_perf['write_bw'] * 
                               (1.0 - degradation_factor) *
                               performance_factor *
                               io_contention *
                               stability_factor)
            
            adjusted_read_bw = (base_perf['read_bw'] * 
                              (1.0 - degradation_factor) *
                              performance_factor *
                              io_contention *
                              stability_factor)
            
            # S_max 계산
            key_size = 16  # bytes
            value_size = 1024  # bytes
            record_size = key_size + value_size
            s_max = (adjusted_write_bw * 1024 * 1024) / record_size  # ops/sec
            
            device_envelope_temporal[phase_name] = {
                'base_performance': base_perf,
                'degradation_factor': degradation_factor,
                'adjusted_write_bw': adjusted_write_bw,
                'adjusted_read_bw': adjusted_read_bw,
                's_max': s_max,
                'io_contention': io_contention,
                'stability_factor': stability_factor,
                'performance_factor': performance_factor,
                'degradation_analysis': {
                    'phase': phase_name,
                    'degradation_factor': degradation_factor,
                    'io_intensity': io_intensity,
                    'stability': stability,
                    'performance_factor': performance_factor,
                    'performance_retention': 1.0 - degradation_factor
                }
            }
        
        return device_envelope_temporal
    
    def _analyze_closed_ledger_with_degradation(self, temporal_analysis):
        """Phase-A 열화 데이터를 반영한 Closed Ledger 모델 분석"""
        print("📊 Phase-A 열화 데이터 반영 Closed Ledger 모델 분석 중...")
        
        degradation_factors = self._calculate_temporal_degradation_factors()
        closed_ledger_temporal = {}
        
        for phase_name, phase_model in temporal_analysis.get('phase_models', {}).items():
            characteristics = phase_model['characteristics']
            degradation_data = degradation_factors[phase_name]
            
            # 기본 성능 (Phase-A 실제 데이터 기반)
            base_perf = degradation_data['base_performance']
            
            # 시기별 열화 인자
            degradation_factor = degradation_data['degradation_factor']
            performance_factor = degradation_data['performance_factor']
            
            # Closed Ledger 모델 계산
            key_size = 16  # bytes
            value_size = 1024  # bytes
            record_size = key_size + value_size
            
            # 열화를 고려한 성능 조정
            adjusted_bw = base_perf['write_bw'] * (1.0 - degradation_factor) * performance_factor
            
            s_max = (adjusted_bw * 1024 * 1024) / record_size  # ops/sec
            
            closed_ledger_temporal[phase_name] = {
                'base_performance': base_perf,
                'degradation_factor': degradation_factor,
                'adjusted_bw': adjusted_bw,
                's_max': s_max,
                'performance_factor': performance_factor
            }
        
        return closed_ledger_temporal
    
    def _analyze_dynamic_simulation_with_degradation(self, temporal_analysis):
        """Phase-A 열화 데이터를 반영한 Dynamic Simulation 모델 분석"""
        print("📊 Phase-A 열화 데이터 반영 Dynamic Simulation 모델 분석 중...")
        
        degradation_factors = self._calculate_temporal_degradation_factors()
        dynamic_simulation_temporal = {}
        
        for phase_name, phase_model in temporal_analysis.get('phase_models', {}).items():
            characteristics = phase_model['characteristics']
            degradation_data = degradation_factors[phase_name]
            
            # 기본 성능 (Phase-A 실제 데이터 기반)
            base_perf = degradation_data['base_performance']
            
            # 시기별 열화 인자
            degradation_factor = degradation_data['degradation_factor']
            performance_factor = degradation_data['performance_factor']
            stability = degradation_data['stability']
            
            # Dynamic Simulation 모델 계산
            key_size = 16  # bytes
            value_size = 1024  # bytes
            record_size = key_size + value_size
            
            # 열화를 고려한 성능 조정
            adjusted_bw = (base_perf['write_bw'] * 
                         (1.0 - degradation_factor) * 
                         performance_factor * 
                         (1.0 + stability * 0.1))
            
            dynamic_smax = (adjusted_bw * 1024 * 1024) / record_size  # ops/sec
            
            dynamic_simulation_temporal[phase_name] = {
                'base_performance': base_perf,
                'degradation_factor': degradation_factor,
                'adjusted_bw': adjusted_bw,
                'dynamic_smax': dynamic_smax,
                'performance_factor': performance_factor,
                'stability': stability
            }
        
        return dynamic_simulation_temporal
    
    def analyze_v4_1_temporal_with_degradation(self):
        """Phase-A 열화 데이터를 반영한 v4.1 Temporal 모델 분석"""
        print("🔍 Phase-A 열화 데이터 반영 v4.1 Temporal 모델 분석 중...")
        
        # 시기별 모델 특성 (기존 데이터)
        temporal_analysis = {
            'phase_models': {
                'initial_phase': {
                    'characteristics': {
                        'io_intensity': 0.8,
                        'performance_factor': 0.3,
                        'stability': 0.2,
                        'io_usage_mb': 500
                    }
                },
                'middle_phase': {
                    'characteristics': {
                        'io_intensity': 0.6,
                        'performance_factor': 0.6,
                        'stability': 0.5,
                        'io_usage_mb': 300
                    }
                },
                'final_phase': {
                    'characteristics': {
                        'io_intensity': 0.4,
                        'performance_factor': 0.9,
                        'stability': 0.8,
                        'io_usage_mb': 100
                    }
                }
            }
        }
        
        # Phase-A 열화 데이터를 반영한 모델 분석
        device_envelope_temporal = self._analyze_device_envelope_with_degradation(temporal_analysis)
        closed_ledger_temporal = self._analyze_closed_ledger_with_degradation(temporal_analysis)
        dynamic_simulation_temporal = self._analyze_dynamic_simulation_with_degradation(temporal_analysis)
        
        # v4.1 Temporal 모델 예측 결과
        self.v4_1_temporal_predictions = {
            'device_envelope_temporal': device_envelope_temporal,
            'closed_ledger_temporal': closed_ledger_temporal,
            'dynamic_simulation_temporal': dynamic_simulation_temporal
        }
        
        # 시기별 성능 분석
        phase_performance = {}
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            if phase_name in device_envelope_temporal:
                device_smax = device_envelope_temporal[phase_name]['s_max']
                ledger_smax = closed_ledger_temporal[phase_name]['s_max']
                dynamic_smax = dynamic_simulation_temporal[phase_name]['dynamic_smax']
                
                # 평균 예측값
                avg_prediction = (device_smax + ledger_smax + dynamic_smax) / 3
                
                phase_performance[phase_name] = {
                    'device_smax': device_smax,
                    'ledger_smax': ledger_smax,
                    'dynamic_smax': dynamic_smax,
                    'avg_prediction': avg_prediction
                }
        
        self.results = {
            'v4_1_temporal_predictions': self.v4_1_temporal_predictions,
            'phase_performance': phase_performance,
            'phase_a_degradation_data': self.phase_a_data,
            'degradation_factors': self._calculate_temporal_degradation_factors()
        }
        
        print("✅ Phase-A 열화 데이터 반영 v4.1 Temporal 모델 분석 완료:")
        print(f"   - 초기 시기 Device Envelope: {device_envelope_temporal['initial_phase']['s_max']:.2f} ops/sec")
        print(f"   - 중기 시기 Device Envelope: {device_envelope_temporal['middle_phase']['s_max']:.2f} ops/sec")
        print(f"   - 후기 시기 Device Envelope: {device_envelope_temporal['final_phase']['s_max']:.2f} ops/sec")
        
        return self.v4_1_temporal_predictions
    
    def create_degradation_visualization(self):
        """Phase-A 열화 데이터 반영 시각화 생성"""
        print("📊 Phase-A 열화 데이터 반영 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('V4.1 Temporal Model with Phase-A Degradation Integration', fontsize=16, fontweight='bold')
        
        # 1. Phase-A 실제 열화 데이터
        phases = ['Initial', 'Middle', 'Final']
        write_bw = [
            max(100, self.phase_a_data['initial']['write_bw']),
            (self.phase_a_data['initial']['write_bw'] + self.phase_a_data['degraded']['write_bw']) / 2,
            self.phase_a_data['degraded']['write_bw']
        ]
        read_bw = [
            max(100, self.phase_a_data['initial']['read_bw']),
            (self.phase_a_data['initial']['read_bw'] + self.phase_a_data['degraded']['read_bw']) / 2,
            self.phase_a_data['degraded']['read_bw']
        ]
        
        x = np.arange(len(phases))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, write_bw, width, label='Write BW', color='skyblue', alpha=0.8)
        bars2 = ax1.bar(x + width/2, read_bw, width, label='Read BW', color='lightcoral', alpha=0.8)
        
        ax1.set_xlabel('Temporal Phase')
        ax1.set_ylabel('Bandwidth (MB/s)')
        ax1.set_title('Phase-A Actual Degradation Data')
        ax1.set_xticks(x)
        ax1.set_xticklabels(phases)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 값 표시
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 2. 시기별 열화 인자
        degradation_factors = self._calculate_temporal_degradation_factors()
        degradation_values = []
        phase_names = []
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            if phase_name in degradation_factors:
                degradation_values.append(degradation_factors[phase_name]['degradation_factor'] * 100)
                phase_names.append(phase_name.replace('_phase', '').title())
        
        colors = ['green' if df < 20 else 'orange' if df < 50 else 'red' for df in degradation_values]
        bars = ax2.bar(phase_names, degradation_values, color=colors, alpha=0.7)
        ax2.set_ylabel('Degradation Factor (%)')
        ax2.set_title('Temporal Degradation Factors')
        ax2.set_ylim(0, 100)
        
        for bar, value in zip(bars, degradation_values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 3. 시기별 S_max 예측
        if self.v4_1_temporal_predictions:
            device_envelope = self.v4_1_temporal_predictions.get('device_envelope_temporal', {})
            s_max_values = []
            
            for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
                if phase_name in device_envelope:
                    s_max_values.append(device_envelope[phase_name]['s_max'])
            
            if s_max_values:
                bars = ax3.bar(phase_names, s_max_values, color='lightgreen', alpha=0.7)
                ax3.set_ylabel('S_max (ops/sec)')
                ax3.set_title('Predicted S_max by Phase')
                ax3.grid(True, alpha=0.3)
                
                for bar, value in zip(bars, s_max_values):
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height,
                            f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 4. 열화 인자 분석
        if degradation_factors:
            io_intensity = []
            stability = []
            performance_factor = []
            
            for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
                if phase_name in degradation_factors:
                    io_intensity.append(degradation_factors[phase_name]['io_intensity'] * 100)
                    stability.append(degradation_factors[phase_name]['stability'] * 100)
                    performance_factor.append(degradation_factors[phase_name]['performance_factor'] * 100)
            
            x = np.arange(len(phase_names))
            width = 0.25
            
            bars1 = ax4.bar(x - width, io_intensity, width, label='I/O Intensity', color='red', alpha=0.7)
            bars2 = ax4.bar(x, stability, width, label='Stability', color='blue', alpha=0.7)
            bars3 = ax4.bar(x + width, performance_factor, width, label='Performance Factor', color='green', alpha=0.7)
            
            ax4.set_xlabel('Temporal Phase')
            ax4.set_ylabel('Percentage (%)')
            ax4.set_title('Degradation Factor Analysis')
            ax4.set_xticks(x)
            ax4.set_xticklabels(phase_names)
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/v4_1_temporal_with_phase_a_degradation.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ Phase-A 열화 데이터 반영 시각화 완료")
    
    def save_results(self):
        """결과 저장"""
        print("💾 Phase-A 열화 데이터 반영 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/v4_1_temporal_with_phase_a_degradation_results.json", 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_report()
            with open(f"{self.results_dir}/v4_1_temporal_with_phase_a_degradation_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_report(self):
        """보고서 생성"""
        report = f"""# V4.1 Temporal Model with Phase-A Degradation Integration Report

## Overview
This report presents the analysis of v4.1 Temporal model with Phase-A actual degradation data integration.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Phase-A Degradation Data
- **Initial State**: Write {self.phase_a_data['initial']['write_bw']:.1f} MB/s, Read {self.phase_a_data['initial']['read_bw']:.1f} MB/s
- **Degraded State**: Write {self.phase_a_data['degraded']['write_bw']:.1f} MB/s, Read {self.phase_a_data['degraded']['read_bw']:.1f} MB/s

## Temporal Degradation Factors
"""
        
        degradation_factors = self._calculate_temporal_degradation_factors()
        for phase_name, factors in degradation_factors.items():
            report += f"""
### {phase_name.replace('_', ' ').title()}
- **Base Performance**: Write {factors['base_performance']['write_bw']:.1f} MB/s, Read {factors['base_performance']['read_bw']:.1f} MB/s
- **Degradation Factor**: {factors['degradation_factor']:.1%}
- **I/O Intensity**: {factors['io_intensity']:.1%}
- **Stability**: {factors['stability']:.1%}
- **Performance Factor**: {factors['performance_factor']:.1%}
"""
        
        if self.v4_1_temporal_predictions:
            device_envelope = self.v4_1_temporal_predictions.get('device_envelope_temporal', {})
            report += """
## Predicted S_max by Phase
"""
            for phase_name, data in device_envelope.items():
                report += f"- **{phase_name.replace('_', ' ').title()}**: {data['s_max']:.2f} ops/sec\n"
        
        report += f"""
## Visualization
![V4.1 Temporal with Phase-A Degradation](v4_1_temporal_with_phase_a_degradation.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 Phase-A 열화 데이터 반영 v4.1 Temporal 모델 분석 시작")
        print("=" * 60)
        
        self.analyze_v4_1_temporal_with_degradation()
        self.create_degradation_visualization()
        self.save_results()
        
        print("=" * 60)
        print("✅ Phase-A 열화 데이터 반영 v4.1 Temporal 모델 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = V4_1_TemporalWithDegradationAnalyzer()
    analyzer.run_analysis()


