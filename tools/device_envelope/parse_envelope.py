#!/usr/bin/env python3
"""
PutModel v4 Device Envelope Parser
fio 그리드 스윕 결과를 파싱하여 4D 엔벌롭 모델 생성
"""

import json
import numpy as np
import os
import sys
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, List, Tuple, Optional
import argparse

def parse_fio_results(output_dir: str) -> Dict[Tuple[int, int, int, int], float]:
    """
    fio 결과를 파싱하여 4D 그리드 생성
    
    Args:
        output_dir: fio 결과 JSON 파일들이 있는 디렉토리
        
    Returns:
        {(rho_r, iodepth, numjobs, bs_k): bandwidth} 딕셔너리
    """
    results = {}
    successful_parses = 0
    failed_parses = 0
    
    print(f"Parsing fio results from: {output_dir}")
    
    for rho_r in [0, 25, 50, 75, 100]:
        for iodepth in [1, 4, 16, 64]:
            for numjobs in [1, 2, 4]:
                for bs_k in [4, 64, 1024]:
                    filename = f"result_{rho_r}_{iodepth}_{numjobs}_{bs_k}.json"
                    filepath = os.path.join(output_dir, filename)
                    
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                            
                            # fio JSON 구조에서 대역폭 추출
                            if 'jobs' in data and len(data['jobs']) > 0:
                                job = data['jobs'][0]
                                
                                # 쓰기 대역폭 (KiB/s)
                                write_bw_kibs = job.get('write', {}).get('bw', 0)
                                # 읽기 대역폭 (KiB/s)  
                                read_bw_kibs = job.get('read', {}).get('bw', 0)
                                
                                # MiB/s로 변환
                                write_bw_mibs = write_bw_kibs / 1024
                                read_bw_mibs = read_bw_kibs / 1024
                                total_bw_mibs = write_bw_mibs + read_bw_mibs
                                
                                results[(rho_r, iodepth, numjobs, bs_k)] = total_bw_mibs
                                successful_parses += 1
                                
                            else:
                                print(f"Warning: Invalid JSON structure in {filename}")
                                failed_parses += 1
                                
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            print(f"Error parsing {filename}: {e}")
                            failed_parses += 1
                    else:
                        print(f"Warning: File not found: {filename}")
                        failed_parses += 1
    
    print(f"Parsing complete: {successful_parses} successful, {failed_parses} failed")
    return results

def create_envelope_model(results: Dict[Tuple[int, int, int, int], float]) -> Dict:
    """
    4D 그리드에서 엔벌롭 모델 생성
    
    Args:
        results: 파싱된 fio 결과
        
    Returns:
        엔벌롭 모델 딕셔너리
    """
    print("Creating 4D envelope model...")
    
    # 축 정의
    rho_r_axis = np.array([0, 25, 50, 75, 100])
    iodepth_axis = np.array([1, 4, 16, 64])
    numjobs_axis = np.array([1, 2, 4])
    bs_axis = np.array([4, 64, 1024])
    
    # 4D 그리드 생성
    bandwidth_grid = np.zeros((5, 4, 3, 3))
    missing_points = []
    
    for i, rho_r in enumerate(rho_r_axis):
        for j, iodepth in enumerate(iodepth_axis):
            for k, numjobs in enumerate(numjobs_axis):
                for l, bs_k in enumerate(bs_axis):
                    key = (rho_r, iodepth, numjobs, bs_k)
                    if key in results:
                        bandwidth_grid[i, j, k, l] = results[key]
                    else:
                        missing_points.append(key)
    
    if missing_points:
        print(f"Warning: {len(missing_points)} missing data points:")
        for point in missing_points[:10]:  # 처음 10개만 출력
            print(f"  {point}")
        if len(missing_points) > 10:
            print(f"  ... and {len(missing_points) - 10} more")
    
    # 통계 정보
    valid_data = bandwidth_grid[bandwidth_grid > 0]
    print(f"Valid data points: {len(valid_data)}")
    print(f"Bandwidth range: {valid_data.min():.1f} - {valid_data.max():.1f} MiB/s")
    print(f"Mean bandwidth: {valid_data.mean():.1f} MiB/s")
    
    return {
        'metadata': {
            'version': 'v4.0',
            'description': 'PutModel v4 Device Envelope Model',
            'created': np.datetime64('now').astype(str),
            'total_points': len(results),
            'missing_points': len(missing_points),
            'bandwidth_range': [float(valid_data.min()), float(valid_data.max())],
            'mean_bandwidth': float(valid_data.mean())
        },
        'axes': {
            'rho_r_axis': rho_r_axis.tolist(),
            'iodepth_axis': iodepth_axis.tolist(),
            'numjobs_axis': numjobs_axis.tolist(),
            'bs_axis': bs_axis.tolist()
        },
        'bandwidth_grid': bandwidth_grid.tolist(),
        'missing_points': missing_points
    }

def test_interpolation(model_data: Dict, test_points: List[Tuple[int, int, int, int]]) -> None:
    """
    보간 정확도 테스트
    
    Args:
        model_data: 엔벌롭 모델 데이터
        test_points: 테스트할 포인트들
    """
    print("\n=== Interpolation Test ===")
    
    # 보간기 생성
    rho_r_axis = np.array(model_data['axes']['rho_r_axis'])
    iodepth_axis = np.array(model_data['axes']['iodepth_axis'])
    numjobs_axis = np.array(model_data['axes']['numjobs_axis'])
    bs_axis = np.array(model_data['axes']['bs_axis'])
    bandwidth_grid = np.array(model_data['bandwidth_grid'])
    
    interpolator = RegularGridInterpolator(
        (rho_r_axis, iodepth_axis, numjobs_axis, bs_axis),
        bandwidth_grid,
        method='linear',
        bounds_error=False,
        fill_value=None
    )
    
    print("Testing interpolation at sample points:")
    for i, point in enumerate(test_points[:5]):  # 처음 5개만 테스트
        rho_r, iodepth, numjobs, bs_k = point
        predicted = interpolator(np.array([rho_r, iodepth, numjobs, bs_k]))
        print(f"  Point {i+1}: {point} -> {predicted:.1f} MiB/s")
    
    # 경계 테스트
    print("\nBoundary tests:")
    boundary_tests = [
        (0, 1, 1, 4),      # 최소값
        (100, 64, 4, 1024), # 최대값
        (50, 16, 2, 64),    # 중간값
    ]
    
    for point in boundary_tests:
        rho_r, iodepth, numjobs, bs_k = point
        predicted = interpolator(np.array([rho_r, iodepth, numjobs, bs_k]))
        print(f"  {point} -> {predicted:.1f} MiB/s")

def main():
    parser = argparse.ArgumentParser(description='Parse fio grid sweep results and create envelope model')
    parser.add_argument('--input-dir', default='device_envelope_results',
                       help='Directory containing fio JSON results')
    parser.add_argument('--output-file', default='envelope_model.json',
                       help='Output envelope model JSON file')
    parser.add_argument('--test-interpolation', action='store_true',
                       help='Test interpolation accuracy')
    
    args = parser.parse_args()
    
    # 입력 디렉토리 확인
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # fio 결과 파싱
    results = parse_fio_results(args.input_dir)
    
    if not results:
        print("Error: No valid fio results found")
        sys.exit(1)
    
    # 엔벌롭 모델 생성
    envelope_model = create_envelope_model(results)
    
    # JSON 파일로 저장
    with open(args.output_file, 'w') as f:
        json.dump(envelope_model, f, indent=2)
    
    print(f"\n✅ Envelope model saved to: {args.output_file}")
    
    # 보간 테스트 (선택적)
    if args.test_interpolation:
        test_points = list(results.keys())[:10]  # 처음 10개 포인트로 테스트
        test_interpolation(envelope_model, test_points)

if __name__ == "__main__":
    main()
