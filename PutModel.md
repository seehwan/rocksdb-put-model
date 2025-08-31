# RocksDB의 Steady-State Put Rate — 모델, 수식, 시뮬레이션 코드 (Full)

이 문서는 RocksDB의 쓰기 경로(put, flush, compaction)를 **정량 모델**로 기술하고, steady state에서 가능한 **지속 put rate**와 **레벨별(compaction 단계별) I/O 대역폭**을 계산하는 방법을 정리합니다. 또한 빈 DB에서 시작하여 `S_in > S_max`인 **초기 버스트** 상황이 **steady state**로 수렴하는 조건을 수식으로 설명하고, 이를 재현하기 위한 **Python 스크립트**를 제공합니다.

> 실사용(Usage)은 `README.md`를, 이 문서는 **모델·수식·논리 전개**에 초점을 둡니다.

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

### 1.2 기호 (MiB/s 또는 “/user-byte” 계수)

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

- **writes/user**: \( w*{req} = CR \cdot WA + w*{wal} \)
- **reads/user**: \( r\_{req} = CR \cdot (WA - 1) \) (컴팩션 read ≈ 컴팩션 write 근사)

### 2.2 세 가지 바운드의 최소

\[
S*{write} = \frac{B_w}{w*{req}},\quad
S*{read} = \frac{B_r}{r*{req}},\quad
S*{mix} = \frac{B*{eff}}{\,w*{req} + \eta r*{req}\,},\quad
\boxed{S*{max} = \min(S*{write}, S*{read}, S*{mix})}
\]
**ops/s** 환산: \(\text{ops/s} = S\_{max}\cdot 2^{20} / U\).

> 현실 팁: `rocksdb.stats` 델타를 이용해 **실제 CR·WA**를 구간별로 추정하면 가장 정확합니다.

### 2.3 Leveled/Universal에서의 `WA` 감

- **Leveled**(`T≈10`, 레벨 수 `L`):
  \[
  WA\_{write} \approx 1\ (\text{flush}) + \frac{T}{T-1}\cdot L \ \approx\ 1 + 1.11\cdot L
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
  \text{Write}\_i \approx S\cdot CR_i (1+\alpha)
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
  w(d) &= CR*0 + w*{wal} + \sum*{i=1}^{d} CR_i (1+\alpha) \\
  r(d) &= \sum*{i=1}^{d} \big( CR\_{i-1} + CR_i \alpha \big)
  \end{aligned}
  \]
- 수용 상한:
  \[
  S*{max}(d) = \min\!\left(\frac{B_w}{w(d)},\; \frac{B_r}{r(d)},\; \frac{B*{eff}}{w(d)+\eta r(d)}\right)
  \]
- 실제 수용: \( S*{acc}(d) = \min(S*{in}, S*{cap}, S*{max}(d)) \)
- 레벨별 I/O는 §4.2의 식에 \(S \leftarrow S\_{acc}(d)\) 대입.

### 5.3 백로그 동역학과 수렴 시간

- on-disk 백로그 \(P(t)\) (MiB) 근사:
  \[
  \frac{dP}{dt} = S*{acc}(t)\, w(t) - C,\quad w(t)=CR\cdot WA(t) + w*{wal}
  \]
- 수렴 조건: 어떤 시점부터든 \( S\_{acc}(t)\, w(t) \le C \).
- 초기 백로그 \(P*0\) 소거 시간:
  \[
  t*{clear} \approx \frac{P*0}{\,C - S*{cap}\,w\,}\quad (C > S\_{cap} w)
  \]

---

## 6) 실험 절차

1. **장치 예산 측정**: fio로 `B_w, B_r, B_eff`(혼합)를 **지속 부하**에서 측정.
2. **경험 계수**: `rocksdb.stats` 델타로 `CR, WA` 추정(구간 기준).
3. **S_max 계산**: 헤드룸 20–30% 반영하여 운영 캡 설정(외부 토큰버킷/`delayed_write_rate`).
4. **레벨별 I/O** 시뮬레이션: 읽기 서비스 여유/리미터 비중 검토.

---

## 7) 참고 스크립트 (발췌)

### 7.1 Steady-State Put-Rate Estimator

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

### 7.2 Per-Level I/O Breakdown

```python
# scripts/per_level_breakdown.py (요약)
S_user,T,L=150.0,10,6; wal_factor,CR_default=1.0,0.50
CR=[CR_default]*(L+1); alpha=T/(T-1.0)
# L0: Write=S_user*CR[0]; Read=0
# Li: Read=S*(CR[i-1]+CR[i]*alpha); Write=S*CR[i]*(1+alpha)
```

### 7.3 Transient (S_in > S_max) — Depth-wise

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

### 7.4 시각화 (matplotlib, 단일 차트/그림)

- `scripts/rocksdb_put_viz.py`
- 생성 파일: `figs/smax_vs_WA.png`, `figs/per_level_reads.png`, `figs/per_level_writes.png`, `figs/depth_summary.png`

---

## 8) 한계와 주의점

- 본 모델은 **엔지니어링 근사**입니다. 실제 값은 **키 분포, 삭제율/TTL, subcompactions, 동시성, 파일 레이아웃, 블록 크기, readahead, 압축 CPU/압축률 변화, RateLimiter/트리거 설정** 등에 따라 달라집니다.
- Universal(티어드)은 per-level 대신 **계층 병합 빈도 기반** 모델이 적합합니다(필요 시 확장 가능).
- WAL이 동일 디바이스일 경우 쓰기 예산 감소를 반영해야 합니다.

---

## 9) 운영 체크리스트

- [ ] fio로 `B_w,B_r,B_eff` 측정(지속 부하)
- [ ] `rocksdb.stats` 델타로 `CR,WA` 산정
- [ ] 계산기로 `S_max` 산출 및 **헤드룸 20–30%** 반영해 캡 설정
- [ ] 레벨별 I/O 분해로 읽기 서비스 여유 확인
- [ ] `RateLimiter`와 `delayed_write_rate`로 `S_acc ≤ S_max` 보장
- [ ] 트리거/리밋 파라미터 히스테리시스 적용(플래핑 방지)

---

## 10) 라이선스

MIT — `LICENSE` 참조.
