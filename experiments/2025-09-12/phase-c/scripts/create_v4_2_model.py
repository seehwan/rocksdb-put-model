#!/usr/bin/env python3
"""
v4.2 모델 생성
장치 열화 모델과 FillRandom 워크로드 특성을 고려한 개선된 모델
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Liberation Serif 폰트 설정 (Times 스타일)
plt.rcParams['font.family'] = 'Liberation Serif'
plt.rcParams['axes.unicode_minus'] = False

class V4_2Model:
    """v4.2 모델: 장치 열화 모델과 FillRandom 워크로드 특성을 고려한 개선된 모델"""
    
    def __init__(self, results_dir="results"):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        self.phase_a_data = self._load_phase_a_degradation_data()
        self.fillrandom_characteristics = self._load_fillrandom_characteristics()
        
    def _load_phase_a_degradation_data(self):
        """Phase-A 장치 열화 데이터 로드"""
        print("📊 Phase-A 장치 열화 데이터 로드 중...")
        
        phase_a_data = {
            'initial': {'write_bw': 0, 'read_bw': 0},
            'degraded': {'write_bw': 0, 'read_bw': 0}
        }
        
        try:
            # 초기 상태 성능 데이터
            initial_seq_write_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_initial.json'
            initial_seq_read_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_initial.json'
            
            if os.path.exists(initial_seq_write_file):
                with open(initial_seq_write_file, 'r') as f:
                    initial_write_data = json.load(f)
                    phase_a_data['initial']['write_bw'] = initial_write_data['jobs'][0]['write']['bw'] / 1024  # KB/s to MB/s
                    
            if os.path.exists(initial_seq_read_file):
                with open(initial_seq_read_file, 'r') as f:
                    initial_read_data = json.load(f)
                    phase_a_data['initial']['read_bw'] = initial_read_data['jobs'][0]['read']['bw'] / 1024  # KB/s to MB/s
            
            # 열화 상태 성능 데이터
            degraded_seq_write_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_write_degraded.json'
            degraded_seq_read_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data/seq_read_degraded.json'
            
            if os.path.exists(degraded_seq_write_file):
                with open(degraded_seq_write_file, 'r') as f:
                    degraded_write_data = json.load(f)
                    phase_a_data['degraded']['write_bw'] = degraded_write_data['jobs'][0]['write']['bw'] / 1024  # KB/s to MB/s
                    
            if os.path.exists(degraded_seq_read_file):
                with open(degraded_seq_read_file, 'r') as f:
                    degraded_read_data = json.load(f)
                    phase_a_data['degraded']['read_bw'] = degraded_read_data['jobs'][0]['read']['bw'] / 1024  # KB/s to MB/s
            
            print(f"✅ Phase-A 장치 열화 데이터 로드 완료:")
            print(f"   - 초기 상태: Write {phase_a_data['initial']['write_bw']:.1f} MB/s, Read {phase_a_data['initial']['read_bw']:.1f} MB/s")
            print(f"   - 열화 상태: Write {phase_a_data['degraded']['write_bw']:.1f} MB/s, Read {phase_a_data['degraded']['read_bw']:.1f} MB/s")
            
            # 실제 열화율 계산
            if phase_a_data['initial']['write_bw'] > 0:
                actual_degradation_rate = (phase_a_data['initial']['write_bw'] - phase_a_data['degraded']['write_bw']) / phase_a_data['initial']['write_bw']
                print(f"   📉 실제 장치 열화율: {actual_degradation_rate * 100:.1f}%")
            
        except Exception as e:
            print(f"⚠️ Phase-A 데이터 로드 실패, 기본값 사용: {e}")
            
        return phase_a_data
    
    def _load_fillrandom_characteristics(self):
        """FillRandom 워크로드 특성 로드"""
        print("📊 FillRandom 워크로드 특성 로드 중...")
        
        fillrandom_characteristics = {
            'workload_type': 'FillRandom',
            'write_pattern': 'Sequential Write Only',
            'read_pattern': 'Compaction Read Only',
            'user_reads': 0,
            'system_reads': 'Compaction Only',
            'io_characteristics': {
                'sequential_write_ratio': 1.0,
                'compaction_read_ratio': 1.0,
                'random_write_ratio': 0.0,
                'user_read_ratio': 0.0
            },
            'performance_impact': {
                'write_amplification': 1.0,  # 순차 쓰기로 인한 낮은 WA
                'read_amplification': 0.0,  # 사용자 읽기 없음
                'compaction_intensity': 0.8,  # 높은 컴팩션 강도
                'io_contention': 0.6  # 중간 I/O 경합
            }
        }
        
        print("✅ FillRandom 워크로드 특성 로드 완료")
        return fillrandom_characteristics
    
    def _calculate_device_degradation_factors(self):
        """장치 열화 인자 계산"""
        print("📊 장치 열화 인자 계산 중...")
        
        initial_perf = self.phase_a_data['initial']
        degraded_perf = self.phase_a_data['degraded']
        
        # 실제 열화율 계산
        actual_degradation_rate = 0.0
        if initial_perf['write_bw'] > 0:
            actual_degradation_rate = (initial_perf['write_bw'] - degraded_perf['write_bw']) / initial_perf['write_bw']
        
        # 시기별 열화 모델링 (FillRandom 워크로드 특성 반영)
        degradation_factors = {
            'initial_phase': {
                'device_degradation': 0.0,  # 초기: 열화 없음
                'workload_impact': 0.3,     # FillRandom 특성: 순차 쓰기로 인한 낮은 영향
                'io_intensity': 0.8,        # 높은 I/O 강도
                'stability_factor': 0.2,    # 낮은 안정성
                'performance_factor': 0.4   # 중간 성능 인자
            },
            'middle_phase': {
                'device_degradation': actual_degradation_rate * 0.5,  # 중기: 실제 열화의 50%
                'workload_impact': 0.5,     # FillRandom 특성: 컴팩션 강도 증가
                'io_intensity': 0.6,        # 중간 I/O 강도
                'stability_factor': 0.5,    # 중간 안정성
                'performance_factor': 0.6    # 중간 성능 인자
            },
            'final_phase': {
                'device_degradation': actual_degradation_rate,  # 후기: 실제 열화율
                'workload_impact': 0.7,     # FillRandom 특성: 높은 컴팩션 강도
                'io_intensity': 0.4,        # 낮은 I/O 강도
                'stability_factor': 0.8,    # 높은 안정성
                'performance_factor': 0.8    # 높은 성능 인자
            }
        }
        
        return degradation_factors
    
    def _analyze_device_envelope_with_degradation(self):
        """장치 열화를 반영한 Device Envelope 모델 분석"""
        print("📊 장치 열화 반영 Device Envelope 모델 분석 중...")
        
        degradation_factors = self._calculate_device_degradation_factors()
        device_envelope_temporal = {}
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            factors = degradation_factors[phase_name]
            
            # 기본 성능 설정
            base_perf = self._get_base_performance_for_phase(phase_name)
            
            # 장치 열화 반영
            device_degradation = factors['device_degradation']
            workload_impact = factors['workload_impact']
            io_intensity = factors['io_intensity']
            stability_factor = factors['stability_factor']
            performance_factor = factors['performance_factor']
            
            # I/O 경합 계산
            io_contention = 1.0 - (io_intensity * 0.3)
            
            # 조정된 성능 계산
            adjusted_write_bw = (base_perf['write_bw'] * 
                                (1.0 - device_degradation) * 
                                (1.0 - workload_impact * 0.2) * 
                                performance_factor * 
                                io_contention * 
                                (1.0 + stability_factor * 0.1))
            
            adjusted_read_bw = (base_perf['read_bw'] * 
                               (1.0 - device_degradation) * 
                               (1.0 - workload_impact * 0.2) * 
                               performance_factor * 
                               io_contention * 
                               (1.0 + stability_factor * 0.1))
            
            # S_max 계산 (FillRandom 특성 반영)
            key_size = 16
            value_size = 1024
            record_size = key_size + value_size
            s_max = (adjusted_write_bw * 1024 * 1024) / record_size
            
            device_envelope_temporal[phase_name] = {
                'base_performance': base_perf,
                'device_degradation': device_degradation,
                'workload_impact': workload_impact,
                'adjusted_write_bw': adjusted_write_bw,
                'adjusted_read_bw': adjusted_read_bw,
                's_max': s_max,
                'io_contention': io_contention,
                'stability_factor': stability_factor,
                'performance_factor': performance_factor,
                'degradation_analysis': factors
            }
        
        return device_envelope_temporal
    
    def _get_base_performance_for_phase(self, phase_name):
        """시기별 기본 성능 설정"""
        initial_bw = self.phase_a_data['initial']
        degraded_bw = self.phase_a_data['degraded']
        
        if phase_name == 'initial_phase':
            return {'write_bw': initial_bw['write_bw'], 'read_bw': initial_bw['read_bw']}
        elif phase_name == 'middle_phase':
            return {
                'write_bw': (initial_bw['write_bw'] + degraded_bw['write_bw']) / 2,
                'read_bw': (initial_bw['read_bw'] + degraded_bw['read_bw']) / 2
            }
        else:  # final_phase
            return {'write_bw': degraded_bw['write_bw'], 'read_bw': degraded_bw['read_bw']}
    
    def _analyze_closed_ledger_with_degradation(self):
        """장치 열화를 반영한 Closed Ledger 모델 분석"""
        print("📊 장치 열화 반영 Closed Ledger 모델 분석 중...")
        
        degradation_factors = self._calculate_device_degradation_factors()
        closed_ledger_temporal = {}
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            factors = degradation_factors[phase_name]
            
            device_degradation = factors['device_degradation']
            workload_impact = factors['workload_impact']
            performance_factor = factors['performance_factor']
            
            # 기본 S_max 설정
            base_s_max = 100000
            
            # 조정된 S_max 계산
            adjusted_s_max = (base_s_max * 
                             (1.0 - device_degradation) * 
                             (1.0 - workload_impact * 0.3) * 
                             performance_factor)
            
            closed_ledger_temporal[phase_name] = {
                'device_degradation': device_degradation,
                'workload_impact': workload_impact,
                'performance_factor': performance_factor,
                's_max': adjusted_s_max,
                'degradation_analysis': factors
            }
        
        return closed_ledger_temporal
    
    def _analyze_dynamic_simulation_with_degradation(self):
        """장치 열화를 반영한 Dynamic Simulation 모델 분석"""
        print("📊 장치 열화 반영 Dynamic Simulation 모델 분석 중...")
        
        degradation_factors = self._calculate_device_degradation_factors()
        dynamic_simulation_temporal = {}
        
        for phase_name in ['initial_phase', 'middle_phase', 'final_phase']:
            factors = degradation_factors[phase_name]
            
            device_degradation = factors['device_degradation']
            workload_impact = factors['workload_impact']
            io_intensity = factors['io_intensity']
            stability_factor = factors['stability_factor']
            
            # 기본 Dynamic S_max 설정
            base_dynamic_s_max = 80000
            
            # 조정된 Dynamic S_max 계산
            adjusted_dynamic_s_max = (base_dynamic_s_max * 
                                     (1.0 - device_degradation) * 
                                     (1.0 - workload_impact * 0.2) * 
                                     (1.0 + stability_factor - io_intensity))
            
            dynamic_simulation_temporal[phase_name] = {
                'device_degradation': device_degradation,
                'workload_impact': workload_impact,
                'io_intensity': io_intensity,
                'stability_factor': stability_factor,
                'dynamic_s_max': adjusted_dynamic_s_max,
                'degradation_analysis': factors
            }
        
        return dynamic_simulation_temporal
    
    def analyze_v4_2_model(self):
        """v4.2 모델 분석 실행"""
        print("🚀 v4.2 모델 분석 시작")
        print("============================================================")
        print("🔍 장치 열화 모델과 FillRandom 워크로드 특성을 고려한 v4.2 모델 분석 중...")
        
        # 각 모델 분석
        self.temporal_predictions = {
            'device_envelope_temporal': self._analyze_device_envelope_with_degradation(),
            'closed_ledger_temporal': self._analyze_closed_ledger_with_degradation(),
            'dynamic_simulation_temporal': self._analyze_dynamic_simulation_with_degradation()
        }
        
        print("✅ v4.2 모델 분석 완료:")
        for phase_name, data in self.temporal_predictions['device_envelope_temporal'].items():
            print(f"   - {phase_name.replace('_phase', '').title()} 시기 Device Envelope: {data['s_max']:.2f} ops/sec")
        print("============================================================")
    
    def create_visualization(self):
        """v4.2 모델 시각화 생성"""
        print("📊 v4.2 모델 시각화 생성 중...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 14))
        fig.suptitle('V4.2 Model: Device Degradation + FillRandom Workload Characteristics', fontsize=16, fontweight='bold')
        
        phases = ['Initial', 'Middle', 'Final']
        x = np.arange(len(phases))
        width = 0.2
        
        # 1. 예측 S_max by 모델 타입
        device_smax = [self.temporal_predictions['device_envelope_temporal'][f'{p.lower()}_phase']['s_max'] for p in phases]
        ledger_smax = [self.temporal_predictions['closed_ledger_temporal'][f'{p.lower()}_phase']['s_max'] for p in phases]
        dynamic_smax = [self.temporal_predictions['dynamic_simulation_temporal'][f'{p.lower()}_phase']['dynamic_s_max'] for p in phases]
        
        ax1.bar(x - width, device_smax, width, label='Device Envelope S_max', color='skyblue', alpha=0.8)
        ax1.bar(x, ledger_smax, width, label='Closed Ledger S_max', color='lightcoral', alpha=0.8)
        ax1.bar(x + width, dynamic_smax, width, label='Dynamic Simulation S_max', color='lightgreen', alpha=0.8)
        ax1.set_ylabel('S_max (ops/sec)')
        ax1.set_title('Predicted S_max by Model and Phase')
        ax1.set_xticks(x)
        ax1.set_xticklabels(phases)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 장치 대역폭 by 시기
        write_bw = [self.temporal_predictions['device_envelope_temporal'][f'{p.lower()}_phase']['adjusted_write_bw'] for p in phases]
        read_bw = [self.temporal_predictions['device_envelope_temporal'][f'{p.lower()}_phase']['adjusted_read_bw'] for p in phases]
        
        ax2.bar(x - width/2, write_bw, width, label='Adjusted Write BW', color='darkblue', alpha=0.8)
        ax2.bar(x + width/2, read_bw, width, label='Adjusted Read BW', color='darkred', alpha=0.8)
        ax2.set_ylabel('Bandwidth (MB/s)')
        ax2.set_title('Adjusted Device Bandwidth by Phase')
        ax2.set_xticks(x)
        ax2.set_xticklabels(phases)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 열화 인자 by 시기
        degradation_factors = self._calculate_device_degradation_factors()
        device_degradation = [degradation_factors[f'{p.lower()}_phase']['device_degradation'] * 100 for p in phases]
        workload_impact = [degradation_factors[f'{p.lower()}_phase']['workload_impact'] * 100 for p in phases]
        io_intensity = [degradation_factors[f'{p.lower()}_phase']['io_intensity'] * 100 for p in phases]
        stability_factor = [degradation_factors[f'{p.lower()}_phase']['stability_factor'] * 100 for p in phases]
        
        ax3.plot(phases, device_degradation, marker='o', label='Device Degradation (%)', color='red', linewidth=2)
        ax3.plot(phases, workload_impact, marker='x', label='Workload Impact (%)', color='blue', linewidth=2)
        ax3.plot(phases, io_intensity, marker='s', label='I/O Intensity (%)', color='green', linewidth=2)
        ax3.plot(phases, stability_factor, marker='^', label='Stability Factor (%)', color='purple', linewidth=2)
        ax3.set_ylabel('Percentage (%)')
        ax3.set_title('V4.2 Degradation Factors (Device + FillRandom)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. FillRandom 워크로드 특성
        ax4.text(0.1, 0.9, 'FillRandom Workload Characteristics:', fontsize=14, fontweight='bold', transform=ax4.transAxes)
        
        y_pos = 0.8
        characteristics = self.fillrandom_characteristics
        ax4.text(0.1, y_pos, f'Workload Type: {characteristics["workload_type"]}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.05
        ax4.text(0.1, y_pos, f'Write Pattern: {characteristics["write_pattern"]}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.05
        ax4.text(0.1, y_pos, f'Read Pattern: {characteristics["read_pattern"]}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.05
        ax4.text(0.1, y_pos, f'User Reads: {characteristics["user_reads"]}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.05
        ax4.text(0.1, y_pos, f'System Reads: {characteristics["system_reads"]}', fontsize=12, transform=ax4.transAxes)
        y_pos -= 0.1
        
        ax4.text(0.1, y_pos, 'Performance Impact:', fontsize=12, fontweight='bold', transform=ax4.transAxes)
        y_pos -= 0.05
        perf_impact = characteristics['performance_impact']
        ax4.text(0.1, y_pos, f'Write Amplification: {perf_impact["write_amplification"]:.1f}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'Read Amplification: {perf_impact["read_amplification"]:.1f}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'Compaction Intensity: {perf_impact["compaction_intensity"]:.1f}', fontsize=11, transform=ax4.transAxes)
        y_pos -= 0.04
        ax4.text(0.1, y_pos, f'I/O Contention: {perf_impact["io_contention"]:.1f}', fontsize=11, transform=ax4.transAxes)
        
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('FillRandom Workload Characteristics')
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.results_dir, "v4_2_model_analysis.png"), dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ v4.2 모델 시각화 완료")
    
    def save_results(self):
        """결과 저장"""
        print("💾 v4.2 모델 결과 저장 중...")
        
        # JSON 결과 저장
        results = {
            'model_version': 'v4.2',
            'model_description': 'Device Degradation + FillRandom Workload Characteristics',
            'temporal_predictions': self.temporal_predictions,
            'phase_a_data': self.phase_a_data,
            'fillrandom_characteristics': self.fillrandom_characteristics,
            'analysis_time': datetime.now().isoformat()
        }
        
        results_path = os.path.join(self.results_dir, "v4_2_model_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print("✅ JSON 결과 저장 완료")
        
        # Markdown 보고서 생성
        report_path = os.path.join(self.results_dir, "v4_2_model_report.md")
        with open(report_path, 'w') as f:
            f.write("# V4.2 Model Analysis Report\n\n")
            f.write(f"## Model Version: v4.2\n")
            f.write(f"## Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Model Description\n")
            f.write("V4.2 model incorporates device degradation and FillRandom workload characteristics:\n\n")
            f.write("### Key Features:\n")
            f.write("1. **Device Degradation Model**: Based on Phase-A actual degradation data\n")
            f.write("2. **FillRandom Workload Characteristics**: Sequential write only, compaction read only\n")
            f.write("3. **Temporal Phase Analysis**: Initial, Middle, Final phases\n")
            f.write("4. **Multi-Model Integration**: Device Envelope, Closed Ledger, Dynamic Simulation\n\n")
            
            f.write("## Phase-A Device Degradation Data\n")
            f.write(f"- **Initial State**: Write {self.phase_a_data['initial']['write_bw']:.1f} MB/s, Read {self.phase_a_data['initial']['read_bw']:.1f} MB/s\n")
            f.write(f"- **Degraded State**: Write {self.phase_a_data['degraded']['write_bw']:.1f} MB/s, Read {self.phase_a_data['degraded']['read_bw']:.1f} MB/s\n\n")
            
            f.write("## FillRandom Workload Characteristics\n")
            f.write(f"- **Workload Type**: {self.fillrandom_characteristics['workload_type']}\n")
            f.write(f"- **Write Pattern**: {self.fillrandom_characteristics['write_pattern']}\n")
            f.write(f"- **Read Pattern**: {self.fillrandom_characteristics['read_pattern']}\n")
            f.write(f"- **User Reads**: {self.fillrandom_characteristics['user_reads']}\n")
            f.write(f"- **System Reads**: {self.fillrandom_characteristics['system_reads']}\n\n")
            
            f.write("## Predicted S_max by Phase\n")
            for phase_name, data in self.temporal_predictions['device_envelope_temporal'].items():
                f.write(f"- **{phase_name.replace('_phase', '').title()} Phase**: {data['s_max']:.2f} ops/sec\n")
            
            f.write(f"\n## Analysis Time\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        print("✅ Markdown 보고서 생성 완료")
    
    def run_analysis(self):
        """전체 분석 실행"""
        self.analyze_v4_2_model()
        self.create_visualization()
        self.save_results()
        print("============================================================")
        print("✅ v4.2 모델 분석 완료!")
        print(f"📊 결과 저장 위치: {self.results_dir}")

def main():
    """메인 함수"""
    print("🚀 v4.2 모델 생성 시작...")
    
    # v4.2 모델 생성
    v4_2_model = V4_2Model()
    v4_2_model.run_analysis()
    
    print("✅ v4.2 모델 생성 완료!")

if __name__ == "__main__":
    main()







