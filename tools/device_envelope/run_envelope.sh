#!/bin/bash

# PutModel v4: Device Envelope Grid Sweep
# This script runs fio grid sweeps to measure device characteristics for mixed I/O workloads

set -e

# Configuration
DEVICE="/dev/nvme1n1p1"
OUTPUT_DIR="device_envelope_results"
RUNTIME=30
RAMP_TIME=10
IOENGINE="io_uring"
DIRECT=1

# Grid parameters
RHO_R_VALUES=(0 25 50 75 100)  # Read ratios in %
IODEPTH_VALUES=(1 4 16 64)      # Queue depths
NUMJOBS_VALUES=(1 2 4)          # Parallel jobs
BS_VALUES=(4 64 1024)           # Block sizes in KiB

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Starting Device Envelope Grid Sweep"
echo "Device: $DEVICE"
echo "Output directory: $OUTPUT_DIR"
echo "Runtime: ${RUNTIME}s, Ramp: ${RAMP_TIME}s"
echo ""

# Count total combinations
TOTAL_COMBINATIONS=$((${#RHO_R_VALUES[@]} * ${#IODEPTH_VALUES[@]} * ${#NUMJOBS_VALUES[@]} * ${#BS_VALUES[@]}))
CURRENT=0

echo "Total combinations: $TOTAL_COMBINATIONS"
echo ""

# Function to run a single fio test
run_fio_test() {
    local rho_r=$1
    local iodepth=$2
    local numjobs=$3
    local bs_k=$4
    
    CURRENT=$((CURRENT + 1))
    echo "[$CURRENT/$TOTAL_COMBINATIONS] Testing: ρr=${rho_r}%, qd=$iodepth, jobs=$numjobs, bs=${bs_k}KiB"
    
    # Calculate read and write percentages
    local read_pct=$rho_r
    local write_pct=$((100 - rho_r))
    
    # Create fio job file
    local job_file="${OUTPUT_DIR}/job_${rho_r}_${iodepth}_${numjobs}_${bs_k}.fio"
    
    cat > "$job_file" << EOF
[global]
ioengine=$IOENGINE
filename=$DEVICE
direct=$DIRECT
runtime=${RUNTIME}s
ramp_time=${RAMP_TIME}s
iodepth=$iodepth
numjobs=$numjobs
bs=${bs_k}k
rw=randrw
rwmixread=$read_pct
rwmixwrite=$write_pct
norandommap=1
randrepeat=0
group_reporting=1
log_avg_msec=1000
write_bw_log=0
write_iops_log=0
write_lat_log=0

[read]
name=read_test

[write]
name=write_test
EOF

    # Run fio test
    local output_file="${OUTPUT_DIR}/result_${rho_r}_${iodepth}_${numjobs}_${bs_k}.json"
    
    if fio --output-format=json "$job_file" > "$output_file" 2>/dev/null; then
        echo "  ✓ Completed successfully"
    else
        echo "  ✗ Failed"
        return 1
    fi
    
    # Clean up job file
    rm "$job_file"
}

# Run all combinations
for rho_r in "${RHO_R_VALUES[@]}"; do
    for iodepth in "${IODEPTH_VALUES[@]}"; do
        for numjobs in "${NUMJOBS_VALUES[@]}"; do
            for bs_k in "${BS_VALUES[@]}"; do
                run_fio_test "$rho_r" "$iodepth" "$numjobs" "$bs_k"
            done
        done
    done
done

echo ""
echo "Grid sweep completed!"
echo "Results saved in: $OUTPUT_DIR"
echo ""

# Run parsing script
echo "Parsing results..."
if [ -f "parse_envelope.py" ]; then
    python3 parse_envelope.py "$OUTPUT_DIR"
else
    echo "Warning: parse_envelope.py not found. Please run it manually."
fi