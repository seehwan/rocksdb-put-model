#!/usr/bin/env python3
"""
Parse RocksDB compaction logs to extract per-level IO per minute and render a dot plot.

The script reads EVENT/STAT lines from `rocksdb_log_phase_b.log`, aggregates
hour/minute level read/write volumes, emits a CSV, and produces a PNG summary.

Usage:
    python compaction_level_io_by_minute.py \
        --log ../rocksdb_log_phase_b.log \
        --csv ../results/compaction_level_io_per_minute.csv \
        --png ../compaction_level_io_per_minute.png
"""

import argparse
import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from PIL import Image, ImageDraw, ImageFont


LOG_RE_COMPACTION_START = re.compile(r"^\*\* Compaction Stats \[default\] \*\*")
LOG_RE_LEVEL_PREFIX = re.compile(r"^\s*(L\d+)")
LOG_RE_UPTIME = re.compile(r"Uptime\(secs\):\s*([0-9.]+)")


def parse_compaction_blocks(lines: Iterable[str]) -> Dict[int, Dict[str, Dict[str, float]]]:
    """
    Parse the log and return per-minute, per-level read/write MB totals.
    """

    minute_level_data: Dict[int, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {"read_mb": 0.0, "write_mb": 0.0})
    )

    lines_list = list(lines)
    total_lines = len(lines_list)
    i = 0
    pending_blocks: List[Dict[str, Dict[str, float]]] = []
    prev_stats: Dict[str, Dict[str, float]] = defaultdict(lambda: {"rn": 0.0, "rnp1": 0.0, "write": 0.0})

    while i < total_lines:
        line = lines_list[i]

        if LOG_RE_COMPACTION_START.match(line):
            # Skip header line and column definition line
            i += 2

            block_data: Dict[str, Dict[str, float]] = defaultdict(lambda: {"read_mb": 0.0, "write_mb": 0.0})

            while i < total_lines:
                text = lines_list[i]
                stripped = text.strip()

                if (
                    not stripped
                    or stripped.startswith("**")
                    or stripped.startswith("Priority")
                    or stripped.startswith("Sum")
                    or stripped.startswith("Int")
                ):
                    break

                if LOG_RE_LEVEL_PREFIX.match(stripped):
                    parts = stripped.split()
                    try:
                        level = parts[0]
                        score = float(parts[4])  # unused but helps align indexes
                        rn_gb = float(parts[6])
                        rnp1_gb = float(parts[7])
                        write_gb = float(parts[8])
                    except (IndexError, ValueError):
                        i += 1
                        continue

                    prev = prev_stats[level]
                    delta_rn = rn_gb - prev["rn"]
                    delta_rnp1 = rnp1_gb - prev["rnp1"]
                    delta_write = write_gb - prev["write"]

                    if delta_rn < 0:
                        delta_rn = rn_gb
                    if delta_rnp1 < 0:
                        delta_rnp1 = rnp1_gb
                    if delta_write < 0:
                        delta_write = write_gb

                    block_data[level]["read_mb"] += delta_rn * 1024.0
                    block_data[level]["write_mb"] += delta_write * 1024.0

                    if delta_rnp1 > 0.0:
                        next_level = f"L{int(level[1:]) + 1}"
                        block_data[next_level]["read_mb"] += delta_rnp1 * 1024.0

                    prev_stats[level] = {"rn": rn_gb, "rnp1": rnp1_gb, "write": write_gb}

                i += 1

            pending_blocks.append(block_data)

            # Skip optional Priority table if present
            if i < total_lines and LOG_RE_COMPACTION_START.match(lines_list[i]):
                if i + 1 < total_lines and "Priority" in lines_list[i + 1]:
                    i += 2
                    while i < total_lines:
                        stripped = lines_list[i].strip()
                        if not stripped or stripped.startswith("**"):
                            break
                        i += 1

            continue

        uptime_match = LOG_RE_UPTIME.search(line)
        if uptime_match and pending_blocks:
            minute_bucket = int(float(uptime_match.group(1)) // 60)
            for block in pending_blocks:
                for level, io in block.items():
                    bucket = minute_level_data[minute_bucket][level]
                    bucket["read_mb"] += io["read_mb"]
                    bucket["write_mb"] += io["write_mb"]
            pending_blocks.clear()

        i += 1

    # Flush any remaining blocks if log ends without uptime line
    if pending_blocks:
        minute_bucket = max(minute_level_data.keys(), default=0)
        for block in pending_blocks:
            for level, io in block.items():
                bucket = minute_level_data[minute_bucket][level]
                bucket["read_mb"] += io["read_mb"]
                bucket["write_mb"] += io["write_mb"]

    return minute_level_data


def write_csv(output_csv: Path, minute_level_data: Dict[int, Dict[str, Dict[str, float]]]) -> None:
    minutes = sorted(minute_level_data.keys())
    levels = sorted({lvl for data in minute_level_data.values() for lvl in data.keys()}, key=lambda x: int(x[1:]))

    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["minute", "hour", "level", "read_mb", "write_mb"])

        for minute in minutes:
            hour = minute / 60.0
            level_map = minute_level_data[minute]
            for level in levels:
                io = level_map.get(level, {"read_mb": 0.0, "write_mb": 0.0})
                writer.writerow([minute, f"{hour:.4f}", level, f"{io['read_mb']:.3f}", f"{io['write_mb']:.3f}"])


def render_png(output_path: Path, minute_level_data: Dict[int, Dict[str, Dict[str, float]]]) -> None:
    minutes = sorted(minute_level_data.keys())
    levels = sorted({lvl for data in minute_level_data.values() for lvl in data.keys()}, key=lambda x: int(x[1:]))

    hours = [m / 60.0 for m in minutes]
    write_series = {lvl: [minute_level_data[m].get(lvl, {}).get("write_mb", 0.0) for m in minutes] for lvl in levels}
    read_series = {lvl: [minute_level_data[m].get(lvl, {}).get("read_mb", 0.0) for m in minutes] for lvl in levels}

    width, height = 1200, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_tick = ImageFont.load_default()

    left_margin = 100
    right_margin = 220
    top_margin = 80
    chart_height = 320
    gap = 80
    chart_width = width - left_margin - right_margin

    palette = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    color_map = {
        level: tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        for level, color in zip(levels, palette)
    }

    def plot_panel(y0: int, title: str, series_dict: Dict[str, List[float]]) -> None:
        y1 = y0 + chart_height
        max_value = max((max(series) for series in series_dict.values()), default=1.0)
        if max_value <= 0:
            max_value = 1.0

        draw.rectangle([left_margin, y0, left_margin + chart_width, y1], outline="black")
        draw.text((left_margin, y0 - 25), title, fill="black", font=font_title)
        draw.text((left_margin - 80, y0 - 15), "MB", fill="black", font=font_tick)
        draw.text((left_margin + chart_width / 2 - 40, y1 + 35), "Time (hours)", fill="black", font=font_tick)

        num_y_ticks = 6
        for i in range(num_y_ticks):
            value = max_value * i / (num_y_ticks - 1)
            y = y1 - (value / max_value) * (y1 - y0)
            draw.line([(left_margin, y), (left_margin + chart_width, y)], fill="#dddddd")
            label = f"{value/1024:.1f} GB" if max_value >= 2048 else f"{value:.0f} MB"
            draw.text((left_margin - 65, y - 7), label, fill="black", font=font_tick)

        num_x_ticks = 8
        min_hour = hours[0]
        max_hour = hours[-1] if hours[-1] > min_hour else min_hour + 1.0
        for i in range(num_x_ticks):
            idx = round((len(hours) - 1) * i / (num_x_ticks - 1)) if len(hours) > 1 else 0
            hour_val = hours[idx]
            x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
            draw.line([(x, y0), (x, y1)], fill="#dddddd")
            draw.text((x - 20, y1 + 10), f"{hour_val:.1f}", fill="black", font=font_tick)

        step = max(1, len(hours) // 4000)
        for level in levels:
            color = color_map.get(level, (0, 0, 0))
            series = series_dict[level]
            for idx in range(0, len(hours), step):
                hour_val = hours[idx]
                value = series[idx]
                x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
                y = y1 - (value / max_value) * (y1 - y0)
                draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color, outline=color)

        legend_x = left_margin + chart_width + 20
        legend_y = y0 + 10
        for level in levels:
            color = color_map.get(level, (0, 0, 0))
            draw.rectangle([legend_x, legend_y, legend_x + 15, legend_y + 15], fill=color, outline=color)
            draw.text((legend_x + 20, legend_y), level, fill="black", font=font_tick)
            legend_y += 20

    plot_panel(top_margin, "Compaction Write Data per Minute by Level (MB)", write_series)
    plot_panel(top_margin + chart_height + gap, "Compaction Read Data per Minute by Level (MB)", read_series)
    image.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse RocksDB compaction log by level per minute.")
    parser.add_argument("--log", type=Path, default=Path("../rocksdb_log_phase_b.log"), help="Path to RocksDB LOG file.")
    parser.add_argument("--csv", type=Path, default=Path("../results/compaction_level_io_per_minute.csv"), help="Output CSV path.")
    parser.add_argument("--png", type=Path, default=Path("../compaction_level_io_per_minute.png"), help="Output PNG path.")
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"Log file not found: {args.log}")

    print(f"Parsing log: {args.log}")
    minute_level_data = parse_compaction_blocks(args.log.read_text().splitlines())

    print(f"Writing CSV: {args.csv}")
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.csv, minute_level_data)

    print(f"Rendering PNG: {args.png}")
    render_png(args.png, minute_level_data)
    print("Done.")


if __name__ == "__main__":
    main()
