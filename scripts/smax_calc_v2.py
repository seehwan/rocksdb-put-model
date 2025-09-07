#!/usr/bin/env python3
"""
RocksDB S_max Calculator v2.1

v2.1 모델을 사용하여 최대 지속 가능한 put rate (S_max)를 계산합니다.
주요 개선사항:
- Harmonic mean을 사용한 Mixed I/O Capacity 모델링
- Per-Level Capacity & Concurrency 고려
- Stall Duty Cycle 모델링
"""
import argparse
import json
from math import inf

def calculate_harmonic_mean_bandwidth(B_r, B_w, rho_r, rho_w):
    """
    Harmonic mean을 사용한 혼합 I/O 대역폭 계산
    
    B_eff(ρ_r, ρ_w) = 1 / (ρ_r / B_r + ρ_w / B_w)
    """
    if rho_r == 0 or rho_w == 0:
        return inf
    
    B_eff = 1 / (rho_r / B_r + rho_w / B_w)
    return B_eff

def calculate_per_level_io(level_data, total_write_gb, S_put):
    """
    레벨별 I/O 계산
    
    Per-level writes W_l = share_l · (WA_device · S_put)
    Per-level reads R_l = (read_to_write)_l · W_l
    """
    level_io = {}
    
    for level, data in level_data.items():
        share_l = data['write_gb'] / total_write_gb
        read_to_write = data['w_amp']
        
        # 레벨별 쓰기 (MiB/s)
        W_l = share_l * S_put
        
        # 레벨별 읽기 (MiB/s)
        R_l = read_to_write * W_l
        
        level_io[level] = {
            'write_mib_s': W_l,
            'read_mib_s': R_l,
            'total_mib_s': W_l + R_l,
            'share_l': share_l,
            'read_to_write': read_to_write
        }
    
    return level_io

def calculate_smax_v2(B_w, B_r, rho_r, rho_w, CR, WA, level_data, total_write_gb, p_stall=0.0):
    """
    v2.1 모델을 사용한 S_max 계산
    
    Args:
        B_w: 쓰기 대역폭 (MiB/s)
        B_r: 읽기 대역폭 (MiB/s)
        rho_r: 읽기 비율
        rho_w: 쓰기 비율
        CR: 압축률
        WA: Write Amplification
        level_data: 레벨별 데이터
        total_write_gb: 총 쓰기 (GB)
        p_stall: Stall 확률
    
    Returns:
        dict: 계산 결과
    """
    
    # 1. Harmonic mean을 사용한 혼합 I/O 대역폭 계산
    B_eff_harmonic = calculate_harmonic_mean_bandwidth(B_r, B_w, rho_r, rho_w)
    
    # 2. per-user 디바이스 요구 바이트
    w_req = CR * WA
    r_req = CR * max(WA - 1.0, 0.0)
    
    # 3. 기본 바운드 계산 (v1과 동일)
    s_write = (B_w / w_req) if w_req > 0 else inf
    s_read = (B_r / r_req) if r_req > 0 else inf
    
    # 4. v2.1의 Harmonic mean 바운드
    s_mix_harmonic = (B_eff_harmonic / (w_req + r_req)) if (B_eff_harmonic and (w_req + r_req) > 0) else inf
    
    # 5. Per-level 제약사항 고려
    # 각 레벨별로 I/O 제약을 확인
    level_constraints = {}
    min_level_s = inf
    
    for level, data in level_data.items():
        share_l = data['write_gb'] / total_write_gb
        read_to_write = data['w_amp']
        
        # 레벨별 I/O 요구량
        level_w_req = share_l * w_req
        level_r_req = read_to_write * level_w_req
        level_total_req = level_w_req + level_r_req
        
        # 레벨별 최대 처리량 (단순화: 전체 대역폭의 비율로 가정)
        level_capacity = B_eff_harmonic * share_l
        
        if level_total_req > 0:
            level_s = level_capacity / level_total_req
            level_constraints[level] = {
                'level_s': level_s,
                'level_capacity': level_capacity,
                'level_total_req': level_total_req,
                'share_l': share_l
            }
            min_level_s = min(min_level_s, level_s)
    
    # 6. 최종 S_max 계산 (모든 제약사항 고려)
    s_max_feasible = min(s_write, s_read, s_mix_harmonic, min_level_s)
    
    # 7. Stall 효과 적용
    s_max_final = s_max_feasible * (1 - p_stall)
    
    # 8. 병목 지점 식별
    bottlenecks = []
    if s_write == s_max_feasible:
        bottlenecks.append("write")
    if s_read == s_max_feasible:
        bottlenecks.append("read")
    if s_mix_harmonic == s_max_feasible:
        bottlenecks.append("mixed_harmonic")
    if min_level_s == s_max_feasible:
        bottlenecks.append("level_constraint")
    
    return {
        's_max_feasible': s_max_feasible,
        's_max_final': s_max_final,
        's_write': s_write,
        's_read': s_read,
        's_mix_harmonic': s_mix_harmonic,
        'B_eff_harmonic': B_eff_harmonic,
        'w_req': w_req,
        'r_req': r_req,
        'rho_r': rho_r,
        'rho_w': rho_w,
        'p_stall': p_stall,
        'bottlenecks': bottlenecks,
        'level_constraints': level_constraints,
        'min_level_s': min_level_s,
        'CR': CR,
        'WA': WA,
        'B_w': B_w,
        'B_r': B_r
    }

def format_value(value):
    """값을 포맷팅합니다."""
    if value == inf:
        return "inf"
    return f"{value:.1f}"

def print_results(result):
    """결과를 출력합니다."""
    print("=" * 70)
    print("RocksDB S_max 계산 결과 (v2.1 모델)")
    print("=" * 70)
    
    print(f"입력 파라미터:")
    print(f"  압축률 (CR): {result['CR']:.2f}")
    print(f"  Write Amplification (WA): {result['WA']:.1f}")
    print(f"  쓰기 대역폭 (B_w): {result['B_w']:.0f} MiB/s")
    print(f"  읽기 대역폭 (B_r): {result['B_r']:.0f} MiB/s")
    print(f"  읽기 비율 (ρ_r): {result['rho_r']:.3f}")
    print(f"  쓰기 비율 (ρ_w): {result['rho_w']:.3f}")
    print(f"  Stall 확률 (p_stall): {result['p_stall']:.3f}")
    
    print(f"\n계산 결과:")
    print(f"  per-user 쓰기 요구량: {result['w_req']:.2f}")
    print(f"  per-user 읽기 요구량: {result['r_req']:.2f}")
    print(f"  Harmonic mean 대역폭: {format_value(result['B_eff_harmonic'])} MiB/s")
    
    print(f"\n바운드별 S_max:")
    print(f"  Write bound:        {format_value(result['s_write'])} MiB/s")
    print(f"  Read bound:         {format_value(result['s_read'])} MiB/s")
    print(f"  Mixed (Harmonic):   {format_value(result['s_mix_harmonic'])} MiB/s")
    print(f"  Level constraint:   {format_value(result['min_level_s'])} MiB/s")
    
    print(f"\n최종 S_max:")
    print(f"  Feasible (stall 전): {format_value(result['s_max_feasible'])} MiB/s")
    print(f"  Final (stall 후):    {format_value(result['s_max_final'])} MiB/s")
    print(f"  병목 지점: {', '.join(result['bottlenecks'])}")
    
    # ops/s 환산 (평균 KV 크기 1024 bytes 가정)
    avg_kv_bytes = 1024
    ops_per_sec = (result['s_max_final'] * 1048576) / avg_kv_bytes if result['s_max_final'] != inf else 0
    print(f"  ops/s (1KB KV): {ops_per_sec:.0f}")
    
    # 레벨별 제약사항 상세
    print(f"\n레벨별 제약사항:")
    for level, constraint in result['level_constraints'].items():
        print(f"  {level}: {format_value(constraint['level_s'])} MiB/s "
              f"(공유율: {constraint['share_l']:.3f}, "
              f"용량: {format_value(constraint['level_capacity'])} MiB/s)")
    
    # v2.1 모델의 개선점
    print(f"\nv2.1 모델 개선점:")
    print(f"  ✅ Harmonic mean 혼합 I/O 모델링")
    print(f"  ✅ Per-level 제약사항 고려")
    print(f"  ✅ Stall 효과 반영 ({(1-result['p_stall'])*100:.1f}% 효율성)")

def main():
    parser = argparse.ArgumentParser(description='RocksDB S_max Calculator v2.1')
    parser.add_argument('--cr', type=float, required=True, help='압축률 (on-disk/user)')
    parser.add_argument('--wa', type=float, required=True, help='Write Amplification')
    parser.add_argument('--bw', type=float, required=True, help='쓰기 대역폭 (MiB/s)')
    parser.add_argument('--br', type=float, required=True, help='읽기 대역폭 (MiB/s)')
    parser.add_argument('--rho-r', type=float, required=True, help='읽기 비율 (ρ_r)')
    parser.add_argument('--rho-w', type=float, required=True, help='쓰기 비율 (ρ_w)')
    parser.add_argument('--p-stall', type=float, default=0.0, help='Stall 확률 (기본 0.0)')
    parser.add_argument('--json', action='store_true', help='JSON 형식으로 출력')
    
    args = parser.parse_args()
    
    # 레벨별 데이터 (실험 데이터에서 추출)
    level_data = {
        'L0': {'write_gb': 1670.1, 'w_amp': 0.0},
        'L1': {'write_gb': 1036.0, 'w_amp': 0.0},
        'L2': {'write_gb': 3968.1, 'w_amp': 22.6},
        'L3': {'write_gb': 2096.4, 'w_amp': 0.9}
    }
    total_write_gb = 8770.6
    
    # v2.1 모델로 S_max 계산
    result = calculate_smax_v2(
        B_w=args.bw,
        B_r=args.br,
        rho_r=args.rho_r,
        rho_w=args.rho_w,
        CR=args.cr,
        WA=args.wa,
        level_data=level_data,
        total_write_gb=total_write_gb,
        p_stall=args.p_stall
    )
    
    if args.json:
        # inf 값을 문자열로 변환
        json_result = result.copy()
        for key in ['s_max_feasible', 's_max_final', 's_write', 's_read', 's_mix_harmonic', 'B_eff_harmonic', 'min_level_s']:
            if json_result[key] == inf:
                json_result[key] = "inf"
        
        # level_constraints의 inf 값도 변환
        for level, constraint in json_result['level_constraints'].items():
            for key in ['level_s', 'level_capacity']:
                if constraint[key] == inf:
                    constraint[key] = "inf"
        
        print(json.dumps(json_result, indent=2))
    else:
        print_results(result)

if __name__ == "__main__":
    main()
