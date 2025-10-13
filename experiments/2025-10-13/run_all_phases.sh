#!/bin/bash

# Run All Phases - Complete Experiment Execution
# Experiment: 2025-10-13
# Usage: ./run_all_phases.sh

set -e  # Exit on error

EXPERIMENT_DIR="/home/sslab/rocksdb-put-model/experiments/2025-10-13"
LOG_DIR="${EXPERIMENT_DIR}/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p "${LOG_DIR}"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Start experiment
log "========================================="
log "RocksDB Put-Rate Model Experiment"
log "Experiment Date: 2025-10-13"
log "========================================="
echo

# Phase-A: Device Calibration
log "Phase-A: Device Calibration"
log "Expected Duration: 4-6 hours"
echo
read -p "Start Phase-A? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting Phase-A..."
    if bash "${EXPERIMENT_DIR}/run_phase_a.sh" 2>&1 | tee "${LOG_DIR}/phase_a.log"; then
        success "Phase-A completed successfully"
    else
        error "Phase-A failed!"
        exit 1
    fi
else
    warning "Phase-A skipped"
fi
echo

# Phase-B: RocksDB Benchmark
log "Phase-B: RocksDB Benchmark"
log "Expected Duration: 2-4 hours"
echo
read -p "Start Phase-B? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting Phase-B..."
    if bash "${EXPERIMENT_DIR}/run_phase_b.sh" 2>&1 | tee "${LOG_DIR}/phase_b.log"; then
        success "Phase-B completed successfully"
    else
        error "Phase-B failed!"
        exit 1
    fi
else
    warning "Phase-B skipped"
fi
echo

# Phase-C: Model Analysis
log "Phase-C: Model Analysis"
log "Expected Duration: 2-3 hours"
echo
read -p "Start Phase-C? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting Phase-C..."
    if bash "${EXPERIMENT_DIR}/run_phase_c.sh" 2>&1 | tee "${LOG_DIR}/phase_c.log"; then
        success "Phase-C completed successfully"
    else
        error "Phase-C failed!"
        exit 1
    fi
else
    warning "Phase-C skipped"
fi
echo

# Phase-D: Validation
log "Phase-D: Validation"
log "Expected Duration: 1-2 hours"
echo
read -p "Start Phase-D? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting Phase-D..."
    if bash "${EXPERIMENT_DIR}/run_phase_d.sh" 2>&1 | tee "${LOG_DIR}/phase_d.log"; then
        success "Phase-D completed successfully"
    else
        error "Phase-D failed!"
        exit 1
    fi
else
    warning "Phase-D skipped"
fi
echo

# Phase-E: Sensitivity Analysis
log "Phase-E: Sensitivity Analysis"
log "Expected Duration: 2-3 hours"
echo
read -p "Start Phase-E? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Starting Phase-E..."
    if bash "${EXPERIMENT_DIR}/run_phase_e.sh" 2>&1 | tee "${LOG_DIR}/phase_e.log"; then
        success "Phase-E completed successfully"
    else
        error "Phase-E failed!"
        exit 1
    fi
else
    warning "Phase-E skipped"
fi
echo

# Experiment Summary
log "========================================="
success "Experiment 2025-10-13 Complete!"
log "========================================="
echo
log "Results Summary:"
log "  Phase-A: ${LOG_DIR}/phase_a.log"
log "  Phase-B: ${LOG_DIR}/phase_b.log"
log "  Phase-C: ${LOG_DIR}/phase_c.log"
log "  Phase-D: ${LOG_DIR}/phase_d.log"
log "  Phase-E: ${LOG_DIR}/phase_e.log"
echo
log "Next Steps:"
log "  1. Review results in each phase directory"
log "  2. Generate EXPERIMENT_SUMMARY.md"
log "  3. Create final visualizations"
log "  4. Update model documentation if needed"
echo

success "All phases completed successfully! 🎉"


