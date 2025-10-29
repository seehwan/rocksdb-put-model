#!/usr/bin/env python3
"""
Visualize compaction and flush bandwidth over time
Considering variable compaction sizes
"""

import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from collections import defaultdict
import pandas as pd

def parse_sizes(s):
    """Parse file sizes from input/output lists"""
    # Example: "15(36MB) 13(36MB)" -> [36, 36]
    sizes = []
    matches = re.findall(r'(\d+)\(([\d.]+)(\w+)\)', s)
    for match in matches:
        size = float(match[1])
        unit = match[2]
        
        # Convert to MB
        if unit == 'KB':
            size /= 1000
        elif unit == 'GB':
            size *= 1000
        elif unit == 'MB':
            pass
        else:
            # Unknown unit, skip
            continue
        
        sizes.append(size)
    return sizes

def parse_log_file(log_path):
    """Parse compaction and flush events with sizes"""
    
    compaction_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)'
        r'.*?Compaction start summary.*?Base level (\d+),'
        r'\s+inputs:\s+\[([^\]]+)\],?\s*\[?([^\]]*)\]?'
    )
    
    # Pattern for flush completion
    flush_pattern = re.compile(
        r'(\d{4}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}\.\d+)'
        r'.*?Level-0 flush table.*?(\d+)\s+bytes'
    )
    
    compactions = []
    flushes = []
    
    print("Parsing LOG file for compaction and flush sizes...")
    line_count = 0
    
    with open(log_path, 'r') as f:
        for line in f:
            line_count += 1
            if line_count % 500000 == 0:
                print(f"  Processed {line_count:,} lines...")
            
            # Parse compaction
            m = compaction_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                level = int(m.group(2))
                inputs_str = m.group(3)
                outputs_str = m.group(4) if len(m.groups()) > 3 and m.group(4) else ""
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    
                    input_sizes = parse_sizes(inputs_str)
                    output_sizes = parse_sizes(outputs_str)
                    
                    input_total = sum(input_sizes)  # MB
                    output_total = sum(output_sizes) if output_sizes else 0  # MB
                    
                    compactions.append({
                        'time': timestamp,
                        'level': level,
                        'input_size_mb': input_total,
                        'output_size_mb': output_total
                    })
                except Exception as e:
                    pass
            
            # Parse flush
            m = flush_pattern.search(line)
            if m:
                timestamp_str = m.group(1)
                size_bytes = int(m.group(2))
                size_mb = size_bytes / (1024 * 1024)
                
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y/%m/%d-%H:%M:%S.%f')
                    
                    flushes.append({
                        'time': timestamp,
                        'size_mb': size_mb
                    })
                except:
                    pass
    
    return compactions, flushes

def calculate_bandwidth(events, window_hours=1.0):
    """Calculate bandwidth over time windows"""
    
    if not events:
        return []
    
    start_time = events[0]['time']
    
    # Calculate hourly bandwidth
    bandwidth_data = []
    window_seconds = window_hours * 3600
    
    for event in events:
        elapsed_hours = (event['time'] - start_time).total_seconds() / 3600
        
        # Calculate size based on event type
        if 'size_mb' in event:
            # Flush event
            size = event['size_mb']
        elif 'input_size_mb' in event:
            # Compaction event: input + output
            size = event['input_size_mb'] + event['output_size_mb']
        else:
            size = 0
        
        bandwidth_data.append({
            'time_hours': elapsed_hours,
            'bandwidth_mb': size  # MB per event
        })
    
    return bandwidth_data

def create_visualization(compactions, flushes, phase_boundaries, output_path):
    """Create visualization of compaction and flush bandwidth"""
    
    initial_end, middle_end = phase_boundaries
    
    # Separate by phase
    initial_comp = [c for c in compactions if c['time_hours'] < initial_end]
    middle_comp = [c for c in compactions if initial_end <= c['time_hours'] < middle_end]
    final_comp = [c for c in compactions if c['time_hours'] >= middle_end]
    
    initial_flush = [f for f in flushes if f['time_hours'] < initial_end]
    middle_flush = [f for f in flushes if initial_end <= f['time_hours'] < middle_end]
    final_flush = [f for f in flushes if f['time_hours'] >= middle_end]
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Compaction size over time (scatter)
    ax = axes[0, 0]
    
    for phase_data, label, color in [
        (initial_comp, 'Initial', 'red'),
        (middle_comp, 'Middle', 'blue'),
        (final_comp, 'Final', 'green')
    ]:
        if phase_data:
            times = [c['time_hours'] for c in phase_data]
            sizes = [c['input_size_mb'] + c['output_size_mb'] for c in phase_data]
            ax.scatter(times, sizes, label=label, alpha=0.5, s=10, c=color)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Compaction Size (MB)', fontsize=18, family='Times New Roman')
    ax.set_title('Compaction Size Over Time', fontsize=20, family='Times New Roman')
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 2. Flush size over time (scatter)
    ax = axes[0, 1]
    
    for phase_data, label, color in [
        (initial_flush, 'Initial', 'red'),
        (middle_flush, 'Middle', 'blue'),
        (final_flush, 'Final', 'green')
    ]:
        if phase_data:
            times = [f['time_hours'] for f in phase_data]
            sizes = [f['size_mb'] for f in phase_data]
            ax.scatter(times, sizes, label=label, alpha=0.5, s=10, c=color)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Flush Size (MB)', fontsize=18, family='Times New Roman')
    ax.set_title('Flush Size Over Time', fontsize=20, family='Times New Roman')
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 3. Cumulative bandwidth by phase
    ax = axes[1, 0]
    
    def calc_cumulative(data_list):
        if not data_list:
            return [], []
        times = sorted([d['time_hours'] for d in data_list])
        cumulative = np.cumsum([d.get('input_size_mb', 0) + d.get('output_size_mb', d.get('size_mb', 0)) 
                               for d in sorted(data_list, key=lambda x: x['time_hours'])])
        return times, cumulative
    
    for phase_data, label, color in [
        (initial_comp, 'Initial Compaction', 'red'),
        (middle_comp, 'Middle Compaction', 'blue'),
        (final_comp, 'Final Compaction', 'green')
    ]:
        times, cumulative = calc_cumulative(phase_data)
        if times:
            ax.plot(times, cumulative, label=label, linewidth=2, c=color)
    
    ax.axvline(x=9.81, color='r', linestyle='--', linewidth=2)
    ax.axvline(x=42.0, color='r', linestyle='--', linewidth=2)
    ax.set_xlabel('Time (hours)', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Cumulative Data (MB)', fontsize=18, family='Times New Roman')
    ax.set_title('Cumulative Compaction Size', fontsize=20, family='Times New Roman')
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    # 4. Average size by phase
    ax = axes[1, 1]
    
    phase_names = ['Initial', 'Middle', 'Final']
    compaction_sizes = [
        np.mean([c['input_size_mb'] + c['output_size_mb'] for c in initial_comp]) if initial_comp else 0,
        np.mean([c['input_size_mb'] + c['output_size_mb'] for c in middle_comp]) if middle_comp else 0,
        np.mean([c['input_size_mb'] + c['output_size_mb'] for c in final_comp]) if final_comp else 0
    ]
    flush_sizes = [
        np.mean([f['size_mb'] for f in initial_flush]) if initial_flush else 0,
        np.mean([f['size_mb'] for f in middle_flush]) if middle_flush else 0,
        np.mean([f['size_mb'] for f in final_flush]) if final_flush else 0
    ]
    
    x = np.arange(len(phase_names))
    width = 0.35
    
    ax.bar(x - width/2, compaction_sizes, width, label='Compaction Avg', alpha=0.7)
    ax.bar(x + width/2, flush_sizes, width, label='Flush Avg', alpha=0.7, color='orange')
    ax.set_xlabel('Phase', fontsize=18, family='Times New Roman')
    ax.set_ylabel('Average Size (MB)', fontsize=18, family='Times New Roman')
    ax.set_title('Average Event Size by Phase', fontsize=20, family='Times New Roman')
    ax.set_xticks(x)
    ax.set_xticklabels(phase_names)
    ax.legend(fontsize=14)
    ax.tick_params(labelsize=14)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved: {output_path}")

def main():
    log_path = 'experiments/2025-09-12/rocksdb_log_phase_b.log'
    output_path = 'figs/compaction_flush_bandwidth.png'
    
    print("=" * 60)
    print("Analyzing Compaction and Flush Bandwidth")
    print("=" * 60)
    
    # Parse LOG file
    compactions, flushes = parse_log_file(log_path)
    
    # Add time_hours
    if compactions:
        start_time = compactions[0]['time']
        for c in compactions:
            c['time_hours'] = (c['time'] - start_time).total_seconds() / 3600
    if flushes:
        start_time = flushes[0]['time']
        for f in flushes:
            f['time_hours'] = (f['time'] - start_time).total_seconds() / 3600
    
    print(f"\nExtracted events:")
    print(f"  Compactions: {len(compactions)}")
    print(f"  Flushes: {len(flushes)}")
    
    if compactions:
        print(f"\n  Avg compaction size: {np.mean([c['input_size_mb'] + c['output_size_mb'] for c in compactions]):.1f} MB")
    
    if flushes:
        print(f"  Avg flush size: {np.mean([f['size_mb'] for f in flushes]):.1f} MB")
    
    # Create visualization
    create_visualization(compactions, flushes, (9.81, 42.0), output_path)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()

