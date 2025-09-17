#!/usr/bin/env python3
"""
v1 모델 분석 스크립트
- 기본 S_max 계산 분석
- Phase-B 데이터와 비교
- 단순 모델의 정확도 평가
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import re

# 프로젝트 루트 경로 추가
sys.path.append('/home/sslab/rocksdb-put-model')
sys.path.append('/home/sslab/rocksdb-put-model/scripts')

# v1 모델 import
from smax_calc import calculate_smax

class V1ModelAnalyzer:
    def __init__(self):
        self.phase_b_data = None
        self.phase_a_data = None
        self.v1_predictions = {}
        self.results = {}
        
    def load_phase_b_data(self):
        """Phase-B 데이터 로드"""
        print("📊 Phase-B 데이터 로드 중...")
        
        # fillrandom_results.json 로드
        fillrandom_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/fillrandom_results.json'
        if os.path.exists(fillrandom_file):
            # CSV 형태로 로드
            self.phase_b_data = pd.read_csv(fillrandom_file, header=0)
            print(f"✅ Phase-B 데이터 로드 완료: {len(self.phase_b_data)} 개 레코드")
        else:
            print("❌ Phase-B 데이터 파일을 찾을 수 없습니다.")
            
    def load_phase_a_data(self):
        """Phase-A 데이터 로드"""
        print("📊 Phase-A 데이터 로드 중...")
        
        phase_a_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-a/data'
        if os.path.exists(phase_a_dir):
            # 초기 상태와 열화 상태 데이터 로드
            initial_files = [f for f in os.listdir(phase_a_dir) if f.endswith('.json') and '_degraded' not in f]
            degraded_files = [f for f in os.listdir(phase_a_dir) if f.endswith('.json') and '_degraded' in f]
            
            print(f"✅ 초기 상태 파일: {len(initial_files)} 개")
            print(f"✅ 열화 상태 파일: {len(degraded_files)} 개")
            
            self.phase_a_data = {
                'initial': initial_files,
                'degraded': degraded_files
            }
        else:
            print("❌ Phase-A 데이터 디렉토리를 찾을 수 없습니다.")
            
    def analyze_v1_model(self):
        """v1 모델 분석"""
        print("🔍 v1 모델 분석 중...")
        
        # v1 모델 파라미터 (기본값)
        params = {
            'B_read_MBps': 2368,  # 읽기 대역폭
            'B_write_MBps': 1484,  # 쓰기 대역폭
            'rate_limiter_MBps': 0,  # 속도 제한
            'p_stall_mean': 0.4531,  # 스톨 확률
            'read_share': {
                'L0': 0.319,
                'L1': 0.404,
                'L2': 0.191,
                'L3': 0.085
            },
            'write_share': {
                'L0': 0.190,
                'L1': 0.118,
                'L2': 0.452,
                'L3': 0.239
            }
        }
        
        # v1 모델로 S_max 계산
        try:
            # v1 모델 파라미터 설정
            cr = 0.5406  # 압축률
            wa = 2.87    # Write Amplification
            bw = params['B_write_MBps']  # 쓰기 대역폭
            br = params['B_read_MBps']   # 읽기 대역폭
            beff = min(bw, br)  # 혼합 대역폭 (간단한 추정)
            
            result = calculate_smax(cr=cr, wa=wa, bw=bw, br=br, beff=beff)
            smax_v1 = result['s_max']
            
            self.v1_predictions['smax'] = smax_v1
            print(f"✅ v1 모델 S_max 예측: {smax_v1:.2f} ops/sec")
            
        except Exception as e:
            print(f"❌ v1 모델 계산 오류: {e}")
            self.v1_predictions['smax'] = 0
            
    def compare_with_phase_b(self):
        """Phase-B 데이터와 비교"""
        print("📊 Phase-B 데이터와 v1 모델 비교 중...")
        
        if self.phase_b_data is None:
            print("❌ Phase-B 데이터가 없습니다.")
            return
            
        # Phase-B 실제 성능 분석
        actual_qps = self.phase_b_data['interval_qps'].mean()
        actual_max_qps = self.phase_b_data['interval_qps'].max()
        actual_min_qps = self.phase_b_data['interval_qps'].min()
        
        # v1 모델 예측값
        predicted_smax = self.v1_predictions.get('smax', 0)
        
        # 오류 계산
        if predicted_smax > 0:
            error_percent = ((actual_qps - predicted_smax) / predicted_smax) * 100
            error_abs = abs(error_percent)
        else:
            error_percent = 0
            error_abs = 0
            
        self.results = {
            'model': 'v1',
            'predicted_smax': predicted_smax,
            'actual_qps_mean': actual_qps,
            'actual_qps_max': actual_max_qps,
            'actual_qps_min': actual_min_qps,
            'error_percent': error_percent,
            'error_abs': error_abs,
            'validation_status': 'Good' if error_abs < 20 else 'Poor' if error_abs > 50 else 'Fair'
        }
        
        print(f"✅ v1 모델 비교 결과:")
        print(f"   예측값: {predicted_smax:.2f} ops/sec")
        print(f"   실제값: {actual_qps:.2f} ops/sec (평균)")
        print(f"   오류율: {error_percent:.2f}%")
        print(f"   검증 상태: {self.results['validation_status']}")
        
    def create_visualizations(self):
        """시각화 생성"""
        print("📊 v1 모델 시각화 생성 중...")
        
        if self.phase_b_data is None:
            print("❌ Phase-B 데이터가 없습니다.")
            return
            
        # 그래프 설정
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('v1 모델 분석 결과', fontsize=16, fontweight='bold')
        
        # 1. Phase-B 성능 트렌드
        ax1 = axes[0, 0]
        ax1.plot(self.phase_b_data['secs_elapsed'], self.phase_b_data['interval_qps'], 
                alpha=0.7, linewidth=1, color='blue')
        ax1.axhline(y=self.v1_predictions.get('smax', 0), color='red', linestyle='--', 
                   linewidth=2, label=f'v1 예측: {self.v1_predictions.get("smax", 0):.0f}')
        ax1.set_xlabel('시간 (초)')
        ax1.set_ylabel('QPS')
        ax1.set_title('Phase-B 성능 트렌드 vs v1 예측')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 성능 분포
        ax2 = axes[0, 1]
        ax2.hist(self.phase_b_data['interval_qps'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(x=self.v1_predictions.get('smax', 0), color='red', linestyle='--', 
                   linewidth=2, label=f'v1 예측: {self.v1_predictions.get("smax", 0):.0f}')
        ax2.set_xlabel('QPS')
        ax2.set_ylabel('빈도')
        ax2.set_title('성능 분포 vs v1 예측')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 모델 정확도
        ax3 = axes[1, 0]
        models = ['v1 모델']
        predictions = [self.v1_predictions.get('smax', 0)]
        actuals = [self.phase_b_data['interval_qps'].mean()]
        
        x = np.arange(len(models))
        width = 0.35
        
        ax3.bar(x - width/2, predictions, width, label='예측값', color='red', alpha=0.7)
        ax3.bar(x + width/2, actuals, width, label='실제값', color='blue', alpha=0.7)
        ax3.set_xlabel('모델')
        ax3.set_ylabel('QPS')
        ax3.set_title('v1 모델 정확도')
        ax3.set_xticks(x)
        ax3.set_xticklabels(models)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 오류 분석
        ax4 = axes[1, 1]
        error_percent = self.results.get('error_percent', 0)
        error_abs = self.results.get('error_abs', 0)
        
        ax4.bar(['오류율 (%)'], [error_abs], color='orange', alpha=0.7)
        ax4.set_ylabel('절대 오류율 (%)')
        ax4.set_title(f'v1 모델 오류 분석\n절대 오류율: {error_abs:.2f}%')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/results/v1_model_analysis.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ v1 모델 시각화 완료")
        
    def save_results(self):
        """결과 저장"""
        print("💾 v1 모델 분석 결과 저장 중...")
        
        # 결과 디렉토리 생성
        results_dir = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/results'
        os.makedirs(results_dir, exist_ok=True)
        
        # JSON 결과 저장 (numpy 타입 변환)
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        # numpy 타입 변환 후 JSON 저장
        converted_results = convert_numpy_types(self.results)
        with open(f'{results_dir}/v1_model_results.json', 'w', encoding='utf-8') as f:
            json.dump(converted_results, f, indent=2, ensure_ascii=False)
            
        # 요약 보고서 생성
        report = f"""
# v1 모델 분석 결과

## 📊 모델 정보
- **모델**: v1 (기본 S_max 계산)
- **분석 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 성능 결과
- **예측 S_max**: {self.results.get('predicted_smax', 0):.2f} ops/sec
- **실제 평균 QPS**: {self.results.get('actual_qps_mean', 0):.2f} ops/sec
- **실제 최대 QPS**: {self.results.get('actual_qps_max', 0):.2f} ops/sec
- **실제 최소 QPS**: {self.results.get('actual_qps_min', 0):.2f} ops/sec

## 📊 정확도 분석
- **오류율**: {self.results.get('error_percent', 0):.2f}%
- **절대 오류율**: {self.results.get('error_abs', 0):.2f}%
- **검증 상태**: {self.results.get('validation_status', 'Unknown')}

## 🎯 결론
v1 모델은 기본적인 S_max 계산을 수행하며, 단순한 모델 구조를 가지고 있습니다.
Phase-B 데이터와의 비교를 통해 모델의 정확도를 평가할 수 있습니다.
"""
        
        with open(f'{results_dir}/v1_model_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
            
        print("✅ v1 모델 분석 결과 저장 완료")
        
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 v1 모델 분석 시작...")
        print("=" * 50)
        
        # 데이터 로드
        self.load_phase_b_data()
        self.load_phase_a_data()
        
        # v1 모델 분석
        self.analyze_v1_model()
        
        # Phase-B와 비교
        self.compare_with_phase_b()
        
        # 시각화 생성
        self.create_visualizations()
        
        # 결과 저장
        self.save_results()
        
        print("✅ v1 모델 분석 완료!")
        print("=" * 50)

def main():
    analyzer = V1ModelAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
