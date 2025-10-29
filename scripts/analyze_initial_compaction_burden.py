#!/usr/bin/env python3
"""
Analyze initial phase compaction burden from RocksDB LOG file
to understand if excessive initial puts cause later performance degradation
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta

def parse_log_file(log_path):
    """Parse RocksDB LOG file to extract compaction and flush events"""
    
    compaction_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)\s+\d+\s+.*?Compaction start summary.*?Base level (\d+), inputs:\s+\[([^\]]+)\],?\s*\[([^\]]+)\]?'
    )
    
    flush_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)\s+\d+\s+\[(\w+)\].*?flush.*?files:\s+(\d+)'
    )
    
    stall_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)\s+\d+\s+\[(\w+)\].*?stall'
    )
    
    events = {
        'compactions': [],
        'flushes': [],
        'stalls': []
    }
    
    start_time = None
    
    print("Parsing LOG file (this may take a while for 2.5GB file)...")
    
    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f):
            if line_num % 100000 == 0:
                print(f"  Processed {line_num:,} lines...")
            
            # Parse compaction events
            m = compaction_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                base_level = int(m.group(2))
                input_files = m.group(3)
                output_files = m.group(4) if len(m.groups()) > 3 else ""
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    if start_time is None:
                        start_time = timestamp
                    
                    elapsed = (timestamp - start_time).total_seconds() / 3600  # hours
                    
                    # Count files from the input string
                    input_count = len(input_files.split(')')) if input_files else 0
                    output_count = len(output_files.split(')')) if output_files and output_files != 'None' else 0
                    
                    events['compactions'].append({
                        'time': elapsed,
                        'timestamp': timestamp,
                        'level': base_level,
                        'input_files': input_count,
                        'output_files': output_count
                    })
                except Exception as e:
                    pass
            
            # Parse flush events
            m = flush_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                thread = m.group(2)
                file_count = int(m.group(3))
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    elapsed = (timestamp - start_time).total_seconds() / 3600  # hours
                    events['flushes'].append({
                        'time': elapsed,
                        'timestamp': timestamp,
                        'thread': thread,
                        'files': file_count
                    })
                except:
                    pass
            
            # Parse stall events
            m = stall_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                thread = m.group(2)
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    elapsed = (timestamp - start_time).total_seconds() / 3600  # hours
                    events['stalls'].append({
                        'time': elapsed,
                        'timestamp': timestamp,
                        'thread': thread
                    })
                except:
                    pass
    
    return events

def analyze_by_phase(events, phase_boundaries):
    """Analyze compaction activity by phase"""
    
    initial_end, middle_end = phase_boundaries
    
    phases = {
        'initial': {'compactions': [], 'flushes': [], 'stalls': []},
        'middle': {'compactions': [], 'flushes': [], 'stalls': []},
        'final': {'compactions': [], 'flushes': [], 'stalls': []}
    }
    
    for event in events['compactions']:
        t = event['time']
        if t < initial_end:
            phases['initial']['compactions'].append(event)
        elif t < middle_end:
            phases['middle']['compactions'].append(event)
        else:
            phases['final']['compactions'].append(event)
    
    for event in events['flushes']:
        t = event['time']
        if t < initial_end:
            phases['initial']['flushes'].append(event)
        elif t < middle_end:
            phases['middle']['flushes'].append(event)
        else:
            phases['final']['flushes'].append(event)
    
    for event in events['stalls']:
        t = event['time']
        if t < initial_end:
            phases['initial']['stalls'].append(event)
        elif t < middle_end:
            phases['middle']['stalls'].append(event)
        else:
            phases['final']['stalls'].append(event)
    
    return phases

def create_visualization(events, phases, output_path):
    """Create comprehensive visualization"""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Compaction frequency over time
    ax = axes[0, 0]
    compaction_times = [e['time'] for e in events['compactions']]
    ax.hist(compaction_times, bins=100, edgecolor='black', alpha=0.7)
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, label='Phase boundary')
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18)
    ax.set_ylabel('Compaction Count', fontsize=18)
    ax.set_title('Compaction Activity Over Time', fontsize=20)
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 2. Flush frequency over time
    ax = axes[0, 1]
    flush_times = [e['time'] for e in events['flushes']]
    ax.hist(flush_times, bins=100, edgecolor='black', alpha=0.7, color='orange')
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, label='Phase boundary')
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18)
    ax.set_ylabel('Flush Count', fontsize=18)
    ax.set_title('Flush Activity Over Time', fontsize=20)
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 3. Events per phase comparison
    ax = axes[1, 0]
    phase_names = ['Initial', 'Middle', 'Final']
    compaction_counts = [
        len(phases['initial']['compactions']),
        len(phases['middle']['compactions']),
        len(phases['final']['compactions'])
    ]
    flush_counts = [
        len(phases['initial']['flushes']),
        len(phases['middle']['flushes']),
        len(phases['final']['flushes'])
    ]
    
    x = np.arange(len(phase_names))
    width = 0.35
    
    ax.bar(x - width/2, compaction_counts, width, label='Compactions', alpha=0.7)
    ax.bar(x + width/2, flush_counts, width, label='Flushes', alpha=0.7, color='orange')
    ax.set_xlabel('Phase', fontsize=18)
    ax.set_ylabel('Event Count', fontsize=18)
    ax.set_title('Activity by Phase', fontsize=20)
    ax.set_xticks(x)
    ax.set_xticklabels(phase_names)
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 4. Stall events over time
    ax = axes[1, 1]
    if events['stalls']:
        stall_times = [e['time'] for e in events['stalls']]
        ax.scatter(stall_times, range(len(stall_times)), alpha=0.5, s=10)
        ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2, label='Phase boundary')
        ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
        ax.set_xlabel('Time (hours)', fontsize=18)
        ax.set_ylabel('Stall Event #', fontsize=18)
        ax.set_title('Write Stall Events', fontsize=20)
        ax.legend(fontsize=14)
        ax.tick_params(labelsize=14)
    else:
        ax.text(0.5, 0.5, 'No stall events detected', 
                ha='center', va='center', fontsize=18)
        ax.set_title('Write Stall Events', fontsize=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved: {output_path}")

def main():
    log_path = 'experiments/2025-09-12/rocksdb_log_phase_b.log'
    output_path = 'figs/initial_compaction_burden.png'
    
    print("=" * 60)
    print("Analyzing Initial Phase Compaction Burden")
    print("=" * 60)
    
    # Parse LOG file
    events = parse_log_file(log_path)
    
    print(f"\nExtracted events:")
    print(f"  Compactions: {len(events['compactions'])}")
    print(f"  Flushes: {len(events['flushes'])}")
    print(f"  Stalls: {len(events['stalls'])}")
    
    # Analyze by phase (9.81h, 42.0h boundaries)
    phases = analyze_by_phase(events, (9.81, 42.0))
    
    print("\n" + "=" * 60)
    print("Phase Analysis:")
    print("=" * 60)
    
    for phase_name in ['initial', 'middle', 'final']:
        phase = phases[phase_name]
        print(f"\n{phase_name.upper()} Phase:")
        print(f"  Compactions: {len(phase['compactions'])}")
        print(f"  Flushes: {len(phase['flushes'])}")
        print(f"  Stalls: {len(phase['stalls'])}")
        
        if phase['compactions']:
            avg_files = np.mean([c['files'] for c in phase['compactions']])
            print(f"  Avg compaction files: {avg_files:.1f}")
    
    # Create visualization
    create_visualization(events, phases, output_path)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

