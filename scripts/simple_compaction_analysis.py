#!/usr/bin/env python3
"""
Simple analysis of compaction events from RocksDB LOG
Focus on whether initial excessive puts cause performance degradation
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
from datetime import datetime

def count_compactions_by_phase(log_path, phase_boundaries=(9.81, 42.0)):
    """Count compaction events by phase"""
    
    initial_end, middle_end = phase_boundaries
    
    compaction_times = []
    flush_times = []
    
    print("Parsing LOG file...")
    line_count = 0
    
    with open(log_path, 'r') as f:
        for line in f:
            line_count += 1
            if line_count % 500000 == 0:
                print(f"  Processed {line_count:,} lines...")
            
            # Extract timestamp
            timestamp_match = re.match(r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            if not timestamp_match:
                continue
            
            timestamp_str = timestamp_match.group(1)
            
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                
                # Count compactions
                if 'Compaction start summary' in line:
                    compaction_times.append(timestamp)
                
                # Count flushes
                if 'flush_started' in line or 'FlushMemTableToOutputFile' in line:
                    flush_times.append(timestamp)
            except:
                pass
    
    print(f"\nTotal compactions: {len(compaction_times)}")
    print(f"Total flushes: {len(flush_times)}")
    
    # Convert to hours since start
    if not compaction_times:
        return {}
    
    start_time = compaction_times[0]
    compaction_hours = [(t - start_time).total_seconds() / 3600 for t in compaction_times]
    flush_hours = [(t - start_time).total_seconds() / 3600 for t in flush_times]
    
    # Count by phase
    phases = {
        'initial': {'compactions': 0, 'flushes': 0},
        'middle': {'compactions': 0, 'flushes': 0},
        'final': {'compactions': 0, 'flushes': 0}
    }
    
    for hours in compaction_hours:
        if hours < initial_end:
            phases['initial']['compactions'] += 1
        elif hours < middle_end:
            phases['middle']['compactions'] += 1
        else:
            phases['final']['compactions'] += 1
    
    for hours in flush_hours:
        if hours < initial_end:
            phases['initial']['flushes'] += 1
        elif hours < middle_end:
            phases['middle']['flushes'] += 1
        else:
            phases['final']['flushes'] += 1
    
    return {
        'compaction_hours': compaction_hours,
        'flush_hours': flush_hours,
        'phases': phases
    }

def create_visualization(data, output_path):
    """Create visualization"""
    
    compaction_hours = data['compaction_hours']
    flush_hours = data['flush_hours']
    phases = data['phases']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Compaction histogram
    ax = axes[0, 0]
    ax.hist(compaction_hours, bins=100, edgecolor='black', alpha=0.7)
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, label='Phase boundary')
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Compaction Count', fontsize=18, family='Times New Roman')
    ax.set_title('Compaction Activity Over Time', fontsize=20, family='Times New Roman')
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 2. Flush histogram
    ax = axes[0, 1]
    ax.hist(flush_hours, bins=100, edgecolor='black', alpha=0.7, color='orange')
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, label='Phase boundary')
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Flush Count', fontsize=18, family='Times New Roman')
    ax.set_title('Flush Activity Over Time', fontsize=20, family='Times New Roman')
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 3. Events per phase
    ax = axes[1, 0]
    phase_names = ['Initial', 'Middle', 'Final']
    compaction_counts = [phases['initial']['compactions'], 
                         phases['middle']['compactions'],
                         phases['final']['compactions']]
    flush_counts = [phases['initial']['flushes'], 
                    phases['middle']['flushes'],
                    phases['final']['flushes']]
    
    x = np.arange(len(phase_names))
    width = 0.35
    
    ax.bar(x - width/2, compaction_counts, width, label='Compactions', alpha=0.7)
    ax.bar(x + width/2, flush_counts, width, label='Flushes', alpha=0.7, color='orange')
    ax.set_xlabel('Phase', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Event Count', fontsize=18, family='Times New Roman')
    ax.set_title('Activity by Phase', fontsize=20, family='Times New Roman')
    ax.set_xticks(x)
    ax.set_xticklabels(phase_names)
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 4. Activity rate (events per hour)
    ax = axes[1, 1]
    initial_duration = 9.81  # hours
    middle_duration = 42.0 - 9.81  # hours
    final_duration = max(compaction_hours) - 42.0  # hours
    
    compaction_rates = [
        phases['initial']['compactions'] / initial_duration,
        phases['middle']['compactions'] / middle_duration,
        phases['final']['compactions'] / final_duration
    ]
    flush_rates = [
        phases['initial']['flushes'] / initial_duration,
        phases['middle']['flushes'] / middle_duration,
        phases['final']['flushes'] / final_duration
    ]
    
    ax.bar(x - width/2, compaction_rates, width, label='Compactions/hour', alpha=0.7)
    ax.bar(x + width/2, flush_rates, width, label='Flushes/hour', alpha=0.7, color='orange')
    ax.set_xlabel('Phase', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Events per Hour', fontsize=18, family='Times New Roman')
    ax.set_title('Activity Rate by Phase', fontsize=20, family='Times New Roman')
    ax.set_xticks(x)
    ax.set_xticklabels(phase_names)
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved: {output_path}")

def main():
    log_path = 'experiments/2025-09-12/rocksdb_log_phase_b.log'
    output_path = 'figs/initial_compaction_burden.png'
    
    print("=" * 60)
    print("Analyzing Initial Phase Compaction Burden")
    print("=" * 60)
    
    data = count_compactions_by_phase(log_path)
    
    print("\n" + "=" * 60)
    print("Phase Analysis:")
    print("=" * 60)
    
    for phase_name in ['initial', 'middle', 'final']:
        phase = data['phases'][phase_name]
        duration = {'initial': 9.81, 'middle': 42.0 - 9.81, 'final': 100}[phase_name]
        rate = phase['compactions'] / duration if duration > 0 else 0
        
        print(f"\n{phase_name.upper()} Phase:")
        print(f"  Compactions: {phase['compactions']}")
        print(f"  Flushes: {phase['flushes']}")
        print(f"  Compaction rate: {rate:.2f} compactions/hour")
    
    create_visualization(data, output_path)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

