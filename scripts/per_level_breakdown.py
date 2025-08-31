#!/usr/bin/env python3
S_user, T, L = 150.0, 10, 6
wal_factor, CR_default = 1.0, 0.50
CR = [CR_default]*(L+1)
B_w, B_r = 1000.0, 2000.0
alpha = T/(T-1.0)

rows = []
l0_w = S_user*CR[0]
rows.append(("L0 (flush)", 0.0, l0_w))
for i in range(1, L+1):
    r_i = S_user*(CR[i-1] + CR[i]*alpha)
    w_i = S_user*(CR[i]*(1.0+alpha))
    rows.append((f"L{i}", r_i, w_i))
rows.append(("WAL", 0.0, S_user*wal_factor))

hdr = "Level                Read(MiB/s)   Write(MiB/s)   %ReadBW  %WriteBW"
print(hdr) ; print("-"*len(hdr))
rt, wt = 0.0, 0.0
for lvl, r, w in rows:
    rt += r; wt += w
    pr = (100.0*r/B_r) if B_r else 0.0
    pw = (100.0*w/B_w) if B_w else 0.0
    print(f"{lvl:16s}  {r:11.2f}   {w:12.2f}   {pr:6.1f}%   {pw:7.1f}%")
print("-"*len(hdr))
pr = (100.0*rt/B_r) if B_r else 0.0
pw = (100.0*wt/B_w) if B_w else 0.0
print(f"TOTAL               {rt:11.2f}   {wt:12.2f}   {pr:6.1f}%   {pw:7.1f}%")
