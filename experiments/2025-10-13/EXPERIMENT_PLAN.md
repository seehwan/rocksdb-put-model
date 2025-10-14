# Experiment Plan - 2025-10-13

**Experiment ID:** EXP-2025-10-13  
**Created:** October 13, 2025  
**Status:** Planning

---

## 🎯 Objectives

### Primary Research Questions

1. **Model Validation:**
   - How do V4, V4.1, and V5.3 models perform on new workloads?
   - Are the accuracy results from 2025-09-12 reproducible?

2. **Model Robustness:**
   - How sensitive are models to configuration changes?
   - Which model is most stable across different conditions?

3. **Parameter Refinement:**
   - Can we further improve V5.3's accuracy?
   - Are there additional optimization opportunities?

4. **Workload Generalization:**
   - Do models generalize to different workload patterns?
   - What are the boundary conditions for model applicability?

---

## 📊 Experimental Design

### Overview

This experiment follows the proven 5-phase methodology:

```
Phase-A (Device)  →  Phase-B (Benchmark)  →  Phase-C (Analysis)
                                                    ↓
Phase-E (Sensitivity)  ←  Phase-D (Validation)
```

### Timeline

| Phase | Duration | Dependencies | Deliverables |
|-------|----------|--------------|--------------|
| **Phase-A** | 4-6 hours | None | Device envelope, degradation analysis |
| **Phase-B** | 2-4 hours | Phase-A complete | RocksDB performance data |
| **Phase-C** | 2-3 hours | Phase-A, Phase-B | Model predictions |
| **Phase-D** | 1-2 hours | Phase-C complete | Validation metrics |
| **Phase-E** | 2-3 hours | Phase-D complete | Sensitivity analysis |
| **Total** | 11-18 hours | - | Complete experiment report |

---

## 🔬 Phase-A: Device Calibration

### Objectives
- Measure device performance characteristics
- Generate device envelope model
- Characterize physical degradation

### Methodology

**1. FIO Grid Sweep**
```bash
# Parameters
ρr ∈ {0, 25, 50, 75, 100}%     # Read ratio
iodepth ∈ {1, 4, 16, 64}       # Queue depth
numjobs ∈ {1, 2, 4}            # Parallel jobs
bs ∈ {4, 64, 1024} KiB         # Block size

# Total combinations: 5 × 4 × 3 × 3 = 180 points
```

**2. Degradation Measurement**
- Initial device performance (fresh state)
- Post-workload performance (degraded state)
- Cross-pattern validation

### Success Criteria
- [ ] All 180 FIO measurements completed
- [ ] Device envelope JSON generated
- [ ] Degradation rate >= 50% observed
- [ ] Physical vs software effects separated

### Expected Outputs
- `device_envelope.json` - 4D interpolation model
- `phase_a_results.json` - Summary statistics
- `degradation_analysis.png` - Visualization
- `PHASE_A_RESULTS.md` - Detailed report

---

## 📈 Phase-B: RocksDB Benchmark

### Objectives
- Execute RocksDB workload
- Collect performance metrics
- Monitor system state evolution

### Workload Configuration

**Primary Workload: FillRandom**
```yaml
workload: fillrandom
record_size: 1040 bytes
duration: 120 minutes
operations: ~1.2 billion
db_growth: 0 → ~50GB
```

**Additional Workloads (Optional):**
- ReadRandomWriteRandom (mixed)
- Overwrite
- ReadWhileWriting

### Monitoring

**RocksDB Metrics:**
- QPS (operations per second)
- Write Amplification (WA)
- Read Amplification (RA)
- LSM-tree depth
- Compaction statistics

**System Metrics:**
- Device I/O bandwidth
- CPU utilization
- Memory usage
- I/O queue depth

### Success Criteria
- [ ] Benchmark completes successfully
- [ ] Full LOG file generated
- [ ] All metrics collected at 1-min intervals
- [ ] Performance degradation observed

### Expected Outputs
- `fillrandom_results.json` - Performance timeline
- `rocksdb.log` - Complete RocksDB LOG
- `system_metrics.csv` - System monitoring data
- `PHASE_B_RESULTS.md` - Analysis report

---

## 🤖 Phase-C: Model Analysis

### Objectives
- Apply all models to collected data
- Generate predictions
- Compare model performance

### Models to Evaluate

**1. V4 Device Envelope (Baseline)**
```python
# Single parameter model
predicted_s_max = (device_write_bw * 1024^2 / 1040) * U_phase
```

**2. V4.1 Temporal**
```python
# Temporal enhancement
predicted_s_max = V4_base * temporal_adjustment_factor
```

**3. V5.3 Initial-Phase-Optimized (Current Champion)**
```python
# Phase-specific optimization
predicted_s_max = V4_base * phase_specific_adjustment
```

### Analysis Tasks

1. **Data Preparation:**
   - Extract device bandwidth timeline
   - Calculate phase boundaries
   - Prepare model input features

2. **Model Execution:**
   - Run each model on experimental data
   - Generate phase-specific predictions
   - Record all intermediate results

3. **Comparison:**
   - Calculate prediction accuracy
   - Generate comparison visualizations
   - Identify model strengths/weaknesses

### Success Criteria
- [ ] All models executed successfully
- [ ] Predictions generated for all phases
- [ ] Comparison metrics calculated
- [ ] Visualizations created

### Expected Outputs
- `v4_predictions.json`
- `v4_1_predictions.json`
- `v5_3_predictions.json`
- `model_comparison.png`
- `PHASE_C_RESULTS.md`

---

## ✅ Phase-D: Validation

### Objectives
- Calculate prediction accuracy
- Validate against actual performance
- Update model rankings

### Validation Metrics

**Primary Metrics:**
- **MAPE** (Mean Absolute Percentage Error): Target <= 15%
- **NRMSE** (Normalized RMSE): Target <= 0.2
- **Phase-wise Accuracy**: Per-phase breakdown

**Secondary Metrics:**
- R² (coefficient of determination)
- MAE (Mean Absolute Error)
- Maximum error
- Prediction bias

### Analysis Methodology

```python
# For each model
for model in [V4, V4_1, V5_3]:
    # Calculate accuracy metrics
    mape = mean(|predicted - actual| / actual) * 100
    
    # Phase-specific analysis
    for phase in [initial, middle, final]:
        phase_accuracy = calculate_phase_accuracy(model, phase)
    
    # Statistical tests
    perform_significance_test(model)
```

### Success Criteria
- [ ] All metrics calculated
- [ ] Statistical significance tested
- [ ] Model ranking updated
- [ ] Validation report generated

### Expected Outputs
- `validation_metrics.json`
- `accuracy_comparison.png`
- `statistical_analysis.pdf`
- `PHASE_D_VALIDATION_REPORT.md`

---

## 🔍 Phase-E: Sensitivity Analysis

### Objectives
- Analyze parameter sensitivity
- Test model robustness
- Identify optimization opportunities

### Analysis Areas

**1. Parameter Sensitivity**
- Device bandwidth variations
- Phase boundary thresholds
- Utilization factors
- Temporal adjustments

**2. Robustness Testing**
- Configuration changes
- Workload variations
- Noise tolerance
- Edge cases

**3. Optimization Opportunities**
- Parameter tuning
- Phase detection improvements
- Context feature selection
- Ensemble strategies

### Methodology

```python
# Sensitivity analysis
for parameter in model_parameters:
    # Vary parameter ±20%
    test_values = parameter * [0.8, 0.9, 1.0, 1.1, 1.2]
    
    # Measure impact on accuracy
    sensitivity = calculate_sensitivity(parameter, test_values)
    
    # Generate recommendations
    recommend_adjustments(sensitivity)
```

### Success Criteria
- [ ] Sensitivity analysis complete
- [ ] Robustness tests passed
- [ ] Optimization recommendations generated
- [ ] Future research directions identified

### Expected Outputs
- `sensitivity_analysis.json`
- `robustness_test_results.json`
- `optimization_recommendations.md`
- `PHASE_E_ANALYSIS_REPORT.md`

---

## 📋 Data Management

### Data Collection

**Raw Data:**
- FIO measurement results (Phase-A)
- RocksDB LOG files (Phase-B)
- System monitoring data (Phase-B)

**Processed Data:**
- Device envelope model (Phase-A)
- Performance timeline (Phase-B)
- Model predictions (Phase-C)

**Analysis Results:**
- Validation metrics (Phase-D)
- Sensitivity analysis (Phase-E)

### Storage Structure

```
data/
├── raw/               # Original measurements
├── processed/         # Cleaned and processed data
├── models/            # Model parameters and state
└── results/           # Analysis outputs
```

### Backup Strategy
- Automatic backup after each phase
- Version control for all scripts
- Data integrity checksums
- Off-site backup of critical results

---

## 🛠️ Tools and Scripts

### Required Tools
- **fio:** Device I/O benchmarking
- **RocksDB:** Database benchmarking
- **Python 3.x:** Data analysis and modeling
- **matplotlib/seaborn:** Visualization

### Key Scripts

```
scripts/
├── phase_a/
│   ├── run_fio_grid_sweep.sh
│   ├── parse_fio_results.py
│   └── generate_envelope_model.py
├── phase_b/
│   ├── run_rocksdb_benchmark.sh
│   ├── monitor_system.py
│   └── parse_rocksdb_log.py
├── phase_c/
│   ├── apply_v4_model.py
│   ├── apply_v4_1_model.py
│   ├── apply_v5_3_model.py
│   └── compare_models.py
├── phase_d/
│   ├── calculate_validation_metrics.py
│   ├── statistical_analysis.py
│   └── generate_validation_report.py
└── phase_e/
    ├── sensitivity_analysis.py
    ├── robustness_testing.py
    └── generate_recommendations.py
```

---

## ⚠️ Risk Management

### Identified Risks

**1. Hardware Issues**
- **Risk:** Device thermal throttling
- **Mitigation:** Monitor temperature, add cooldown periods
- **Contingency:** Reduce workload intensity

**2. Software Issues**
- **Risk:** RocksDB crashes during long runs
- **Mitigation:** Checkpoint system, automatic recovery
- **Contingency:** Restart from last checkpoint

**3. Data Issues**
- **Risk:** Incomplete or corrupted measurements
- **Mitigation:** Validation checks, redundant measurements
- **Contingency:** Re-run affected measurements

**4. Time Constraints**
- **Risk:** Experiment duration exceeds available time
- **Mitigation:** Parallel execution where possible
- **Contingency:** Prioritize critical measurements

### Contingency Plans

| Issue | Detection | Response | Recovery Time |
|-------|-----------|----------|---------------|
| Thermal throttling | Temperature monitors | Pause + cooldown | 15-30 min |
| Disk full | Space monitoring | Cleanup or expand | 5-10 min |
| RocksDB crash | Process monitoring | Automatic restart | 2-5 min |
| Script failure | Error logging | Debug + fix | 10-30 min |

---

## 📊 Expected Results

### Quantitative Targets

**Model Accuracy:**
- V4: 80-85% overall
- V4.1: 75-80% overall
- V5.3: 83-87% overall (target: maintain/exceed 84.5%)

**Performance Metrics:**
- MAPE <= 15% for all models
- NRMSE <= 0.2
- Phase accuracy variance <= 20%

### Qualitative Goals

1. **Validation:** Confirm model rankings from previous experiments
2. **Insights:** Identify new optimization opportunities
3. **Documentation:** Comprehensive experiment documentation
4. **Reproducibility:** Full reproduction package

---

## 📚 Documentation Requirements

### During Experiment
- [ ] Real-time logging of all operations
- [ ] Screenshot/save important observations
- [ ] Document any deviations from plan
- [ ] Record all parameter changes

### Post-Experiment
- [ ] Complete EXPERIMENT_SUMMARY.md
- [ ] Generate comprehensive report
- [ ] Update model documentation
- [ ] Create visualization gallery

### Deliverables
1. Technical report (20-30 pages)
2. Executive summary (2-3 pages)
3. Dataset release package
4. Updated model implementations
5. Lessons learned document

---

## 🔄 Iterative Refinement

### Feedback Loops

**Intra-Experiment:**
- Adjust parameters based on Phase-A results
- Refine workload based on initial observations
- Optimize analysis based on data characteristics

**Post-Experiment:**
- Update model parameters
- Revise validation criteria
- Improve automation scripts
- Enhance documentation

---

## ✅ Acceptance Criteria

### Experiment Success

The experiment is considered successful if:

- [ ] All 5 phases completed
- [ ] Model accuracy targets met
- [ ] Validation MAPE <= 15%
- [ ] Complete documentation generated
- [ ] Results reproducible
- [ ] Key insights documented
- [ ] Recommendations for future work provided

### Quality Gates

**Phase Completion:**
- Each phase has comprehensive results
- All success criteria met
- Documentation complete
- Peer review passed (optional)

**Overall Quality:**
- Data integrity verified
- Statistical significance confirmed
- Reproducibility validated
- Documentation standards met

---

*Plan Version: 1.0*  
*Created: 2025-10-13*  
*Status: Ready for Execution*




