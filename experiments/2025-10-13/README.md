# RocksDB Put-Rate Model Experiment - 2025-10-13

**Experiment Date:** October 13, 2025  
**Status:** 🚧 In Progress  
**Purpose:** New experimental validation and model refinement

---

## 📋 Experiment Overview

### Objectives

1. **Primary Goals:**
   - [ ] Validate V5.3 model in new conditions
   - [ ] Explore additional workload patterns
   - [ ] Refine model parameters based on new data
   - [ ] Test model robustness across different configurations

2. **Secondary Goals:**
   - [ ] Collect extended performance metrics
   - [ ] Analyze new phase transitions
   - [ ] Compare with previous experimental results

### Experimental Design

Based on the successful framework from 2025-09-12 experiment:

- **Phase-A:** Device Calibration and Envelope Measurement
- **Phase-B:** RocksDB Benchmark Execution
- **Phase-C:** Model Analysis and Comparison
- **Phase-D:** Validation and Accuracy Assessment
- **Phase-E:** Sensitivity Analysis and Optimization

---

## 📊 Experiment Phases

### Phase-A: Device Calibration
**Status:** ⏳ Pending  
**Directory:** `phase-a/`

**Tasks:**
- [ ] FIO grid sweep measurement
- [ ] Device envelope generation
- [ ] Baseline performance characterization
- [ ] Physical degradation analysis

**Expected Outputs:**
- `device_envelope.json`
- `phase_a_results.json`
- Performance degradation analysis report

---

### Phase-B: RocksDB Benchmark
**Status:** ⏳ Pending  
**Directory:** `phase-b/`

**Tasks:**
- [ ] Configure RocksDB workloads
- [ ] Execute FillRandom benchmark
- [ ] Monitor system metrics
- [ ] Collect performance logs

**Expected Outputs:**
- `fillrandom_results.json`
- RocksDB LOG files
- System metrics timeline

---

### Phase-C: Model Analysis
**Status:** ⏳ Pending  
**Directory:** `phase-c/`

**Tasks:**
- [ ] Apply V4 Device Envelope Model
- [ ] Apply V4.1 Temporal Model
- [ ] Apply V5.3 Initial-Optimized Model
- [ ] Generate prediction comparisons

**Expected Outputs:**
- Model prediction results
- Accuracy comparison charts
- Phase-specific analysis

---

### Phase-D: Validation
**Status:** ⏳ Pending  
**Directory:** `phase-d/`

**Tasks:**
- [ ] Calculate prediction errors (MAPE, NRMSE)
- [ ] Cross-validate with holdout data
- [ ] Statistical significance testing
- [ ] Model ranking update

**Expected Outputs:**
- Validation report
- Error analysis
- Model performance comparison

---

### Phase-E: Sensitivity Analysis
**Status:** ⏳ Pending  
**Directory:** `phase-e/`

**Tasks:**
- [ ] Parameter sensitivity analysis
- [ ] Robustness testing
- [ ] Edge case exploration
- [ ] Optimization recommendations

**Expected Outputs:**
- Sensitivity analysis report
- Optimization recommendations
- Future research directions

---

## 🗂️ Directory Structure

```
2025-10-13/
├── README.md                    # This file
├── EXPERIMENT_PLAN.md          # Detailed experiment plan
├── EXPERIMENT_SUMMARY.md       # Results summary (after completion)
│
├── phase-a/                    # Device Calibration
│   ├── data/                   # Raw measurement data
│   ├── scripts/                # Analysis scripts
│   ├── results/                # Processed results
│   └── PHASE_A_PLAN.md        # Phase-specific plan
│
├── phase-b/                    # RocksDB Benchmark
│   ├── data/                   # Benchmark data
│   ├── scripts/                # Benchmark scripts
│   ├── results/                # Performance results
│   └── PHASE_B_PLAN.md        # Phase-specific plan
│
├── phase-c/                    # Model Analysis
│   ├── data/                   # Model input data
│   ├── scripts/                # Model evaluation scripts
│   ├── results/                # Model predictions
│   └── PHASE_C_PLAN.md        # Phase-specific plan
│
├── phase-d/                    # Validation
│   ├── data/                   # Validation data
│   ├── scripts/                # Validation scripts
│   ├── results/                # Validation results
│   └── PHASE_D_PLAN.md        # Phase-specific plan
│
├── phase-e/                    # Sensitivity Analysis
│   ├── data/                   # Analysis data
│   ├── scripts/                # Analysis scripts
│   ├── results/                # Analysis results
│   └── PHASE_E_PLAN.md        # Phase-specific plan
│
├── data/                       # Shared experimental data
├── scripts/                    # Shared utility scripts
├── results/                    # Final consolidated results
└── logs/                       # Execution logs
```

---

## 🔧 Configuration

### Hardware Setup
- **Device:** TBD
- **Capacity:** TBD
- **File System:** TBD
- **RocksDB Version:** TBD

### Software Environment
- **OS:** Linux 6.8.0-79-generic
- **Python:** 3.x
- **Key Dependencies:**
  - RocksDB
  - fio
  - Python packages (numpy, pandas, scipy, matplotlib)

---

## 📈 Expected Outcomes

### Success Criteria
- [ ] All phases completed successfully
- [ ] Model accuracy >= 80% overall
- [ ] Validation MAPE <= 15%
- [ ] Comprehensive documentation generated
- [ ] Results reproducible

### Deliverables
1. Complete experimental dataset
2. Model validation results
3. Comprehensive analysis report
4. Updated model parameters (if needed)
5. Lessons learned and recommendations

---

## 🔗 Related Experiments

- **2025-09-12:** Previous comprehensive experiment (V5.3 champion established)
- **2025-09-09:** Earlier validation experiments
- **2025-09-08:** Initial framework development
- **2025-09-05:** Baseline experiments

---

## 📝 Notes

### Key Learnings from Previous Experiments

From **2025-09-12 Experiment:**
- V5.3 achieved 84.5% accuracy (new champion)
- Dual-structure performance decline validated
- Phase-specific optimization proved effective
- V4 remains excellent for simplicity (81.4%)

### Focus Areas for This Experiment

1. **Extended Validation:** Test models in new conditions
2. **Robustness:** Verify model stability across configurations
3. **Refinement:** Fine-tune parameters based on new data
4. **Documentation:** Comprehensive recording of all observations

---

## 🚀 Quick Start

### Running the Complete Experiment

```bash
# Navigate to experiment directory
cd /home/sslab/rocksdb-put-model/experiments/2025-10-13

# Execute phases sequentially
./run_phase_a.sh  # Device calibration
./run_phase_b.sh  # RocksDB benchmark
./run_phase_c.sh  # Model analysis
./run_phase_d.sh  # Validation
./run_phase_e.sh  # Sensitivity analysis

# Or run all phases
./run_all_phases.sh
```

### Individual Phase Execution

See individual phase `PHASE_X_PLAN.md` files for detailed instructions.

---

## 📞 Contact & Support

**Research Team:** Systems and Storage Lab  
**Project:** RocksDB Put-Rate Model  
**Documentation:** See main project README.md

---

*Experiment Status: Initialized*  
*Created: 2025-10-13*  
*Last Updated: 2025-10-13*


