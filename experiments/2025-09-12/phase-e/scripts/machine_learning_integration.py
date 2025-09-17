#!/usr/bin/env python3
"""
Machine Learning Integration for Phase-E
머신러닝 기반 RocksDB 성능 예측 모델 개발
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.svm import SVR
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns

class MachineLearningIntegration:
    def __init__(self):
        self.ml_models = {}
        self.feature_importance = {}
        self.model_performance = {}
        self.scaler = StandardScaler()
        
        # ML 모델들 정의
        self.available_models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'linear_regression': LinearRegression(),
            'ridge_regression': Ridge(alpha=1.0),
            'lasso_regression': Lasso(alpha=1.0),
            'svr': SVR(kernel='rbf'),
            'neural_network': MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42, max_iter=1000)
        }
    
    def extract_rocksdb_features(self, rocksdb_data):
        """RocksDB 성능 특성 추출"""
        print("🔍 RocksDB 성능 특성 추출 중...")
        
        features = {}
        
        # 기본 성능 메트릭
        if 'qps' in rocksdb_data:
            features['qps'] = rocksdb_data['qps']
        if 'latency' in rocksdb_data:
            features['latency'] = rocksdb_data['latency']
        if 'throughput' in rocksdb_data:
            features['throughput'] = rocksdb_data['throughput']
        
        # I/O 관련 특성
        if 'io_utilization' in rocksdb_data:
            features['io_utilization'] = rocksdb_data['io_utilization']
        if 'read_bandwidth' in rocksdb_data:
            features['read_bandwidth'] = rocksdb_data['read_bandwidth']
        if 'write_bandwidth' in rocksdb_data:
            features['write_bandwidth'] = rocksdb_data['write_bandwidth']
        
        # 컴팩션 관련 특성
        if 'compaction_activity' in rocksdb_data:
            features['compaction_activity'] = rocksdb_data['compaction_activity']
        if 'compaction_ratio' in rocksdb_data:
            features['compaction_ratio'] = rocksdb_data['compaction_ratio']
        
        # 시스템 리소스 특성
        if 'cpu_usage' in rocksdb_data:
            features['cpu_usage'] = rocksdb_data['cpu_usage']
        if 'memory_usage' in rocksdb_data:
            features['memory_usage'] = rocksdb_data['memory_usage']
        
        # 파생 특성 생성
        features = self._generate_derived_features(features)
        
        print(f"✅ 특성 추출 완료: {len(features)} 개 특성")
        
        return features
    
    def _generate_derived_features(self, features):
        """파생 특성 생성"""
        # I/O 효율성
        if 'read_bandwidth' in features and 'write_bandwidth' in features:
            features['io_efficiency'] = features['read_bandwidth'] / (features['write_bandwidth'] + 1e-6)
        
        # 시스템 부하
        if 'cpu_usage' in features and 'memory_usage' in features:
            features['system_load'] = (features['cpu_usage'] + features['memory_usage']) / 2
        
        # 성능 대비 리소스 사용률
        if 'qps' in features and 'system_load' in features:
            features['performance_efficiency'] = features['qps'] / (features['system_load'] + 1e-6)
        
        # 컴팩션 압박
        if 'compaction_activity' in features and 'io_utilization' in features:
            features['compaction_pressure'] = features['compaction_activity'] * features['io_utilization']
        
        return features
    
    def prepare_training_data(self, features_list, targets):
        """훈련 데이터 준비"""
        print("📊 훈련 데이터 준비 중...")
        
        # 특성 매트릭스 생성
        feature_names = list(features_list[0].keys())
        X = np.array([[features[feature] for feature in feature_names] for features in features_list])
        y = np.array(targets)
        
        # 데이터 정규화
        X_scaled = self.scaler.fit_transform(X)
        
        # 훈련/테스트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        print(f"✅ 훈련 데이터 준비 완료:")
        print(f"   - 훈련 샘플: {X_train.shape[0]} 개")
        print(f"   - 테스트 샘플: {X_test.shape[0]} 개")
        print(f"   - 특성 수: {X_train.shape[1]} 개")
        
        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'feature_names': feature_names
        }
    
    def train_ml_models(self, training_data):
        """ML 모델 훈련"""
        print("🤖 ML 모델 훈련 중...")
        
        X_train = training_data['X_train']
        y_train = training_data['y_train']
        X_test = training_data['X_test']
        y_test = training_data['y_test']
        
        for model_name, model in self.available_models.items():
            print(f"   📈 {model_name} 모델 훈련 중...")
            
            try:
                # 모델 훈련
                model.fit(X_train, y_train)
                
                # 예측
                y_pred = model.predict(X_test)
                
                # 성능 평가
                performance = self._evaluate_model_performance(y_test, y_pred)
                
                # 특성 중요도 (가능한 경우)
                feature_importance = self._get_feature_importance(model, training_data['feature_names'])
                
                self.ml_models[model_name] = {
                    'model': model,
                    'performance': performance,
                    'feature_importance': feature_importance
                }
                
                print(f"   ✅ {model_name} 완료: R² = {performance['r2_score']:.4f}")
                
            except Exception as e:
                print(f"   ❌ {model_name} 실패: {e}")
                self.ml_models[model_name] = {
                    'model': None,
                    'performance': None,
                    'error': str(e)
                }
        
        print(f"✅ ML 모델 훈련 완료: {len(self.ml_models)} 개 모델")
        
        return self.ml_models
    
    def _evaluate_model_performance(self, y_true, y_pred):
        """모델 성능 평가"""
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        
        # 상대 오류율
        relative_errors = np.abs((y_true - y_pred) / (y_true + 1e-6)) * 100
        mean_relative_error = np.mean(relative_errors)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2_score': r2,
            'mae': mae,
            'mean_relative_error': mean_relative_error,
            'accuracy_level': self._classify_ml_accuracy(r2, mean_relative_error)
        }
    
    def _classify_ml_accuracy(self, r2, mean_relative_error):
        """ML 모델 정확도 분류"""
        if r2 > 0.95 and mean_relative_error < 5:
            return "Excellent"
        elif r2 > 0.9 and mean_relative_error < 10:
            return "Very Good"
        elif r2 > 0.8 and mean_relative_error < 20:
            return "Good"
        elif r2 > 0.7 and mean_relative_error < 30:
            return "Fair"
        else:
            return "Poor"
    
    def _get_feature_importance(self, model, feature_names):
        """특성 중요도 추출"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
                return dict(zip(feature_names, importance))
            elif hasattr(model, 'coef_'):
                # 선형 모델의 경우 계수 절댓값 사용
                importance = np.abs(model.coef_)
                return dict(zip(feature_names, importance))
            else:
                return None
        except:
            return None
    
    def select_best_model(self):
        """최적 모델 선택"""
        print("🏆 최적 모델 선택 중...")
        
        best_model = None
        best_score = -float('inf')
        
        for model_name, model_info in self.ml_models.items():
            if model_info['performance'] is not None:
                score = model_info['performance']['r2_score']
                if score > best_score:
                    best_score = score
                    best_model = model_name
        
        if best_model:
            print(f"✅ 최적 모델 선택: {best_model} (R² = {best_score:.4f})")
            return best_model, self.ml_models[best_model]
        else:
            print("❌ 유효한 모델이 없습니다.")
            return None, None
    
    def cross_validate_models(self, training_data):
        """모델 교차 검증"""
        print("🔄 모델 교차 검증 중...")
        
        X = training_data['X_train']
        y = training_data['y_train']
        
        cv_results = {}
        
        for model_name, model in self.available_models.items():
            print(f"   📊 {model_name} 교차 검증 중...")
            
            try:
                # 5-fold 교차 검증
                scores = cross_val_score(model, X, y, cv=5, scoring='r2')
                
                cv_results[model_name] = {
                    'mean_score': np.mean(scores),
                    'std_score': np.std(scores),
                    'scores': scores.tolist()
                }
                
                print(f"   ✅ {model_name} 완료: 평균 R² = {np.mean(scores):.4f} (±{np.std(scores):.4f})")
                
            except Exception as e:
                print(f"   ❌ {model_name} 실패: {e}")
                cv_results[model_name] = {'error': str(e)}
        
        return cv_results
    
    def generate_ml_report(self):
        """ML 모델 보고서 생성"""
        print("📝 ML 모델 보고서 생성 중...")
        
        # 모델 성능 비교
        performance_comparison = {}
        for model_name, model_info in self.ml_models.items():
            if model_info['performance'] is not None:
                performance_comparison[model_name] = model_info['performance']
        
        # 특성 중요도 분석
        feature_importance_analysis = {}
        for model_name, model_info in self.ml_models.items():
            if model_info['feature_importance'] is not None:
                feature_importance_analysis[model_name] = model_info['feature_importance']
        
        # 최적 모델 선택
        best_model_name, best_model_info = self.select_best_model()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'model_performance': performance_comparison,
            'feature_importance': feature_importance_analysis,
            'best_model': {
                'name': best_model_name,
                'performance': best_model_info['performance'] if best_model_info else None
            },
            'summary': self._generate_ml_summary(performance_comparison)
        }
        
        # 보고서 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-e/results'
        os.makedirs(results_dir, exist_ok=True)
        
        report_file = f"{results_dir}/machine_learning_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ ML 모델 보고서 생성 완료: {report_file}")
        
        return report
    
    def _generate_ml_summary(self, performance_comparison):
        """ML 요약 생성"""
        if not performance_comparison:
            return {'status': 'no_models'}
        
        # 최고 성능 모델 찾기
        best_model = max(performance_comparison.items(), key=lambda x: x[1]['r2_score'])
        
        # 평균 성능 계산
        avg_r2 = np.mean([perf['r2_score'] for perf in performance_comparison.values()])
        avg_rmse = np.mean([perf['rmse'] for perf in performance_comparison.values()])
        
        return {
            'total_models': len(performance_comparison),
            'best_model': best_model[0],
            'best_r2_score': best_model[1]['r2_score'],
            'average_r2_score': avg_r2,
            'average_rmse': avg_rmse,
            'overall_performance': 'Excellent' if avg_r2 > 0.9 else 'Good' if avg_r2 > 0.8 else 'Fair'
        }
    
    def create_ml_visualizations(self, training_data):
        """ML 시각화 생성"""
        print("📊 ML 시각화 생성 중...")
        
        # 모델 성능 비교 차트
        self._create_performance_comparison_chart()
        
        # 특성 중요도 차트
        self._create_feature_importance_chart()
        
        # 예측 vs 실제 값 산점도
        self._create_prediction_scatter_plot(training_data)
        
        print("✅ ML 시각화 생성 완료")
    
    def _create_performance_comparison_chart(self):
        """성능 비교 차트 생성"""
        if not self.ml_models:
            return
        
        model_names = []
        r2_scores = []
        
        for model_name, model_info in self.ml_models.items():
            if model_info['performance'] is not None:
                model_names.append(model_name)
                r2_scores.append(model_info['performance']['r2_score'])
        
        if not model_names:
            return
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(model_names, r2_scores, color='skyblue', alpha=0.7)
        plt.title('ML Models Performance Comparison (R² Score)')
        plt.xlabel('Model')
        plt.ylabel('R² Score')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 값 표시
        for bar, score in zip(bars, r2_scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-e/results'
        plt.savefig(f"{results_dir}/ml_models_performance_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_feature_importance_chart(self):
        """특성 중요도 차트 생성"""
        if not self.ml_models:
            return
        
        # 특성 중요도가 있는 모델 찾기
        importance_data = {}
        for model_name, model_info in self.ml_models.items():
            if model_info['feature_importance'] is not None:
                importance_data[model_name] = model_info['feature_importance']
        
        if not importance_data:
            return
        
        # 첫 번째 모델의 특성 중요도 사용
        first_model = list(importance_data.keys())[0]
        features = list(importance_data[first_model].keys())
        importance = list(importance_data[first_model].values())
        
        plt.figure(figsize=(10, 6))
        bars = plt.barh(features, importance, color='lightcoral', alpha=0.7)
        plt.title(f'Feature Importance - {first_model.title()}')
        plt.xlabel('Importance')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-e/results'
        plt.savefig(f"{results_dir}/feature_importance_chart.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_prediction_scatter_plot(self, training_data):
        """예측 vs 실제 값 산점도 생성"""
        if not self.ml_models:
            return
        
        # 최적 모델 선택
        best_model_name, best_model_info = self.select_best_model()
        if not best_model_name:
            return
        
        model = best_model_info['model']
        X_test = training_data['X_test']
        y_test = training_data['y_test']
        
        # 예측
        y_pred = model.predict(X_test)
        
        plt.figure(figsize=(8, 8))
        plt.scatter(y_test, y_pred, alpha=0.6, color='blue')
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        plt.xlabel('Actual Values')
        plt.ylabel('Predicted Values')
        plt.title(f'Prediction vs Actual - {best_model_name.title()}')
        plt.grid(True, alpha=0.3)
        
        # R² 점수 표시
        r2 = best_model_info['performance']['r2_score']
        plt.text(0.05, 0.95, f'R² = {r2:.3f}', transform=plt.gca().transAxes,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        plt.tight_layout()
        
        # 저장
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-e/results'
        plt.savefig(f"{results_dir}/prediction_scatter_plot.png", dpi=300, bbox_inches='tight')
        plt.close()

def main():
    """Machine Learning Integration 테스트"""
    print("🤖 Machine Learning Integration 시작")
    print("=" * 60)
    
    # ML 통합 시스템 생성
    ml_system = MachineLearningIntegration()
    
    # 테스트 데이터 생성
    n_samples = 1000
    n_features = 10
    
    # 특성 데이터 생성
    features_list = []
    targets = []
    
    for _ in range(n_samples):
        features = {
            'qps': np.random.uniform(100, 1000),
            'latency': np.random.uniform(0.5, 5.0),
            'io_utilization': np.random.uniform(20, 80),
            'cpu_usage': np.random.uniform(30, 90),
            'memory_usage': np.random.uniform(40, 95),
            'compaction_activity': np.random.uniform(10, 60),
            'read_bandwidth': np.random.uniform(50, 200),
            'write_bandwidth': np.random.uniform(50, 200)
        }
        
        # 파생 특성 추가
        features = ml_system._generate_derived_features(features)
        features_list.append(features)
        
        # 타겟 생성 (성능 지표)
        target = features['qps'] * (1 - features['latency']/10) + np.random.normal(0, 50)
        targets.append(target)
    
    # 특성 추출
    extracted_features = ml_system.extract_rocksdb_features(features_list[0])
    print(f"추출된 특성: {list(extracted_features.keys())}")
    
    # 훈련 데이터 준비
    training_data = ml_system.prepare_training_data(features_list, targets)
    
    # ML 모델 훈련
    ml_models = ml_system.train_ml_models(training_data)
    
    # 교차 검증
    cv_results = ml_system.cross_validate_models(training_data)
    
    # 시각화 생성
    ml_system.create_ml_visualizations(training_data)
    
    # 보고서 생성
    report = ml_system.generate_ml_report()
    
    print("\n" + "=" * 60)
    print("🎉 Machine Learning Integration 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
