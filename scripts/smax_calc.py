#!/usr/bin/env python3
"""
RocksDB S_max Calculator

디바이스 특성과 압축률, Write Amplification을 기반으로 
최대 지속 가능한 put rate (S_max)를 계산합니다.
"""
import argparse
from math import inf

def calculate_smax(cr, wa, bw, br, beff, eta=1.0, wwal=0.0):
    """
    S_max를 계산합니다.
    
    Args:
        cr: 압축률 (on-disk/user)
        wa: Write Amplification
        bw: 쓰기 대역폭 (MiB/s)
        br: 읽기 대역폭 (MiB/s)
        beff: 혼합 대역폭 (MiB/s)
        eta: 혼합 제약의 읽기 가중 (기본 1.0)
        wwal: WAL 바이트/유저바이트 (기본 0.0)
    
    Returns:
        dict: 계산 결과
    """
    # per-user 디바이스 요구 바이트
    w_req = cr * wa + wwal
    r_req = cr * max(wa - 1.0, 0.0)
    
    # 세 가지 바운드 계산
    s_write = (bw / w_req) if w_req > 0 else inf
    s_read = (br / r_req) if r_req > 0 else inf
    s_mix = (beff / (w_req + eta * r_req)) if (beff and (w_req + eta * r_req) > 0) else inf
    
    # S_max는 세 바운드의 최소값
    s_max = min(s_write, s_read, s_mix)
    
    # 병목 지점 식별
    bottlenecks = []
    if s_write == s_max:
        bottlenecks.append("write")
    if s_read == s_max:
        bottlenecks.append("read")
    if s_mix == s_max:
        bottlenecks.append("mixed")
    
    return {
        's_max': s_max,
        's_write': s_write,
        's_read': s_read,
        's_mix': s_mix,
        'w_req': w_req,
        'r_req': r_req,
        'bottlenecks': bottlenecks,
        'cr': cr,
        'wa': wa,
        'bw': bw,
        'br': br,
        'beff': beff,
        'eta': eta,
        'wwal': wwal
    }

def format_value(value):
    """값을 포맷팅합니다."""
    if value == inf:
        return "inf"
    return f"{value:.1f}"

def print_results(result):
    """결과를 출력합니다."""
    print("=" * 60)
    print("RocksDB S_max 계산 결과")
    print("=" * 60)
    
    print(f"입력 파라미터:")
    print(f"  압축률 (CR): {result['cr']:.2f}")
    print(f"  Write Amplification (WA): {result['wa']:.1f}")
    print(f"  쓰기 대역폭 (B_w): {result['bw']:.0f} MiB/s")
    print(f"  읽기 대역폭 (B_r): {result['br']:.0f} MiB/s")
    print(f"  혼합 대역폭 (B_eff): {result['beff']:.0f} MiB/s")
    print(f"  읽기 가중 (η): {result['eta']:.1f}")
    print(f"  WAL 팩터 (w_wal): {result['wwal']:.1f}")
    
    print(f"\n계산 결과:")
    print(f"  per-user 쓰기 요구량: {result['w_req']:.2f}")
    print(f"  per-user 읽기 요구량: {result['r_req']:.2f}")
    
    print(f"\n바운드별 S_max:")
    print(f"  Write bound:  {format_value(result['s_write'])} MiB/s")
    print(f"  Read bound:   {format_value(result['s_read'])} MiB/s")
    print(f"  Mixed bound:  {format_value(result['s_mix'])} MiB/s")
    
    print(f"\n최종 S_max: {format_value(result['s_max'])} MiB/s")
    print(f"병목 지점: {', '.join(result['bottlenecks'])}")
    
    # ops/s 환산 (평균 KV 크기 1024 bytes 가정)
    avg_kv_bytes = 1024
    ops_per_sec = (result['s_max'] * 1048576) / avg_kv_bytes if result['s_max'] != inf else 0
    print(f"ops/s (1KB KV): {ops_per_sec:.0f}")
    
    # 성능 권장사항
    print(f"\n성능 권장사항:")
    if "write" in result['bottlenecks']:
        print("  ⚠️  Write 대역폭이 병목입니다.")
        print("     - SSD 업그레이드 고려")
        print("     - WAL을 별도 디바이스로 분리")
        print("     - 압축률 개선으로 쓰기 요구량 감소")
    
    if "read" in result['bottlenecks']:
        print("  ⚠️  Read 대역폭이 병목입니다.")
        print("     - 읽기 전용 디바이스 추가 고려")
        print("     - 압축률 개선으로 읽기 요구량 감소")
    
    if "mixed" in result['bottlenecks']:
        print("  ⚠️  혼합 I/O 대역폭이 병목입니다.")
        print("     - 전체 시스템 대역폭 개선 필요")
        print("     - I/O 패턴 최적화 고려")
    
    if result['s_max'] > 0 and result['s_max'] != inf:
        print(f"  ✅ 예상 지속 가능한 put rate: {format_value(result['s_max'])} MiB/s")
    else:
        print("  ❌ 현재 설정으로는 지속 가능한 put rate를 달성할 수 없습니다.")

def main():
    parser = argparse.ArgumentParser(description='RocksDB S_max Calculator')
    parser.add_argument('--cr', type=float, required=True, help='압축률 (on-disk/user)')
    parser.add_argument('--wa', type=float, required=True, help='Write Amplification')
    parser.add_argument('--bw', type=float, required=True, help='쓰기 대역폭 (MiB/s)')
    parser.add_argument('--br', type=float, required=True, help='읽기 대역폭 (MiB/s)')
    parser.add_argument('--beff', type=float, required=True, help='혼합 대역폭 (MiB/s)')
    parser.add_argument('--eta', type=float, default=1.0, help='읽기 가중 (기본 1.0)')
    parser.add_argument('--wwal', type=float, default=0.0, help='WAL 팩터 (기본 0.0)')
    parser.add_argument('--json', action='store_true', help='JSON 형식으로 출력')
    
    args = parser.parse_args()
    
    # S_max 계산
    result = calculate_smax(
        cr=args.cr,
        wa=args.wa,
        bw=args.bw,
        br=args.br,
        beff=args.beff,
        eta=args.eta,
        wwal=args.wwal
    )
    
    if args.json:
        import json
        # inf 값을 문자열로 변환
        json_result = result.copy()
        for key in ['s_max', 's_write', 's_read', 's_mix']:
            if json_result[key] == inf:
                json_result[key] = "inf"
        print(json.dumps(json_result, indent=2))
    else:
        print_results(result)

if __name__ == "__main__":
    main()
