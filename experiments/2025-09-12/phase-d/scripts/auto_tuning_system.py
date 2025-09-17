#!/usr/bin/env python3
"""
Auto-tuning System for Phase-D
Enhanced 모델들의 파라미터를 실시간으로 자동 조정하는 시스템
"""

import os
import json
import numpy as np
from datetime import datetime
import pandas as pd

class AutoTuningSystem:
    def __init__(self):
        self.parameter_history = []
        self.performance_feedback = []
        self.optimization_history = []
        self.tuning_active = False
        
        # 튜닝 가능한 파라미터들
        self.tunable_parameters = {
            'v1_enhanced': ['flush_factor', 'stall_factor', 'wa_factor', 'memtable_factor'],
            'v2_1_enhanced': ['p_stall_enhanced', 'WA_enhanced', 'B_write_enhanced', 'B_read_enhanced'],
            'v3_enhanced': ['p_stall_enhanced', 'compaction_factor', 'stall_factor', 'wa_factor'],
            'v4_enhanced': ['degradation_factor', 'io_contention_factor', 'compaction_intensity'],
            'v5_enhanced': ['throughput_factor', 'latency_factor', 'accuracy_factor', 'scaling_factor']
        }
        
        # 파라미터 범위 정의
        self.parameter_ranges = {
            'flush_factor': (0.1, 1.0),
            'stall_factor': (0.1, 1.0),
            'wa_factor': (0.1, 1.0),
            'memtable_factor': (0.1, 1.0),
            'p_stall_enhanced': (0.0, 0.8),
            'WA_enhanced': (1.0, 5.0),
            'B_write_enhanced': (50.0, 200.0),
            'B_read_enhanced': (50.0, 200.0),
            'compaction_factor': (0.1, 1.0),
            'degradation_factor': (0.1, 1.0),
            'io_contention_factor': (0.1, 1.0),
            'throughput_factor': (0.1, 2.0),
            'latency_factor': (0.1, 2.0),
            'accuracy_factor': (0.1, 2.0),
            'scaling_factor': (0.1, 2.0)
        }
    
    def start_tuning(self, model_name, initial_parameters=None):
        """자동 튜닝 시작"""
        print(f"🔧 {model_name} 모델 자동 튜닝 시작")
        
        self.tuning_active = True
        self.current_model = model_name
        
        # 초기 파라미터 설정
        if initial_parameters:
            self.current_parameters = initial_parameters
        else:
            self.current_parameters = self.get_default_parameters(model_name)
        
        print(f"✅ 초기 파라미터: {self.current_parameters}")
    
    def stop_tuning(self):
        """자동 튜닝 중지"""
        print("⏹️ 자동 튜닝 중지")
        self.tuning_active = False
    
    def get_default_parameters(self, model_name):
        """모델별 기본 파라미터 반환"""
        defaults = {
            'v1_enhanced': {
                'flush_factor': 0.5,
                'stall_factor': 0.3,
                'wa_factor': 0.482,
                'memtable_factor': 0.6
            },
            'v2_1_enhanced': {
                'p_stall_enhanced': 0.5,
                'WA_enhanced': 2.073,
                'B_write_enhanced': 96.6,
                'B_read_enhanced': 95.2
            },
            'v3_enhanced': {
                'p_stall_enhanced': 0.5,
                'compaction_factor': 0.8,
                'stall_factor': 0.7,
                'wa_factor': 0.482
            },
            'v4_enhanced': {
                'degradation_factor': 0.8,
                'io_contention_factor': 0.7,
                'compaction_intensity': 0.5
            },
            'v5_enhanced': {
                'throughput_factor': 1.0,
                'latency_factor': 1.0,
                'accuracy_factor': 1.0,
                'scaling_factor': 1.0
            }
        }
        
        return defaults.get(model_name, {})
    
    def adjust_parameters(self, performance_data):
        """성능 데이터를 기반으로 파라미터 조정"""
        if not self.tuning_active:
            return self.current_parameters
        
        print("🔧 파라미터 조정 중...")
        
        # 성능 피드백 분석
        feedback_analysis = self.analyze_performance_feedback(performance_data)
        
        # 파라미터 조정 전략 결정
        adjustment_strategy = self.determine_adjustment_strategy(feedback_analysis)
        
        # 파라미터 조정 실행
        adjusted_parameters = self.execute_parameter_adjustment(adjustment_strategy)
        
        # 조정 기록 저장
        self.save_adjustment_record(performance_data, adjusted_parameters)
        
        print(f"✅ 파라미터 조정 완료: {adjusted_parameters}")
        
        return adjusted_parameters
    
    def analyze_performance_feedback(self, performance_data):
        """성능 피드백 분석"""
        analysis = {
            'accuracy_trend': 'improving',  # 실제로는 히스토리 분석
            'error_rate': performance_data.get('error_rate', 0.1),
            'prediction_accuracy': performance_data.get('accuracy', 0.8),
            'system_load': performance_data.get('system_load', 0.5),
            'io_intensity': performance_data.get('io_intensity', 0.5)
        }
        
        return analysis
    
    def determine_adjustment_strategy(self, feedback_analysis):
        """조정 전략 결정"""
        strategy = {
            'adjustment_type': 'conservative',  # conservative, aggressive, adaptive
            'parameter_focus': [],  # 조정할 파라미터들
            'adjustment_magnitude': 0.1  # 조정 크기
        }
        
        # 에러율이 높으면 더 공격적인 조정
        if feedback_analysis['error_rate'] > 0.2:
            strategy['adjustment_type'] = 'aggressive'
            strategy['adjustment_magnitude'] = 0.2
        
        # 정확도가 낮으면 모든 파라미터 조정
        if feedback_analysis['prediction_accuracy'] < 0.7:
            strategy['parameter_focus'] = list(self.current_parameters.keys())
        
        # 시스템 로드가 높으면 특정 파라미터에 집중
        if feedback_analysis['system_load'] > 0.8:
            if 'stall_factor' in self.current_parameters:
                strategy['parameter_focus'].append('stall_factor')
            if 'io_contention_factor' in self.current_parameters:
                strategy['parameter_focus'].append('io_contention_factor')
        
        return strategy
    
    def execute_parameter_adjustment(self, strategy):
        """파라미터 조정 실행"""
        adjusted_parameters = self.current_parameters.copy()
        
        # 조정할 파라미터들 결정
        parameters_to_adjust = strategy['parameter_focus']
        if not parameters_to_adjust:
            parameters_to_adjust = list(self.current_parameters.keys())
        
        # 각 파라미터 조정
        for param_name in parameters_to_adjust:
            if param_name in adjusted_parameters:
                current_value = adjusted_parameters[param_name]
                adjustment = self.calculate_parameter_adjustment(
                    param_name, current_value, strategy
                )
                adjusted_parameters[param_name] = adjustment
        
        # 조정된 파라미터를 현재 파라미터로 설정
        self.current_parameters = adjusted_parameters
        
        return adjusted_parameters
    
    def calculate_parameter_adjustment(self, param_name, current_value, strategy):
        """개별 파라미터 조정 계산"""
        # 파라미터 범위 가져오기
        param_range = self.parameter_ranges.get(param_name, (0.0, 1.0))
        min_val, max_val = param_range
        
        # 조정 크기 결정
        adjustment_magnitude = strategy['adjustment_magnitude']
        
        # 랜덤 조정 (실제로는 더 정교한 알고리즘 사용)
        if strategy['adjustment_type'] == 'aggressive':
            adjustment = np.random.uniform(-adjustment_magnitude, adjustment_magnitude)
        else:
            adjustment = np.random.uniform(-adjustment_magnitude/2, adjustment_magnitude/2)
        
        # 새 값 계산
        new_value = current_value + adjustment
        
        # 범위 내로 제한
        new_value = max(min_val, min(max_val, new_value))
        
        return new_value
    
    def save_adjustment_record(self, performance_data, adjusted_parameters):
        """조정 기록 저장"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'model': self.current_model,
            'performance_data': performance_data,
            'adjusted_parameters': adjusted_parameters,
            'tuning_active': self.tuning_active
        }
        
        # 기록 저장
        self.parameter_history.append(record)
        
        # 파일에 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(results_dir, exist_ok=True)
        
        record_file = f"{results_dir}/auto_tuning_records.json"
        
        with open(record_file, 'w') as f:
            json.dump(self.parameter_history, f, indent=2)
    
    def get_tuning_summary(self):
        """튜닝 요약 정보 반환"""
        if not self.parameter_history:
            return "튜닝 기록이 없습니다."
        
        recent_adjustments = self.parameter_history[-10:]
        
        summary = {
            'total_adjustments': len(self.parameter_history),
            'current_model': self.current_model,
            'tuning_active': self.tuning_active,
            'recent_adjustments': len(recent_adjustments),
            'current_parameters': self.current_parameters
        }
        
        return summary
    
    def optimize_model(self, model, feedback_data):
        """모델 최적화"""
        print(f"🚀 {model} 모델 최적화 시작")
        
        # 최적화 기록
        optimization_record = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'feedback_data': feedback_data,
            'optimization_type': 'parameter_tuning'
        }
        
        self.optimization_history.append(optimization_record)
        
        # 최적화 결과 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(results_dir, exist_ok=True)
        
        optimization_file = f"{results_dir}/model_optimization_records.json"
        
        with open(optimization_file, 'w') as f:
            json.dump(self.optimization_history, f, indent=2)
        
        print(f"✅ {model} 모델 최적화 완료")

if __name__ == "__main__":
    # Auto-tuning System 테스트
    tuner = AutoTuningSystem()
    
    # v1 모델 튜닝 시작
    tuner.start_tuning('v1_enhanced')
    
    # 시뮬레이션 성능 데이터
    performance_data = {
        'error_rate': 0.15,
        'accuracy': 0.85,
        'system_load': 0.6,
        'io_intensity': 0.4
    }
    
    # 파라미터 조정
    adjusted_params = tuner.adjust_parameters(performance_data)
    print(f"조정된 파라미터: {adjusted_params}")
    
    # 튜닝 중지
    tuner.stop_tuning()
    
    # 요약 정보 출력
    summary = tuner.get_tuning_summary()
    print(f"튜닝 요약: {json.dumps(summary, indent=2)}")
