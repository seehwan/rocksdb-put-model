#!/usr/bin/env python3
"""
Real-time Monitor for Phase-D
실시간 성능 모니터링 및 알림 시스템
"""

import os
import json
import time
import threading
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

class RealTimeMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_system = AlertSystem()
        self.monitoring_active = False
        self.metrics_history = []
        self.alerts_history = []
        
    def start_monitoring(self, interval=5):
        """실시간 모니터링 시작"""
        print(f"📊 실시간 모니터링 시작 (간격: {interval}초)")
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # 메트릭 수집
                    current_metrics = self.metrics_collector.collect_metrics()
                    
                    # 메트릭 기록
                    self.record_metrics(current_metrics)
                    
                    # 이상 탐지
                    anomalies = self.detect_anomalies(current_metrics)
                    
                    # 알림 생성
                    if anomalies:
                        self.alert_system.generate_alerts(anomalies)
                    
                    # 대시보드 업데이트
                    self.update_dashboard(current_metrics)
                    
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
    
    def record_metrics(self, metrics):
        """메트릭 기록"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        self.metrics_history.append(record)
        
        # 파일에 저장
        self.save_metrics_to_file(record)
    
    def detect_anomalies(self, metrics):
        """이상 탐지"""
        anomalies = []
        
        # QPS 이상 탐지
        if metrics.get('qps', 0) > 5000:  # 임계값
            anomalies.append({
                'type': 'high_qps',
                'value': metrics['qps'],
                'threshold': 5000,
                'severity': 'warning'
            })
        
        # 지연시간 이상 탐지
        if metrics.get('latency', 0) > 5.0:  # 임계값
            anomalies.append({
                'type': 'high_latency',
                'value': metrics['latency'],
                'threshold': 5.0,
                'severity': 'critical'
            })
        
        # CPU 사용률 이상 탐지
        if metrics.get('cpu_usage', 0) > 90:  # 임계값
            anomalies.append({
                'type': 'high_cpu',
                'value': metrics['cpu_usage'],
                'threshold': 90,
                'severity': 'warning'
            })
        
        # 메모리 사용률 이상 탐지
        if metrics.get('memory_usage', 0) > 95:  # 임계값
            anomalies.append({
                'type': 'high_memory',
                'value': metrics['memory_usage'],
                'threshold': 95,
                'severity': 'critical'
            })
        
        return anomalies
    
    def update_dashboard(self, metrics):
        """대시보드 업데이트"""
        # 실시간 대시보드 데이터 생성
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': metrics,
            'system_status': self.get_system_status(metrics),
            'performance_trend': self.get_performance_trend()
        }
        
        # 대시보드 파일 저장
        self.save_dashboard_data(dashboard_data)
    
    def get_system_status(self, metrics):
        """시스템 상태 평가"""
        status = 'healthy'
        
        # 상태 평가 로직
        if metrics.get('latency', 0) > 5.0 or metrics.get('memory_usage', 0) > 95:
            status = 'critical'
        elif metrics.get('cpu_usage', 0) > 90 or metrics.get('qps', 0) > 5000:
            status = 'warning'
        
        return status
    
    def get_performance_trend(self):
        """성능 트렌드 분석"""
        if len(self.metrics_history) < 10:
            return {'trend': 'insufficient_data'}
        
        # 최근 10개 기록 분석
        recent_metrics = self.metrics_history[-10:]
        qps_values = [record['metrics'].get('qps', 0) for record in recent_metrics]
        latency_values = [record['metrics'].get('latency', 0) for record in recent_metrics]
        
        # 트렌드 계산
        qps_trend = np.polyfit(range(len(qps_values)), qps_values, 1)[0]
        latency_trend = np.polyfit(range(len(latency_values)), latency_values, 1)[0]
        
        trend_analysis = {
            'qps_trend': 'increasing' if qps_trend > 0 else 'decreasing',
            'latency_trend': 'increasing' if latency_trend > 0 else 'decreasing',
            'overall_trend': 'improving' if qps_trend > 0 and latency_trend < 0 else 'degrading'
        }
        
        return trend_analysis
    
    def save_metrics_to_file(self, record):
        """메트릭을 파일에 저장"""
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(results_dir, exist_ok=True)
        
        metrics_file = f"{results_dir}/real_time_metrics.json"
        
        # 기존 데이터 로드
        all_metrics = []
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r') as f:
                    all_metrics = json.load(f)
            except:
                all_metrics = []
        
        # 새 기록 추가
        all_metrics.append(record)
        
        # 최근 1000개 기록만 유지
        if len(all_metrics) > 1000:
            all_metrics = all_metrics[-1000:]
        
        # 파일 저장
        with open(metrics_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
    
    def save_dashboard_data(self, dashboard_data):
        """대시보드 데이터 저장"""
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(results_dir, exist_ok=True)
        
        dashboard_file = f"{results_dir}/dashboard_data.json"
        
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
    
    def generate_performance_report(self):
        """성능 보고서 생성"""
        print("📊 성능 보고서 생성 중...")
        
        if not self.metrics_history:
            print("❌ 성능 데이터가 없습니다.")
            return
        
        # 데이터 분석
        df = pd.DataFrame([
            {
                'timestamp': record['timestamp'],
                **record['metrics']
            }
            for record in self.metrics_history
        ])
        
        # 통계 계산
        stats = {
            'total_records': len(df),
            'time_range': {
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            },
            'qps_stats': {
                'mean': df['qps'].mean(),
                'std': df['qps'].std(),
                'min': df['qps'].min(),
                'max': df['qps'].max()
            },
            'latency_stats': {
                'mean': df['latency'].mean(),
                'std': df['latency'].std(),
                'min': df['latency'].min(),
                'max': df['latency'].max()
            }
        }
        
        # 보고서 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        report_file = f"{results_dir}/performance_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ 성능 보고서 생성 완료: {report_file}")
        
        return stats

class MetricsCollector:
    def __init__(self):
        self.collection_count = 0
    
    def collect_metrics(self):
        """메트릭 수집"""
        self.collection_count += 1
        
        # 실제 구현에서는 RocksDB 통계, 시스템 메트릭 등을 수집
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'qps': np.random.normal(1000, 200),  # 시뮬레이션
            'latency': np.random.normal(1.0, 0.2),
            'cpu_usage': np.random.normal(50, 15),
            'memory_usage': np.random.normal(60, 10),
            'io_utilization': np.random.normal(40, 10),
            'compaction_activity': np.random.normal(30, 8),
            'collection_count': self.collection_count
        }
        
        return metrics

class AlertSystem:
    def __init__(self):
        self.alert_count = 0
    
    def generate_alerts(self, anomalies):
        """알림 생성"""
        for anomaly in anomalies:
            alert = {
                'timestamp': datetime.now().isoformat(),
                'type': anomaly['type'],
                'severity': anomaly['severity'],
                'value': anomaly['value'],
                'threshold': anomaly['threshold'],
                'message': self.generate_alert_message(anomaly)
            }
            
            self.alert_count += 1
            print(f"🚨 알림 #{self.alert_count}: {alert['message']}")
            
            # 알림 기록 저장
            self.save_alert(alert)
    
    def generate_alert_message(self, anomaly):
        """알림 메시지 생성"""
        messages = {
            'high_qps': f"높은 QPS 감지: {anomaly['value']:.2f} (임계값: {anomaly['threshold']})",
            'high_latency': f"높은 지연시간 감지: {anomaly['value']:.2f}초 (임계값: {anomaly['threshold']}초)",
            'high_cpu': f"높은 CPU 사용률 감지: {anomaly['value']:.1f}% (임계값: {anomaly['threshold']}%)",
            'high_memory': f"높은 메모리 사용률 감지: {anomaly['value']:.1f}% (임계값: {anomaly['threshold']}%)"
        }
        
        return messages.get(anomaly['type'], f"알 수 없는 이상: {anomaly['type']}")
    
    def save_alert(self, alert):
        """알림 저장"""
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-d/results'
        os.makedirs(results_dir, exist_ok=True)
        
        alerts_file = f"{results_dir}/alerts.json"
        
        # 기존 알림 로드
        alerts = []
        if os.path.exists(alerts_file):
            try:
                with open(alerts_file, 'r') as f:
                    alerts = json.load(f)
            except:
                alerts = []
        
        # 새 알림 추가
        alerts.append(alert)
        
        # 파일 저장
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)

if __name__ == "__main__":
    # Real-time Monitor 테스트
    monitor = RealTimeMonitor()
    
    # 모니터링 시작
    monitor.start_monitoring(interval=3)
    
    # 15초 동안 모니터링
    time.sleep(15)
    
    # 모니터링 중지
    monitor.stop_monitoring()
    
    # 성능 보고서 생성
    stats = monitor.generate_performance_report()
    print(f"📊 성능 통계: {json.dumps(stats, indent=2)}")
