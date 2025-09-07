#!/usr/bin/env python3
import os, argparse
from math import inf
import matplotlib.pyplot as plt

# Set font size to 18pt for better readability
plt.rcParams.update({
    'font.size': 18,
    'axes.titlesize': 20,
    'axes.labelsize': 18,
    'xtick.labelsize': 16,
    'ytick.labelsize': 16,
    'legend.fontsize': 16,
    'figure.titlesize': 22
})

B_w, B_r, B_eff, eta = 1000.0, 2000.0, 2500.0, 1.0
wal_factor, avg_kv_bytes = 1.0, 1024.0
CR_curve = [1.0, 0.7, 0.5, 0.33]
WA_min, WA_max, WA_step = 2, 12, 1
T, L = 10, 6
CR_default = 0.50
CR_levels = [CR_default]*(L+1)
S_user = 150.0
S_in, S_cap = 400.0, None

def bounds_for(CR, WA):
    w_req = CR*WA + wal_factor
    r_req = CR*max(WA-1.0, 0.0)
    s_w = (B_w / w_req) if w_req > 0 else float('inf')
    s_r = (B_r / r_req) if r_req > 0 else float('inf')
    s_m = (B_eff / (w_req + eta*r_req)) if (B_eff and (w_req + eta*r_req) > 0) else float('inf')
    s_max = min(s_w, s_r, s_m)
    return s_max

def alpha(): return T/(T-1.0)

def per_level_flows(S):
    a = alpha()
    labels, reads, writes = [], [], []
    labels.append("L0"); reads.append(0.0); writes.append(S*CR_levels[0])
    for i in range(1, L+1):
        r_i = S*(CR_levels[i-1] + CR_levels[i]*a)
        w_i = S*(CR_levels[i]*(1.0+a))
        labels.append(f"L{i}"); reads.append(r_i); writes.append(w_i)
    labels.append("WAL"); reads.append(0.0); writes.append(S*wal_factor)
    return labels, reads, writes

def coeffs(depth):
    a = alpha()
    w = CR_levels[0] + wal_factor
    r = 0.0
    for i in range(1, depth+1):
        r += (CR_levels[i-1] + CR_levels[i]*a)
        w += (CR_levels[i]*(1.0+a))
    return w, r

def smax_depth(depth):
    w, r = coeffs(depth)
    s_w = (B_w/w)
    s_r = (B_r/r) if r>0 else float('inf')
    s_m = (B_eff/(w + eta*r)) if (B_eff and (w+eta*r)>0) else float('inf')
    return min(s_w, s_r, s_m)

def plot_smax_vs_WA(outdir):
    xs = list(range(WA_min, WA_max+1, WA_step))
    plt.figure()
    for CR in CR_curve:
        ys = [bounds_for(CR, WA) for WA in xs]
        plt.plot(xs, ys, marker='o', label=f"CR={CR:.2f}")
    plt.xlabel("Write Amplification (WA)")
    plt.ylabel("S_max (MiB/s user)")
    plt.title("Steady-State S_max vs WA (by CR)")
    plt.legend()
    out = os.path.join(outdir, "smax_vs_WA.png")
    plt.savefig(out, dpi=144, bbox_inches="tight"); plt.close(); return out

def plot_per_level_bars(outdir, S):
    labels, reads, writes = per_level_flows(S)
    plt.figure(); plt.bar(labels, writes); plt.title(f"Per-Level Writes @ S={S:.1f} MiB/s"); plt.ylabel("Write MiB/s")
    out_w = os.path.join(outdir, "per_level_writes.png"); plt.savefig(out_w, dpi=144, bbox_inches="tight"); plt.close()
    plt.figure(); plt.bar(labels, reads); plt.title(f"Per-Level Reads @ S={S:.1f} MiB/s"); plt.ylabel("Read MiB/s")
    out_r = os.path.join(outdir, "per_level_reads.png"); plt.savefig(out_r, dpi=144, bbox_inches="tight"); plt.close()
    return out_w, out_r

def plot_depth_summary(outdir):
    xs = list(range(1, L+1))
    smax_list = [smax_depth(d) for d in xs]
    s_full = smax_depth(L)
    s_cap_eff = s_full if S_cap is None else min(S_cap, s_full)
    sacc_list = [min(S_in, s_cap_eff, smax_depth(d)) for d in xs]
    plt.figure(); plt.plot(xs, smax_list, marker='o', label="S_max(depth)"); plt.plot(xs, sacc_list, marker='x', label="S_acc(depth)")
    plt.xlabel("Active Depth (levels built)"); plt.ylabel("Throughput (MiB/s user)"); plt.title("Depth-wise S_max and S_acc"); plt.legend()
    out = os.path.join(outdir, "depth_summary.png"); plt.savefig(out, dpi=144, bbox_inches="tight"); plt.close(); return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--outdir", default="figs"); ap.add_argument("--run", action="store_true"); args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    if args.run:
        print(plot_smax_vs_WA(args.outdir)); print(plot_per_level_bars(args.outdir, S_user)); print(plot_depth_summary(args.outdir))
    else:
        print("Run with --run to generate figures.")
if __name__ == "__main__": main()
