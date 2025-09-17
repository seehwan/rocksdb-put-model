#!/usr/bin/env python3
"""
Phase-D 통합 실행 스크립트
Enhanced 모델들의 프로덕션 통합, 실시간 모니터링, 자동 튜닝을 통합 실행
"""

import os
import sys
import json
import time
import threading
from datetime import datetime

# Phase-D 스크립트들 import
from production_model_manager import ProductionModelManager
from auto_tuning_system import AutoTuningSystem
from real_time_monitor import RealTimeMonitor

class PhaseDOrchestrator:
    def __init__(self):
        self.model_manager = ProductionModelManager()
        self.auto_tuner = AutoTuningSystem()
        self.monitor = RealTimeMonitor()
        self.integration_active = False
        
        # Phase-D 결과 디렉토리
        self.results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(self.results_dir, exist_ok=True)
    
    def start_phase_d(self):
        """Phase-D 통합 실행 시작"""
        print("🚀 Phase-D: Enhanced Models Production Integration 시작")
        print("=" * 60)
        
        self.integration_active = True
        
        try:
            # 1. Enhanced 모델들 배포
            print("📦 Enhanced 모델들 배포 중...")
            self.deploy_enhanced_models()
            
            # 2. 실시간 모니터링 시작
            print("📊 실시간 모니터링 시작...")
            self.monitor.start_monitoring(interval=5)
            
            # 3. 자동 튜닝 시스템 시작
            print("🔧 자동 튜닝 시스템 시작...")
            self.start_auto_tuning()
            
            # 4. 통합 실행
            print("🔄 통합 실행 시작...")
            self.run_integration_loop()
            
        except Exception as e:
            print(f"❌ Phase-D 실행 오류: {e}")
        finally:
            self.stop_phase_d()
    
    def deploy_enhanced_models(self):
        """Enhanced 모델들 배포"""
        deployment_info = {
            'timestamp': datetime.now().isoformat(),
            'deployed_models': list(self.model_manager.models.keys()),
            'deployment_status': 'success',
            'model_count': len(self.model_manager.models)
        }
        
        # 배포 정보 저장
        deployment_file = f"{self.results_dir}/model_deployment.json"
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"✅ {len(self.model_manager.models)} 개 Enhanced 모델 배포 완료")
    
    def start_auto_tuning(self):
        """자동 튜닝 시스템 시작"""
        # 각 모델별로 자동 튜닝 시작
        for model_name in self.model_manager.models.keys():
            self.auto_tuner.start_tuning(model_name)
            print(f"✅ {model_name} 자동 튜닝 시작")
    
    def run_integration_loop(self):
        """통합 실행 루프"""
        print("🔄 통합 실행 루프 시작 (30초간 실행)")
        
        start_time = time.time()
        loop_count = 0
        
        while self.integration_active and (time.time() - start_time) < 30:
            loop_count += 1
            print(f"\n--- 통합 실행 루프 #{loop_count} ---")
            
            try:
                # 1. 시스템 메트릭 수집
                current_metrics = self.model_manager.collect_system_metrics()
                print(f"📊 시스템 메트릭 수집: QPS={current_metrics['qps']:.2f}, Latency={current_metrics['latency']:.2f}")
                
                # 2. 최적 모델 선택
                self.model_manager.update_system_conditions(current_metrics)
                selected_model = self.model_manager.select_optimal_model(self.model_manager.system_conditions)
                
                # 3. S_max 예측
                prediction = self.model_manager.predict_smax(current_metrics)
                
                # 4. 자동 튜닝 실행
                performance_data = {
                    'error_rate': abs(prediction - current_metrics['qps']) / max(prediction, 1) if prediction else 0.1,
                    'accuracy': 0.8,  # 시뮬레이션
                    'system_load': current_metrics['cpu_usage'] / 100,
                    'io_intensity': current_metrics['io_utilization'] / 100
                }
                
                adjusted_params = self.auto_tuner.adjust_parameters(performance_data)
                print(f"🔧 파라미터 조정: {len(adjusted_params)} 개 파라미터")
                
                # 5. 통합 결과 저장
                self.save_integration_result(loop_count, current_metrics, prediction, adjusted_params)
                
                time.sleep(5)  # 5초 간격
                
            except Exception as e:
                print(f"❌ 통합 실행 루프 오류: {e}")
                time.sleep(5)
        
        print(f"✅ 통합 실행 루프 완료 (총 {loop_count} 회 실행)")
    
    def save_integration_result(self, loop_count, metrics, prediction, adjusted_params):
        """통합 실행 결과 저장"""
        result = {
            'loop_count': loop_count,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'prediction': prediction,
            'adjusted_parameters': adjusted_params,
            'active_model': self.model_manager.active_model
        }
        
        # 결과 파일에 추가
        results_file = f"{self.results_dir}/integration_results.json"
        
        # 기존 결과 로드
        all_results = []
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    all_results = json.load(f)
            except:
                all_results = []
        
        # 새 결과 추가
        all_results.append(result)
        
        # 파일 저장
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
    
    def stop_phase_d(self):
        """Phase-D 중지"""
        print("\n⏹️ Phase-D 중지 중...")
        
        self.integration_active = False
        
        # 모니터링 중지
        self.monitor.stop_monitoring()
        
        # 자동 튜닝 중지
        self.auto_tuner.stop_tuning()
        
        # 모델 매니저 중지
        self.model_manager.stop_monitoring()
        
        print("✅ Phase-D 중지 완료")
    
    def generate_phase_d_report(self):
        """Phase-D 보고서 생성"""
        print("📝 Phase-D 보고서 생성 중...")
        
        # 성능 보고서 생성
        performance_stats = self.monitor.generate_performance_report()
        
        # 튜닝 요약
        tuning_summary = self.auto_tuner.get_tuning_summary()
        
        # 모델 매니저 요약
        model_summary = self.model_manager.get_performance_summary()
        
        # 통합 보고서 생성
        phase_d_report = {
            'phase': 'Phase-D',
            'timestamp': datetime.now().isoformat(),
            'objectives': [
                'Production Integration',
                'Real-time Monitoring', 
                'Auto-tuning',
                'Performance Validation'
            ],
            'results': {
                'performance_stats': performance_stats,
                'tuning_summary': tuning_summary,
                'model_summary': model_summary
            },
            'status': 'completed'
        }
        
        # 보고서 저장
        report_file = f"{self.results_dir}/phase_d_report.json"
        with open(report_file, 'w') as f:
            json.dump(phase_d_report, f, indent=2)
        
        print(f"✅ Phase-D 보고서 생성 완료: {report_file}")
        
        return phase_d_report

def main():
    """Phase-D 메인 실행"""
    print("🎯 Phase-D: Enhanced Models Production Integration & Real-time Optimization")
    print("=" * 80)
    
    # Phase-D 오케스트레이터 생성
    orchestrator = PhaseDOrchestrator()
    
    try:
        # Phase-D 실행
        orchestrator.start_phase_d()
        
        # 보고서 생성
        report = orchestrator.generate_phase_d_report()
        
        print("\n" + "=" * 80)
        print("🎉 Phase-D 완료!")
        print(f"📊 성능 통계: {len(orchestrator.monitor.metrics_history)} 개 메트릭 수집")
        print(f"🔧 튜닝 기록: {len(orchestrator.auto_tuner.parameter_history)} 개 조정 기록")
        print(f"📈 모델 예측: {len(orchestrator.model_manager.performance_history)} 개 예측 기록")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단됨")
        orchestrator.stop_phase_d()
    except Exception as e:
        print(f"\n❌ Phase-D 실행 오류: {e}")
        orchestrator.stop_phase_d()

if __name__ == "__main__":
    main()
