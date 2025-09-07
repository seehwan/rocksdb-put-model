#!/usr/bin/env python3
"""
PutModel v4: Device Envelope Parser

This script parses fio JSON results and creates the envelope model data.
It processes the grid sweep results and generates the 4D interpolation grid.
"""

import json
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import argparse


def parse_fio_json(file_path: str) -> Dict:
    """
    Parse a single fio JSON result file.
    
    Args:
        file_path: Path to fio JSON result file
        
    Returns:
        Dictionary with parsed results
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract bandwidth information
    jobs = data.get('jobs', [])
    if not jobs:
        raise ValueError(f"No jobs found in {file_path}")
    
    # Calculate total bandwidth (read + write)
    total_read_bw = 0
    total_write_bw = 0
    
    for job in jobs:
        read_bw = job.get('read', {}).get('bw', 0)  # KiB/s
        write_bw = job.get('write', {}).get('bw', 0)  # KiB/s
        total_read_bw += read_bw
        total_write_bw += write_bw
    
    # Convert to MiB/s
    total_bw_mibs = (total_read_bw + total_write_bw) / 1024
    
    return {
        'read_bw_mibs': total_read_bw / 1024,
        'write_bw_mibs': total_write_bw / 1024,
        'total_bw_mibs': total_bw_mibs,
        'read_ratio': total_read_bw / (total_read_bw + total_write_bw) if (total_read_bw + total_write_bw) > 0 else 0
    }


def parse_grid_sweep_results(results_dir: str) -> Dict:
    """
    Parse all fio results from a grid sweep.
    
    Args:
        results_dir: Directory containing fio JSON result files
        
    Returns:
        Dictionary with grid data for envelope model
    """
    results_dir = Path(results_dir)
    
    # Define grid axes
    rho_r_values = [0, 25, 50, 75, 100]
    iodepth_values = [1, 4, 16, 64]
    numjobs_values = [1, 2, 4]
    bs_values = [4, 64, 1024]
    
    # Initialize grid
    grid_shape = (len(rho_r_values), len(iodepth_values), len(numjobs_values), len(bs_values))
    bandwidth_grid = np.zeros(grid_shape)
    
    # Parse all result files
    parsed_count = 0
    failed_count = 0
    
    for i, rho_r in enumerate(rho_r_values):
        for j, iodepth in enumerate(iodepth_values):
            for k, numjobs in enumerate(numjobs_values):
                for l, bs_k in enumerate(bs_values):
                    result_file = results_dir / f"result_{rho_r}_{iodepth}_{numjobs}_{bs_k}.json"
                    
                    if result_file.exists():
                        try:
                            result = parse_fio_json(str(result_file))
                            bandwidth_grid[i, j, k, l] = result['total_bw_mibs']
                            parsed_count += 1
                        except Exception as e:
                            print(f"Warning: Failed to parse {result_file}: {e}")
                            failed_count += 1
                    else:
                        print(f"Warning: Result file not found: {result_file}")
                        failed_count += 1
    
    print(f"Parsed {parsed_count} results, {failed_count} failed")
    
    # Create grid data
    grid_data = {
        'rho_r_axis': rho_r_values,
        'iodepth_axis': iodepth_values,
        'numjobs_axis': numjobs_values,
        'bs_axis': bs_values,
        'bandwidth_grid': bandwidth_grid.tolist(),
        'metadata': {
            'created_by': 'PutModel v4',
            'version': '1.0',
            'description': 'Device envelope model from fio grid sweep',
            'device': '/dev/nvme1n1p1',
            'parsed_count': parsed_count,
            'failed_count': failed_count,
            'grid_shape': grid_shape
        }
    }
    
    return grid_data


def save_envelope_model(grid_data: Dict, output_path: str):
    """
    Save envelope model data to JSON file.
    
    Args:
        grid_data: Grid data dictionary
        output_path: Output JSON file path
    """
    with open(output_path, 'w') as f:
        json.dump(grid_data, f, indent=2)
    
    print(f"Envelope model saved to: {output_path}")


def create_csv_summary(grid_data: Dict, output_path: str):
    """
    Create a CSV summary of the envelope model data.
    
    Args:
        grid_data: Grid data dictionary
        output_path: Output CSV file path
    """
    import csv
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['rho_r', 'iodepth', 'numjobs', 'bs_k', 'bandwidth_mibs'])
        
        rho_r_axis = grid_data['rho_r_axis']
        iodepth_axis = grid_data['iodepth_axis']
        numjobs_axis = grid_data['numjobs_axis']
        bs_axis = grid_data['bs_axis']
        bandwidth_grid = np.array(grid_data['bandwidth_grid'])
        
        for i, rho_r in enumerate(rho_r_axis):
            for j, iodepth in enumerate(iodepth_axis):
                for k, numjobs in enumerate(numjobs_axis):
                    for l, bs_k in enumerate(bs_axis):
                        bandwidth = bandwidth_grid[i, j, k, l]
                        writer.writerow([rho_r, iodepth, numjobs, bs_k, bandwidth])
    
    print(f"CSV summary saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Parse fio grid sweep results')
    parser.add_argument('results_dir', help='Directory containing fio JSON result files')
    parser.add_argument('--output', '-o', default='envelope_model.json', 
                       help='Output JSON file path')
    parser.add_argument('--csv', '-c', default='device_envelope.csv',
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    print(f"Parsing fio results from: {args.results_dir}")
    
    # Parse grid sweep results
    grid_data = parse_grid_sweep_results(args.results_dir)
    
    # Save envelope model
    save_envelope_model(grid_data, args.output)
    
    # Create CSV summary
    create_csv_summary(grid_data, args.csv)
    
    # Print summary statistics
    bandwidth_grid = np.array(grid_data['bandwidth_grid'])
    print(f"\nSummary statistics:")
    print(f"  Grid shape: {bandwidth_grid.shape}")
    print(f"  Min bandwidth: {bandwidth_grid.min():.1f} MiB/s")
    print(f"  Max bandwidth: {bandwidth_grid.max():.1f} MiB/s")
    print(f"  Mean bandwidth: {bandwidth_grid.mean():.1f} MiB/s")
    print(f"  Std bandwidth: {bandwidth_grid.std():.1f} MiB/s")


if __name__ == "__main__":
    main()