# PutModel v4 구체적 구현 가이드

## 1. v4 모델의 핵심 문제점과 해결방안

### 1.1 v3의 4가지 블로킹 이슈

#### 🔧 **혼합 I/O 대역폭의 물리적 불일치**
- **문제**: `Beff = 1/(ρr/Br + ρw/Bw)`는 큐깊이, 병렬도, 블록크기 간섭 무시
- **해결**: fio 그리드 스윕으로 실제 장치 특성 측정 → 4D 엔벌롭 모델

#### 📊 **수치/정의의 자기모순**
- **문제**: WA/RA/혼합 비율이 표·본문·통계 간 불일치 (GB vs GiB 혼용)
- **해결**: Closed Ledger 회계 시스템으로 물리적 검증

#### 🔄 **검증의 순환성**
- **문제**: LOG 기반 WA를 모델 입력으로 사용하면서 "0% 오차" 주장
- **해결**: Phase-A(캘리브레이션)와 Phase-D(검증) 엄격 분리

#### 📈 **Per-level 지표 정의 미흡**
- **문제**: Compaction In/Out/Read/Write 정의·추출식·로그 매핑 부재
- **해결**: 표준화된 per-level 회계 시스템 구축

### 1.2 v4의 핵심 혁신

1. **Device Envelope Modeling**: 실제 장치 특성 반영
2. **Closed Ledger Accounting**: 물리적 검증 시스템
3. **Dynamic Simulation**: 시간가변 시스템 동작 모델링
4. **Calibration/Validation Separation**: 엄격한 분리

## 2. Device Envelope Modeling 구체적 구현

### 2.1 fio 그리드 스윕 설계

```bash
# 축 정의
ρr ∈ {0, 25, 50, 75, 100}%     # 읽기 비율
iodepth ∈ {1, 4, 16, 64}       # 큐 깊이
numjobs ∈ {1, 2, 4}            # 병렬 작업 수
bs ∈ {4, 64, 1024} KiB         # 블록 크기

# 총 조합: 5 × 4 × 3 × 3 = 180개 포인트
```

### 2.2 EnvelopeModel 클래스 설계

```python
class EnvelopeModel:
    def __init__(self, grid_data: Dict):
        self.rho_r_axis = grid_data['rho_r_axis']
        self.iodepth_axis = grid_data['iodepth_axis'] 
        self.numjobs_axis = grid_data['numjobs_axis']
        self.bs_axis = grid_data['bs_axis']
        self.bandwidth_grid = grid_data['bandwidth_grid']  # 4D 배열
        
    @classmethod
    def from_json_path(cls, path: str) -> "EnvelopeModel":
        """JSON 파일에서 엔벌롭 모델 로드"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(data)
    
    def query(self, rho_r: float, qd: int, numjobs: int, bs_k: int,
              Br: float = None, Bw: float = None) -> float:
        """4D 선형보간으로 Beff 계산"""
        # 1. 격자 내 보간
        beff = self._interpolate_4d(rho_r, qd, numjobs, bs_k)
        
        # 2. 물리적 상한 클램프 (선택적)
        if Br is not None and Bw is not None:
            beff = min(beff, min(Br, Bw))
            
        return beff
    
    def _interpolate_4d(self, rho_r, qd, numjobs, bs_k):
        """4D 선형보간 구현"""
        # scipy.interpolate.RegularGridInterpolator 사용
        pass
```

### 2.3 fio 그리드 스윕 실행

```bash
#!/bin/bash
# tools/device_envelope/run_envelope.sh

DEVICE="/dev/nvme1n1p1"
OUTPUT_DIR="device_envelope_results"
FIO_TEMPLATE="fio_template.json"

# 그리드 스윕 실행
for rho_r in 0 25 50 75 100; do
    for iodepth in 1 4 16 64; do
        for numjobs in 1 2 4; do
            for bs_k in 4 64 1024; do
                echo "Testing: rho_r=${rho_r}%, iodepth=${iodepth}, numjobs=${numjobs}, bs=${bs_k}K"
                
                # fio 명령 생성 및 실행
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
```

## 3. Closed Ledger Accounting 시스템

### 3.1 회계 정의

```python
class ClosedLedger:
    def __init__(self):
        self.user_write_bytes = 0
        self.wal_bytes = 0
        self.flush_bytes = 0
        self.comp_write_bytes = {}  # level별
        self.comp_read_bytes = {}   # level별
        self.device_write_bytes = 0
        self.device_read_bytes = 0
    
    def calculate_wa_ra(self):
        """WA/RA 계산"""
        total_comp_write = sum(self.comp_write_bytes.values())
        total_comp_read = sum(self.comp_read_bytes.values())
        
        # WA 계산
        wa_stat = (self.wal_bytes + self.flush_bytes + total_comp_write) / self.user_write_bytes
        wa_device = self.device_write_bytes / self.user_write_bytes
        
        # RA 계산  
        ra_comp = total_comp_read / self.user_write_bytes
        ra_runtime = self.device_read_bytes / self.user_write_bytes
        
        return {
            'wa_stat': wa_stat,
            'wa_device': wa_device,
            'ra_comp': ra_comp,
            'ra_runtime': ra_runtime,
            'closure_error': abs(wa_stat - wa_device) / wa_stat
        }
    
    def verify_closure(self, tolerance=0.1):
        """폐곡선 검증 (±10%)"""
        metrics = self.calculate_wa_ra()
        return metrics['closure_error'] <= tolerance
```

### 3.2 RocksDB LOG 파서

```python
class RocksDBLogParser:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.ledger = ClosedLedger()
    
    def parse_log(self):
        """LOG 파일에서 I/O 통계 추출"""
        with open(self.log_file, 'r') as f:
            for line in f:
                self._parse_line(line)
    
    def _parse_line(self, line: str):
        """개별 로그 라인 파싱"""
        # WAL 쓰기 패턴
        if "WAL write" in line:
            self.ledger.wal_bytes += self._extract_bytes(line)
        
        # Flush 패턴
        elif "Flush" in line:
            self.ledger.flush_bytes += self._extract_bytes(line)
        
        # Compaction 패턴
        elif "Compaction" in line:
            level, write_bytes, read_bytes = self._extract_compaction(line)
            self.ledger.comp_write_bytes[level] = write_bytes
            self.ledger.comp_read_bytes[level] = read_bytes
```

## 4. Dynamic Simulation Framework

### 4.1 v4 시뮬레이터 설계

```python
class V4Simulator:
    def __init__(self, envelope_model: EnvelopeModel, config: Dict):
        self.envelope = envelope_model
        self.config = config
        self.levels = config['levels']
        self.Q = {level: 0.0 for level in self.levels}  # Backlog (GiB)
        self.mu = config['mu']  # 스케줄러 계수
        self.k = config['k']    # 코덱 계수
        
    def simulate(self, steps: int, dt: float = 1.0):
        """동적 시뮬레이션 실행"""
        results = []
        
        for t in range(steps):
            # 1. 현재 상태에서 ρr 추정 (휴리스틱)
            rho_r = self._estimate_rho_r()
            
            # 2. 엔벌롭에서 Beff 조회
            beff = self.envelope.query(
                rho_r=rho_r,
                qd=self.config['iodepth'],
                numjobs=self.config['numjobs'],
                bs_k=self.config['bs_k']
            )
            
            # 3. 레벨별 처리용량 계산
            C = {}
            for level in self.levels:
                eta = self._calculate_eta(level, t)  # 시간가변 효율
                C[level] = self.mu[level] * self.k[level] * eta * beff
            
            # 4. Backlog 업데이트
            self._update_backlog(C, dt)
            
            # 5. 결과 기록
            results.append({
                't': t * dt,
                'rho_r': rho_r,
                'beff': beff,
                'Q': self.Q.copy(),
                'C': C.copy()
            })
        
        return results
    
    def _estimate_rho_r(self) -> float:
        """ρr 추정 (초기: 휴리스틱, 추후: LOG 기반 학습)"""
        # 간단한 휴리스틱: L0 백로그 비율 기반
        total_backlog = sum(self.Q.values())
        if total_backlog == 0:
            return 0.5  # 기본값
        
        l0_ratio = self.Q.get('L0', 0) / total_backlog
        return min(1.0, l0_ratio * 2)  # L0 비율이 높을수록 읽기 증가
    
    def _calculate_eta(self, level: str, t: int) -> float:
        """시간가변 효율 계산"""
        # 경합, 혼합비, 컨디션 반영
        base_efficiency = 0.8
        
        # 경합 효과
        contention = min(1.0, sum(self.Q.values()) / 100.0)  # 100GiB 기준
        
        # 시간 효과 (주기적 변동)
        time_factor = 1.0 + 0.1 * math.sin(t * 0.1)
        
        return base_efficiency * (1.0 - contention) * time_factor
    
    def _update_backlog(self, C: Dict, dt: float):
        """Backlog 동역학 업데이트"""
        for level in self.levels:
            # 유입량 (상위 레벨에서)
            inflow = self._calculate_inflow(level)
            
            # 처리량
            outflow = C[level] * dt
            
            # Backlog 업데이트
            self.Q[level] = max(0, self.Q[level] + inflow - outflow)
```

## 5. Validation Pipeline 구체적 설계

### 5.1 5단계 검증 파이프라인

```python
class V4ValidationPipeline:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        
    def run_validation(self):
        """전체 검증 파이프라인 실행"""
        # Phase-A: 장치 캘리브레이션
        envelope_model = self.phase_a_device_calibration()
        
        # Phase-B: 전이 관찰
        transition_data = self.phase_b_transition_observation()
        
        # Phase-C: 레벨 분해
        level_breakdown = self.phase_c_level_breakdown()
        
        # Phase-D: 경계 검증 (홀드아웃)
        validation_results = self.phase_d_boundary_validation(envelope_model)
        
        # Phase-E: 민감도 분석
        sensitivity_results = self.phase_e_sensitivity_analysis()
        
        return {
            'envelope_model': envelope_model,
            'transition_data': transition_data,
            'level_breakdown': level_breakdown,
            'validation_results': validation_results,
            'sensitivity_results': sensitivity_results
        }
    
    def phase_a_device_calibration(self):
        """Phase-A: 장치 캘리브레이션"""
        # 1. fio 그리드 스윕 실행
        self._run_fio_grid_sweep()
        
        # 2. 결과 파싱 및 엔벌롭 모델 생성
        envelope_data = self._parse_fio_results()
        envelope_model = EnvelopeModel(envelope_data)
        
        # 3. 엔벌롭 모델 저장
        self._save_envelope_model(envelope_model)
        
        return envelope_model
    
    def phase_d_boundary_validation(self, envelope_model):
        """Phase-D: 경계 검증 (홀드아웃)"""
        # 1. 홀드아웃 데이터셋 준비
        holdout_configs = self._prepare_holdout_configs()
        
        validation_results = []
        for config in holdout_configs:
            # 2. v4 시뮬레이터 실행
            simulator = V4Simulator(envelope_model, config)
            predicted_results = simulator.simulate(config['steps'])
            
            # 3. 실제 RocksDB 벤치마크 실행
            actual_results = self._run_rocksdb_benchmark(config)
            
            # 4. 예측 vs 실제 비교
            metrics = self._calculate_validation_metrics(predicted_results, actual_results)
            
            validation_results.append({
                'config': config,
                'predicted': predicted_results,
                'actual': actual_results,
                'metrics': metrics
            })
        
        return validation_results
    
    def _calculate_validation_metrics(self, predicted, actual):
        """검증 메트릭 계산"""
        # MAPE (Mean Absolute Percentage Error)
        mape = self._calculate_mape(predicted, actual)
        
        # NRMSE (Normalized Root Mean Square Error)
        nrmse = self._calculate_nrmse(predicted, actual)
        
        # Bland-Altman bias (선택적)
        bias = self._calculate_bias(predicted, actual)
        
        return {
            'mape': mape,
            'nrmse': nrmse,
            'bias': bias,
            'acceptance': mape <= 0.15  # 15% 이내 수용
        }
```

### 5.2 수용 기준

```python
ACCEPTANCE_CRITERIA = {
    'A1_ledger_closure': {
        'description': 'Same-run ledger closure',
        'criterion': '|WA_stat − WA_device| ≤ 10%',
        'check': lambda ledger: ledger.verify_closure(tolerance=0.1)
    },
    'A2_holdout_mape': {
        'description': 'Holdout MAPE',
        'criterion': 'MAPE ≤ 10–15%',
        'check': lambda metrics: metrics['mape'] <= 0.15
    },
    'A3_documentation_consistency': {
        'description': 'Unit/symbol consistency',
        'criterion': '100% consistency',
        'check': lambda docs: self._check_consistency(docs)
    },
    'A4_reproducibility_metadata': {
        'description': 'Reproducibility metadata',
        'criterion': 'Complete metadata',
        'check': lambda meta: self._check_metadata_completeness(meta)
    }
}
```

## 6. 개발 일정 및 마일스톤

### 6.1 5일 개발 일정

```python
DEVELOPMENT_SCHEDULE = {
    'D+1': {
        'task': 'fio grid measurement → envelope_model.json completion',
        'deliverables': ['device_envelope.csv', 'envelope_model.json'],
        'success_criteria': ['180 fio runs completed', '4D interpolation working']
    },
    'D+2': {
        'task': 'ledger.csv closure verification',
        'deliverables': ['ledger.csv', 'closure_verification_report'],
        'success_criteria': ['±10% closure achieved', 'LOG parser working']
    },
    'D+3': {
        'task': 'v4 simulator integration and initial calibration',
        'deliverables': ['v4_simulator.py', 'calibration_results.json'],
        'success_criteria': ['Simulator runs end-to-end', 'μ, k, η calibrated']
    },
    'D+4': {
        'task': 'Holdout validation (MAPE/NRMSE)',
        'deliverables': ['validation_report.html', 'performance_metrics.json'],
        'success_criteria': ['MAPE ≤ 15%', 'All acceptance criteria met']
    },
    'D+5': {
        'task': 'Release packaging',
        'deliverables': ['PutModel_v4.html', 'Complete package'],
        'success_criteria': ['Documentation complete', 'Package ready for release']
    }
}
```

### 6.2 체크리스트

```python
V4_CHECKLIST = [
    "fio 스윕 완료 → envelope_model.json 생성",
    "LOG 파싱 → ledger.csv 생성(닫힘 확인)",
    "v4 시뮬레이터 실행 → sim_out.csv 산출",
    "metrics.py로 Truth vs Pred 평가",
    "문서/표/그림/메타데이터 정리 및 저장소 커밋"
]
```

## 7. 위험요소 및 대응방안

### 7.1 주요 위험요소

1. **LOG 포맷 차이**: 정규식 다중 버전 지원, 샘플 기반 유닛테스트
2. **NVMe 스로틀/온도**: 런 간 휴지, 전력모드 고정, 온도 로그 수집
3. **엔벌롭 외삽 위험**: 보간 격자 확장 또는 최근접 클램프, 경고 출력
4. **순환 검증 재발**: Phase-A/Phase-D 산출물 폴더 분리, 교차사용 방지 체크

### 7.2 대응 전략

```python
RISK_MITIGATION = {
    'log_format_differences': {
        'strategy': 'Multi-version regex support + unit tests',
        'implementation': 'VersionedLogParser class with fallback patterns'
    },
    'nvme_throttling': {
        'strategy': 'Temperature monitoring + cooldown periods',
        'implementation': 'ThermalMonitor class + adaptive delays'
    },
    'envelope_extrapolation': {
        'strategy': 'Grid expansion + nearest neighbor clamping',
        'implementation': 'ExtrapolationWarning + ClampPolicy classes'
    },
    'circular_validation': {
        'strategy': 'Strict folder separation + cross-usage checks',
        'implementation': 'PhaseIsolationValidator class'
    }
}
```

이 구체적인 구현 가이드를 통해 PutModel v4의 모든 구성요소를 체계적으로 개발할 수 있습니다.
