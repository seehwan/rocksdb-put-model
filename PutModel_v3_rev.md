# PutModel v3 — Dynamic Compaction‑Aware Put‑Rate Model

*(This document is fully self‑contained and does not rely on prior versions.)*

---

## 1. Scope & Objectives
PutModel v3 predicts **time‑varying put throughput** and **device I/O usage** for a RocksDB‑like LSM storage engine under **leveled compaction** on a single storage device. It captures:

- Mixed read/write bandwidth limits and their interaction with device capabilities.
- Level‑wise asynchronous compactions and their capacity constraints.
- **Stall dynamics** driven by L0 file accumulation (slowdown/stop behavior).
- **Concurrency scaling** effects (limited parallelism, scheduler overheads).
- **Backlog evolution** during warm‑up and load transients.

The model is simulation‑based (discrete time), supports **log‑driven calibration**, and produces per‑level and aggregate time series (throughput, I/O shares, WA/RA, stall duty, L0 file count).

---

## 2. Entities & Notation
- Time: discrete steps of size Δ (seconds). Index by k (t = k·Δ).
- Levels: L0 … Ln. L0 receives flushes; compaction moves data Lℓ→Lℓ+1.
- Workload:
  - \(U(t)\): user data arrival rate (MiB/s) if no stall (target put rate).
  - \(S_{put}(t)\): realized put rate after stall.
  - \(\rho_r(t)\in[0,1]\): read fraction of device I/O mix, \(\rho_w(t)=1-\rho_r(t)\).
- Device capability:
  - \(B_r\): max sequential/random **read** bandwidth (MiB/s).
  - \(B_w\): max sequential/random **write** bandwidth (MiB/s).
  - Mixed effective bandwidth (harmonic aggregation):
    \[
      B_{eff}(t)\;=\;\frac{1}{\frac{\rho_r(t)}{B_r}+\frac{\rho_w(t)}{B_w}}\,.
    \]
- Level capacity shaping:
  - \(k_\ell\in(0,1]\): per‑level share weight (policy or measured share).
  - \(\mu_\ell^{eff}(t)\in(0,1]\): effective concurrency scaling for level ℓ.
  - Cap of level ℓ at time t: \(C_\ell(t)=k_\ell\,\mu_\ell^{eff}(t)\,B_{eff}(t)\).
- Level work demands (device I/O intents before capacity):
  - \(D^W_\ell(t)\): write demand (MiB/s) of level ℓ compactions.
  - \(D^R_\ell(t)\): read demand (MiB/s) of level ℓ compactions.
- Backlogs (unserved I/O): \(Q^W_\ell(t), Q^R_\ell(t)\) in MiB.
- L0 files: \(N_{L0}(t)\). Stall probability: \(p_{stall}(t)\in[0,1]\).

---

## 3. Model Assumptions
1. Single storage device; device R/W limits summarized by \(B_r, B_w\). Mixed usage follows the harmonic aggregation above.
2. Compactions are **asynchronous** and run concurrently across levels but are bounded by per‑level capacity \(C_\ell(t)\) and a **global device envelope** \(B_{eff}(t)\).
3. Put stalls are driven by L0 pressure: more L0 files → higher stall probability. We model this with a **smooth logistic** to reflect slowdown/stop thresholds.
4. Level demands can be **data‑driven** (from logs) or **geometry‑driven** (from compaction rules). The simulator accepts either: you may supply per‑level W/R **share functions** or **multipliers**.
5. Time discretization Δ is chosen so that state changes are small per step (e.g., 0.5–2 s typical). The simulator is explicit‑update with optional global rescaling to enforce device envelope.

---

## 4. Stall & Concurrency Functions
### 4.1 Stall probability \(p_{stall}(t)\)
Let \(n_0\) be the L0 slowdown threshold and \(n_1>n_0\) the stop threshold. A smooth mapping keeps the simulator differentiable and robust:
\[
  p_{stall}(t)=\sigma\!\left(\beta\,[\,N_{L0}(t)-n_*\,]\right), \quad n_*\triangleq\frac{n_0+n_1}{2},\; \beta>0,
\]
where \(\sigma(x)=\frac{1}{1+e^{-x}}\). Optionally clamp to \([0,p_{max}]\) if partial stalls are observed (\(p_{max}\le1\)).

Realized put:
\[
  S_{put}(t)\;=\;\bigl(1-p_{stall}(t)\bigr)\,U(t)\,.
\]

### 4.2 Concurrency scaling \(\mu_\ell^{eff}(t)\)
To capture diminishing returns with more threads/jobs (context switches, contention), use a logistic:
\[
  \mu_\ell^{eff}(t)\;=\;\mu_{min,\ell}\;+
  \frac{\mu_{max,\ell}-\mu_{min,\ell}}{1+\exp\{ -\gamma_\ell\,[\,k_s(t)-k_{0,\ell}\,] \}}\, ,
\]
with total active jobs \(k_s(t)\) (global or per‑level). Commonly \(\mu_{min,\ell}\in[0.3,0.6],\;\mu_{max,\ell}\le1\).

---

## 5. Demand Construction (Two Modes)
### 5.1 Log‑driven shares (recommended for validation)
Let \(\zeta^W_\ell(t)\) and \(\zeta^R_\ell(t)\) be per‑level write/read **share functions** (either constants or time series), obtained from logs. Define total compaction write/read pressures proportional to user rate:
\[
  X^W(t)\;=\;WA^*(t)\,S_{put}(t),\quad X^R(t)\;=\;RA^*(t)\,S_{put}(t),
\]
where \(WA^*(t), RA^*(t)\) are **external** (log‑measured) write/read amplification factors. Then
\[
  D^W_\ell(t)\;=\;\zeta^W_\ell(t)\,X^W(t),\quad
  D^R_\ell(t)\;=\;\zeta^R_\ell(t)\,X^R(t),\quad \sum_\ell\zeta^{\{W,R\}}_\ell(t)=1.
\]

### 5.2 Geometry‑driven multipliers (analytical mode)
Alternatively, specify per‑level multipliers \(a_\ell, b_\ell\) (read/write MiB per user MiB) from compaction geometry (fan‑out, overlap, compression). Then
\[
  D^W_\ell(t)=b_\ell\,S_{put}(t),\quad D^R_\ell(t)=a_\ell\,S_{put}(t),\quad
  WA^*(t)=\sum_\ell b_\ell,\; RA^*(t)=\sum_\ell a_\ell.
\]

Both modes can be mixed (e.g., use logs for major levels, geometry for minors).

---

## 6. Capacity Allocation & Backlog Updates
### 6.1 Device envelope
For a given \(\rho_r(t)\), the **device‑wide** feasible I/O is \(B_{eff}(t)\). Aggregate allocated read/write across all levels must satisfy:
\[
  \sum_\ell A^W_\ell(t)\;\le\;\rho_w(t)\,B_{eff}(t),\qquad
  \sum_\ell A^R_\ell(t)\;\le\;\rho_r(t)\,B_{eff}(t).
\]

### 6.2 Level caps
Each level is further limited by \(C_\ell(t)=k_\ell\,\mu_\ell^{eff}(t)\,B_{eff}(t)\). We first compute **tentative allocations** using per‑level caps:
\[
  \tilde{A}^W_\ell(t)=\min\{D^W_\ell(t)+Q^W_\ell(t)/\Delta,\;\rho_w(t)C_\ell(t)\},
\]
\[
  \tilde{A}^R_\ell(t)=\min\{D^R_\ell(t)+Q^R_\ell(t)/\Delta,\;\rho_r(t)C_\ell(t)\}.
\]
If the sum of \(\tilde{A}\) exceeds the device envelope, apply a **global scaling** factor \(\eta^{\{W,R\}}(t)\in(0,1]\) to all levels so that constraints are tight.

### 6.3 Backlog integration
With final allocations \(A^{\{W,R\}}_\ell(t)=\eta^{\{W,R\}}\,\tilde{A}^{\{W,R\}}_\ell(t)\), update backlogs:
\[
  Q^W_\ell(t+\!\Delta)\;=\;\max\{0,\;Q^W_\ell(t)\; +\; (D^W_\ell(t)-A^W_\ell(t))\,\Delta\},
\]
\[
  Q^R_\ell(t+\!\Delta)\;=\;\max\{0,\;Q^R_\ell(t)\; +\; (D^R_\ell(t)-A^R_\ell(t))\,\Delta\}.
\]

### 6.4 L0 file dynamics
Let \(f(t)\) be flush file creation rate (files/s), and let compaction L0→L1 remove files at rate \(g(t)\) (files/s). Then
\[
  N_{L0}(t+\!\Delta)=\max\{0,\;N_{L0}(t)+\bigl(f(t)-g(t)\bigr)\,\Delta\}.
\]
A convenient link is to derive \(f(t)\) from \(S_{put}(t)\) and memtable/target size; similarly derive \(g(t)\) from allocated L0 write \(A^W_{L0}(t)\) and file size.

---

## 7. Outputs & Derived Metrics
- **Throughput**: \(S_{put}(t)\).
- **Stall duty**: time average of \(p_{stall}(t)\) or fraction of steps with \(p_{stall}>0\).
- **Per‑level I/O shares**: \(A^W_\ell(t), A^R_\ell(t)\) and aggregates.
- **Amplifications** (model‑side):
  \[ WA(t)=\frac{\sum_\ell A^W_\ell(t)}{S_{put}(t)}\,,\qquad RA(t)=\frac{\sum_\ell A^R_\ell(t)}{S_{put}(t)}\,. \]
- **Backlogs**: \(Q^W_\ell(t), Q^R_\ell(t)\) trajectories.
- **L0 pressure**: \(N_{L0}(t)\) and its excursions beyond \(n_0,n_1\).

---

## 8. Calibration Pathways
1. **Device**: Measure \(B_r, B_w\) via fio (read/write separately). Optionally profile mixed workloads to sanity‑check the harmonic aggregation.
2. **Stall**: From RocksDB logs, extract slowdown/stop thresholds and empirical stall fraction; fit \(\beta, n_*\) (and \(p_{max}\) if used).
3. **Shares or multipliers**:
   - Log‑driven: compute per‑level \(\zeta^{\{W,R\}}_\ell\) as time‑averaged shares of total W/R bytes. Optionally allow them to vary slowly over time.
   - Geometry‑driven: compute \(a_\ell,b_\ell\) from compaction design (fan‑out, overlap, compression ratio, target file sizes).
4. **Concurrency**: From scheduling stats or experiments, fit \(\mu_{min,\ell},\mu_{max,\ell},\gamma_\ell,k_{0,\ell}\). If unknown, start with \(\mu_{min}=0.6, \mu_{max}=1\) and adjust.
5. **Flush/L0 mapping**: Identify memtable size and L0 target file size to convert MiB/s to files/s for \(f(t), g(t)\).

---

## 9. Simulation Loop (Pseudocode)
```text
initialize state: Q^W_ℓ=Q^R_ℓ=0, N_L0=N_L0_init
for t in [0, T) step Δ:
  # 1) Workload & stall
  U = U_target(t)
  p = p_stall(N_L0)
  S_put = (1 - p) * U

  # 2) Mix & device envelope
  ρ_r = rho_r(t); ρ_w = 1 - ρ_r
  B_eff = 1 / (ρ_r/B_r + ρ_w/B_w)

  # 3) Level demands (choose log- or geometry-driven)
  if log_driven:
    XW = WA_star(t) * S_put;  XR = RA_star(t) * S_put
    D^W_ℓ = ζ^W_ℓ(t) * XW;   D^R_ℓ = ζ^R_ℓ(t) * XR
  else:
    D^W_ℓ = b_ℓ * S_put;     D^R_ℓ = a_ℓ * S_put

  # 4) Tentative per-level caps
  C_ℓ = k_ℓ * μ_ℓ^{eff}(k_s) * B_eff
  W̃_ℓ = min(D^W_ℓ + Q^W_ℓ/Δ,  ρ_w * C_ℓ)
  R̃_ℓ = min(D^R_ℓ + Q^R_ℓ/Δ,  ρ_r * C_ℓ)

  # 5) Global rescale to respect device envelope
  η_W = min(1, ρ_w*B_eff / Σℓ W̃_ℓ)
  η_R = min(1, ρ_r*B_eff / Σℓ R̃_ℓ)
  A^W_ℓ = η_W * W̃_ℓ
  A^R_ℓ = η_R * R̃_ℓ

  # 6) Backlog updates
  Q^W_ℓ += (D^W_ℓ - A^W_ℓ) * Δ;  Q^W_ℓ = max(0, Q^W_ℓ)
  Q^R_ℓ += (D^R_ℓ - A^R_ℓ) * Δ;  Q^R_ℓ = max(0, Q^R_ℓ)

  # 7) L0 files (flush/compact)
  f = S_put / L0_file_size   # files/s
  g = A^W_{L0} / L0_file_size
  N_L0 = max(0, N_L0 + (f - g) * Δ)
end
```

---

## 10. Practical Defaults & Tips
- **Δ**: 1 s is a safe default. Reduce if oscillations alias.
- **ρ_r(t)**: If unknown, start with a small constant (e.g., 1–5%) and fit from logs.
- **k_ℓ**: Initialize proportional to observed shares; ensure \(\sum_ℓ k_ℓ ≤ 1\).
- **Stall**: If your system stalls abruptly, increase β; if it shows gradual slowdown, reduce β.
- **Warm‑up**: Set \(Q_ℓ=0\), \(N_{L0}=0\) for a cold start, or recover from snapshots to mimic mid‑run restarts.

---

## 11. Outputs to Inspect
1. **S_put(t)** vs observed put rate (MAPE/NRMSE).
2. **Aggregate I/O**: \(\sum A^W_ℓ, \sum A^R_ℓ\) vs device counters.
3. **Per‑level shares**: \(A^W_ℓ/\sum A^W, A^R_ℓ/\sum A^R\).
4. **WA/RA** time series.
5. **Stall duty** and **L0 trajectories** vs logs.
6. **Backlog decay** after load drop (should show exponential‑like relaxation when capacity > demand).

---

## 12. JSON Parameter Schema (example)
```json
{
  "device": {"B_r": 2400, "B_w": 1500},
  "sim": {"dt": 1.0, "T": 3600},
  "workload": {
    "U_target": {"kind": "piecewise", "points": [[0,180],[1200,220],[2400,180]]},
    "rho_r": {"kind": "constant", "value": 0.02}
  },
  "stall": {"n0": 8, "n1": 20, "beta": 0.6, "pmax": 1.0},
  "levels": [
    {"name": "L0", "k": 0.18, "mu_min": 0.7, "mu_max": 1.0, "gamma": 0.3, "k0": 3},
    {"name": "L1", "k": 0.22, "mu_min": 0.6, "mu_max": 1.0, "gamma": 0.25, "k0": 4},
    {"name": "L2", "k": 0.30, "mu_min": 0.6, "mu_max": 1.0, "gamma": 0.25, "k0": 4},
    {"name": "L3", "k": 0.30, "mu_min": 0.6, "mu_max": 1.0, "gamma": 0.25, "k0": 4}
  ],
  "shares": {
    "mode": "log",
    "WA_star": 2.8, "RA_star": 0.1,
    "zeta_w": {"L0": 0.08, "L1": 0.25, "L2": 0.45, "L3": 0.22},
    "zeta_r": {"L0": 0.05, "L1": 0.20, "L2": 0.55, "L3": 0.20}
  },
  "l0_files": {"file_size_mib": 64, "N0_init": 0}
}
```
*Switch to `mode:"geom"` with per‑level multipliers if you prefer geometry‑driven operation:*
```json
"shares": {
  "mode": "geom",
  "a": {"L0": 0.02, "L1": 0.10, "L2": 0.60, "L3": 0.28},
  "b": {"L0": 0.08, "L1": 0.25, "L2": 0.45, "L3": 0.22}
}
```

---

## 13. Quality Checks (Sanity/Conservation)
- **Device envelope**: \(\sum_ℓ A^W_ℓ ≤ \rho_w B_{eff}\) and \(\sum_ℓ A^R_ℓ ≤ \rho_r B_{eff}\) at every step (by construction after rescaling).
- **Share sums**: \(\sum_ℓ \zeta^{\{W,R\}}_ℓ = 1\) (log mode) or \(WA^*=\sum b_ℓ\), \(RA^*=\sum a_ℓ\) (geom mode).
- **Non‑negative states**: Backlogs and \(N_{L0}\) never negative.
- **Mass balance**: Over long windows, modeled WA/RA should match observed totals within tolerance (e.g., ±10–15%).

---

## 14. What the Model Captures / Limits
**Captures:** transient stalls, level contention, read/write mix effects, concurrency saturation, warm‑up and relaxation.  
**Not modeled explicitly:** per‑SST file pickers, compaction priority heuristics, multi‑device striping, compression CPU bottlenecks, and background read‑cache interactions. These can be partially absorbed into \(k_ℓ\), \(\mu_ℓ^{eff}\), and share/multiplier choices.

---

## 15. Minimal Reproduction Steps
1. Measure \(B_r, B_w\).  
2. Extract stall thresholds and level shares (or multipliers) from logs.  
3. Prepare a JSON like §12; load it into the simulator.  
4. Run for a horizon covering warm‑up → steady → perturbation.  
5. Export CSV; compute MAPE for \(S_{put}(t)\), WA/RA, level shares, and stall duty.

---

## 16. Extensions (Optional)
- Multi‑device envelope (per‑device \(B_r,B_w\) and routing matrix).  
- CPU‑bounded compaction: add a second resource envelope and take the minimum.  
- Priority scheduling: replace global rescale with weighted water‑filling.  
- Adaptive \(\rho_r(t)\) from cache hit/miss time series.

---

*End of self‑contained v3 specification.*

