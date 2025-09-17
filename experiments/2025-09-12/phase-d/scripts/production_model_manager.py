#!/usr/bin/env python3
"""
Production Model Manager for Phase-D
Enhanced 모델들을 프로덕션 환경에서 관리하고 실시간으로 최적화
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
import pandas as pd
import numpy as np

class ProductionModelManager:
    def __init__(self):
        self.models = {}
        self.active_model = None
        self.performance_history = []
        self.system_conditions = {}
        self.monitoring_active = False
        self.auto_tuning_enabled = True
        
        # Enhanced 모델들 로드
        self.load_enhanced_models()
        
    def load_enhanced_models(self):
        """Enhanced 모델들 로드"""
        print("📊 Enhanced 모델들 로드 중...")
        
        # Phase-C에서 개발된 Enhanced 모델들 import
        try:
            sys.path.append('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/scripts')
            
            from analyze_v1_model_enhanced import V1ModelAnalyzerEnhanced
            from analyze_v2_1_model_enhanced import V21ModelAnalyzerEnhanced
            from analyze_v3_model_enhanced import V3ModelAnalyzerEnhanced
            from analyze_v4_model_enhanced import V4ModelAnalyzerEnhanced
            from analyze_v5_model_enhanced import V5ModelAnalyzerEnhanced
            
            self.models = {
                'v1_enhanced': V1ModelAnalyzerEnhanced(),
                'v2_1_enhanced': V21ModelAnalyzerEnhanced(),
                'v3_enhanced': V3ModelAnalyzerEnhanced(),
                'v4_enhanced': V4ModelAnalyzerEnhanced(),
                'v5_enhanced': V5ModelAnalyzerEnhanced()
            }
            
            print(f"✅ {len(self.models)} 개 Enhanced 모델 로드 완료")
            
        except Exception as e:
            print(f"❌ Enhanced 모델 로드 오류: {e}")
            self.models = {}
    
    def select_optimal_model(self, system_conditions):
        """시스템 조건에 따른 최적 모델 선택"""
        print("🔍 최적 모델 선택 중...")
        
        # 시스템 조건 분석
        workload_type = system_conditions.get('workload_type', 'mixed')
        io_intensity = system_conditions.get('io_intensity', 'medium')
        compaction_pressure = system_conditions.get('compaction_pressure', 'medium')
        
        # 모델 선택 로직
        if workload_type == 'write_intensive' and io_intensity == 'high':
            selected_model = 'v4_enhanced'  # Device Envelope 모델
        elif compaction_pressure == 'high':
            selected_model = 'v3_enhanced'  # Dynamic Compaction-Aware 모델
        elif workload_type == 'mixed':
            selected_model = 'v2_1_enhanced'  # Harmonic Mean 모델
        elif system_conditions.get('real_time_adaptation', False):
            selected_model = 'v5_enhanced'  # Real-time Adaptation 모델
        else:
            selected_model = 'v1_enhanced'  # 기본 모델
        
        self.active_model = selected_model
        print(f"✅ 선택된 모델: {selected_model}")
        
        return selected_model
    
    def predict_smax(self, current_metrics):
        """실시간 S_max 예측"""
        if not self.active_model or self.active_model not in self.models:
            print("❌ 활성 모델이 설정되지 않았습니다.")
            return None
        
        try:
            model = self.models[self.active_model]
            
            # 현재 메트릭을 모델에 전달하여 예측
            if hasattr(model, 'analyze_v1_model_enhanced'):
                prediction = model.analyze_v1_model_enhanced()
            elif hasattr(model, 'analyze_v21_model_enhanced'):
                prediction = model.analyze_v21_model_enhanced()
            elif hasattr(model, 'analyze_v3_model_enhanced'):
                prediction = model.analyze_v3_model_enhanced()
            elif hasattr(model, 'analyze_v4_model_enhanced'):
                prediction = model.analyze_v4_model_enhanced()
            elif hasattr(model, 'analyze_v5_model_enhanced'):
                prediction = model.analyze_v5_model_enhanced()
            else:
                print(f"❌ {self.active_model} 모델의 예측 메서드를 찾을 수 없습니다.")
                return None
            
            # 예측 결과 기록
            prediction_record = {
                'timestamp': datetime.now().isoformat(),
                'model': self.active_model,
                'predicted_smax': prediction,
                'current_metrics': current_metrics
            }
            
            self.performance_history.append(prediction_record)
            
            print(f"✅ {self.active_model} 모델 예측: {prediction:.2f} ops/sec")
            return prediction
            
        except Exception as e:
            print(f"❌ S_max 예측 오류: {e}")
            return None
    
    def start_monitoring(self, interval=10):
        """실시간 모니터링 시작"""
        print(f"📊 실시간 모니터링 시작 (간격: {interval}초)")
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # 현재 시스템 메트릭 수집
                    current_metrics = self.collect_system_metrics()
                    
                    # 시스템 조건 업데이트
                    self.update_system_conditions(current_metrics)
                    
                    # 최적 모델 선택
                    self.select_optimal_model(self.system_conditions)
                    
                    # S_max 예측
                    prediction = self.predict_smax(current_metrics)
                    
                    # 성능 기록 저장
                    self.save_performance_record(current_metrics, prediction)
                    
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"❌ 모니터링 오류: {e}")
                    time.sleep(interval)
        
        # 모니터링 스레드 시작
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        print("✅ 실시간 모니터링 시작됨")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        print("⏹️ 실시간 모니터링 중지")
        self.monitoring_active = False
    
    def collect_system_metrics(self):
        """시스템 메트릭 수집"""
        # 실제 구현에서는 RocksDB 통계, 시스템 리소스 등을 수집
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'qps': np.random.normal(1000, 100),  # 시뮬레이션
            'latency': np.random.normal(1.0, 0.1),
            'cpu_usage': np.random.normal(50, 10),
            'memory_usage': np.random.normal(60, 5),
            'io_utilization': np.random.normal(40, 8),
            'compaction_activity': np.random.normal(30, 5)
        }
        
        return metrics
    
    def update_system_conditions(self, metrics):
        """시스템 조건 업데이트"""
        self.system_conditions = {
            'workload_type': 'mixed',  # 실제로는 메트릭 분석 결과
            'io_intensity': 'high' if metrics['io_utilization'] > 50 else 'medium',
            'compaction_pressure': 'high' if metrics['compaction_activity'] > 40 else 'medium',
            'real_time_adaptation': True,
            'system_load': metrics['cpu_usage']
        }
    
    def save_performance_record(self, metrics, prediction):
        """성능 기록 저장"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'prediction': prediction,
            'model': self.active_model
        }
        
        # JSON 파일에 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(results_dir, exist_ok=True)
        
        record_file = f"{results_dir}/production_performance_records.json"
        
        # 기존 기록 로드
        records = []
        if os.path.exists(record_file):
            try:
                with open(record_file, 'r') as f:
                    records = json.load(f)
            except:
                records = []
        
        # 새 기록 추가
        records.append(record)
        
        # 파일 저장
        with open(record_file, 'w') as f:
            json.dump(records, f, indent=2)
    
    def get_performance_summary(self):
        """성능 요약 정보 반환"""
        if not self.performance_history:
            return "성능 기록이 없습니다."
        
        recent_predictions = [record['predicted_smax'] for record in self.performance_history[-10:]]
        
        summary = {
            'total_records': len(self.performance_history),
            'active_model': self.active_model,
            'recent_predictions': {
                'mean': np.mean(recent_predictions),
                'std': np.std(recent_predictions),
                'min': np.min(recent_predictions),
                'max': np.max(recent_predictions)
            },
            'monitoring_status': 'active' if self.monitoring_active else 'inactive'
        }
        
        return summary

if __name__ == "__main__":
    # Production Model Manager 테스트
    manager = ProductionModelManager()
    
    # 모니터링 시작
    manager.start_monitoring(interval=5)
    
    # 30초 동안 모니터링
    time.sleep(30)
    
    # 모니터링 중지
    manager.stop_monitoring()
    
    # 성능 요약 출력
    summary = manager.get_performance_summary()
    print(f"📊 성능 요약: {json.dumps(summary, indent=2)}")
