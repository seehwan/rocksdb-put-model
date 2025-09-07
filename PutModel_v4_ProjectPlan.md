# PutModel_v4 — 생성 계획서 (계획 단계 전용 문서)

**버전:** v0.2 (planning-only)  
**목표:** v3의 한계를 해결한 **동적 LSM Put-Rate 모델(v4)**을 설계·구현·검증·문서화한다. 본 문서는 *왜(v4의 필요성)*, *무엇(모델 구성과 수식)*, *어떻게(실험·검증 설계)*, *코드 작성 계획*을 **실행 관점**에서 정리한다.

---

## 1. 왜 v4 인가? (배경·문제정의·핵심 변화)

### 1.1 v3의 블로킹 이슈(해결 대상)
- **혼합 I/O 대역폭(HM 가정)의 물리적 불일치**: `Beff = 1/(ρr/Br + ρw/Bw)`는 큐깊이, 병렬도, 블록크기에 따른 장치 상호간섭을 무시한다. 일부 실측값은 HM의 물리적 상한(`min(Br,Bw)`)을 초과하거나, “혼합 성능 저하” 서술과 충돌한다.
- **수치/정의의 자기모순**: WA/RA/혼합 비율과 합계가 표·본문·통계 간 불일치. GB vs GiB, 절대치(B) vs 정규화(η)의 혼용.
- **검증의 순환성**: LOG 기반 WA 값을 **모델 입력**으로 사용하면서 “0% 오차”를 주장하는 구조(캘리브레이션≠검증).
- **per-level 지표 정의 미흡**: Compaction In/Out/Read/Write에 대한 정의·추출식·로그 컬럼 매핑 부재.

### 1.2 v4의 핵심 변화(요약)
- **HM → 실측 엔벌롭(Envelope)**: `Beff = Envelope(ρr, qd, numjobs, bs)` (fio 그리드 스윕 + 선형보간, 선택적 `min(Br,Bw)` 클램프).
- **Closed Ledger(폐곡선 검산)**: 동일 런에 대해 `UserWrite → (WAL + Flush + Σ CompWrite) ↔ DeviceWrite`가 **닫히는** 표준 회계 정의.
- **캘리브레이션/검증 분리**: 장치·상수 보정(Phase‑A)과 홀드아웃 검증(Phase‑D)을 엄격히 분리.
- **기호/단위 표준화**: GiB/GB, 절대치 B(=MiB/s) vs 정규화 η(무차원) 명확화.

---

## 2. v4 모델 개요 (수식·구성요소)

### 2.1 모델의 y(출력)과 x(입력)
- **출력(예측 타깃)**: 시간 t에서의 put 처리량(또는 backlog 안정도 지표), 레벨별 처리율/대기열.
- **입력(주요 외생 변수)**: 장치 엔벌롭 `Envelope(ρr,qd,numjobs,bs)`, DB 옵션(threads, size ratio T, compression), workload 특성(value_size 등), 트리거/스톨 임계값.

### 2.2 핵심 수식(요약)
- 레벨 ℓ의 순간 처리용량(Write-path 기준):
  \n`C_ℓ(t) = μ_ℓ · k_ℓ · η_ℓ(t) · Beff(t)`\n
  - μ_ℓ: 스케줄러/서브컴팩션/리드어헤드 등 상수 계수(캘리브레이션 대상)  
  - k_ℓ: 코덱/블록크기/팬인 영향 상수(캘리브레이션 대상)  
  - η_ℓ(t): 시간가변 효율(경합·혼합비·컨디션 반영)  
  - Beff(t): **엔벌롭 보간값** = `Envelope(ρr(t), qd, numjobs, bs)`
- Backlog(간략 큐 동역학):
  \n`Q_ℓ(t+Δ) = max{0, Q_ℓ(t) + I_ℓ(t) − C_ℓ(t)·Δ}`\n
  - I_ℓ(t): 상위 레벨 outflow(Flush 또는 L(ℓ−1) compaction out)로부터 유도
- 혼합 대역폭: \n`Beff = Envelope(ρr, qd, numjobs, bs; Θ_device)`  
  - Θ_device: fio 스윕으로 획득한 4D 격자(ρr×qd×jobs×bs) + 선형보간 테이블

### 2.3 WA/RA 정의(Closed Ledger)
- `WA_stat = (WAL + Flush + Σ_ℓ CompWrite_ℓ) / UserWrite`  
- `WA_device = DeviceWrite / UserWrite`  
- `RA_comp = (Σ_ℓ CompRead_ℓ) / UserWrite` (선택: `RA_runtime = DeviceRead / UserWrite`)  
- **검산 목표**: 동일 런에서 위 항들이 물리적으로 **닫히는지** 확인(±10% 이내).

---

## 3. 구현 전략 (코드 작성 계획)

### 3.1 모듈 구조 & 역할
- `model/envelope.py`  
  - `class EnvelopeModel`: `from_json_path()`, `query(rho_r, qd, numjobs, bs_k, Br=None, Bw=None)`  
  - 선형보간(최대 4축), 선택적 `min(Br,Bw)` 클램프
- `model/v4_simulator.py`  
  - CLI: `--envelope_json`, `--config_yaml`, `--out_csv`  
  - 상태: `Q[ℓ]`(GiB), 입력: `ρr(t)`(초기엔 휴리스틱), 출력: `C_ℓ(t)`, `Beff(t)`
  - CSV 로그: `t_s, rho_r, Beff_mibs, Qℓ_GiB..., Cℓ_mibs...`
- `tools/device_envelope/`  
  - `run_envelope.sh`: fio 그리드 스윕(JSON)  
  - `parse_envelope.py`: JSON → CSV  
  - `fit_envelope.py`: CSV → `envelope_model.json`(격자+텐서)
- `tools/wa_ra_accounting/`  
  - `parse_rocksdb_log.py`: LOG에서 WAL/Flush/Comp(Read/Write) 추출(JSON)  
  - `closed_ledger.py`: JSON → `ledger.csv` (WA/RA, device 합산 옵션)
- `tools/validation/metrics.py`  
  - Truth vs Prediction → `MAPE`, `NRMSE` 계산

### 3.2 함수 시그니처(예시)
```python
class EnvelopeModel:
    @classmethod
    def from_json_path(cls, path: str) -> "EnvelopeModel": ...
    def query(self, rho_r: float, qd: int, numjobs: int, bs_k: int,
              Br: float|None=None, Bw: float|None=None) -> float: ...
```
```python
# v4_simulator.py (핵심 루프)
for t in range(steps):
    rho_r = rho_r_from_backlog(Q)           # 휴리스틱(초기) → 추후 로그 학습치 대체
    Beff = env.query(rho_r, qd, numjobs, bs_k, Br, Bw)
    C = [ (mu*l.k*eta) * Beff for each level ]
    update_backlog(Q, inflow, C, dt)
    dump_csv(...)
```

### 3.3 개발 순서
1) Envelope 보간기(순수 파이썬) → 단위테스트(경계·보간 정확도)  
2) v4 시뮬레이터 스켈레톤 → 간단 입력으로 smoke test  
3) LOG 파서 최소기능(WAL/Flush/Comp Read/Write) → `ledger.csv` 생성  
4) 검증 스크립트(metrics) → end-to-end 스모크  
5) (선택) ρr(t) 휴리스틱 개선: LOG 기반 추정으로 보정

---

## 4. 검증을 위한 실험 설계 (Validation Design)

### 4.1 실험 원칙
- **동일 런 단위의 회계 폐곡선**: ledger가 닫히는지부터 확인(±10%).
- **캘리브레이션과 검증의 분리**: Phase‑A로 엔벌롭과 상수 보정, Phase‑D로 **홀드아웃 런** 평가.
- **측정 환경 안정화**: NVMe 온도/전력 프로파일, 커널/FS 마운트 옵션 고정, 캐시·리클레임 영향 최소화(direct=1).

### 4.2 장치 엔벌롭 측정 (fio grid)
- 축: `ρr ∈ {0,25,50,75,100}%`, `iodepth ∈ {1,4,16,64}`, `numjobs ∈ {1,2,4}`, `bs ∈ {4,64,1024}KiB`
- 런타임: `ramp=10s, runtime=30s`, `ioengine=io_uring`, `direct=1`, `norandommap=1`, `randrepeat=0`
- 산출물: `device_envelope.csv` → `envelope_model.json`(4D 격자)  
- **검증 포인트**: `Beff ≤ min(Br,Bw)` 위반 시 클램프 여부/정책 기록

### 4.3 회계(ledger) 검산
- 소스: RocksDB LOG(+statistics), 선택적으로 iostat 요약 JSON  
- 산출: `ledger.csv` (열: user_write_bytes, wal, flush, Σcomp_write, Σcomp_read, device_write, device_read, WA/RA 파생치)  
- 합격선: `WA_stat ≈ WA_device`(±10%), GiB/GB·정규화 표기 충돌 없음

### 4.4 v4 예측 vs 실측 비교(홀드아웃)
- Truth: `ground_truth.csv`(시간-처리량), Pred: `sim_out.csv`  
- 지표: `MAPE`, `NRMSE`, (선택) Bland–Altman 편향 확인  
- 수용기준(초안): `MAPE ≤ 10–15%`

### 4.5 테스트 매트릭스(예시)
- DB 옵션 축: `max_background_jobs∈{4,8,16}`, `compression∈{none,zstd}`, `T(레벨배수)∈{8,10}`, `value_size∈{256,1024}`  
- 워크로드 축: `fillrandom`(기본), (선택) `overwrite`, `mixgraph`  
- 장치 축: `qd/numjobs/bs_k`는 엔벌롭 측정 격자 내/근처로 설정

---

## 5. 데이터·메타데이터 관리 (재현성)

- **RocksDB 커밋 SHA, 빌드 플래그**, `options.ini`, `db_bench` 커맨드라인 기록  
- **커널/FS 마운트**, 스케줄러, 전원/온도 상태 기록  
- `envelope_model.json`, `ledger.csv`, `sim_out.csv` 파일 해시와 타임스탬프 고정  
- (선택) `scripts/build_html.py`로 문서 HTML 변환: `PutModel_v4.html`

---

## 6. 위험요소·대응

- **LOG 포맷 차이** → 정규식 다중 버전 지원, 샘플 기반 유닛테스트  
- **NVMe 스로틀/온도** → 런 간 휴지, 전력모드 고정, 온도 로그 수집  
- **엔벌롭 외삽 위험** → 보간 격자 확장 또는 최근접 클램프, 경고 출력  
- **순환 검증 재발** → Phase‑A/Phase‑D 산출물 폴더 분리, 스크립트에서 교차사용 방지 체크

---

## 7. 타임라인 & 마일스톤(초안)

- **D+1**: fio 그리드 측정 → `envelope_model.json` 완성  
- **D+2**: `ledger.csv` 닫힘 확인(필요시 파서 보강)  
- **D+3**: v4 시뮬레이터 연결·초기 보정(μ, k, η, 클램프)  
- **D+4**: 홀드아웃 검증(MAPE/NRMSE), 문서/그림 업데이트  
- **D+5**: 릴리스 패키징(Plan/Spec/HTML + 데이터/옵션/스크립트)

---

## 8. 수용 기준 (Acceptance)

- (A1) 동일 런 ledger **닫힘**: `|WA_stat − WA_device| ≤ 10%`  
- (A2) 홀드아웃에서 `MAPE ≤ 10–15%`(내부 기준)  
- (A3) 문서/그림/표 단위·기호 일관성 100%  
- (A4) 재현성 메타데이터(옵션·커밋·커맨드라인 등) 부록 고정

---

## 9. 체크리스트

- [ ] fio 스윕 완료 → `envelope_model.json` 생성  
- [ ] LOG 파싱 → `ledger.csv` 생성(닫힘 확인)  
- [ ] v4 시뮬레이터 실행 → `sim_out.csv` 산출  
- [ ] `metrics.py`로 Truth vs Pred 평가  
- [ ] 문서/표/그림/메타데이터 정리 및 저장소 커밋

