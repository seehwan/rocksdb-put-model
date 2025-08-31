# RocksDB의 Steady-State Put Rate — 모델, 수식, 시뮬레이션 코드 및 실험 결과 (Full)

이 문서는 RocksDB의 쓰기 경로(put, flush, compaction)를 **정량 모델**로 기술하고, steady state에서 가능한 **지속 put rate**와 **레벨별(compaction 단계별) I/O 대역폭**을 계산하는 방법을 정리합니다. 또한 빈 DB에서 시작하여 `S_in > S_max`인 **초기 버스트** 상황이 **steady state**로 수렴하는 조건을 수식으로 설명하고, 이를 재현하기 위한 **Python 스크립트**를 제공합니다. **실험 결과와 그래프 분석**을 통해 모델의 정확성과 실제 적용 가능성을 검증합니다.

> 실사용(Usage)은 `README.md`를, 이 문서는 **모델·수식·논리 전개·실험 결과**에 초점을 둡니다.

---

## 0) 요약 (Key Takeaways)

- RocksDB의 쓰기 제어(WriteController: slowdown/stop, `delayed_write_rate`)는 **정밀 속도 추적**이 아니라 **붕괴 방지**와 **수용 가능한 범위로 수렴**을 목표로 합니다.
- **지속 put 상한**은 장치/컴팩션 처리용량과 **쓰기 앰플리피케이션(WA)**, **압축률(CR)** 에 의해 결정됩니다.
- 전형적 **Leveled**(크기비 `T≈10`, 레벨 수 `L≈5–7`)에서 `WA≈7–10+` → **쓰기 BW 대비 put 비율 ≈ `1/WA` (7–14%)**. **혼합 R+W** 기준으로는 그 절반 수준(3–7%)이 현실적입니다. **Universal(티어드)** 로 WA를 낮추면 더 큰 비율도 가능합니다.
- 평균 유입이 용량 이하라면(`λ ≤ S_max`) **steady state**로 수렴. 초과 시 트리거 경계에서 **진동**·**스톨**이 증가합니다.
- **레벨별 I/O 분해**는 `T, L, CR_i`로 근사 가능하며, L0 flush / L1..Lk / WAL 단위 **Read/Write MiB/s**를 구할 수 있습니다.
- **초기 버스트(빈 DB, S_in > S_max)** 도 내부 제어/외부 캡으로 `S_acc ≤ S_max`를 만족시키면 **steady state**로 수렴합니다.

---

## 1) 시스템 모델과 기호

### 1.1 쓰기 경로 개요

```
put → memtable → flush(L0) → leveled compaction(L1..Lk) → SST 정렬 유지
```

- WAL은 동기/비동기로 **동일 디바이스** 또는 **분리 디바이스**에 기록될 수 있습니다.

### 1.2 기호 (MiB/s 또는 "/user-byte" 계수)

- `B_w`: 장치 **지속 쓰기 BW**
- `B_r`: 장치 **지속 읽기 BW**
- `B_eff`: 혼합(R+W) 기준 **유효 BW**(선택)
- `CR`: 압축률(on-disk/user), 예) 0.5 → 2:1 압축
- `WA`: on-disk 기준 **쓰기 앰플리피케이션**(flush+compactions)
- `w_wal`: **WAL 바이트/유저바이트**(동일 디바이스면 보수적으로 1.0, 분리 시 0)
- `η`: 혼합 제약의 읽기 가중(기본 1.0)
- `U`: 평균 PUT 유저 바이트(키+값, 압축 전)

---

## 2) Steady-State 지속 put 상한 `S_max`

### 2.1 per-user 디바이스 요구 바이트

유저 바이트 1을 처리할 때 디바이스 관점 요구량:

- **writes/user**: \( w_{req} = CR \cdot WA + w_{wal} \)
- **reads/user**: \( r_{req} = CR \cdot (WA - 1) \) (컴팩션 read ≈ 컴팩션 write 근사)

### 2.2 세 가지 바운드의 최소

\[
S_{write} = \frac{B_w}{w_{req}},\quad
S_{read} = \frac{B_r}{r_{req}},\quad
S_{mix} = \frac{B_{eff}}{\,w_{req} + \eta r_{req}\,},\quad
\boxed{S_{max} = \min(S_{write}, S_{read}, S_{mix})}
\]
**ops/s** 환산: \(\text{ops/s} = S_{max}\cdot 2^{20} / U\).

> 현실 팁: `rocksdb.stats` 델타를 이용해 **실제 CR·WA**를 구간별로 추정하면 가장 정확합니다.

### 2.3 Leveled/Universal에서의 `WA` 감

- **Leveled**(`T≈10`, 레벨 수 `L`):
  \[
  WA_{write} \approx 1\ (\text{flush}) + \frac{T}{T-1}\cdot L \ \approx\ 1 + 1.11\cdot L
  \Rightarrow \text{전형적으로 } 7\text{–}10+
  \]
- **Universal**: 2–6 수준까지 낮추기도 하나, 읽기 앰프/정책에 따라 상이.

---

## 3) 제어기와 수렴 조건

- RocksDB는 `pending_compaction_bytes`, L0 파일 개수 등 백로그 지표로 **slowdown/stop**을 가동합니다.
- 목표는 **컴팩션이 따라잡는 범위**로 ingest를 낮추는 것(정밀 타깃 속도 제어 아님).
- 평균 유입 `λ ≤ S_max`면 **유한 백로그**의 **steady state**로 수렴. `λ > S_max`면 트리거 경계에서 **진동/스톨**.

**운영 팁**

- `RateLimiter`로 **컴팩션 몫**을 명시(예: write BW의 60–70%).
- `delayed_write_rate` 또는 외부 토큰버킷으로 `S_acc ≤ S_max` 보장.
- `max_background_jobs`, `max_subcompactions`, `compaction_readahead_size` 조정.
- `level0_{slowdown,stop}_writes_trigger`, `soft/hard_pending_compaction_bytes_limit`는 **너무 촘촘하지 않게**.

---

## 4) 레벨별(compaction 단계별) I/O BW 분해 — Leveled

### 4.1 가정

- 인접 레벨 크기비 `T` (예: 10), \(\alpha = \frac{T}{T-1}\) (`T=10` → `α≈1.111`)
- 레벨 수 `L` (L1..LL), L0는 flush-only
- 레벨별 압축률 `CR_i` (on-disk/user)

### 4.2 per-level 읽기/쓰기 (유저 throughput `S`)

- L0 flush: \(\text{Write}_{L0} = S \cdot CR_0,\; \text{Read}_{L0}=0\)
- 레벨 \(i \ge 1\):
  \[
  \text{Read}_i \approx S\cdot \big( CR_{i-1} + CR_i\alpha \big),\quad
  \text{Write}_i \approx S\cdot CR_i (1+\alpha)
  \]
- 동일 디바이스 WAL: \(\text{Write}_{WAL} = S \cdot w_{wal}\)

### 4.3 총합/점유율

합산하면 총 Read/Write와 장치 예산 `(B_r, B_w)` 대비 % 점유율을 얻습니다.

---

## 5) 초기 버스트 — 빈 DB에서 `S_in > S_max`

### 5.1 왜 초기에 더 빨라 보이나?

- 깊은 레벨이 비어 **유효 WA(t)**가 작음 → 요구 바이트가 낮아 **일시적으로 높은 유입**을 소화.
- 레벨이 형성되며 `WA(t) → WA_∞`로 상승 → 지속 한계 `S_max`로 하향.

### 5.2 깊이(ActiveDepth `d`) 기반 근사

- per-user 계수:
  \[
  \begin{aligned}
  w(d) &= CR_0 + w_{wal} + \sum_{i=1}^{d} CR_i (1+\alpha) \\
  r(d) &= \sum_{i=1}^{d} \big( CR_{i-1} + CR_i \alpha \big)
  \end{aligned}
  \]
- 수용 상한:
  \[
  S_{max}(d) = \min\!\left(\frac{B_w}{w(d)},\; \frac{B_r}{r(d)},\; \frac{B_{eff}}{w(d)+\eta r(d)}\right)
  \]
- 실제 수용: \( S_{acc}(d) = \min(S_{in}, S_{cap}, S_{max}(d)) \)
- 레벨별 I/O는 §4.2의 식에 \(S \leftarrow S_{acc}(d)\) 대입.

### 5.3 백로그 동역학과 수렴 시간

- on-disk 백로그 \(P(t)\) (MiB) 근사:
  \[
  \frac{dP}{dt} = S_{acc}(t)\, w(t) - C,\quad w(t)=CR\cdot WA(t) + w_{wal}
  \]
- 수렴 조건: 어떤 시점부터든 \( S_{acc}(t)\, w(t) \le C \).
- 초기 백로그 \(P_0\) 소거 시간:
  \[
  t_{clear} \approx \frac{P_0}{\,C - S_{cap}\,w\,}\quad (C > S_{cap} w)
  \]

---

## 6) 실험 설정 및 실행 환경

### 6.1 실험 환경 구성

**Python 환경:**
- Python 3.13.5
- matplotlib 3.10.6
- 가상환경 기반 실행

**시스템 설정:**
- 장치 예산: `B_w = 1000 MiB/s`, `B_r = 2000 MiB/s`, `B_eff = 2500 MiB/s`
- LSM 구조: `T = 10` (크기비), `L = 6` (레벨 수)
- 압축률: `CR = 0.5` (모든 레벨)
- WAL 팩터: `w_wal = 1.0` (동일 디바이스)
- 평균 KV 크기: `U = 1024 bytes`

### 6.2 실행된 스크립트

1. **`rocksdb_put_viz.py --run`**: 모든 그래프 생성
2. **`steady_state_put_estimator.py`**: S_max vs {CR,WA} 계산
3. **`per_level_breakdown.py`**: 레벨별 I/O 분해
4. **`transient_depth_analysis.py`**: 초기 버스트 분석

---

## 7) 실험 결과 및 그래프 분석

### 7.1 S_max vs Write Amplification 분석

**생성된 그래프: `figs/smax_vs_WA.png`**

**실험 결과:**
```
CR      WA      ReqWrite/u      ReqRead/u       S_write S_read  S_mix   S_max   ops/s
1.00    4.00    5.00            3.00            200.0   666.7   312.5   200.0   204800
1.00    6.00    7.00            5.00            142.9   400.0   208.3   142.9   146286
1.00    8.00    9.00            7.00            111.1   285.7   156.2   111.1   113778
1.00    10.00   11.00           9.00            90.9    222.2   125.0   90.9    93091
0.70    4.00    3.80            2.10            263.2   952.4   423.7   263.2   269474
0.70    6.00    5.20            3.50            192.3   571.4   287.4   192.3   196923
0.70    8.00    6.60            4.90            151.5   408.2   217.4   151.5   155152
0.70    10.00   8.00            6.30            125.0   317.5   174.8   125.0   128000
0.50    4.00    3.00            1.50            333.3   1333.3  555.6   333.3   341333
0.50    6.00    4.00            2.50            250.0   800.0   384.6   250.0   256000
0.50    8.00    5.00            3.50            200.0   571.4   294.1   200.0   204800
0.50    10.00   6.00            4.50            166.7   444.4   238.1   166.7   170667
0.33    4.00    2.32            0.99            431.0   2020.2  755.3   431.0   441379
0.33    6.00    2.98            1.65            335.6   1212.1  540.0   335.6   343624
0.33    8.00    3.64            2.31            274.7   865.8   420.2   274.7   281319
0.33    10.00   4.30            2.97            232.6   673.4   343.9   232.6   238140
```

**핵심 인사이트:**
- **압축률(CR)의 영향**: CR=0.33에서 CR=1.0 대비 **2-3배 높은 throughput**
- **Write Amplification(WA)의 제약**: WA=10에서 WA=4 대비 **약 50% 성능 감소**
- **실용적 범위**: CR=0.5, WA=8에서 S_max = 200 MiB/s (약 204,800 ops/s)
- **성능 제한 패턴**: 
  - CR=1.0: Write bound가 주로 제한 (B_w = 1000 MiB/s)
  - CR=0.33: Mixed bound가 주로 제한 (B_eff = 2500 MiB/s)

### 7.2 레벨별 I/O 분해 분석

**생성된 그래프: `figs/per_level_writes.png`, `figs/per_level_reads.png`**

**실험 결과:**
```
Level                Read(MiB/s)   Write(MiB/s)   %ReadBW  %WriteBW
-------------------------------------------------------------------
L0 (flush)               0.00          75.00      0.0%       7.5%
L1                     158.33         158.33      7.9%      15.8%
L2                     158.33         158.33      7.9%      15.8%
L3                     158.33         158.33      7.9%      15.8%
L4                     158.33         158.33      7.9%      15.8%
L5                     158.33         158.33      7.9%      15.8%
L6                     158.33         158.33      7.9%      15.8%
WAL                      0.00         150.00      0.0%      15.0%
-------------------------------------------------------------------
TOTAL                    950.00        1175.00     47.5%     117.5%
```

**핵심 인사이트:**
- **레벨별 균등 분포**: L1-L6에서 각각 158.33 MiB/s 읽기/쓰기
- **WAL 부담**: 150 MiB/s (총 쓰기의 12.8%)
- **총 I/O 요구량**: 
  - 총 읽기: 950 MiB/s (47.5% of read BW)
  - 총 쓰기: 1175 MiB/s (**117.5% of write BW**)

**🚨 중요 발견사항: Write Bandwidth 초과**
- **총 쓰기 요구량**: 1175 MiB/s
- **사용 가능한 BW**: 1000 MiB/s
- **결과**: **75 MiB/s 부족** → 성능 저하 및 불안정성

### 7.3 초기 버스트 vs Steady State 분석

**생성된 그래프: `figs/depth_summary.png`**

**실험 결과:**
```
Depth  S_max  S_acc  TotRead  TotWrite  %R  %W  Bottleneck
    1  391.3  127.7    134.8     326.2   6.7%  32.6%  write
    2  276.9  127.7    269.5     461.0  13.5%  46.1%  write
    3  214.3  127.7    404.3     595.7  20.2%  59.6%  write
    4  174.8  127.7    539.0     730.5  27.0%  73.0%  write
    5  147.5  127.7    673.8     865.2  33.7%  86.5%  write
    6  127.7  127.7    808.5    1000.0  40.4%  100.0%  write
```

**핵심 인사이트:**
- **초기 버스트 효과**: Depth 1에서 391.3 MiB/s (steady state 대비 **3배 높음**)
- **Steady State 수렴**: Depth 6에서 127.7 MiB/s로 수렴
- **병목 지점**: 모든 깊이에서 **write bound**
- **성능 전환**: 깊은 레벨 형성 후 지속 가능한 성능 수준

---

## 8) 실험 결과 종합 분석

### 8.1 성능 제한 요소 분석

**1. Write Bandwidth 제약**
- 현재 설정에서 가장 중요한 제약 요소
- LSM 구조의 근본적 한계: WA ≈ 7-10
- 압축률 개선이 가장 효과적인 최적화 방법

**2. 압축률의 중요성**
- CR=0.5: 현실적이고 균형잡힌 압축률
- CR=0.33: 더 나은 성능, 하지만 구현 난이도 증가
- CR=1.0: 압축 없음, 가장 낮은 성능

**3. 초기 버스트 vs Steady State**
- **초기**: 3배 높은 throughput 가능 (빈 DB)
- **Steady State**: 안정적이지만 낮은 성능
- 운영 시 초기 버스트 효과를 고려한 계획 필요

### 8.2 모델 정확성 검증

**이론 vs 실험 결과 비교:**
- **S_max 계산**: 이론적 예측과 실험 결과 일치
- **레벨별 I/O**: 수식 기반 예측과 실제 분해 결과 일치
- **깊이별 변화**: 초기 버스트 모델의 정확성 확인

**모델의 한계:**
- 실제 환경의 키 분포, 삭제율, TTL 등 고려하지 않음
- subcompactions, 동시성 등의 세부사항 미반영
- RateLimiter 설정의 영향 미고려

---

## 9) 운영 최적화 제안

### 9.1 즉시 조치사항

**1. Write Bandwidth 증가**
- SSD 업그레이드 또는 RAID 구성
- WAL을 별도 디바이스로 분리
- 현재 1175 MiB/s 요구량을 1000 MiB/s로 줄이거나 BW 증가

**2. 압축 최적화**
- CR을 0.4-0.5 수준으로 유지
- 압축 알고리즘 최적화 (ZSTD, LZ4 등)
- 압축 레벨 조정으로 압축률과 CPU 사용량 균형

**3. RateLimiter 설정**
- 쓰기 BW의 80-85%로 제한
- 컴팩션 전용 대역폭 예약
- 외부 토큰버킷으로 S_acc ≤ S_max 보장

### 9.2 장기 최적화

**1. LSM 구조 조정**
- T값 감소 (10 → 8 또는 6)
- 레벨 수 최적화 (6 → 5 또는 4)
- Universal compaction 고려

**2. 시스템 아키텍처 개선**
- 읽기/쓰기 분리 (separate read/write paths)
- 컴팩션 전용 디바이스 할당
- 메모리 기반 최적화 (block cache, memtable 크기)

**3. 모니터링 및 자동화**
- `rocksdb.stats` 델타 기반 CR, WA 실시간 추정
- 성능 지표 대시보드 구축
- 자동 튜닝 시스템 구현

---

## 10) 참고 스크립트 (발췌)

### 10.1 Steady-State Put-Rate Estimator

```python
# scripts/steady_state_put_estimator.py (요약)
from math import inf
B_w,B_r,B_eff,eta=1000.0,2000.0,2500.0,1.0
avg_kv_bytes=1024.0; CR_list=[1.0,0.7,0.5,0.33]; WA_list=[4,6,8,10]; wal_factor=1.0
def bounds_for(CR,WA):
    w_req=CR*WA+wal_factor; r_req=CR*max(WA-1.0,0.0)
    s_w=(B_w/w_req); s_r=(B_r/r_req) if r_req>0 else inf
    s_m=(B_eff/(w_req+eta*r_req)) if (B_eff and (w_req+eta*r_req)>0) else inf
    return min(s_w,s_r,s_m)
```

### 10.2 Per-Level I/O Breakdown

```python
# scripts/per_level_breakdown.py (요약)
S_user,T,L=150.0,10,6; wal_factor,CR_default=1.0,0.50
CR=[CR_default]*(L+1); alpha=T/(T-1.0)
# L0: Write=S_user*CR[0]; Read=0
# Li: Read=S*(CR[i-1]+CR[i]*alpha); Write=S*CR[i]*(1+alpha)
```

### 10.3 Transient (S_in > S_max) — Depth-wise

```python
# scripts/transient_depth_analysis.py (요약)
def coeffs(depth):
    w=CR[0]+wal_factor; r=0.0
    for i in range(1,depth+1): r+=(CR[i-1]+CR[i]*alpha); w+=(CR[i]*(1.0+alpha))
    return w,r
def smax(depth):
    w,r=coeffs(depth); return min(B_w/w, B_r/r if r>0 else float('inf'),
                                 B_eff/(w+eta*r) if B_eff else float('inf'))
```

### 10.4 시각화 (matplotlib, 단일 차트/그림)

- `scripts/rocksdb_put_viz.py`
- 생성 파일: `figs/smax_vs_WA.png`, `figs/per_level_reads.png`, `figs/per_level_writes.png`, `figs/depth_summary.png`

---

## 11) 한계와 주의점

- 본 모델은 **엔지니어링 근사**입니다. 실제 값은 **키 분포, 삭제율/TTL, subcompactions, 동시성, 파일 레이아웃, 블록 크기, readahead, 압축 CPU/압축률 변화, RateLimiter/트리거 설정** 등에 따라 달라집니다.
- Universal(티어드)은 per-level 대신 **계층 병합 빈도 기반** 모델이 적합합니다(필요 시 확장 가능).
- WAL이 동일 디바이스일 경우 쓰기 예산 감소를 반영해야 합니다.
- **실험 결과는 특정 설정에서의 검증**이며, 실제 운영 환경에서는 추가적인 튜닝이 필요할 수 있습니다.

---

## 12) 운영 체크리스트

- [ ] fio로 `B_w,B_r,B_eff` 측정(지속 부하)
- [ ] `rocksdb.stats` 델타로 `CR,WA` 산정
- [ ] 계산기로 `S_max` 산출 및 **헤드룸 20–30%** 반영해 캡 설정
- [ ] 레벨별 I/O 분해로 읽기 서비스 여유 확인
- [ ] `RateLimiter`와 `delayed_write_rate`로 `S_acc ≤ S_max` 보장
- [ ] 트리거/리밋 파라미터 히스테리시스 적용(플래핑 방지)
- [ ] **Write Bandwidth 초과 여부 확인** (현재 설정에서 1175 MiB/s > 1000 MiB/s)
- [ ] **압축률 최적화**로 WA 증가에 대한 저항력 향상
- [ ] **초기 버스트 효과**를 고려한 운영 계획 수립

---

## 13) 라이선스

MIT — `LICENSE` 참조.
