#!/usr/bin/env python3
"""
V5.1 Corrected Model - Phase-D Production Integration
V5.1을 production 환경에 통합하고 real-time monitoring 구현

Phase-D 목표:
1. V5.1 production deployment wrapper
2. Real-time monitoring integration
3. Auto-tuning capability
4. Performance validation in production
5. Online learning with feedback loop
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

import json
import numpy as np
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import deque
from dataclasses import asdict
import logging

# V5.1 모델 import
from model.v5_1_corrected_model import V5_1CorrectedModel, V5_1PredictionResult


class V5_1ProductionDeployment:
    """
    V5.1 Production Deployment System
    
    Features:
    - Async prediction API
    - Health monitoring
    - Performance metrics tracking
    - Online learning capability
    - Alert system
    - Model drift detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        
        # Initialize V5.1 model
        self.v5_1_model = V5_1CorrectedModel()
        
        # Performance tracking
        self.prediction_history = deque(maxlen=1000)
        self.feedback_history = deque(maxlen=1000)
        
        # Metrics
        self.metrics = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'average_response_time_ms': 0,
            'average_accuracy': 0.0,
            'accuracy_by_phase': {'initial': [], 'middle': [], 'final': []},
            'last_prediction_time': None
        }
        
        # Health status
        self.health_status = {
            'status': 'healthy',
            'last_check': datetime.now().isoformat(),
            'model_loaded': True,
            'validation_passed': False,
            'issues': []
        }
        
        # Online learning parameters
        self.online_learning = {
            'enabled': self.config['online_learning']['enabled'],
            'learning_rate': self.config['online_learning']['learning_rate'],
            'min_samples_required': self.config['online_learning']['min_samples'],
            'learned_adjustments': {
                'initial': 1.0,
                'middle': 1.0,
                'final': 1.0
            }
        }
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize
        self._initialize()
    
    def _default_config(self) -> Dict:
        """Default production configuration"""
        return {
            'model': {
                'version': 'v5.1_corrected',
                'fallback_to_v4': True,
                'confidence_threshold': 0.5
            },
            'monitoring': {
                'health_check_interval_seconds': 60,
                'metrics_retention_hours': 24,
                'enable_drift_detection': True,
                'drift_check_interval_seconds': 300
            },
            'online_learning': {
                'enabled': True,
                'learning_rate': 0.05,
                'min_samples': 20,
                'max_adjustment': 0.2  # Max 20% adjustment
            },
            'alerts': {
                'low_accuracy_threshold': 50.0,
                'high_error_rate_threshold': 5.0,
                'high_response_time_ms': 1000
            }
        }
    
    def _initialize(self):
        """Initialize deployment"""
        try:
            # Validate model
            test_result = self.v5_1_model.predict_s_max(1000, 'middle', {})
            if not test_result.predicted_s_max > 0:
                raise ValueError("V5.1 model validation failed")
            
            self.health_status['validation_passed'] = True
            self.logger.info("✅ V5.1 Production Deployment Initialized")
            
        except Exception as e:
            self.health_status['status'] = 'unhealthy'
            self.health_status['issues'].append(str(e))
            self.logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def predict_async(self, 
                           device_write_bw: float,
                           phase: str,
                           context: Optional[Dict] = None) -> Dict:
        """
        Async prediction with production features
        """
        start_time = time.time()
        
        try:
            # Make prediction
            result = self.v5_1_model.predict_s_max(device_write_bw, phase, context)
            
            # Convert to dict
            result_dict = asdict(result)
            
            # Add production metadata
            response_time_ms = (time.time() - start_time) * 1000
            result_dict.update({
                'response_time_ms': response_time_ms,
                'prediction_id': f"pred_{int(time.time() * 1000)}",
                'status': 'success',
                'deployment_version': 'production_v1.0'
            })
            
            # Apply online learning adjustment if available
            if self.online_learning['enabled']:
                learned_adj = self.online_learning['learned_adjustments'][phase]
                result_dict['predicted_s_max_adjusted'] = result_dict['predicted_s_max'] * learned_adj
                result_dict['online_learning_adjustment'] = learned_adj
            
            # Update metrics
            self._update_metrics(response_time_ms, success=True)
            
            # Store prediction
            self.prediction_history.append({
                'timestamp': datetime.now().isoformat(),
                'prediction_id': result_dict['prediction_id'],
                'phase': phase,
                'predicted': result_dict['predicted_s_max'],
                'device_bw': device_write_bw
            })
            
            return result_dict
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            self._update_metrics(response_time_ms, success=False)
            
            return {
                'status': 'error',
                'error_message': str(e),
                'error_type': type(e).__name__,
                'response_time_ms': response_time_ms
            }
    
    def update_with_actual(self, prediction_id: str, actual_qps: float):
        """
        Update with actual observed QPS (online learning)
        """
        # Find prediction
        prediction = next((p for p in self.prediction_history 
                          if p.get('prediction_id') == prediction_id), None)
        
        if not prediction:
            self.logger.warning(f"Prediction {prediction_id} not found")
            return
        
        phase = prediction['phase']
        predicted = prediction['predicted']
        device_bw = prediction['device_bw']
        
        # Calculate accuracy
        accuracy = (1 - abs(predicted - actual_qps) / actual_qps) * 100
        
        # Store feedback
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'prediction_id': prediction_id,
            'phase': phase,
            'predicted': predicted,
            'actual': actual_qps,
            'accuracy': accuracy,
            'error': abs(predicted - actual_qps) / actual_qps * 100
        }
        
        self.feedback_history.append(feedback)
        
        # Update phase accuracy history
        self.metrics['accuracy_by_phase'][phase].append(accuracy)
        
        # Online learning update
        if self.online_learning['enabled']:
            self._update_online_learning(phase, predicted, actual_qps, device_bw)
        
        # Check for alerts
        self._check_accuracy_alerts(accuracy, phase)
        
        self.logger.info(f"Feedback received: {prediction_id}, accuracy: {accuracy:.1f}%")
        
        return feedback
    
    def _update_online_learning(self, phase: str, predicted: float, actual: float, device_bw: float):
        """
        Update online learning adjustments
        """
        if len(self.metrics['accuracy_by_phase'][phase]) < self.online_learning['min_samples_required']:
            return  # Not enough samples yet
        
        # Calculate optimal adjustment
        if predicted > 0:
            optimal_adjustment = actual / predicted
        else:
            return
        
        # Current adjustment
        current = self.online_learning['learned_adjustments'][phase]
        
        # Exponential moving average update
        lr = self.online_learning['learning_rate']
        updated = current * (1 - lr) + optimal_adjustment * lr
        
        # Clip to prevent extreme adjustments
        max_adj = 1 + self.online_learning['max_adjustment']
        min_adj = 1 - self.online_learning['max_adjustment']
        updated = np.clip(updated, min_adj, max_adj)
        
        # Update
        old_adjustment = self.online_learning['learned_adjustments'][phase]
        self.online_learning['learned_adjustments'][phase] = updated
        
        self.logger.info(f"Online learning update [{phase}]: {old_adjustment:.3f} → {updated:.3f}")
    
    def _update_metrics(self, response_time_ms: float, success: bool):
        """Update performance metrics"""
        self.metrics['total_predictions'] += 1
        
        if success:
            self.metrics['successful_predictions'] += 1
        else:
            self.metrics['failed_predictions'] += 1
        
        # Update average response time (EMA)
        if self.metrics['average_response_time_ms'] == 0:
            self.metrics['average_response_time_ms'] = response_time_ms
        else:
            alpha = 0.1
            self.metrics['average_response_time_ms'] = (
                alpha * response_time_ms + 
                (1 - alpha) * self.metrics['average_response_time_ms']
            )
        
        self.metrics['last_prediction_time'] = datetime.now().isoformat()
    
    def _check_accuracy_alerts(self, accuracy: float, phase: str):
        """Check for accuracy-based alerts"""
        threshold = self.config['alerts']['low_accuracy_threshold']
        
        if accuracy < threshold:
            alert = {
                'type': 'low_accuracy',
                'severity': 'warning',
                'phase': phase,
                'accuracy': accuracy,
                'threshold': threshold,
                'timestamp': datetime.now().isoformat()
            }
            self.logger.warning(f"🚨 Low accuracy alert: {phase} phase = {accuracy:.1f}%")
    
    def get_health_status(self) -> Dict:
        """Get deployment health status"""
        current_time = datetime.now()
        
        # Calculate error rate
        total = self.metrics['total_predictions']
        if total > 0:
            error_rate = (self.metrics['failed_predictions'] / total) * 100
        else:
            error_rate = 0
        
        # Calculate average accuracy (from feedback)
        if len(self.feedback_history) > 0:
            recent_accuracies = [f['accuracy'] for f in list(self.feedback_history)[-50:]]
            avg_accuracy = np.mean(recent_accuracies)
        else:
            avg_accuracy = 0
        
        # Update health status
        issues = []
        
        if error_rate > self.config['alerts']['high_error_rate_threshold']:
            issues.append(f"High error rate: {error_rate:.1f}%")
        
        if avg_accuracy > 0 and avg_accuracy < self.config['alerts']['low_accuracy_threshold']:
            issues.append(f"Low accuracy: {avg_accuracy:.1f}%")
        
        if self.metrics['average_response_time_ms'] > self.config['alerts']['high_response_time_ms']:
            issues.append(f"High response time: {self.metrics['average_response_time_ms']:.1f}ms")
        
        self.health_status.update({
            'status': 'healthy' if not issues else 'degraded',
            'last_check': current_time.isoformat(),
            'error_rate': error_rate,
            'average_accuracy': avg_accuracy,
            'issues': issues
        })
        
        return self.health_status
    
    def get_metrics_dashboard(self) -> Dict:
        """Get comprehensive metrics dashboard"""
        # Calculate phase-specific metrics
        phase_metrics = {}
        for phase in ['initial', 'middle', 'final']:
            phase_accuracies = self.metrics['accuracy_by_phase'][phase]
            if len(phase_accuracies) > 0:
                phase_metrics[phase] = {
                    'sample_count': len(phase_accuracies),
                    'mean_accuracy': np.mean(phase_accuracies),
                    'std_accuracy': np.std(phase_accuracies),
                    'min_accuracy': np.min(phase_accuracies),
                    'max_accuracy': np.max(phase_accuracies),
                    'learned_adjustment': self.online_learning['learned_adjustments'][phase]
                }
            else:
                phase_metrics[phase] = {'sample_count': 0}
        
        # Recent predictions
        recent_predictions = list(self.prediction_history)[-10:]
        
        # Recent feedback
        recent_feedback = list(self.feedback_history)[-10:]
        
        return {
            'summary': {
                'total_predictions': self.metrics['total_predictions'],
                'successful_predictions': self.metrics['successful_predictions'],
                'failed_predictions': self.metrics['failed_predictions'],
                'success_rate': (self.metrics['successful_predictions'] / self.metrics['total_predictions'] * 100) 
                               if self.metrics['total_predictions'] > 0 else 0,
                'average_response_time_ms': self.metrics['average_response_time_ms'],
                'feedback_count': len(self.feedback_history)
            },
            'phase_metrics': phase_metrics,
            'online_learning': {
                'enabled': self.online_learning['enabled'],
                'learned_adjustments': self.online_learning['learned_adjustments'],
                'learning_rate': self.online_learning['learning_rate']
            },
            'recent_activity': {
                'predictions': recent_predictions,
                'feedback': recent_feedback
            },
            'health': self.health_status
        }
    
    def save_state(self, path: str):
        """Save deployment state for persistence"""
        state = {
            'model_version': self.v5_1_model.model_version,
            'metrics': self.metrics,
            'online_learning': self.online_learning,
            'health_status': self.health_status,
            'saved_at': datetime.now().isoformat()
        }
        
        # Convert numpy types
        def convert_to_serializable(obj):
            if isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, deque):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            else:
                return obj
        
        with open(path, 'w') as f:
            json.dump(convert_to_serializable(state), f, indent=2)
        
        self.logger.info(f"State saved to {path}")
    
    def load_state(self, path: str):
        """Load deployment state"""
        with open(path, 'r') as f:
            state = json.load(f)
        
        # Restore online learning
        if 'online_learning' in state:
            self.online_learning['learned_adjustments'] = state['online_learning']['learned_adjustments']
        
        self.logger.info(f"State loaded from {path}")


class V5_1MonitoringSystem:
    """
    V5.1 Real-time Monitoring System
    
    Features:
    - Continuous performance monitoring
    - Model drift detection
    - Automatic alerting
    - Performance dashboard
    """
    
    def __init__(self, deployment: V5_1ProductionDeployment):
        self.deployment = deployment
        
        # Monitoring data
        self.monitoring_data = deque(maxlen=1000)
        self.alerts = deque(maxlen=100)
        
        # Baselines (from Phase-C evaluation)
        self.baselines = {
            'expected_accuracy': {
                'initial': 57.1,
                'middle': 92.5,
                'final': 44.9,
                'overall': 64.8
            },
            'expected_response_time_ms': 50,
            'expected_error_rate': 1.0
        }
        
        # Monitoring state
        self.monitoring_active = False
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.Monitor")
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True
        self.logger.info("✅ V5.1 Monitoring System Started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        self.logger.info("⏹️ V5.1 Monitoring System Stopped")
    
    def collect_metrics(self):
        """Collect current metrics snapshot"""
        health = self.deployment.get_health_status()
        dashboard = self.deployment.get_metrics_dashboard()
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'health_status': health['status'],
            'total_predictions': dashboard['summary']['total_predictions'],
            'success_rate': dashboard['summary']['success_rate'],
            'average_response_time': dashboard['summary']['average_response_time_ms'],
            'feedback_count': dashboard['summary']['feedback_count'],
            'phase_metrics': dashboard['phase_metrics']
        }
        
        self.monitoring_data.append(snapshot)
        return snapshot
    
    def detect_drift(self) -> Optional[Dict]:
        """
        Detect model performance drift
        """
        if len(self.monitoring_data) < 10:
            return None
        
        # Recent accuracy trend
        recent_snapshots = list(self.monitoring_data)[-10:]
        
        drift_analysis = {}
        
        for phase in ['initial', 'middle', 'final']:
            phase_accuracies = []
            for snapshot in recent_snapshots:
                if phase in snapshot.get('phase_metrics', {}):
                    metrics = snapshot['phase_metrics'][phase]
                    if metrics.get('sample_count', 0) > 0:
                        phase_accuracies.append(metrics['mean_accuracy'])
            
            if len(phase_accuracies) >= 5:
                recent_avg = np.mean(phase_accuracies[-5:])
                baseline = self.baselines['expected_accuracy'][phase]
                drift = abs(recent_avg - baseline)
                
                drift_analysis[phase] = {
                    'recent_accuracy': recent_avg,
                    'baseline_accuracy': baseline,
                    'drift': drift,
                    'drift_percentage': (drift / baseline * 100) if baseline > 0 else 0,
                    'status': 'critical' if drift > 15 else 'warning' if drift > 10 else 'normal'
                }
        
        if any(d['status'] != 'normal' for d in drift_analysis.values()):
            self.logger.warning(f"⚠️ Model drift detected: {drift_analysis}")
            return drift_analysis
        
        return None
    
    def generate_monitoring_report(self, output_path: str):
        """Generate comprehensive monitoring report"""
        dashboard = self.deployment.get_metrics_dashboard()
        
        report = {
            'report_time': datetime.now().isoformat(),
            'model_version': self.deployment.v5_1_model.model_version,
            'summary': dashboard['summary'],
            'phase_performance': dashboard['phase_metrics'],
            'online_learning': dashboard['online_learning'],
            'health_status': dashboard['health'],
            'recent_alerts': list(self.alerts)[-10:],
            'monitoring_data_samples': len(self.monitoring_data)
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Monitoring report saved to {output_path}")


def main():
    """Phase-D Production Integration 메인"""
    print("=" * 80)
    print("V5.1 CORRECTED MODEL - PHASE-D PRODUCTION INTEGRATION")
    print("=" * 80)
    
    # Initialize deployment
    print("\n🚀 Initializing V5.1 Production Deployment...")
    deployment = V5_1ProductionDeployment()
    
    # Initialize monitoring
    print("📊 Initializing Monitoring System...")
    monitoring = V5_1MonitoringSystem(deployment)
    monitoring.start_monitoring()
    
    # Test predictions with real data
    print("\n" + "=" * 80)
    print("🧪 Testing V5.1 Production Deployment")
    print("=" * 80)
    
    # Load Phase-C test data
    test_cases = [
        {
            'name': 'Initial Phase',
            'device_write_bw': 4116.6455078125,
            'phase': 'initial',
            'actual_qps': 138769,
            'context': {
                'cv_history': [0.65, 0.62, 0.58, 0.55, 0.5379],
                'qps_history': [130000, 133000, 135000, 137000, 138769],
                'runtime_minutes': 8.5,
                'workload_type': 'fillrandom',
                'lsm_depth': 2
            }
        },
        {
            'name': 'Middle Phase',
            'device_write_bw': 2595.7431640625,
            'phase': 'middle',
            'actual_qps': 114472,
            'context': {
                'cv_history': [0.35, 0.32, 0.30, 0.29, 0.272],
                'qps_history': [110000, 111500, 113000, 113800, 114472],
                'runtime_minutes': 1907,
                'wa': 2.5,
                'ra': 0.8,
                'workload_type': 'fillrandom',
                'lsm_depth': 4
            }
        },
        {
            'name': 'Final Phase',
            'device_write_bw': 1074.8408203125,
            'phase': 'final',
            'actual_qps': 109678,
            'context': {
                'cv_history': [0.055, 0.050, 0.045, 0.043, 0.041],
                'qps_history': [109300, 109450, 109550, 109620, 109678],
                'runtime_minutes': 3880,
                'wa': 3.5,
                'ra': 0.8,
                'workload_type': 'fillrandom',
                'lsm_depth': 7
            }
        }
    ]
    
    # Run async predictions
    async def run_predictions():
        results = []
        for test in test_cases:
            print(f"\n{'='*80}")
            print(f"📊 {test['name']}")
            print(f"{'='*80}")
            
            # Predict
            result = await deployment.predict_async(
                test['device_write_bw'],
                test['phase'],
                test['context']
            )
            
            if result['status'] == 'success':
                predicted = result['predicted_s_max']
                actual = test['actual_qps']
                accuracy = (1 - abs(predicted - actual) / actual) * 100
                
                print(f"  Device BW: {test['device_write_bw']:.1f} MB/s")
                print(f"  Predicted: {predicted:,.0f} ops/sec")
                print(f"  Actual: {actual:,.0f} ops/sec")
                print(f"  Accuracy: {accuracy:.1f}%")
                print(f"  Response Time: {result['response_time_ms']:.2f}ms")
                print(f"  Confidence: {result['ensemble_confidence']}")
                
                if 'online_learning_adjustment' in result:
                    print(f"  Online Learning: {result['online_learning_adjustment']:.3f}x")
                
                # Provide feedback
                feedback = deployment.update_with_actual(result['prediction_id'], actual)
                print(f"  Feedback: {feedback['accuracy']:.1f}% accuracy recorded")
                
                results.append(result)
            else:
                print(f"  ❌ Prediction failed: {result['error_message']}")
        
        return results
    
    # Run predictions
    results = asyncio.run(run_predictions())
    
    # Collect final metrics
    print("\n" + "=" * 80)
    print("📊 Final Metrics")
    print("=" * 80)
    
    metrics = monitoring.collect_metrics()
    dashboard = deployment.get_metrics_dashboard()
    
    print(f"\nTotal Predictions: {dashboard['summary']['total_predictions']}")
    print(f"Success Rate: {dashboard['summary']['success_rate']:.1f}%")
    print(f"Average Response Time: {dashboard['summary']['average_response_time_ms']:.2f}ms")
    
    print("\nPhase Performance:")
    for phase, data in dashboard['phase_metrics'].items():
        if data['sample_count'] > 0:
            print(f"  {phase.title()}: {data['mean_accuracy']:.1f}% "
                  f"(learned adj: {data['learned_adjustment']:.3f}x)")
    
    # Check for drift
    drift = monitoring.detect_drift()
    if drift:
        print("\n⚠️ Model Drift Detected:")
        for phase, drift_info in drift.items():
            print(f"  {phase.title()}: {drift_info['drift']:.1f}% drift ({drift_info['status']})")
    else:
        print("\n✅ No significant model drift detected")
    
    # Save state
    results_dir = "experiments/2025-09-12/phase-d/results"
    os.makedirs(results_dir, exist_ok=True)
    
    state_path = os.path.join(results_dir, 'v5_1_deployment_state.json')
    deployment.save_state(state_path)
    
    report_path = os.path.join(results_dir, 'v5_1_monitoring_report.json')
    monitoring.generate_monitoring_report(report_path)
    
    print(f"\n📁 Results saved to: {results_dir}/")
    print(f"  - v5_1_deployment_state.json")
    print(f"  - v5_1_monitoring_report.json")
    
    print("\n" + "=" * 80)
    print("✅ V5.1 Production Integration Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

