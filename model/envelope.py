#!/usr/bin/env python3
"""
PutModel v4 Device Envelope Model
4D 선형보간을 통한 혼합 I/O 대역폭 모델링
"""

import json
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from typing import Dict, Optional, Tuple, List
import warnings

class EnvelopeModel:
    """
    Device Envelope Model for Mixed I/O Bandwidth Prediction
    
    이 클래스는 fio 그리드 스윕 결과를 기반으로 4D 선형보간을 통해
    혼합 I/O 대역폭을 예측합니다.
    
    Attributes:
        rho_r_axis: 읽기 비율 축 (0, 25, 50, 75, 100)
        iodepth_axis: 큐 깊이 축 (1, 4, 16, 64)
        numjobs_axis: 병렬 작업 수 축 (1, 2, 4)
        bs_axis: 블록 크기 축 (4, 64, 1024 KiB)
        bandwidth_grid: 4D 대역폭 그리드
        interpolator: 4D 선형보간기
    """
    
    def __init__(self, grid_data: Dict):
        """
        엔벌롭 모델 초기화
        
        Args:
            grid_data: fio 그리드 스윕 결과 딕셔너리
        """
        self.rho_r_axis = np.array(grid_data['axes']['rho_r_axis'])
        self.iodepth_axis = np.array(grid_data['axes']['iodepth_axis'])
        self.numjobs_axis = np.array(grid_data['axes']['numjobs_axis'])
        self.bs_axis = np.array(grid_data['axes']['bs_axis'])
        self.bandwidth_grid = np.array(grid_data['bandwidth_grid'])
        self.metadata = grid_data.get('metadata', {})
        
        # 4D 선형보간기 생성
        self.interpolator = RegularGridInterpolator(
            (self.rho_r_axis, self.iodepth_axis, self.numjobs_axis, self.bs_axis),
            self.bandwidth_grid,
            method='linear',
            bounds_error=False,
            fill_value=None
        )
        
        # 경계 경고 설정
        self._setup_boundary_warnings()
    
    @classmethod
    def from_json_path(cls, path: str) -> "EnvelopeModel":
        """
        JSON 파일에서 엔벌롭 모델 로드
        
        Args:
            path: JSON 파일 경로
            
        Returns:
            EnvelopeModel 인스턴스
        """
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(data)
    
    def query(self, rho_r: float, qd: int, numjobs: int, bs_k: int,
              Br: Optional[float] = None, Bw: Optional[float] = None,
              clamp_physical_limits: bool = True) -> float:
        """
        4D 선형보간으로 Beff 계산
        
        Args:
            rho_r: 읽기 비율 (0-100)
            qd: 큐 깊이 (iodepth)
            numjobs: 병렬 작업 수
            bs_k: 블록 크기 (KiB)
            Br: 읽기 대역폭 상한 (MiB/s, 선택적)
            Bw: 쓰기 대역폭 상한 (MiB/s, 선택적)
            clamp_physical_limits: 물리적 상한 클램프 여부
            
        Returns:
            예측된 혼합 I/O 대역폭 (MiB/s)
        """
        # 입력 검증
        self._validate_inputs(rho_r, qd, numjobs, bs_k)
        
        # 보간 실행
        point = np.array([rho_r, qd, numjobs, bs_k])
        beff = self.interpolator(point)
        
        # 경계 경고
        self._check_boundary_warnings(rho_r, qd, numjobs, bs_k)
        
        # 물리적 상한 클램프 (선택적)
        if clamp_physical_limits and Br is not None and Bw is not None:
            physical_limit = min(Br, Bw)
            if beff > physical_limit:
                warnings.warn(
                    f"Beff ({beff:.1f}) exceeds physical limit ({physical_limit:.1f}), "
                    f"clamping to {physical_limit:.1f} MiB/s"
                )
                beff = physical_limit
        
        return float(beff)
    
    def get_interpolation_error(self, test_points: List[Tuple[int, int, int, int]], 
                              actual_values: List[float]) -> float:
        """
        보간 오차 계산
        
        Args:
            test_points: 테스트 포인트 리스트
            actual_values: 실제 측정값 리스트
            
        Returns:
            평균 절대 백분율 오차 (MAPE)
        """
        if len(test_points) != len(actual_values):
            raise ValueError("test_points and actual_values must have the same length")
        
        errors = []
        for point, actual in zip(test_points, actual_values):
            rho_r, qd, numjobs, bs_k = point
            predicted = self.query(rho_r, qd, numjobs, bs_k)
            
            if actual > 0:
                error = abs(predicted - actual) / actual
                errors.append(error)
        
        return np.mean(errors) if errors else 0.0
    
    def get_grid_statistics(self) -> Dict:
        """
        그리드 통계 정보 반환
        
        Returns:
            통계 정보 딕셔너리
        """
        valid_data = self.bandwidth_grid[self.bandwidth_grid > 0]
        
        return {
            'total_points': self.bandwidth_grid.size,
            'valid_points': len(valid_data),
            'missing_points': self.bandwidth_grid.size - len(valid_data),
            'min_bandwidth': float(valid_data.min()) if len(valid_data) > 0 else 0.0,
            'max_bandwidth': float(valid_data.max()) if len(valid_data) > 0 else 0.0,
            'mean_bandwidth': float(valid_data.mean()) if len(valid_data) > 0 else 0.0,
            'std_bandwidth': float(valid_data.std()) if len(valid_data) > 0 else 0.0
        }
    
    def _validate_inputs(self, rho_r: float, qd: int, numjobs: int, bs_k: int) -> None:
        """입력 값 검증"""
        if not (0 <= rho_r <= 100):
            raise ValueError(f"rho_r must be between 0 and 100, got {rho_r}")
        if qd <= 0:
            raise ValueError(f"qd must be positive, got {qd}")
        if numjobs <= 0:
            raise ValueError(f"numjobs must be positive, got {numjobs}")
        if bs_k <= 0:
            raise ValueError(f"bs_k must be positive, got {bs_k}")
    
    def _setup_boundary_warnings(self) -> None:
        """경계 경고 설정"""
        self.rho_r_bounds = (self.rho_r_axis.min(), self.rho_r_axis.max())
        self.iodepth_bounds = (self.iodepth_axis.min(), self.iodepth_axis.max())
        self.numjobs_bounds = (self.numjobs_axis.min(), self.numjobs_axis.max())
        self.bs_bounds = (self.bs_axis.min(), self.bs_axis.max())
    
    def _check_boundary_warnings(self, rho_r: float, qd: int, numjobs: int, bs_k: int) -> None:
        """경계 경고 확인"""
        warnings_list = []
        
        if not (self.rho_r_bounds[0] <= rho_r <= self.rho_r_bounds[1]):
            warnings_list.append(f"rho_r ({rho_r}) outside grid range {self.rho_r_bounds}")
        
        if not (self.iodepth_bounds[0] <= qd <= self.iodepth_bounds[1]):
            warnings_list.append(f"iodepth ({qd}) outside grid range {self.iodepth_bounds}")
        
        if not (self.numjobs_bounds[0] <= numjobs <= self.numjobs_bounds[1]):
            warnings_list.append(f"numjobs ({numjobs}) outside grid range {self.numjobs_bounds}")
        
        if not (self.bs_bounds[0] <= bs_k <= self.bs_bounds[1]):
            warnings_list.append(f"bs_k ({bs_k}) outside grid range {self.bs_bounds}")
        
        if warnings_list:
            warnings.warn("Extrapolation detected: " + "; ".join(warnings_list))
    
    def __repr__(self) -> str:
        """문자열 표현"""
        stats = self.get_grid_statistics()
        return (f"EnvelopeModel(valid_points={stats['valid_points']}, "
                f"bandwidth_range=[{stats['min_bandwidth']:.1f}, {stats['max_bandwidth']:.1f}] MiB/s)")


def test_envelope_model():
    """엔벌롭 모델 테스트"""
    print("=== EnvelopeModel Test ===")
    
    # 테스트용 더미 데이터 생성
    test_data = {
        'metadata': {'version': 'v4.0-test'},
        'axes': {
            'rho_r_axis': [0, 25, 50, 75, 100],
            'iodepth_axis': [1, 4, 16, 64],
            'numjobs_axis': [1, 2, 4],
            'bs_axis': [4, 64, 1024]
        },
        'bandwidth_grid': np.random.uniform(1000, 3000, (5, 4, 3, 3)).tolist()
    }
    
    # 모델 생성
    model = EnvelopeModel(test_data)
    print(f"Model created: {model}")
    
    # 통계 정보
    stats = model.get_grid_statistics()
    print(f"Grid statistics: {stats}")
    
    # 테스트 쿼리
    test_points = [
        (50, 16, 2, 64),    # 중간값
        (0, 1, 1, 4),       # 최소값
        (100, 64, 4, 1024), # 최대값
        (25, 8, 3, 128),    # 경계값
    ]
    
    print("\nTest queries:")
    for point in test_points:
        rho_r, qd, numjobs, bs_k = point
        beff = model.query(rho_r, qd, numjobs, bs_k)
        print(f"  {point} -> {beff:.1f} MiB/s")
    
    print("✅ EnvelopeModel test completed")

if __name__ == "__main__":
    test_envelope_model()
