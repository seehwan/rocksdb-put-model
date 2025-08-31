# RocksDB Put-Rate Model — Usage Guide

This repo provides small Python tools to **estimate steady-state put rate**, **break down per‑level compaction I/O**, and **plot** the results for RocksDB-like LSM settings.

> For the full theory/model and derivations, see **`PutModel.md`**.

---

## Requirements
- Python 3.8+
- matplotlib (for plots)

Install (optional virtualenv recommended):
```bash
python -m venv .venv && source .venv/bin/activate
pip install matplotlib
```

---

## Repo Layout
```
rocksdb-put-model/
├─ README.md              # ← You are here (Usage only)
├─ PutModel.md            # Full model + math + derivations + code
├─ LICENSE
├─ scripts/
│  ├─ steady_state_put_estimator.py      # S_max vs {CR,WA}
│  ├─ per_level_breakdown.py             # Per-level read/write MiB/s in steady state
│  ├─ transient_depth_analysis.py        # S_in > S_max startup → depth-wise S_max/S_acc
│  └─ rocksdb_put_viz.py                 # Matplotlib charts
└─ figs/                                  # Generated figures (PNG)
```

---

## Quick Start

### 1) Plot everything with defaults
```bash
python scripts/rocksdb_put_viz.py --run
# Creates PNGs under ./figs:
#   - smax_vs_WA.png
#   - per_level_writes.png
#   - per_level_reads.png
#   - depth_summary.png
```

### 2) Compute steady-state S_max table
```bash
python scripts/steady_state_put_estimator.py
```
- Edit **CONFIG** at the top of the script:
  - Device budgets: `B_w, B_r, B_eff` (MiB/s)
  - Workload/LSM: `CR_list, WA_list, wal_factor, avg_kv_bytes`
- The script prints a table with `S_max` and corresponding `ops/s`.

### 3) Per-level I/O breakdown (steady state)
```bash
python scripts/per_level_breakdown.py
```
- Set accepted user throughput: `S_user`
- Set LSM shape: `T, L, CR` (list: CR0..CRL), `wal_factor`
- Output: table of **Read/Write MiB/s** per stage (L0, L1..L, WAL) plus device % share.

### 4) Startup burst → steady state (S_in > S_max)
```bash
python scripts/transient_depth_analysis.py
```
- Set offered rate: `S_in`
- Optional external cap: `S_cap` (default = S_max at full depth)
- See how `S_max(depth)` and accepted `S_acc(depth)` evolve as deeper levels build.

---

## Tuning Checklist (operational)
- Measure device budgets with fio (**sustained** mixed workload).
- Estimate **CR** and **WA** from RocksDB `stats` **deltas** (bytes written/read vs user input).
- Use `steady_state_put_estimator.py` to compute **S_max**, then run with **20–30% headroom**.
- Reserve device share for background work with a **RateLimiter** (e.g., 60–70% of write BW).
- Prevent flapping: avoid overly tight `level0_{slowdown,stop}_writes_trigger`, use hysteresis.
- WAL on same device reduces write budget; separate if possible.

---

## Reproducibility
The default settings are conservative engineering **approximations**. For precise numbers in your environment:
1. Measure device `B_w, B_r, B_eff` under relevant IO depths and block sizes.
2. Derive `CR, WA` from your workload’s stats deltas over stable intervals.
3. Re-run the scripts and compare with production metrics.

---

## License
MIT — see `LICENSE`.
