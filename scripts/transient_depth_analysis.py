#!/usr/bin/env python3
from math import inf
B_w, B_r, B_eff, eta = 1000.0, 2000.0, 2500.0, 1.0
T, L = 10, 6
CR_default, wal_factor = 0.50, 1.0
CR = [CR_default]*(L+1)
S_in, S_cap = 400.0, None
alpha = T/(T-1.0)

def coeffs(depth):
    w = CR[0] + wal_factor
    r = 0.0
    for i in range(1, depth+1):
        r += (CR[i-1] + CR[i]*alpha)
        w += (CR[i]*(1.0+alpha))
    return w, r

def smax(depth):
    w, r = coeffs(depth)
    s_w = (B_w/w) if w>0 else inf
    s_r = (B_r/r) if r>0 else inf
    s_m = (B_eff/(w + eta*r)) if (B_eff and (w+eta*r)>0) else inf
    s = min(s_w, s_r, s_m)
    return s, s_w, s_r, s_m, w, r

Smax_full, *_ = smax(L)
if S_cap is None: S_cap = Smax_full

print("Depth  S_max  S_acc  TotRead  TotWrite  %R  %W  Bottleneck")
for d in range(1, L+1):
    S_d, S_w, S_r, S_m, w_c, r_c = smax(d)
    S_acc = min(S_in, S_cap, S_d)
    R = S_acc * r_c
    W = S_acc * w_c
    vals = [(S_w,'write'), (S_r,'read'), (S_m,'mix')]
    bname = min(vals, key=lambda x: x[0])[1]
    print(f"{d:5d}  {S_d:5.1f}  {S_acc:5.1f}  {R:7.1f}  {W:8.1f}  {100*R/B_r:4.1f}%  {100*W/B_w:4.1f}%  {bname}")
