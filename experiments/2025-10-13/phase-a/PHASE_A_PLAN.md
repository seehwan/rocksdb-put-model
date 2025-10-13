# Phase-A: Device Calibration and Envelope Measurement

**Phase:** A - Device Calibration  
**Status:** ⏳ Pending  
**Duration:** 4-6 hours

---

## 🎯 Objectives

1. Measure baseline device performance characteristics
2. Generate 4D device envelope model
3. Characterize physical degradation patterns
4. Establish performance boundaries

---

## 📋 Tasks

### Task 1: FIO Grid Sweep (Initial State)

**Objective:** Measure device performance across parameter space

**Parameters:**
```bash
ρr (Read Ratio):    {0, 25, 50, 75, 100}%
iodepth:            {1, 4, 16, 64}
numjobs:            {1, 2, 4}
bs (Block Size):    {4, 64, 1024} KiB

Total combinations: 180 measurements
Estimated time:     2-3 hours
```

**Command:**
```bash
cd /home/sslab/rocksdb-put-model/experiments/2025-10-13/phase-a
./scripts/run_fio_grid_sweep.sh --state initial --output data/initial_sweep.json
```

---

### Task 2: Device Envelope Generation

**Objective:** Create 4D interpolation model from measurements

**Steps:**
1. Parse FIO results
2. Build 4D grid (ρr, iodepth, numjobs, bs) → bandwidth
3. Generate envelope_model.json
4. Validate interpolation accuracy

**Command:**
```bash
python scripts/generate_envelope_model.py \
    --input data/initial_sweep.json \
    --output results/device_envelope.json
```

---

### Task 3: Degradation Measurement (Post-Workload)

**Objective:** Measure performance degradation after intensive workload

**Prerequisites:**
- Phase-B benchmark must be completed first
- OR run preliminary stress workload

**Command:**
```bash
./scripts/run_fio_grid_sweep.sh --state degraded --output data/degraded_sweep.json
```

---

### Task 4: Degradation Analysis

**Objective:** Quantify physical degradation rate

**Metrics:**
- Bandwidth degradation rate (%)
- Pattern consistency across workloads
- Phase-A vs Phase-B contribution

**Command:**
```bash
python scripts/analyze_degradation.py \
    --initial data/initial_sweep.json \
    --degraded data/degraded_sweep.json \
    --output results/degradation_analysis.json
```

---

## 📊 Expected Outputs

### Primary Deliverables

1. **device_envelope.json**
   - 4D interpolation model
   - Bandwidth lookup table
   - Interpolation parameters

2. **degradation_analysis.json**
   - Degradation rates by pattern
   - Statistical analysis
   - Confidence intervals

3. **PHASE_A_RESULTS.md**
   - Comprehensive analysis report
   - Visualizations
   - Key findings

### Visualizations

- Device performance heatmap
- Degradation comparison charts
- Parameter sensitivity plots
- Envelope model validation

---

## ✅ Success Criteria

- [ ] All 180 FIO measurements completed (initial)
- [ ] Device envelope model generated
- [ ] Envelope validation RMSE < 5%
- [ ] Degradation analysis complete
- [ ] All visualizations generated
- [ ] Results documented

---

## 🛠️ Scripts and Tools

### Required Scripts

```
phase-a/scripts/
├── run_fio_grid_sweep.sh          # FIO benchmark executor
├── parse_fio_results.py           # Result parser
├── generate_envelope_model.py     # Model generator
├── analyze_degradation.py         # Degradation analyzer
└── create_visualizations.py       # Plotting scripts
```

### Create Basic Scripts

```bash
# Create script directory structure
mkdir -p scripts

# Create placeholder scripts
touch scripts/run_fio_grid_sweep.sh
touch scripts/parse_fio_results.py
touch scripts/generate_envelope_model.py
touch scripts/analyze_degradation.py
touch scripts/create_visualizations.py

# Make shell scripts executable
chmod +x scripts/*.sh
```

---

## 📈 Validation

### Envelope Model Validation

**Cross-validation:**
- Hold out 10% of measurements
- Test interpolation accuracy
- Verify boundary conditions

**Acceptance Criteria:**
- RMSE < 5% of mean bandwidth
- No systematic bias
- Smooth interpolation (no discontinuities)

---

## ⚠️ Notes and Considerations

### Hardware Considerations

**Temperature Management:**
- Monitor device temperature
- Add cooldown periods between tests
- Target: Keep temp < 70°C

**I/O Scheduling:**
- Disable system I/O interference
- Set I/O scheduler to none or deadline
- Ensure no background processes

### Data Quality

**Measurement Stability:**
- Discard first 20% (ramp-up)
- Use last 80% for statistics
- Check for outliers

**Reproducibility:**
- Record all system settings
- Document environment variables
- Save complete command history

---

## 🔗 Dependencies

**Prerequisites:**
- Device accessible and formatted
- fio installed (version >= 3.x)
- Python 3.x with numpy, scipy
- Sufficient disk space (>100GB recommended)

**Outputs Used By:**
- Phase-C: Uses device_envelope.json for model predictions
- Phase-D: Uses degradation data for validation

---

*Phase-A Plan Version: 1.0*  
*Created: 2025-10-13*  
*Status: Ready for Execution*


