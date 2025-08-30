# RocksDB의 Steady-State Put Rate: 모델, 수식, 그리고 시뮬레이션 코드

> 목적: RocksDB의 쓰기 성능(put, flush, compaction)을 **정량적으로** 분석하고, steady state에서 달성 가능한 **지속 put rate**와 **레벨별(compaction 단계별) I/O BW 분해**를 계산하는 방법을 정리합니다. 또한 초기 버스트(빈 DB에서 $S_{in} > S_{max}$) 상황에서 steady state로 **수렴**하는 조건과 레벨별 I/O를 근사하는 시뮬레이터 코드를 제공합니다.

---

## 0) 요약 (Key Takeaways)

* RocksDB의 내부 제어기(WriteController: slowdown/stop, `delayed_write_rate`)는 **정밀 목표 속도 추적**이 아니라 **붕괴 방지**와 **수용 가능한 범위로의 수렴**이 목표입니다.
* **지속 가능한 put 상한**은 저장장치/컴팩션 용량과 쓰기 앰플리피케이션(WA), 압축률(CR)에 의해 결정됩니다.
* 전형적 Leveled($T\!\approx\!10$, $L\!\approx\!5\!\sim\!7$)에서 $WA$는 \*\*7–10+\*\*로 관찰되며, \*\*디바이스 쓰기 BW 기준 put 비율은 대략 1/WA (≈ 7–14%)\*\*입니다. 혼합 R+W 기준으로는 그의 절반 수준(≈ 3–7%)이 현실적입니다. Universal(티어드)로 WA를 낮추면 크게 늘어날 수 있습니다.
* 평균 유입이 용량 이하라면($\lambda \le S_{max}$) steady state로 **수렴**합니다. 용량을 넘으면 트리거 경계에서 **출렁임**(slowdown↔stop)이 발생합니다.
* **레벨별 I/O 분해**는 $T$ (크기비), 레벨 수 $L$, 레벨별 압축률 $CR_i$로 근사 가능하며, 아래 시뮬레이터로 **L0 flush / L1..Lk / WAL** 단위의 읽기·쓰기 MiB/s와 장치 점유율(%)을 산출할 수 있습니다.

---

## 1) 시스템 모델과 기호 정의

### 1.1 쓰기 경로 요소

* **put** → memtable → **flush**(L0 SST 생성) → **compaction**(L1..Lk로 정렬 병합)
* **WAL**: 동일 디바이스에 기록되면 디바이스 쓰기를 추가로 소모합니다.

### 1.2 기호 (단위: 기본적으로 MiB/s 또는 “/user-byte” 계수)

* $B_w$: 장치 **지속 쓰기** BW
* $B_r$: 장치 **지속 읽기** BW
* $B_{eff}$: 혼합(R+W)에서의 유효 BW (선택)
* $CR$: 압축률(on-disk/user). 예) 0.5면 2:1 압축
* $WA$: on-disk 기준 **쓰기 앰플리피케이션**(flush+compaction으로 실제 기록된 바이트 / on-disk 바이트)
* $w_{wal}$: 동일 디바이스에 기록되는 WAL 바이트/유저바이트(동일 디바이스면 보수적으로 1.0, 분리 배치 시 0)
* $\eta$: 혼합 제약에서 읽기 가중(기본 1.0)
* $U$: 평균 put당 유저 바이트(키+값, 압축 전)

---

## 2) Steady-State 지속 put 상한 $S_{max}$

### 2.1 per-user 디바이스 요구 바이트 (근사)

유저 바이트 1을 처리할 때 디바이스 기준 요구:

$$
\begin{aligned}
\text{writes/user} &:\quad w_{req} = CR\cdot WA + w_{wal} \\
\text{reads/user}  &:\quad r_{req} = CR\cdot (WA-1) \quad (\text{compaction read가 flush write와 대칭이라는 근사})
\end{aligned}
$$

### 2.2 상한 (세 가지 바운드의 최소)

$$
S_{write} = \frac{B_w}{w_{req}},\qquad
S_{read}  = \frac{B_r}{r_{req}},\qquad
S_{mix}   = \frac{B_{eff}}{\,w_{req}+\eta\, r_{req}\,},
$$

$$
\boxed{\; S_{max} = \min(S_{write}, S_{read}, S_{mix})\;}
$$

**ops/s**로 환산: $\text{ops/s} = S_{max}\cdot 2^{20} / U$.

> 현실 팁: 실제 $WA$·$CR$은 워크로드/옵션에 따라 달라지므로, **rocksdb.stats 델타**(일정 구간 전후의 바이트 카운터 차)로 **경험 계수**를 구해 넣는 것이 가장 정확합니다.

### 2.3 Leveled/Universal에서의 $WA$ 감

* **Leveled**($T\!\approx\!10$, 레벨 수 $L$):

  $$
  WA_{write} \approx 1\,(\text{flush}) + \frac{T}{T-1}\cdot L \;\approx\; 1 + 1.11\cdot L \quad \Rightarrow \quad 7\text{–}10+ \text{ (전형)}
  $$
* **Universal(티어드)**: 튜닝과 데이터 특성에 따라 **2–6**까지 낮출 수 있으나, 읽기 앰프/레이지 머지 등에 따라 달라짐.

---

## 3) 제어기(WriteController)와 수렴 조건

* RocksDB는 **`pending_compaction_bytes`**, **L0 파일 개수** 등 백로그가 임계치를 넘으면 **slowdown**(지연)→**stop**(일시 정지)을 발동합니다.
* 목표는 **정밀 속도 유지**가 아니라 **컴팩션이 따라잡을 수 있는 범위로 유입을 낮추는 것**입니다.
* 평균 유입 $\lambda \le S_{max}$이면 **steady state(유한 백로그)** 로 수렴. $\lambda > S_{max}$이면 트리거 경계에서 **진동**·**스톨**이 증가합니다.

**운영 팁:**

* `RateLimiter`(background write MB/s)로 **컴팩션 몫**을 명시(예: 장치 쓰기의 60–70%).
* `delayed_write_rate` 또는 외부 토큰버킷으로 $S_{acc} \le S_{max}$를 보장.
* `max_background_jobs`, `max_subcompactions`, `compaction_readahead_size`로 **병렬도/효율** 확보.
* `level0_{slowdown,stop}_writes_trigger`, `soft/hard_pending_compaction_bytes_limit`는 **너무 촘촘하지 않게**(플래핑 방지).

---

## 4) 레벨별(compaction 단계별) I/O BW 분해 (Leveled)

### 4.1 가정

* 인접 레벨 크기비 $T$ (예: 10)
* 레벨 수 $L$ (L1..L$L$ 참여, L0는 flush-only)
* 레벨별 압축률 $CR_i$ (on-disk/user)
* $\alpha = \tfrac{T}{T-1}$ (겹침 재작성 계수; $T=10$이면 $\alpha\approx1.111$)

### 4.2 per-level 읽기/쓰기 (steady state, 유저 throughput $S$)

* L0 flush: $\;\text{Write}_{L0} = S\cdot CR_0,\quad \text{Read}_{L0}=0$
* 레벨 $i\ge1$:

  $$
  \text{Read}_i \approx S\cdot \big( CR_{i-1} + CR_i\,\alpha \big),\qquad
  \text{Write}_i \approx S\cdot CR_i\, (1+\alpha)
  $$
* 동일 디바이스의 WAL: $\text{Write}_{WAL} = S\cdot w_{wal}$

위 식을 합하면 총 읽기/쓰기와 장치 예산 $(B_r,B_w)$ 대비 점유율(%)을 구할 수 있습니다.

---

## 5) 초기 버스트: 빈 DB에서 $S_{in} > S_{max}$인 경우

### 5.1 왜 초기엔 더 빨라 보이나?

* 빈 DB에서는 깊은 레벨이 아직 없어 **유효 $WA(t)$** 가 작습니다(실질 요구 바이트가 적음) → 일시적으로 큰 입력을 소화.
* 레벨이 형성되며 $WA(t) \to WA_\infty$로 **상승** → **지속 한계** $S_{max}$로 **하향**.

### 5.2 깊이 기반 근사(ActiveDepth $d$)

* 깊이 $d$에서의 per-user 계수(유저 throughput $S$):

  $$
  \begin{aligned}
  w(d) &= CR_0 + w_{wal} + \sum_{i=1}^{d} CR_i\,(1+\alpha) \\
  r(d) &= \sum_{i=1}^{d} \big( CR_{i-1} + CR_i\,\alpha \big)
  \end{aligned}
  $$
* 깊이 $d$에서의 수용 상한:

  $$
  S_{max}(d)=\min\!\left(\frac{B_w}{w(d)},\;\frac{B_r}{r(d)},\;\frac{B_{eff}}{w(d)+\eta r(d)}\right)
  $$
* 컨트롤/외부 캡 $S_{cap}$를 고려한 실제 수용: $\;S_{acc}(d) = \min(S_{in}, S_{cap}, S_{max}(d))$
* 레벨별 I/O는 4.2식에 $S \leftarrow S_{acc}(d)$를 대입하여 계산.

### 5.3 백로그 동역학과 수렴 시간

* on-disk 백로그 $P(t)$ (MiB) 근사:

  $$
  \frac{dP}{dt} = S_{acc}(t)\, w(t) - C
  $$

  여기서 $C$는 컴팩션 **출력 쓰기 처리량**(MiB/s), $w(t)=CR\cdot WA(t)+w_{wal}$.
* **수렴 조건**: 어느 시점부터든 $S_{acc}(t)\,w(t) \le C$.
* 초기 백로그 $P_0$를 해소하는 데 걸리는 시간:

  $$
  t_{clear} \approx \frac{P_0}{\,C - S_{cap}\,w\,}\quad(\text{단 }C>S_{cap}\,w)
  $$

---

## 6) 실험 절차 (추천)

1. **장치 예산 측정**: fio 등으로 $B_w,B_r$ (필요 시 $B_{eff}$)를 **지속 부하** 기준으로 측정.
2. **경험 계수 추정**: 일정 구간(수십 초\~수분) 동안 쓰기 진행 후 `rocksdb.stats` 델타로 $CR,WA$ 근사.
3. **계산기**로 $S_{max}$ 산출 → **20–30% 헤드룸**을 두고 운영 캡 설정(외부 토큰버킷 또는 `delayed_write_rate`).
4. **레벨별 I/O**를 시뮬레이션하여 장치 점유율을 검토(읽기 서비스 여유 포함).

> 참고: WAL이 동일 디바이스라면 그만큼 쓰기 여유가 줄어듭니다. 가능하면 WAL 분리 고려.

---

## 7) 시뮬레이션/계산 코드 (Python, 표준 라이브러리)

아래 스니펫들은 독립 실행 가능한 단일 파일로 붙여넣어도 됩니다. `argparse` 등은 생략했고, 코드 상단 파라미터를 수정 후 실행하는 방식을 기본으로 합니다. (pandas 없이 표 출력)

### 7.1 Steady-State Put-Rate Estimator

```python
#!/usr/bin/env python3
"""Steady-state put-rate estimator for RocksDB.
Edit parameters in the CONFIG section and run.
"""
from math import inf

# ===== CONFIG =====
# Device budgets (MiB/s)
B_w   = 1000.0   # sustained write BW
B_r   = 2000.0   # sustained read BW
B_eff = 2500.0   # mixed R+W BW (set None to ignore)
eta   = 1.0      # read weight in mixed cap

# Workload / LSM parameters
avg_kv_bytes = 1024.0  # user bytes per PUT (key+value, pre-compression)
CR_list = [1.0, 0.7, 0.5, 0.33]  # on-disk/user compression ratio candidates
WA_list = [4, 6, 8, 10]          # write amplification (flush+compactions) per on-disk byte
wal_factor = 1.0                 # WAL bytes per user byte on the same device (0.0 if separate)

# ===== LOGIC =====

def bounds_for(CR: float, WA: float):
    w_req = CR*WA + wal_factor
    r_req = CR*max(WA-1.0, 0.0)
    s_w = (B_w / w_req) if w_req > 0 else inf
    s_r = (B_r / r_req) if r_req > 0 else inf
    s_m = (B_eff / (w_req + eta*r_req)) if (B_eff and (w_req + eta*r_req) > 0) else inf
    s_max = min(s_w, s_r, s_m)
    return s_w, s_r, s_m, s_max, w_req, r_req

print("CR\tWA\tReqWrite/u\tReqRead/u\tS_write\tS_read\tS_mix\tS_max\tops/s")
for CR in CR_list:
    for WA in WA_list:
        s_w, s_r, s_m, s_max, w_req, r_req = bounds_for(CR, WA)
        ops = (s_max*1048576.0)/avg_kv_bytes
        def f(x):
            return "inf" if x == inf else f"{x:.1f}"
        print(f"{CR:.2f}\t{WA:.2f}\t{w_req:.2f}\t\t{r_req:.2f}\t\t{f(s_w)}\t{f(s_r)}\t{f(s_m)}\t{f(s_max)}\t{ops:.0f}")
```

### 7.2 Per-Level I/O Breakdown (Leveled)

```python
#!/usr/bin/env python3
"""Per-level compaction I/O breakdown in steady state (Leveled model)."""

# ===== CONFIG =====
S_user = 150.0   # accepted user throughput (MiB/s)
T = 10           # size ratio
L = 6            # number of leveled levels (L1..L)
wal_factor = 1.0 # WAL on same device (0.0 if separate)
CR_default = 0.50
CR = [CR_default]*(L+1)  # CR0..CRL (on-disk/user)

B_w = 1000.0  # device write BW for % share (MiB/s)
B_r = 2000.0  # device read BW for % share (MiB/s)

# ===== LOGIC =====
alpha = T/(T-1.0)

rows = []
# L0 flush
l0_w = S_user*CR[0]
rows.append(("L0 (flush)", 0.0, l0_w))
# L1..L
for i in range(1, L+1):
    r_i = S_user*(CR[i-1] + CR[i]*alpha)
    w_i = S_user*(CR[i]*(1.0+alpha))
    rows.append((f"L{i}", r_i, w_i))
# WAL
rows.append(("WAL", 0.0, S_user*wal_factor))

# Print table
hdr = "Level                Read(MiB/s)   Write(MiB/s)   %ReadBW  %WriteBW"
print(hdr) ; print("-"*len(hdr))
rt, wt = 0.0, 0.0
for lvl, r, w in rows:
    rt += r; wt += w
    pr = (100.0*r/B_r) if B_r else 0.0
    pw = (100.0*w/B_w) if B_w else 0.0
    print(f"{lvl:16s}  {r:11.2f}   {w:12.2f}   {pr:6.1f}%   {pw:7.1f}%")
print("-"*len(hdr))
pr = (100.0*rt/B_r) if B_r else 0.0
pw = (100.0*wt/B_w) if B_w else 0.0
print(f"TOTAL               {rt:11.2f}   {wt:12.2f}   {pr:6.1f}%   {pw:7.1f}%")
```

### 7.3 초기 버스트→수렴 (깊이별 상한과 레벨별 I/O)

```python
#!/usr/bin/env python3
"""Transient-to-steady analysis when starting with S_in > S_max (empty DB)."""
from math import inf

# ===== CONFIG =====
# Device budgets
B_w   = 1000.0
B_r   = 2000.0
B_eff = 2500.0  # set None to ignore
eta   = 1.0

# LSM layout
T = 10
L = 6
CR_default = 0.50
CR = [CR_default]*(L+1) # CR0..CRL
wal_factor = 1.0

# Workload
S_in = 400.0   # offered user rate (MiB/s)
S_cap = None   # external/controller cap; if None, use S_max at full depth

# ===== LOGIC =====
alpha = T/(T-1.0)

def coeffs(depth):
    w = CR[0] + wal_factor
    r = 0.0
    for i in range(1, depth+1):
        r += (CR[i-1] + CR[i]*alpha)
        w += (CR[i]*(1.0+alpha))
    return w, r

def smax(depth):
    w, r = coeffs(depth)
    s_w = (B_w/w) if w>0 else inf
    s_r = (B_r/r) if r>0 else inf
    s_m = (B_eff/(w + eta*r)) if (B_eff and (w+eta*r)>0) else inf
    s = min(s_w, s_r, s_m)
    return s, s_w, s_r, s_m, w, r

# decide cap
Smax_full, *_ = smax(L)
if S_cap is None:
    S_cap = Smax_full

print("Depth  S_max  S_acc  TotRead  TotWrite  %R  %W  Bottleneck")
for d in range(1, L+1):
    S_d, S_w, S_r, S_m, w_c, r_c = smax(d)
    S_acc = min(S_in, S_cap, S_d)
    R = S_acc * r_c
    W = S_acc * w_c
    # bottleneck
    vals = [(S_w, 'write'), (S_r,'read'), (S_m,'mix')]
    bname = min(vals, key=lambda x: x[0])[1]
    print(f"{d:5d}  {S_d:5.1f}  {S_acc:5.1f}  {R:7.1f}  {W:8.1f}  {100*R/B_r:4.1f}%  {100*W/B_w:4.1f}%  {bname}")

# Example: per-level flows at a chosen depth
chosen_depth = L
S_d, *_ = smax(chosen_depth)
S_acc = min(S_in, S_cap, S_d)
print("\nPer-level flows at depth=", chosen_depth, "(S_acc=", f"{S_acc:.1f}", ")")
print("Level          Read(MiB/s)  Write(MiB/s)")
# L0
print(f"L0 (flush)     {0.0:11.2f}  {S_acc*CR[0]:11.2f}")
for i in range(1, L+1):
    if i <= chosen_depth:
        r_i = S_acc*(CR[i-1] + CR[i]*alpha)
        w_i = S_acc*(CR[i]*(1.0+alpha))
    else:
        r_i = 0.0; w_i = 0.0
    print(f"L{i:<2d}            {r_i:11.2f}  {w_i:11.2f}")
print(f"WAL            {0.0:11.2f}  {S_acc:11.2f}")
```

---

## 8) 한계와 주의점

* 본 모델은 **엔지니어링 근사**입니다. 실제 값은 **키 분포, 삭제율/TTL, subcompactions, 동시성, 파일 레이아웃, 블록 크기, readahead, 압축 CPU/압축률 변화, RateLimiter 설정** 등에 의해 달라집니다.
* Universal(티어드)의 경우 머지 정책/윈도/크기 임계에 따라 per-level이 아닌 **계층 병합 빈도 기반 모델**이 필요합니다(요청 시 별도 스니펫 제공 가능).
* WAL이 동일 디바이스일 때는 디바이스 쓰기 예산이 추가로 소모됩니다. 분리 배치 여부를 명확히 반영하세요.

---

## 9) GitHub에 올리는 방법 (권장 레이아웃)

```
rocksdb-put-model/
├─ README.md            # 이 문서
├─ scripts/
│  ├─ steady_state_put_estimator.py
│  ├─ per_level_breakdown.py
│  └─ transient_depth_analysis.py
└─ LICENSE
```

* `README.md`에 모델/수식 요약과 사용법을 정리하고, `scripts/`에 위의 세 스크립트를 파일로 저장하세요.
* 필요 시 Jupyter notebook으로 재구성하고, 실측치로 파라미터를 채워 **재현 그래프/표**를 포함하세요.

---

## 10) 운영 체크리스트

* [ ] fio로 $B_w,B_r,B_{eff}$ 측정(지속 부하)
* [ ] `rocksdb.stats` 델타로 $CR,WA$ 산정
* [ ] 계산기로 $S_{max}$ 산출 및 **헤드룸 20–30%** 반영해 캡 설정
* [ ] 레벨별 I/O 분해로 읽기 서비스 여유 확인
* [ ] `RateLimiter`와 `delayed_write_rate`로 $S_{acc}\le S_{max}$ 보장
* [ ] 트리거/리밋 파라미터에 히스테리시스 적용(플래핑 방지)

---
