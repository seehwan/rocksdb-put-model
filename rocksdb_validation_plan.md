
# RocksDB Envelope Model — Validation & Experiment Plan
_Last updated: 2025-09-05 (KST)_

This document describes a practical, reproducible plan to validate the **PutModel/Envelope** for RocksDB: sustainable ingest ceiling \(S_{\max}\), per‑level WAF decomposition, and transient stabilization from an empty database.

---

## 0) Objectives & Hypotheses
**Objective.** Verify that the model’s predictions match a real RocksDB system.

**Hypotheses.**
1. The **ingest boundary** observed in the system matches the model’s \(S_{\max}\) within ±10–15%.
2. **Mass balance:** \(\sum_i \text{Write}_i \approx CR \cdot WA \cdot \text{user\_MB}\) within ±5–10%.
3. When changing knobs \((T, \text{compression}, \text{intra-L0}, \text{partial compaction})\), the **direction/trend** of \(S_{\max}\) and level‑wise WAF changes agrees with the model.

---

## 1) Metrics & Success Criteria
- **Envelope error:**  \(|S_{\max}^{meas} - S_{\max}^{pred}| / S_{\max}^{pred} \le \mathbf{10\%}\) (target; ≤15% acceptable).
- **Mass-balance error:**  \(\big|\sum_i \text{Write}_i - CR \cdot WA \cdot \text{user\_MB}\big| / (CR \cdot WA \cdot \text{user\_MB}) \le \mathbf{10\%}\).
- **Stabilization:** `pending_compaction_bytes` long‑run slope ≤ 0 at steady ingest.
- **Stall time:** below/near/above boundary shows expected monotone pattern (few ⇢ some ⇢ many).

---

## 2) Testbed & Software
- **Hardware:** 1× NVMe SSD (WAL on same device or separate second NVMe). Dedicated machine preferred.
- **OS/FS:** Linux (5.x+), ext4 or XFS, `noatime` recommended.
- **RocksDB build:** recent release; enable stats.
- **Logging:** `stats_dump_period_sec=60`, `statistics=true`, `report_bg_io_stats=true`.

> Tip: Keep an **options file** under version control for reproducibility.

---

## 3) Device Calibration (Phase‑A)
Measure device limits for **write, read, and mixed** workloads using `fio` (example: `bs=128k, iodepth=32`).
```bash
# Write limit → B_w
fio --name=w --filename=/dev/nvme0n1 --rw=write --bs=128k --iodepth=32 \
    --numjobs=1 --time_based=1 --runtime=60

# Read limit → B_r
fio --name=r --filename=/dev/nvme0n1 --rw=read --bs=128k --iodepth=32 \
    --time_based=1 --runtime=60

# Mixed read:write = 50:50 → B_eff(@ρ=0.5)
fio --name=rw --filename=/dev/nvme0n1 --rw=rw --rwmixread=50 --bs=128k \
    --iodepth=32 --time_based=1 --runtime=60
```
- Choose \(B_w\) from the write run, \(B_r\) from the read run, \(B_{\mathrm{eff}}\) from the mixed run closest to your expected mixture.
- Set coupling \(\eta \in [0.3, 0.7]\) (default 0.5).

---

## 4) RocksDB Configuration (Leveled baseline)
Minimal leveled profile (example; tune to your HW):
```ini
# options-leveled.ini
compaction_style=kCompactionStyleLevel
compaction_pri=kMinOverlappingRatio

# Compression
compression=kSnappy
bottommost_compression=kZSTD

# Threads / jobs (match CPU & SSD)
max_background_jobs=12
max_subcompactions=4

# Logging & stats
statistics=true
report_bg_io_stats=true
stats_dump_period_sec=60

# (Optional) Protect reads
rate_limiter_bytes_per_sec=0   # set >0 to cap background IO if needed

# L0 triggers (tune to device; examples)
level0_slowdown_writes_trigger=20
level0_stop_writes_trigger=24
```
> For **Universal** compaction, use a different overlap model; the envelope form still applies.

---

## 5) Empty → Steady Transient (Phase‑B)
1. Create an empty DB. Run `db_bench` with a **nearly constant ingest** target.
```bash
# RocksDB 10.7.0+ 호환 옵션 파일 생성
cat > options-leveled.ini << 'EOF'
[DBOptions]
db_path=/rocksdb/data
wal_dir=/rocksdb/wal
max_open_files=2048
keep_log_file_num=3
statistics=true
report_bg_io_stats=true
stats_dump_period_sec=60
bytes_per_sync=1048576
wal_bytes_per_sync=1048576
use_direct_reads=true
use_direct_io_for_flush_and_compaction=true
compaction_readahead_size=0
rate_limiter_bytes_per_sec=0

[CFOptions "default"]
compaction_style=kCompactionStyleLevel
compaction_pri=kMinOverlappingRatio
num_levels=7
level_compaction_dynamic_level_bytes=false
max_bytes_for_level_multiplier=10
target_file_size_base=268435456
target_file_size_multiplier=1
max_bytes_for_level_base=2684354560
compression=kSnappy
bottommost_compression=kZSTD
write_buffer_size=268435456
max_write_buffer_number=3
min_write_buffer_number_to_merge=1
enable_pipelined_write=true
allow_concurrent_memtable_write=true
max_background_jobs=12
max_subcompactions=4
level0_file_num_compaction_trigger=4
level0_slowdown_writes_trigger=20
level0_stop_writes_trigger=36
EOF

./db_bench --options_file=options-leveled.ini \
  --benchmarks=fillrandom --num=200000000 --value_size=1024 --threads=8 \
  --db=/rocksdb/data --wal_dir=/rocksdb/wal --statistics=1
```
2. Monitor: `pending_compaction_bytes`, L0 file count, stall/slowdown counters.
3. **Stabilization** achieved when `pending_compaction_bytes` no longer increases over long windows.

---

## 6) Per‑Level WAF Mass Balance (Phase‑C)
Parse **Compaction Stats** from the LOG to obtain per‑level bytes and WAF:
```bash
python scripts/waf_analyzer.py --log /path/to/LOG \
  --user-mb <MB_written_in_same_window> --out-dir out --plot
```
- Check: \(\sum_i \text{Write}_i \approx CR \cdot WA \cdot \text{user\_MB}\) (±5–10%).

---

## 7) Envelope Boundary S_max (Phase‑D)
1. From the same window, estimate **CR** and **WA** (Compaction Stats summary).
2. Compute the predicted boundary:
```bash
python scripts/smax_calc.py --cr <CR> --wa <WA> \
  --bw <B_w> --br <B_r> --beff <B_eff> --eta 0.5 --wwal 0
```
3. Sweep ingest around the prediction: \(0.9\times\), \(1.0\times\), \(1.1\times S_{\max}^{pred}\).
   - Below: backlog bounded; minimal slowdown.
   - Near: occasional write controller activations.
   - Above: backlog rises; slowdown/stall frequent.

---

## 8) Sensitivity / Ablations (Phase‑E)
Change one knob at a time and repeat Phases C–D:
- **Size ratio \(T\)**: 8 ↔ 10
- **Compression profile**: (mid=Snappy, bottom=ZSTD) ↔ (all Snappy)
- **Intra‑L0**: on ↔ off
- **Partial compaction**: on ↔ off
- **WAL placement**: same device ↔ separate device (separate → \(w_{wal}\to 0\))

**Expected trends** (examples):
- Stronger bottommost compression → **CR↓ (physical bytes)** → **WAF mass same**, but **device write burden per user byte↓**, typically **S_max↑**.
- Enabling Intra‑L0 during bursts → **WAF\_L0↑(≈+1)** but faster L0 file reduction → **stall risk↓**.

---

## 9) Data Collection & Analysis
- Save: LOG, `out/waf_per_level.csv`, `summary.json`, fio results, ingest targets/achieved, stall statistics.
- Compute errors:
  - \(e_{S_{\max}} = \frac{|S_{\max}^{meas}-S_{\max}^{pred}|}{S_{\max}^{pred}}\)
  - \(e_{\text{mass}} = \frac{|\sum \text{Write}_i - CR\cdot WA \cdot user\_MB|}{CR\cdot WA \cdot user\_MB}\)
- Report trends: \(\Delta S_{\max}, \Delta \text{WAF}_i\) signs vs. model predictions.

---

## 10) Risks & Mitigations
| Risk | Symptom | Mitigation |
|---|---|---|
| Background IO noise | Irregular boundary / large variance | Isolate device; single‑tenant runs |
| Thermal throttling | Throughput decay over time | Short repeated runs; monitor temperatures |
| FS cache effects | Over‑optimistic read figures | Data > RAM; drop_caches between runs |
| Scheduler jitter | High variance across runs | ≥3 repetitions; report median + IQR |
| Misconfigured options | Non‑reproducible results | Version‑controlled options file |

---

## 11) Report Template
- **Table 1**: Device calibration \(B_w, B_r, B_{\mathrm{eff}}\) (with fio parameters)
- **Table 2**: \(S_{\max}\) predicted vs. measured (mean±std, rel. error)
- **Figure 1**: `pending_compaction_bytes` over time (stabilization)
- **Figure 2**: Per‑level WAF bar plot + mass‑balance check
- **Table 3**: Sensitivity matrix (case → trend agreement ✓/✗)

---

## 12) Artifacts
- Validation kit (scripts + quick README): **`rocksdb_validation_kit.zip`**
- Modeling & references pack (BibTeX, stability box): **`rocksdb_putmodel_pack.zip`**

> If you need an options file for `db_bench` and `fio` jobfiles, ask and we’ll append them here.

---

### Appendix A. Quick Commands
```bash
# Per-level WAF from LOG
python scripts/waf_analyzer.py --log /path/to/LOG --user-mb 10240 --out-dir out --plot

# S_max prediction
python scripts/smax_calc.py --cr 1.6 --wa 12.0 --bw 1200 --br 1800 --beff 1300 --eta 0.5 --wwal 0
```
