#!/usr/bin/env python3
from math import inf

B_w, B_r, B_eff, eta = 1000.0, 2000.0, 2500.0, 1.0
avg_kv_bytes = 1024.0
CR_list = [1.0, 0.7, 0.5, 0.33]
WA_list = [4, 6, 8, 10]
wal_factor = 1.0

def bounds_for(CR, WA):
    w_req = CR*WA + wal_factor
    r_req = CR*max(WA-1.0, 0.0)
    s_w = (B_w / w_req) if w_req > 0 else inf
    s_r = (B_r / r_req) if r_req > 0 else inf
    s_m = (B_eff / (w_req + eta*r_req)) if (B_eff and (w_req + eta*r_req) > 0) else inf
    s_max = min(s_w, s_r, s_m)
    return s_w, s_r, s_m, s_max, w_req, r_req

print('CR\tWA\tReqWrite/u\tReqRead/u\tS_write\tS_read\tS_mix\tS_max\tops/s')
for CR in CR_list:
    for WA in WA_list:
        s_w, s_r, s_m, s_max, w_req, r_req = bounds_for(CR, WA)
        ops = (s_max*1048576.0)/avg_kv_bytes
        def f(x): return 'inf' if x == inf else f'{x:.1f}'
        print(f'{CR:.2f}\t{WA:.2f}\t{w_req:.2f}\t\t{r_req:.2f}\t\t{f(s_w)}\t{f(s_r)}\t{f(s_m)}\t{f(s_max)}\t{ops:.0f}')
