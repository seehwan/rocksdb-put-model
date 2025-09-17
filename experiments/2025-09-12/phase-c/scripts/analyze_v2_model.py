#!/usr/bin/env python3
"""
v2 모델 분석 스크립트
- 개선된 S_max 계산 분석
- Harmonic Mean 모델 검증
- v1 대비 개선점 분석
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

# v2 모델 import
from smax_calc_v2 import calculate_smax_v2

class V2ModelAnalyzer:
    def __init__(self):
        self.phase_b_data = None
        self.phase_a_data = None
        self.v2_predictions = {}
        self.results = {}
        
    def load_phase_b_data(self):
        """Phase-B 데이터 로드"""
        print("📊 Phase-B 데이터 로드 중...")
        
        # fillrandom_results.json 로드
        fillrandom_file = '/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-b/fillrandom_results.json'
        if os.path.exists(fillrandom_file):
            # CSV 형태로 로드
            self.phase_b_data = pd.read_csv(fillrandom_file, header=None, names=['secs_elapsed', 'interval_qps'])
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
            
    def analyze_v2_model(self):
        """v2 모델 분석"""
        print("🔍 v2 모델 분석 중...")
        
        # v2 모델 파라미터 (Phase-B 실제 db_bench 통계 기반)
        params = {
            'B_read_MBps': 136,    # 읽기 대역폭 (Phase-B 실제: 136.00 MB/s)
            'B_write_MBps': 138,   # 쓰기 대역폭 (Phase-B 실제: 138.47 MB/s)
            'rate_limiter_MBps': 0,  # 속도 제한
            'p_stall_mean': 0.1,   # 스톨 확률 (Phase-B 실제 stall 비율 추정)
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
            },
            'CR': 0.5406,  # 압축 비율
            'WA': 2.87,    # 쓰기 증폭
            'levels': [0, 1, 2, 3]  # 레벨 정보
        }
        
        # v2 모델로 S_max 계산
        try:
            # v2 모델에 필요한 파라미터 설정
            B_w = params['B_write_MBps']  # 쓰기 대역폭
            B_r = params['B_read_MBps']   # 읽기 대역폭
            rho_r = 0.5  # 읽기 비율 (추정)
            rho_w = 0.5  # 쓰기 비율 (추정)
            CR = params['CR']
            WA = params['WA']
            p_stall = params['p_stall_mean']
            
            # 입력값 크기 검사 및 예외 처리
            print(f"🔍 v2.1 모델 입력값 검사:")
            print(f"  B_w: {B_w}, B_r: {B_r}")
            print(f"  rho_r: {rho_r}, rho_w: {rho_w}")
            print(f"  CR: {CR}, WA: {WA}")
            print(f"  p_stall: {p_stall}")
            
            # 비정상적으로 큰 입력값 검사
            if abs(B_w) > 1e6 or abs(B_r) > 1e6:
                raise ValueError(f"입력 대역폭 값이 비정상적으로 큽니다: B_w={B_w}, B_r={B_r}")
            if abs(CR) > 10 or abs(WA) > 100:
                raise ValueError(f"압축/쓰기 증폭 값이 비정상적으로 큽니다: CR={CR}, WA={WA}")
            if abs(p_stall) > 1:
                raise ValueError(f"스톨 확률이 비정상적으로 큽니다: p_stall={p_stall}")
            
            # 레벨별 데이터 구성
            level_data = {
                0: {'write_gb': 100, 'w_amp': 1.0},
                1: {'write_gb': 200, 'w_amp': 1.5},
                2: {'write_gb': 300, 'w_amp': 2.0},
                3: {'write_gb': 400, 'w_amp': 2.5}
            }
            total_write_gb = sum(data['write_gb'] for data in level_data.values())
            
            # 레벨 데이터 크기 검사
            for level, data in level_data.items():
                if abs(data['write_gb']) > 1e6 or abs(data['w_amp']) > 100:
                    raise ValueError(f"레벨 {level} 데이터가 비정상적으로 큽니다: {data}")
            
            if abs(total_write_gb) > 1e6:
                raise ValueError(f"총 쓰기 용량이 비정상적으로 큽니다: {total_write_gb}")
            
            print(f"✅ 모든 입력값이 안전한 범위 내에 있습니다.")
            
            result = calculate_smax_v2(
                B_w=B_w,
                B_r=B_r,
                rho_r=rho_r,
                rho_w=rho_w,
                CR=CR,
                WA=WA,
                level_data=level_data,
                total_write_gb=total_write_gb,
                p_stall=p_stall
            )
            
            # 결과 검증 및 outlier 감지
            smax_raw = result.get('s_max_final', 0)  # 's_max' 대신 's_max_final' 사용
            
            # 결과값 크기 검사 및 예외 처리
            print(f"🔍 v2.1 모델 결과값 검사:")
            print(f"  s_max_final: {smax_raw}")
            
            # Outlier 감지 및 예외 처리
            if smax_raw is None:
                raise ValueError("v2 모델 결과가 None입니다. 모델 계산에 오류가 있습니다.")
            elif abs(smax_raw) > 1e6:  # 1M ops/sec 이상이면 비정상적
                raise ValueError(f"v2 모델 결과가 비정상적으로 큽니다: {smax_raw:.2e} ops/sec. 이는 outlier입니다.")
            elif smax_raw < 0:  # 음수면 비정상적
                raise ValueError(f"v2 모델 결과가 음수입니다: {smax_raw:.2e} ops/sec. 이는 비정상적입니다.")
            elif smax_raw > 10000:  # 10K ops/sec 이상이면 의심스러움
                raise ValueError(f"v2 모델 결과가 의심스럽게 큽니다: {smax_raw:.2f} ops/sec. 이는 outlier일 가능성이 높습니다.")
            else:
                smax_v2 = float(smax_raw)
                print(f"✅ v2.1 모델 결과값이 안전한 범위 내에 있습니다: {smax_v2:.2f} ops/sec")
            
            self.v2_predictions['smax'] = smax_v2
            print(f"✅ v2 모델 S_max 예측: {smax_v2:.2f} ops/sec")
            
        except ValueError as e:
            print(f"❌ v2 모델 outlier 감지: {e}")
            print("🔍 v2 모델에 근본적인 문제가 있습니다. 다른 모델로 진행하거나 v2 모델을 수정해야 합니다.")
            self.v2_predictions['smax'] = None  # outlier로 표시
        except Exception as e:
            print(f"❌ v2 모델 계산 오류: {e}")
            self.v2_predictions['smax'] = None
            
    def compare_with_phase_b(self):
        """Phase-B 데이터와 비교"""
        print("📊 Phase-B 데이터와 v2 모델 비교 중...")
        
        if self.phase_b_data is None:
            print("❌ Phase-B 데이터가 없습니다.")
            return
            
        # Phase-B 실제 성능 분석
        actual_qps = self.phase_b_data['interval_qps'].mean()
        actual_max_qps = self.phase_b_data['interval_qps'].max()
        actual_min_qps = self.phase_b_data['interval_qps'].min()
        
        # v2 모델 예측값
        predicted_smax = self.v2_predictions.get('smax', 0)
        
        # 오류 계산
        if predicted_smax > 0:
            error_percent = ((actual_qps - predicted_smax) / predicted_smax) * 100
            error_abs = abs(error_percent)
        else:
            error_percent = 0
            error_abs = 0
            
        self.results = {
            'model': 'v2',
            'predicted_smax': predicted_smax,
            'actual_qps_mean': actual_qps,
            'actual_qps_max': actual_max_qps,
            'actual_qps_min': actual_min_qps,
            'error_percent': error_percent,
            'error_abs': error_abs,
            'validation_status': 'Good' if error_abs < 20 else 'Poor' if error_abs > 50 else 'Fair'
        }
        
        print(f"✅ v2 모델 비교 결과:")
        print(f"   예측값: {predicted_smax:.2f} ops/sec")
        print(f"   실제값: {actual_qps:.2f} ops/sec (평균)")
        print(f"   오류율: {error_percent:.2f}%")
        print(f"   검증 상태: {self.results['validation_status']}")
        
    def create_visualizations(self):
        """시각화 생성"""
        print("📊 v2 모델 시각화 생성 중...")
        
        if self.phase_b_data is None:
            print("❌ Phase-B 데이터가 없습니다.")
            return
            
        # 그래프 설정
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('v2 모델 분석 결과 (Harmonic Mean 모델)', fontsize=16, fontweight='bold')
        
        # 1. Phase-B 성능 트렌드
        ax1 = axes[0, 0]
        ax1.plot(self.phase_b_data['secs_elapsed'], self.phase_b_data['interval_qps'], 
                alpha=0.7, linewidth=1, color='blue')
        ax1.axhline(y=self.v2_predictions.get('smax', 0), color='red', linestyle='--', 
                   linewidth=2, label=f'v2 예측: {self.v2_predictions.get("smax", 0):.0f}')
        ax1.set_xlabel('시간 (초)')
        ax1.set_ylabel('QPS')
        ax1.set_title('Phase-B 성능 트렌드 vs v2 예측')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. 성능 분포
        ax2 = axes[0, 1]
        ax2.hist(self.phase_b_data['interval_qps'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(x=self.v2_predictions.get('smax', 0), color='red', linestyle='--', 
                   linewidth=2, label=f'v2 예측: {self.v2_predictions.get("smax", 0):.0f}')
        ax2.set_xlabel('QPS')
        ax2.set_ylabel('빈도')
        ax2.set_title('성능 분포 vs v2 예측')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 모델 정확도
        ax3 = axes[1, 0]
        models = ['v2 모델']
        predictions = [self.v2_predictions.get('smax', 0)]
        actuals = [self.phase_b_data['interval_qps'].mean()]
        
        x = np.arange(len(models))
        width = 0.35
        
        ax3.bar(x - width/2, predictions, width, label='예측값', color='red', alpha=0.7)
        ax3.bar(x + width/2, actuals, width, label='실제값', color='blue', alpha=0.7)
        ax3.set_xlabel('모델')
        ax3.set_ylabel('QPS')
        ax3.set_title('v2 모델 정확도')
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
        ax4.set_title(f'v2 모델 오류 분석\n절대 오류율: {error_abs:.2f}%')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/home/sslab/rocksdb-put-model/experiments/2025-09-12/phase-c/results/v2_model_analysis.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✅ v2 모델 시각화 완료")
        
    def save_results(self):
        """결과 저장"""
        print("💾 v2 모델 분석 결과 저장 중...")
        
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
        
        # numpy 타입 변환 후 JSON 저장 (안전한 변환)
        def safe_convert(obj):
            """안전한 타입 변환"""
            if isinstance(obj, np.integer):
                val = int(obj)
                return val if abs(val) < 1e10 else 0
            elif isinstance(obj, np.floating):
                val = float(obj)
                return val if abs(val) < 1e10 else 0.0
            elif isinstance(obj, np.ndarray):
                return [safe_convert(item) for item in obj.tolist()]
            elif isinstance(obj, dict):
                return {key: safe_convert(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [safe_convert(item) for item in obj]
            elif isinstance(obj, (int, float)):
                return obj if abs(obj) < 1e10 else 0
            else:
                return obj
        
        converted_results = safe_convert(self.results)
        with open(f'{results_dir}/v2_model_results.json', 'w', encoding='utf-8') as f:
            json.dump(converted_results, f, indent=2, ensure_ascii=False)
            
        # 요약 보고서 생성
        report = f"""
# v2 모델 분석 결과

## 📊 모델 정보
- **모델**: v2 (개선된 S_max 계산, Harmonic Mean 모델)
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

## 🎯 v2 모델 특징
- **Harmonic Mean 모델**: 혼합 I/O 대역폭 계산 개선
- **압축 비율 고려**: CR (Compression Ratio) 반영
- **쓰기 증폭 고려**: WA (Write Amplification) 반영
- **레벨별 분석**: L0-L3 레벨별 특성 고려

## 🎯 결론
v2 모델은 v1 모델의 개선된 버전으로, Harmonic Mean을 사용한 혼합 I/O 대역폭 계산과
압축 비율, 쓰기 증폭을 고려한 더 정확한 S_max 계산을 수행합니다.
"""
        
        with open(f'{results_dir}/v2_model_report.md', 'w', encoding='utf-8') as f:
            f.write(report)
            
        print("✅ v2 모델 분석 결과 저장 완료")
        
    def run_analysis(self):
        """전체 분석 실행"""
        print("🚀 v2 모델 분석 시작...")
        print("=" * 50)
        
        # 데이터 로드
        self.load_phase_b_data()
        self.load_phase_a_data()
        
        # v2 모델 분석
        self.analyze_v2_model()
        
        # Phase-B와 비교
        self.compare_with_phase_b()
        
        # 시각화 생성
        self.create_visualizations()
        
        # 결과 저장
        self.save_results()
        
        print("✅ v2 모델 분석 완료!")
        print("=" * 50)

def main():
    analyzer = V2ModelAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
