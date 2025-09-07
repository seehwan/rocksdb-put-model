# PutModel v4 정량 분석 로드맵

## **현재 상태 (2025-09-07)**

### ✅ 완료된 작업
- [x] v4 모델 이론적 설계 완료
- [x] HTML 문서화 완료 (4개 파일)
- [x] 구현 가이드 작성 완료
- [x] 기존 v1-v3 실험 데이터 보유
- [x] Phase-A~E 실험 결과 일부 보유

### 🔄 진행 중인 작업
- [ ] v4 모델 핵심 구성요소 구현
- [ ] Device Envelope Modeling
- [ ] Closed Ledger Accounting
- [ ] Dynamic Simulation Framework

---

## **다음 단계: 정량 분석을 위한 구체적 실행 계획**

### **Phase 1: Device Envelope Modeling (D+1~D+2)**

#### **1.1 fio 그리드 스윕 설계**
```bash
# 목표: 180개 포인트 그리드 스윕
ρr ∈ {0, 25, 50, 75, 100}%     # 읽기 비율
iodepth ∈ {1, 4, 16, 64}       # 큐 깊이  
numjobs ∈ {1, 2, 4}            # 병렬 작업 수
bs ∈ {4, 64, 1024} KiB         # 블록 크기
```

#### **1.2 실행 스크립트 개발**
- `tools/device_envelope/run_envelope.sh`: fio 그리드 스윕 실행
- `tools/device_envelope/parse_envelope.py`: JSON 결과 파싱
- `tools/device_envelope/fit_envelope.py`: 4D 선형보간 모델 생성

#### **1.3 예상 결과**
- `envelope_model.json`: 4D 그리드 + 선형보간 테이블
- `device_envelope.csv`: 원시 측정 데이터
- 보간 정확도: ≤5% 오차

### **Phase 2: Closed Ledger Accounting (D+2~D+3)**

#### **2.1 RocksDB LOG 파서 개발**
- `tools/wa_ra_accounting/parse_rocksdb_log.py`: LOG 파일 파싱
- `tools/wa_ra_accounting/closed_ledger.py`: 회계 폐곡선 검증

#### **2.2 회계 정의 구현**
```python
WA_stat = (WAL + Flush + Σ CompWrite) / UserWrite
WA_device = DeviceWrite / UserWrite
RA_comp = Σ CompRead / UserWrite
폐곡선 검증: |WA_stat - WA_device| ≤ 10%
```

#### **2.3 예상 결과**
- `ledger.csv`: 표준화된 회계 데이터
- 폐곡선 오차: ≤10% 달성
- Per-level I/O 분해 완료

### **Phase 3: Dynamic Simulation Framework (D+3~D+4)**

#### **3.1 v4 시뮬레이터 구현**
- `model/v4_simulator.py`: 핵심 시뮬레이션 엔진
- `model/envelope.py`: Device Envelope 모델
- `model/closed_ledger.py`: 회계 시스템

#### **3.2 핵심 수식 구현**
```python
C_ℓ(t) = μ_ℓ · k_ℓ · η_ℓ(t) · Beff(t)
Q_ℓ(t+Δ) = max{0, Q_ℓ(t) + I_ℓ(t) - C_ℓ(t)·Δ}
Beff = Envelope(ρr, qd, numjobs, bs)
```

#### **3.3 예상 결과**
- 시뮬레이션 속도: ≥1000 steps/sec
- 메모리 사용량: ≤2GB (10K steps)
- CPU 사용률: ≤70% (8코어)

### **Phase 4: 5단계 검증 파이프라인 (D+4~D+5)**

#### **4.1 Phase-A: 장치 캘리브레이션**
- fio 그리드 스윕 완료
- 엔벌롭 모델 검증
- 상수 계수 (μ, k) 보정

#### **4.2 Phase-B: 전이 관찰**
- 빈 DB → Steady State 수렴 과정
- Backlog 동역학 분석
- 제어기 동작 패턴 관찰

#### **4.3 Phase-C: 레벨 분해**
- Per-level I/O 분석
- 병목 지점 진단
- 리소스 활용률 측정

#### **4.4 Phase-D: 홀드아웃 검증**
- 20개 홀드아웃 설정
- MAPE ≤15% 달성
- R² ≥0.85 달성

#### **4.5 Phase-E: 민감도 분석**
- 파라미터 변화 영향 분석
- 최적화 권장사항 도출
- 비용-효과 분석

### **Phase 5: v3 모델과의 정량적 비교 (D+5~D+6)**

#### **5.1 성능 메트릭 비교**
- MAPE: v3 (23.4%) vs v4 (목표: ≤15%)
- R²: v3 (0.67) vs v4 (목표: ≥0.85)
- 실행 속도: v3 vs v4
- 메모리 효율성: v3 vs v4

#### **5.2 정확도 분석**
- 처리량 예측 정확도
- 지연 시간 예측 정확도
- 백로그 예측 정확도
- Per-level 분석 정확도

#### **5.3 신뢰성 분석**
- 폐곡선 검증 (v4만)
- 물리적 일관성 (v4만)
- 재현성 테스트
- 안정성 분석

---

## **구체적 실행 계획**

### **즉시 시작 가능한 작업**

#### **1. Device Envelope Modeling 시작**
```bash
# 1. fio 그리드 스윕 스크립트 작성
mkdir -p tools/device_envelope
cd tools/device_envelope

# 2. fio 실행 스크립트 생성
cat > run_envelope.sh << 'EOF'
#!/bin/bash
DEVICE="/dev/nvme1n1p1"
OUTPUT_DIR="device_envelope_results"
mkdir -p $OUTPUT_DIR

for rho_r in 0 25 50 75 100; do
    for iodepth in 1 4 16 64; do
        for numjobs in 1 2 4; do
            for bs_k in 4 64 1024; do
                echo "Testing: rho_r=${rho_r}%, iodepth=${iodepth}, numjobs=${numjobs}, bs=${bs_k}K"
                
                fio --name=mixed_test \
                    --filename=${DEVICE} \
                    --ioengine=io_uring \
                    --direct=1 \
                    --rw=randrw \
                    --rwmixread=${rho_r} \
                    --iodepth=${iodepth} \
                    --numjobs=${numjobs} \
                    --bs=${bs_k}k \
                    --runtime=30 \
                    --ramp_time=10 \
                    --norandommap=1 \
                    --randrepeat=0 \
                    --output-format=json \
                    --output=${OUTPUT_DIR}/result_${rho_r}_${iodepth}_${numjobs}_${bs_k}.json
            done
        done
    done
done
EOF

chmod +x run_envelope.sh
```

#### **2. Python 파싱 스크립트 작성**
```python
# tools/device_envelope/parse_envelope.py
import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import os

def parse_fio_results(output_dir: str) -> dict:
    """fio 결과를 파싱하여 4D 그리드 생성"""
    results = {}
    
    for rho_r in [0, 25, 50, 75, 100]:
        for iodepth in [1, 4, 16, 64]:
            for numjobs in [1, 2, 4]:
                for bs_k in [4, 64, 1024]:
                    filename = f"result_{rho_r}_{iodepth}_{numjobs}_{bs_k}.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    if os.path.exists(filepath):
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                        
                        # 대역폭 추출 (MiB/s)
                        write_bw = data['jobs'][0]['write']['bw'] / 1024  # KiB/s to MiB/s
                        read_bw = data['jobs'][0]['read']['bw'] / 1024
                        total_bw = write_bw + read_bw
                        
                        results[(rho_r, iodepth, numjobs, bs_k)] = total_bw
    
    return results

def create_envelope_model(results: dict) -> dict:
    """4D 그리드에서 엔벌롭 모델 생성"""
    # 축 정의
    rho_r_axis = np.array([0, 25, 50, 75, 100])
    iodepth_axis = np.array([1, 4, 16, 64])
    numjobs_axis = np.array([1, 2, 4])
    bs_axis = np.array([4, 64, 1024])
    
    # 4D 그리드 생성
    bandwidth_grid = np.zeros((5, 4, 3, 3))
    
    for i, rho_r in enumerate(rho_r_axis):
        for j, iodepth in enumerate(iodepth_axis):
            for k, numjobs in enumerate(numjobs_axis):
                for l, bs_k in enumerate(bs_axis):
                    key = (rho_r, iodepth, numjobs, bs_k)
                    if key in results:
                        bandwidth_grid[i, j, k, l] = results[key]
    
    return {
        'rho_r_axis': rho_r_axis.tolist(),
        'iodepth_axis': iodepth_axis.tolist(),
        'numjobs_axis': numjobs_axis.tolist(),
        'bs_axis': bs_axis.tolist(),
        'bandwidth_grid': bandwidth_grid.tolist()
    }

if __name__ == "__main__":
    # fio 결과 파싱
    results = parse_fio_results("device_envelope_results")
    
    # 엔벌롭 모델 생성
    envelope_model = create_envelope_model(results)
    
    # JSON 파일로 저장
    with open("envelope_model.json", "w") as f:
        json.dump(envelope_model, f, indent=2)
    
    print(f"Envelope model created with {len(results)} data points")
    print(f"Model saved to envelope_model.json")
```

#### **3. EnvelopeModel 클래스 구현**
```python
# model/envelope.py
import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, Optional

class EnvelopeModel:
    def __init__(self, grid_data: Dict):
        self.rho_r_axis = np.array(grid_data['rho_r_axis'])
        self.iodepth_axis = np.array(grid_data['iodepth_axis'])
        self.numjobs_axis = np.array(grid_data['numjobs_axis'])
        self.bs_axis = np.array(grid_data['bs_axis'])
        self.bandwidth_grid = np.array(grid_data['bandwidth_grid'])
        
        # 보간기 생성
        self.interpolator = RegularGridInterpolator(
            (self.rho_r_axis, self.iodepth_axis, self.numjobs_axis, self.bs_axis),
            self.bandwidth_grid,
            method='linear',
            bounds_error=False,
            fill_value=None
        )
    
    @classmethod
    def from_json_path(cls, path: str) -> "EnvelopeModel":
        """JSON 파일에서 엔벌롭 모델 로드"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(data)
    
    def query(self, rho_r: float, qd: int, numjobs: int, bs_k: int,
              Br: Optional[float] = None, Bw: Optional[float] = None) -> float:
        """4D 선형보간으로 Beff 계산"""
        # 보간 실행
        point = np.array([rho_r, qd, numjobs, bs_k])
        beff = self.interpolator(point)
        
        # 물리적 상한 클램프 (선택적)
        if Br is not None and Bw is not None:
            beff = min(beff, min(Br, Bw))
        
        return float(beff)
    
    def get_interpolation_error(self, test_points: list) -> float:
        """보간 오차 계산"""
        errors = []
        for point in test_points:
            rho_r, qd, numjobs, bs_k = point
            predicted = self.query(rho_r, qd, numjobs, bs_k)
            # 실제 측정값과 비교 (여기서는 간단히 0으로 설정)
            actual = 0  # 실제로는 측정값과 비교
            if actual > 0:
                error = abs(predicted - actual) / actual
                errors.append(error)
        
        return np.mean(errors) if errors else 0.0
```

### **다음 주 작업 계획**

#### **주 1: Device Envelope Modeling**
- [ ] fio 그리드 스윕 실행 (180개 포인트)
- [ ] 결과 파싱 및 엔벌롭 모델 생성
- [ ] 보간 정확도 검증
- [ ] 물리적 상한 클램프 테스트

#### **주 2: Closed Ledger Accounting**
- [ ] RocksDB LOG 파서 개발
- [ ] 회계 폐곡선 검증 시스템 구현
- [ ] Per-level I/O 분해 완료
- [ ] 단위 테스트 작성

#### **주 3: Dynamic Simulation Framework**
- [ ] v4 시뮬레이터 핵심 구현
- [ ] 시간가변 효율 모델링
- [ ] Backlog 동역학 구현
- [ ] 성능 최적화

#### **주 4: 검증 파이프라인**
- [ ] 5단계 검증 파이프라인 구현
- [ ] 홀드아웃 데이터셋 준비
- [ ] 성능 메트릭 계산
- [ ] v3 모델과 비교 분석

---

## **성공 기준**

### **정량적 목표**
- [ ] Device Envelope 보간 오차 ≤5%
- [ ] Closed Ledger 폐곡선 오차 ≤10%
- [ ] 홀드아웃 MAPE ≤15%
- [ ] 시뮬레이션 속도 ≥1000 steps/sec
- [ ] v3 대비 정확도 향상 ≥50%

### **품질 기준**
- [ ] 모든 코드에 단위 테스트 작성
- [ ] 문서화 완료 (API 문서, 사용법)
- [ ] 재현성 보장 (시드 고정, 환경 일관성)
- [ ] 확장성 고려 (모듈화, 설정 파일)

---

## **위험 요소 및 대응 방안**

### **주요 위험요소**
1. **fio 실행 시간**: 180개 포인트 × 45초 = 2.25시간
   - **대응**: 병렬 실행, 배치 처리
2. **메모리 사용량**: 4D 그리드 + 보간 테이블
   - **대응**: 스파스 그리드, 압축 저장
3. **정확도 목표**: 15% MAPE 달성 어려움
   - **대응**: 단계적 개선, 휴리스틱 보정

### **대응 전략**
- **점진적 개발**: MVP → 완전 구현
- **지속적 검증**: 각 단계별 테스트
- **성능 모니터링**: 실시간 메트릭 추적
- **백업 계획**: 대안 알고리즘 준비

---

## **결론**

v4 모델의 정량 분석을 위해서는 **Device Envelope Modeling**부터 시작하여 **Closed Ledger Accounting**, **Dynamic Simulation Framework** 순으로 체계적으로 구현해야 합니다. 

각 단계마다 명확한 성공 기준을 설정하고, 지속적인 검증을 통해 모델의 정확성과 신뢰성을 보장해야 합니다.

**즉시 시작 가능한 작업**: fio 그리드 스윕 스크립트 작성 및 실행
