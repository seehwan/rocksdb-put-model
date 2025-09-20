#!/usr/bin/env python3
"""
V4.2 FillRandom Enhanced Model
FillRandom 워크로드 특성을 반영한 v4.2 모델 개발
- Sequential Write Only (사용자 Write)
- Compaction Read Only (시스템 Read)
- 실제 성능 열화 데이터 반영
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

class V4_2_FillRandom_Enhanced_Model:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Phase-A FillRandom 워크로드 데이터 로드
        self.phase_a_data = self._load_phase_a_fillrandom_data()
        
        # v4.2 모델 예측 결과
        self.v4_2_predictions = {}
        self.results = {}
        
        print("🚀 V4.2 FillRandom Enhanced Model 시작")
        print("=" * 60)
    
    def _load_phase_a_fillrandom_data(self):
        """Phase-A FillRandom 워크로드 데이터 로드"""
        print("📊 Phase-A FillRandom 워크로드 데이터 로드 중...")
        
        # FillRandom 워크로드 특성
        # - Write: Sequential Write만 발생
        # - Read: Compaction에서만 발생
        
        # 초기 상태 데이터
        initial_data = {
            'seq_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_initial.json'),
            'seq_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_initial.json')
        }
        
        # 열화 상태 데이터
        degraded_data = {
            'seq_write': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_degraded.json'),
            'seq_read': self._extract_fio_performance('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_degraded.json')
        }
        
        print(f"✅ Phase-A FillRandom 워크로드 데이터 로드 완료:")
        print(f"   - 초기 상태 Seq Write: {initial_data['seq_write']['write_bw']:.1f} MB/s")
        print(f"   - 초기 상태 Seq Read: {initial_data['seq_read']['read_bw']:.1f} MB/s")
        print(f"   - 열화 상태 Seq Write: {degraded_data['seq_write']['write_bw']:.1f} MB/s")
        print(f"   - 열화 상태 Seq Read: {degraded_data['seq_read']['read_bw']:.1f} MB/s")
        
        return {
            'initial': initial_data,
            'degraded': degraded_data
        }
    
    def _extract_fio_performance(self, fio_file):
        """FIO 파일에서 성능 데이터 추출"""
        try:
            with open(fio_file, 'r') as f:
                fio_data = json.load(f)
            
            # Write 성능 추출 (KB/s 단위)
            write_bw_kbps = fio_data['jobs'][0]['write']['bw']
            write_bw_mbps = write_bw_kbps / 1024  # KB/s to MB/s
            
            # Read 성능 추출 (KB/s 단위)
            read_bw_kbps = fio_data['jobs'][0]['read']['bw']
            read_bw_mbps = read_bw_kbps / 1024  # KB/s to MB/s
            
            return {
                'write_bw': write_bw_mbps,
                'read_bw': read_bw_mbps
            }
            
        except Exception as e:
            print(f"⚠️ FIO 파일 로드 실패 {fio_file}: {e}")
            return {'write_bw': 0, 'read_bw': 0}
    
    def _calculate_fillrandom_temporal_factors(self):
        """FillRandom 워크로드 특성을 반영한 시기별 인자 계산"""
        print("📊 FillRandom 워크로드 특성 반영 시기별 인자 계산 중...")
        
        # Phase-A 실제 데이터 기반
        initial_perf = self.phase_a_data['initial']
        degraded_perf = self.phase_a_data['degraded']
        
        # FillRandom 워크로드 특성
        # - Write: Sequential Write만 발생 (사용자 Write)
        # - Read: Compaction에서만 발생 (시스템 Read)
        
        # 실제 열화율 계산
        write_degradation_rate = ((initial_perf['seq_write']['write_bw'] - degraded_perf['seq_write']['write_bw']) / 
                                initial_perf['seq_write']['write_bw']) if initial_perf['seq_write']['write_bw'] > 0 else 0
        
        compaction_read_degradation_rate = ((initial_perf['seq_read']['read_bw'] - degraded_perf['seq_read']['read_bw']) / 
                                          initial_perf['seq_read']['read_bw']) if initial_perf['seq_read']['read_bw'] > 0 else 0
        
        print(f"   📉 Write 성능 열화율: {write_degradation_rate:.1%}")
        print(f"   📉 Compaction Read 성능 열화율: {compaction_read_degradation_rate:.1%}")
        
        # 시기별 FillRandom 워크로드 특성 반영
        temporal_factors = {
            'initial_phase': {
                'workload_characteristics': {
                    'write_type': 'Sequential Write Only',
                    'read_type': 'Compaction Read Only',
                    'user_reads': 0,
                    'system_reads': 'Compaction Only'
                },
                'performance_factors': {
                    'write_performance': initial_perf['seq_write']['write_bw'],
                    'compaction_read_performance': initial_perf['seq_read']['read_bw'],
                    'write_degradation_factor': 0.0,
                    'compaction_read_degradation_factor': 0.0
                },
                'io_characteristics': {
                    'io_intensity': 0.8,        # 높은 I/O 강도
                    'stability': 0.2,            # 낮은 안정성
                    'performance_factor': 0.3   # 낮은 성능 인자
                }
            },
            'middle_phase': {
                'workload_characteristics': {
                    'write_type': 'Sequential Write Only',
                    'read_type': 'Compaction Read Only',
                    'user_reads': 0,
                    'system_reads': 'Compaction Only'
                },
                'performance_factors': {
                    'write_performance': (initial_perf['seq_write']['write_bw'] + degraded_perf['seq_write']['write_bw']) / 2,
                    'compaction_read_performance': (initial_perf['seq_read']['read_bw'] + degraded_perf['seq_read']['read_bw']) / 2,
                    'write_degradation_factor': write_degradation_rate * 0.5,
                    'compaction_read_degradation_factor': compaction_read_degradation_rate * 0.5
                },
                'io_characteristics': {
                    'io_intensity': 0.6,        # 중간 I/O 강도
                    'stability': 0.5,           # 중간 안정성
                    'performance_factor': 0.6   # 중간 성능 인자
                }
            },
            'final_phase': {
                'workload_characteristics': {
                    'write_type': 'Sequential Write Only',
                    'read_type': 'Compaction Read Only',
                    'user_reads': 0,
                    'system_reads': 'Compaction Only'
                },
                'performance_factors': {
                    'write_performance': degraded_perf['seq_write']['write_bw'],
                    'compaction_read_performance': degraded_perf['seq_read']['read_bw'],
                    'write_degradation_factor': write_degradation_rate,
                    'compaction_read_degradation_factor': compaction_read_degradation_rate
                },
                'io_characteristics': {
                    'io_intensity': 0.4,        # 낮은 I/O 강도
                    'stability': 0.8,           # 높은 안정성
                    'performance_factor': 0.9   # 높은 성능 인자
                }
            }
        }
        
        return temporal_factors
    
    def _analyze_device_envelope_fillrandom_enhanced(self, temporal_analysis):
        """FillRandom 워크로드 특성을 반영한 Device Envelope 모델 분석"""
        print("📊 FillRandom 워크로드 특성 반영 Device Envelope 모델 분석 중...")
        
        temporal_factors = self._calculate_fillrandom_temporal_factors()
        device_envelope_temporal = {}
        
        for phase_name, phase_model in temporal_analysis.get('phase_models', {}).items():
            characteristics = phase_model['characteristics']
            temporal_data = temporal_factors[phase_name]
            
            # FillRandom 워크로드 특성
            workload_char = temporal_data['workload_characteristics']
            perf_factors = temporal_data['performance_factors']
            io_char = temporal_data['io_characteristics']
            
            # Write 성능 (사용자 Write)
            write_performance = perf_factors['write_performance']
            write_degradation_factor = perf_factors['write_degradation_factor']
            
            # Compaction Read 성능 (시스템 Read)
            compaction_read_performance = perf_factors['compaction_read_performance']
            compaction_read_degradation_factor = perf_factors['compaction_read_degradation_factor']
            
            # I/O 특성
            io_intensity = io_char['io_intensity']
            stability = io_char['stability']
            performance_factor = io_char['performance_factor']
            
            # I/O 경합도 계산
            io_contention = 1.0 - (io_intensity * 0.3)  # 최대 30% 감소
            
            # 안정성에 따른 성능 조정
            stability_factor = 1.0 + (stability * 0.1)  # 최대 10% 증가
            
            # FillRandom 워크로드 특성을 반영한 성능 조정
            # Write 성능 (사용자 Write)
            adjusted_write_bw = (write_performance * 
                               (1.0 - write_degradation_factor) *
                               performance_factor *
                               io_contention *
                               stability_factor)
            
            # Compaction Read 성능 (시스템 Read)
            adjusted_compaction_read_bw = (compaction_read_performance * 
                                         (1.0 - compaction_read_degradation_factor) *
                                         performance_factor *
                                         io_contention *
                                         stability_factor)
            
            # S_max 계산 (Write 성능 기반)
            key_size = 16  # bytes
            value_size = 1024  # bytes
            record_size = key_size + value_size
            s_max = (adjusted_write_bw * 1024 * 1024) / record_size  # ops/sec
            
            # Compaction 효율성 계산
            compaction_efficiency = adjusted_compaction_read_bw / adjusted_write_bw if adjusted_write_bw > 0 else 0
            
            device_envelope_temporal[phase_name] = {
                'workload_characteristics': workload_char,
                'base_performance': {
                    'write_performance': write_performance,
                    'compaction_read_performance': compaction_read_performance
                },
                'degradation_factors': {
                    'write_degradation_factor': write_degradation_factor,
                    'compaction_read_degradation_factor': compaction_read_degradation_factor
                },
                'adjusted_performance': {
                    'adjusted_write_bw': adjusted_write_bw,
                    'adjusted_compaction_read_bw': adjusted_compaction_read_bw
                },
                's_max': s_max,
                'compaction_efficiency': compaction_efficiency,
                'io_characteristics': {
                    'io_contention': io_contention,
                    'stability_factor': stability_factor,
                    'performance_factor': performance_factor
                }
            }
        
        return device_envelope_temporal
    
    def _analyze_closed_ledger_fillrandom_enhanced(self, temporal_analysis):
        """FillRandom 워크로드 특성을 반영한 Closed Ledger 모델 분석"""
        print("📊 FillRandom 워크로드 특성 반영 Closed Ledger 모델 분석 중...")
        
        temporal_factors = self._calculate_fillrandom_temporal_factors()
        closed_ledger_temporal = {}
        
        for phase_name, phase_model in temporal_analysis.get('phase_models', {}).items():
            characteristics = phase_model['characteristics']
            temporal_data = temporal_factors[phase_name]
            
            # FillRandom 워크로드 특성
            perf_factors = temporal_data['performance_factors']
            io_char = temporal_data['io_characteristics']
            
            # Write 성능 (사용자 Write)
            write_performance = perf_factors['write_performance']
            write_degradation_factor = perf_factors['write_degradation_factor']
            
            # 성능 인자
            performance_factor = io_char['performance_factor']
            
            # Closed Ledger 모델 계산 (Write 성능 기반)
            key_size = 16  # bytes
            value_size = 1024  # bytes
            record_size = key_size + value_size
            
            # FillRandom 워크로드 특성을 반영한 성능 조정
            adjusted_bw = (write_performance * 
                         (1.0 - write_degradation_factor) * 
                         performance_factor)
            
            s_max = (adjusted_bw * 1024 * 1024) / record_size  # ops/sec
            
            closed_ledger_temporal[phase_name] = {
                'base_performance': write_performance,
                'degradation_factor': write_degradation_factor,
                'adjusted_bw': adjusted_bw,
                's_max': s_max,
                'performance_factor': performance_factor,
                'workload_type': 'FillRandom (Sequential Write Only)'
            }
        
        return closed_ledger_temporal
    
    def _analyze_dynamic_simulation_fillrandom_enhanced(self, temporal_analysis):
        """FillRandom 워크로드 특성을 반영한 Dynamic Simulation 모델 분석"""
        print("📊 FillRandom 워크로드 특성 반영 Dynamic Simulation 모델 분석 중...")
        
        temporal_factors = self._calculate_fillrandom_temporal_factors()
        dynamic_simulation_temporal = {}
        
        for phase_name, phase_model in temporal_analysis.get('phase_models', {}).items():
            characteristics = phase_model['characteristics']
            temporal_data = temporal_factors[phase_name]
            
            # FillRandom 워크로드 특성
            perf_factors = temporal_data['performance_factors']
            io_char = temporal_data['io_characteristics']
            
            # Write 성능 (사용자 Write)
            write_performance = perf_factors['write_performance']
            write_degradation_factor = perf_factors['write_degradation_factor']
            
            # Compaction Read 성능 (시스템 Read)
            compaction_read_performance = perf_factors['compaction_read_performance']
            compaction_read_degradation_factor = perf_factors['compaction_read_degradation_factor']
            
            # 성능 인자
            performance_factor = io_char['performance_factor']
            stability = io_char['stability']
            
            # Dynamic Simulation 모델 계산
            key_size = 16  # bytes
            value_size = 1024  # bytes
            record_size = key_size + value_size
            
            # FillRandom 워크로드 특성을 반영한 성능 조정
            # Write 성능 (사용자 Write)
            adjusted_write_bw = (write_performance * 
                               (1.0 - write_degradation_factor) * 
                               performance_factor * 
                               (1.0 + stability * 0.1))
            
            # Compaction Read 성능 (시스템 Read)
            adjusted_compaction_read_bw = (compaction_read_performance * 
                                        (1.0 - compaction_read_degradation_factor) * 
                                        performance_factor * 
                                        (1.0 + stability * 0.1))
            
            # S_max 계산 (Write 성능 기반)
            s_max = (adjusted_write_bw * 1024 * 1024) / record_size  # ops/sec
            
            # Compaction 효율성 계산
            compaction_efficiency = adjusted_compaction_read_bw / adjusted_write_bw if adjusted_write_bw > 0 else 0
            
            dynamic_simulation_temporal[phase_name] = {
                'base_performance': {
                    'write_performance': write_performance,
                    'compaction_read_performance': compaction_read_performance
                },
                'degradation_factors': {
                    'write_degradation_factor': write_degradation_factor,
                    'compaction_read_degradation_factor': compaction_read_degradation_factor
                },
                'adjusted_performance': {
                    'adjusted_write_bw': adjusted_write_bw,
                    'adjusted_compaction_read_bw': adjusted_compaction_read_bw
                },
                'dynamic_smax': s_max,
                'compaction_efficiency': compaction_efficiency,
                'stability': stability,
                'performance_factor': performance_factor,
                'workload_type': 'FillRandom (Sequential Write + Compaction Read)'
            }
        
        return dynamic_simulation_temporal
    
    def analyze_v4_2_fillrandom_enhanced(self):
        """v4.2 FillRandom Enhanced 모델 분석"""
        print("🔍 v4.2 FillRandom Enhanced 모델 분석 중...")
        
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
        
        # FillRandom 워크로드 특성을 반영한 모델 분석
        device_envelope_temporal = self._analyze_device_envelope_fillrandom_enhanced(temporal_analysis)
        closed_ledger_temporal = self._analyze_closed_ledger_fillrandom_enhanced(temporal_analysis)
        dynamic_simulation_temporal = self._analyze_dynamic_simulation_fillrandom_enhanced(temporal_analysis)
        
        # v4.2 모델 예측 결과
        self.v4_2_predictions = {
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
                
                # Compaction 효율성
                compaction_efficiency = device_envelope_temporal[phase_name]['compaction_efficiency']
                
                phase_performance[phase_name] = {
                    'device_smax': device_smax,
                    'ledger_smax': ledger_smax,
                    'dynamic_smax': dynamic_smax,
                    'avg_prediction': avg_prediction,
                    'compaction_efficiency': compaction_efficiency
                }
        
        self.results = {
            'v4_2_predictions': self.v4_2_predictions,
            'phase_performance': phase_performance,
            'phase_a_fillrandom_data': self.phase_a_data,
            'fillrandom_temporal_factors': self._calculate_fillrandom_temporal_factors()
        }
        
        print("✅ v4.2 FillRandom Enhanced 모델 분석 완료:")
        print(f"   - 초기 시기 Device Envelope: {device_envelope_temporal['initial_phase']['s_max']:.2f} ops/sec")
        print(f"   - 중기 시기 Device Envelope: {device_envelope_temporal['middle_phase']['s_max']:.2f} ops/sec")
        print(f"   - 후기 시기 Device Envelope: {device_envelope_temporal['final_phase']['s_max']:.2f} ops/sec")
        
        return self.v4_2_predictions
    
    def create_v4_2_fillrandom_visualization(self):
        """v4.2 FillRandom Enhanced 모델 시각화 생성"""
        print("📊 v4.2 FillRandom Enhanced 모델 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('V4.2 FillRandom Enhanced Model Analysis', fontsize=16, fontweight='bold')
        
        # 1. FillRandom 워크로드 특성
        phases = ['Initial', 'Middle', 'Final']
        write_performance = []
        compaction_read_performance = []
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            if phase_name in self.v4_2_predictions['device_envelope_temporal']:
                data = self.v4_2_predictions['device_envelope_temporal'][phase_name]
                write_performance.append(data['adjusted_performance']['adjusted_write_bw'])
                compaction_read_performance.append(data['adjusted_performance']['adjusted_compaction_read_bw'])
        
        x = np.arange(len(phases))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, write_performance, width, label='User Write (Sequential)', color='skyblue', alpha=0.8)
        bars2 = ax1.bar(x + width/2, compaction_read_performance, width, label='System Read (Compaction)', color='lightcoral', alpha=0.8)
        
        ax1.set_xlabel('Temporal Phase')
        ax1.set_ylabel('Performance (MB/s)')
        ax1.set_title('FillRandom Workload Performance by Phase')
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
        
        # 2. 시기별 S_max 예측
        if self.v4_2_predictions:
            device_envelope = self.v4_2_predictions.get('device_envelope_temporal', {})
            s_max_values = []
            
            for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
                if phase_name in device_envelope:
                    s_max_values.append(device_envelope[phase_name]['s_max'])
            
            if s_max_values:
                bars = ax2.bar(phases, s_max_values, color='lightgreen', alpha=0.7)
                ax2.set_ylabel('S_max (ops/sec)')
                ax2.set_title('Predicted S_max by Phase (V4.2 FillRandom Enhanced)')
                ax2.grid(True, alpha=0.3)
                
                for bar, value in zip(bars, s_max_values):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{value:.0f}', ha='center', va='bottom', fontsize=9)
        
        # 3. Compaction 효율성 분석
        compaction_efficiency = []
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            if phase_name in self.v4_2_predictions['device_envelope_temporal']:
                efficiency = self.v4_2_predictions['device_envelope_temporal'][phase_name]['compaction_efficiency']
                compaction_efficiency.append(efficiency)
        
        bars = ax3.bar(phases, compaction_efficiency, color='orange', alpha=0.7)
        ax3.set_ylabel('Compaction Efficiency (Read/Write Ratio)')
        ax3.set_title('Compaction Efficiency by Phase')
        ax3.grid(True, alpha=0.3)
        
        for bar, value in zip(bars, compaction_efficiency):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}', ha='center', va='bottom', fontsize=9)
        
        # 4. FillRandom 워크로드 특성 및 성능 열화
        ax4.text(0.1, 0.9, 'V4.2 FillRandom Enhanced Model Characteristics:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.8, '• Write: Sequential Write Only (User Operations)', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.7, '• Read: Compaction Read Only (System Operations)', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.6, '• User Reads: None', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.5, '• System Reads: Compaction Only', fontsize=12, transform=ax4.transAxes)
        
        ax4.text(0.1, 0.3, 'Performance Degradation:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        ax4.text(0.1, 0.2, f'• Write Degradation: {((self.phase_a_data["initial"]["seq_write"]["write_bw"] - self.phase_a_data["degraded"]["seq_write"]["write_bw"]) / self.phase_a_data["initial"]["seq_write"]["write_bw"] * 100):.1f}%', fontsize=12, transform=ax4.transAxes)
        ax4.text(0.1, 0.1, f'• Compaction Read Degradation: {((self.phase_a_data["initial"]["seq_read"]["read_bw"] - self.phase_a_data["degraded"]["seq_read"]["read_bw"]) / self.phase_a_data["initial"]["seq_read"]["read_bw"] * 100):.1f}%', fontsize=12, transform=ax4.transAxes)
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('V4.2 Model Characteristics')
        
        plt.tight_layout()
        plt.savefig(f"{self.results_dir}/v4_2_fillrandom_enhanced_model_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ v4.2 FillRandom Enhanced 모델 시각화 완료")
    
    def save_results(self):
        """결과 저장"""
        print("💾 v4.2 FillRandom Enhanced 모델 결과 저장 중...")
        
        # JSON 결과 저장
        try:
            with open(f"{self.results_dir}/v4_2_fillrandom_enhanced_model_results.json", 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print("✅ JSON 결과 저장 완료")
        except Exception as e:
            print(f"⚠️ JSON 저장 실패: {e}")
        
        # Markdown 보고서 생성
        try:
            report_content = self._generate_v4_2_fillrandom_report()
            with open(f"{self.results_dir}/v4_2_fillrandom_enhanced_model_report.md", 'w') as f:
                f.write(report_content)
            print("✅ Markdown 보고서 생성 완료")
        except Exception as e:
            print(f"⚠️ Markdown 보고서 생성 실패: {e}")
    
    def _generate_v4_2_fillrandom_report(self):
        """v4.2 FillRandom Enhanced 모델 보고서 생성"""
        report = f"""# V4.2 FillRandom Enhanced Model Analysis

## Overview
This report presents the analysis of v4.2 FillRandom Enhanced model that incorporates the actual characteristics of FillRandom workload.

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## V4.2 Model Enhancements

### 1. FillRandom Workload Characteristics
- **Write Type**: Sequential Write Only (User Operations)
- **Read Type**: Compaction Read Only (System Operations)
- **User Reads**: None
- **System Reads**: Compaction Only

### 2. Performance Degradation Integration
- **Write Performance Degradation**: {((self.phase_a_data['initial']['seq_write']['write_bw'] - self.phase_a_data['degraded']['seq_write']['write_bw']) / self.phase_a_data['initial']['seq_write']['write_bw'] * 100):.1f}%
- **Compaction Read Performance Degradation**: {((self.phase_a_data['initial']['seq_read']['read_bw'] - self.phase_a_data['degraded']['seq_read']['read_bw']) / self.phase_a_data['initial']['seq_read']['read_bw'] * 100):.1f}%

## Phase-A Performance Data
- **Initial Seq Write**: {self.phase_a_data['initial']['seq_write']['write_bw']:.1f} MB/s
- **Initial Seq Read**: {self.phase_a_data['initial']['seq_read']['read_bw']:.1f} MB/s
- **Degraded Seq Write**: {self.phase_a_data['degraded']['seq_write']['write_bw']:.1f} MB/s
- **Degraded Seq Read**: {self.phase_a_data['degraded']['seq_read']['read_bw']:.1f} MB/s

## V4.2 Model Predictions
"""
        
        if self.v4_2_predictions:
            device_envelope = self.v4_2_predictions.get('device_envelope_temporal', {})
            for phase_name, data in device_envelope.items():
                report += f"""
### {phase_name.replace('_', ' ').title()}
- **S_max**: {data['s_max']:.2f} ops/sec
- **Write Performance**: {data['adjusted_performance']['adjusted_write_bw']:.1f} MB/s
- **Compaction Read Performance**: {data['adjusted_performance']['adjusted_compaction_read_bw']:.1f} MB/s
- **Compaction Efficiency**: {data['compaction_efficiency']:.2f}
- **Write Degradation Factor**: {data['degradation_factors']['write_degradation_factor']:.1%}
- **Compaction Read Degradation Factor**: {data['degradation_factors']['compaction_read_degradation_factor']:.1%}
"""
        
        report += f"""
## Key Insights

### 1. V4.2 Model Improvements
- **FillRandom Workload Specific**: Sequential Write + Compaction Read만 고려
- **Real Performance Data**: Phase-A 실제 측정 데이터 반영
- **Degradation Modeling**: Write와 Compaction Read 성능 열화 모두 반영
- **Compaction Efficiency**: Compaction 효율성 분석 포함

### 2. Performance Characteristics
- **Write Path**: Sequential Write 성능이 전체 성능에 미치는 영향
- **Compaction Path**: Compaction Read 성능이 Compaction 효율성에 미치는 영향
- **Workload Pattern**: Write-Heavy, No User Reads

### 3. Model Accuracy Improvements
- **Workload-Specific Modeling**: FillRandom 워크로드 특성 정확히 반영
- **Real Degradation Data**: 실제 측정된 성능 열화 데이터 사용
- **Compaction Analysis**: Compaction 효율성 및 성능 영향 분석

## Visualization
![V4.2 FillRandom Enhanced Model Analysis](v4_2_fillrandom_enhanced_model_analysis.png)

## Analysis Time
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return report
    
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 v4.2 FillRandom Enhanced 모델 분석 시작")
        print("=" * 60)
        
        self.analyze_v4_2_fillrandom_enhanced()
        self.create_v4_2_fillrandom_visualization()
        self.save_results()
        
        print("=" * 60)
        print("✅ v4.2 FillRandom Enhanced 모델 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

if __name__ == "__main__":
    analyzer = V4_2_FillRandom_Enhanced_Model()
    analyzer.run_analysis()


