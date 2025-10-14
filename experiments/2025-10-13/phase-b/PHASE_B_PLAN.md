# Phase-B: RocksDB Benchmark Execution

**Phase:** B - RocksDB Performance Measurement  
**Status:** ⏳ Pending  
**Duration:** 2-4 hours  
**Depends On:** Phase-A (recommended)

---

## 🎯 Objectives

1. Execute RocksDB benchmark workload
2. Collect comprehensive performance metrics
3. Monitor system state evolution
4. Generate validation dataset for models

---

## 📋 Tasks

### Task 1: Environment Setup

**Objective:** Prepare RocksDB environment

**Steps:**
```bash
# Clear previous data
rm -rf /path/to/rocksdb_data/*

# Configure RocksDB
cat > rocksdb_config.txt <<EOF
write_buffer_size=67108864
max_write_buffer_number=3
target_file_size_base=67108864
max_bytes_for_level_base=268435456
compression=none
statistics=true
stats_dump_period_sec=60
EOF

# Set system parameters
echo deadline > /sys/block/nvme1n1/queue/scheduler
echo 3 > /proc/sys/vm/drop_caches
```

---

### Task 2: FillRandom Benchmark

**Objective:** Execute primary workload

**Configuration:**
```yaml
Workload:        fillrandom
Duration:        120 minutes
Record Size:     1040 bytes
Total Records:   ~1.2 billion
Target DB Size:  ~50 GB
```

**Execution:**
```bash
cd phase-b

# Start benchmark
./scripts/run_fillrandom_benchmark.sh \
    --duration 120 \
    --record-size 1040 \
    --output data/fillrandom_results.json
```

**Monitoring:**
- Start time: Record start timestamp
- Monitor every 60 seconds
- Collect RocksDB stats
- Collect system metrics

---

### Task 3: Performance Monitoring

**Objective:** Collect real-time metrics

**Metrics to Monitor:**

**RocksDB Metrics:**
- QPS (operations per second)
- Write Amplification (WA)
- Read Amplification (RA)
- LSM tree depth
- Compaction stats
- Memtable flush count

**System Metrics:**
- Device I/O bandwidth (read/write)
- CPU utilization
- Memory usage
- I/O queue depth
- Cache hit rate

**Monitoring Script:**
```bash
# Start monitoring daemon
python scripts/monitor_system.py \
    --interval 60 \
    --output data/system_metrics.csv &

MONITOR_PID=$!
```

---

### Task 4: Log Collection

**Objective:** Preserve all diagnostic information

**Logs to Collect:**
- RocksDB LOG file (complete)
- System dmesg output
- Monitoring daemon output
- Benchmark stdout/stderr

**Commands:**
```bash
# After benchmark completes
cp /path/to/rocksdb/LOG data/rocksdb.log
dmesg > data/system_dmesg.log
journalctl -u rocksdb > data/systemd.log
```

---

## 📊 Expected Outputs

### Primary Data Files

1. **fillrandom_results.json**
   ```json
   {
     "start_time": "2025-10-13T...",
     "duration_seconds": 7200,
     "total_operations": 1200000000,
     "timeline": [
       {
         "timestamp": 60,
         "qps": 138769,
         "wa": 1.2,
         "ra": 0.1,
         "device_write_bw": 4116.6,
         "lsm_depth": 2
       },
       ...
     ]
   }
   ```

2. **system_metrics.csv**
   ```csv
   timestamp,cpu_util,mem_used_gb,io_read_mbps,io_write_mbps,io_queue_depth
   60,45.2,8.5,100.2,4116.6,32
   120,48.1,12.3,150.3,3800.2,28
   ...
   ```

3. **rocksdb.log**
   - Complete RocksDB diagnostic log
   - Compaction details
   - Flush operations
   - Performance statistics

---

## 📈 Data Analysis

### Immediate Analysis

**After benchmark completion:**

1. **Parse RocksDB LOG:**
```bash
python scripts/parse_rocksdb_log.py \
    --log data/rocksdb.log \
    --output results/parsed_log.json
```

2. **Generate Performance Timeline:**
```bash
python scripts/create_timeline.py \
    --results data/fillrandom_results.json \
    --metrics data/system_metrics.csv \
    --output results/performance_timeline.json
```

3. **Create Visualizations:**
```bash
python scripts/visualize_results.py \
    --input results/performance_timeline.json \
    --output results/
```

---

## ✅ Success Criteria

- [ ] Benchmark runs for full 120 minutes
- [ ] No crashes or errors
- [ ] Complete LOG file generated
- [ ] All metrics collected at 60-second intervals
- [ ] System metrics monitoring successful
- [ ] Performance degradation observed (>10%)
- [ ] Data parsed and validated

---

## 🛠️ Scripts Required

### Create Basic Scripts

```bash
cd phase-b/scripts

# Benchmark execution
cat > run_fillrandom_benchmark.sh <<'EOF'
#!/bin/bash
# FillRandom benchmark executor
# Usage: ./run_fillrandom_benchmark.sh [options]

DURATION=${1:-120}
OUTPUT=${2:-../data/fillrandom_results.json}

echo "Starting FillRandom benchmark for ${DURATION} minutes..."
# Add actual db_bench command here
EOF

# System monitoring
cat > monitor_system.py <<'EOF'
#!/usr/bin/env python3
"""System metrics monitoring daemon"""

import time
import psutil
import json
from datetime import datetime

def collect_metrics():
    return {
        'timestamp': time.time(),
        'cpu_percent': psutil.cpu_percent(),
        'memory_mb': psutil.virtual_memory().used / (1024**2),
        # Add I/O metrics
    }

# Add monitoring loop
EOF

# Make executable
chmod +x run_fillrandom_benchmark.sh
chmod +x monitor_system.py
```

---

## 📊 Validation

### Data Quality Checks

**Completeness:**
- [ ] All 120 data points collected
- [ ] No missing timestamps
- [ ] All metrics present

**Consistency:**
- [ ] QPS trends make sense
- [ ] WA increases over time
- [ ] Device bandwidth decreases
- [ ] No sudden jumps/drops

**Accuracy:**
- [ ] Cross-validate with LOG file
- [ ] Verify calculated vs reported WA
- [ ] Check ledger closure (±10%)

---

## ⚠️ Risk Management

### Common Issues

**1. Benchmark Timeout/Crash**
- **Detection:** Monitor process status
- **Recovery:** Checkpoint every 30 min
- **Contingency:** Restart from checkpoint

**2. Disk Full**
- **Prevention:** Check free space before start
- **Monitoring:** Alert at 80% full
- **Action:** Expand or cleanup

**3. Device Throttling**
- **Detection:** Sudden bandwidth drop
- **Prevention:** Monitor temperature
- **Action:** Pause and cool down

---

## 🔗 Dependencies

**Prerequisites:**
- RocksDB compiled and installed
- db_bench tool available
- Target device formatted and mounted
- Phase-A completed (recommended)

**Required Tools:**
- RocksDB (db_bench)
- Python 3.x
- psutil library
- System monitoring tools

**Outputs Used By:**
- Phase-C: Performance data for model input
- Phase-D: Validation ground truth
- Phase-E: Sensitivity analysis data

---

## 📝 Notes

### Expected Performance Pattern

**Initial Phase (0-30 min):**
- High QPS (~140K ops/sec)
- Low WA (~1.2)
- High device bandwidth (>4000 MB/s)
- Simple LSM structure (L0-L1)

**Middle Phase (30-90 min):**
- Moderate QPS (~115K ops/sec)
- Increasing WA (~2.5)
- Declining bandwidth (~1000 MB/s)
- Growing LSM (L0-L3)

**Final Phase (90-120 min):**
- Lower QPS (~110K ops/sec)
- High WA (~3.5)
- Low bandwidth (~850 MB/s)
- Complex LSM (L0-L6)

---

*Phase-B Plan Version: 1.0*  
*Created: 2025-10-13*  
*Status: Ready for Execution*




