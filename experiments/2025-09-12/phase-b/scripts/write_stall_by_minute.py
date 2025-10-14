#!/usr/bin/env python3
"""
Parse write stall information from RocksDB LOG and aggregate by minute.

Outputs a CSV with flush/compaction delay/stop counts and interval stall
duration (seconds) per minute. Also produces a PNG visualization.
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable

from PIL import Image, ImageDraw, ImageFont


STALL_COUNT_PATTERN = re.compile(r"([a-z0-9_-]+):\s*([0-9]+)")
UPTIME_PATTERN = re.compile(r"Uptime\(secs\):\s*([0-9.]+)")
INTERVAL_STALL_PATTERN = re.compile(r"Interval stall:\s*([0-9:.]+) H:M:S")


def parse_time_string(hms: str) -> float:
    h, m, s = hms.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_stall_data(lines: Iterable[str]) -> Dict[int, Dict[str, float]]:
    minute_data = defaultdict(lambda: {
        "flush_delays": 0.0,
        "flush_stops": 0.0,
        "comp_delays": 0.0,
        "comp_stops": 0.0,
        "stall_seconds": 0.0,
    })

    current_minute = 0
    prev_counts = {}

    for line in lines:
        uptime_match = UPTIME_PATTERN.search(line)
        if uptime_match:
            current_minute = int(float(uptime_match.group(1)) // 60)

        if line.startswith("Write Stall (count):"):
            counts = dict(STALL_COUNT_PATTERN.findall(line))
            for key, value_str in counts.items():
                value = int(value_str)
                prev = prev_counts.get(key, 0)
                delta = value - prev
                if delta < 0:
                    delta = value
                prev_counts[key] = value

                if "memtable" in key or "write-buffer-manager" in key:
                    if "delays" in key:
                        minute_data[current_minute]["flush_delays"] += delta
                    elif "stops" in key:
                        minute_data[current_minute]["flush_stops"] += delta
                elif "compaction" in key or "l0" in key:
                    if "delays" in key:
                        minute_data[current_minute]["comp_delays"] += delta
                    elif "stops" in key:
                        minute_data[current_minute]["comp_stops"] += delta

        if line.startswith("Interval stall:"):
            match = INTERVAL_STALL_PATTERN.search(line)
            if match:
                seconds = parse_time_string(match.group(1))
                minute_data[current_minute]["stall_seconds"] += seconds

    return minute_data


def write_csv(output_csv: Path, minute_data: Dict[int, Dict[str, float]]) -> None:
    minutes = sorted(minute_data.keys())
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "minute",
            "hour",
            "flush_delays",
            "flush_stops",
            "comp_delays",
            "comp_stops",
            "stall_seconds",
        ])
        for minute in minutes:
            hour = minute / 60.0
            data = minute_data[minute]
            writer.writerow([
                minute,
                f"{hour:.4f}",
                int(data["flush_delays"]),
                int(data["flush_stops"]),
                int(data["comp_delays"]),
                int(data["comp_stops"]),
                f"{data['stall_seconds']:.6f}",
            ])


def render_png(output_png: Path, minute_data: Dict[int, Dict[str, float]]) -> None:
    minutes = sorted(minute_data.keys())
    if not minutes:
        raise SystemExit("No stall data found; cannot render PNG.")

    hours = [m / 60.0 for m in minutes]
    flush_stops = [minute_data[m]["flush_stops"] for m in minutes]
    comp_delays = [minute_data[m]["comp_delays"] for m in minutes]
    stall_seconds = [minute_data[m]["stall_seconds"] for m in minutes]

    width, height = 1200, 800
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_tick = ImageFont.load_default()

    panels = [
        ("Flush Stops per Minute", flush_stops, (214, 39, 40)),
        ("Compaction Delays per Minute", comp_delays, (33, 113, 181)),
        ("Interval Stall Seconds per Minute", stall_seconds, (44, 160, 44)),
    ]

    left_margin = 100
    right_margin = 80
    top_margin = 60
    bottom_margin = 60
    panel_gap = 40
    panel_height = (height - top_margin - bottom_margin - panel_gap * (len(panels) - 1)) // len(panels)
    chart_width = width - left_margin - right_margin

    min_hour = hours[0]
    max_hour = hours[-1] if hours[-1] > min_hour else min_hour + 1.0
    step = max(1, len(hours) // 4000)

    for idx, (title, series, color) in enumerate(panels):
        y0 = top_margin + idx * (panel_height + panel_gap)
        y1 = y0 + panel_height

        max_value = max(series) if series else 1.0
        if max_value <= 0:
            max_value = 1.0

        draw.rectangle([left_margin, y0, left_margin + chart_width, y1], outline="black")
        draw.text((left_margin, y0 - 20), title, fill="black", font=font_title)
        draw.text((left_margin - 80, y0 - 10), "", fill="black", font=font_tick)

        num_y_ticks = 5
        for i in range(num_y_ticks):
            value = max_value * i / (num_y_ticks - 1)
            y = y1 - (value / max_value) * (y1 - y0)
            draw.line([(left_margin, y), (left_margin + chart_width, y)], fill="#dddddd")
            label = f"{value:.0f}" if max_value >= 5 else f"{value:.2f}"
            draw.text((left_margin - 60, y - 7), label, fill="black", font=font_tick)

        if idx == len(panels) - 1:
            draw.text((left_margin + chart_width / 2 - 40, y1 + 25), "Time (hours)", fill="black", font=font_tick)

        num_x_ticks = 8
        for i in range(num_x_ticks):
            tick_idx = round((len(hours) - 1) * i / (num_x_ticks - 1)) if len(hours) > 1 else 0
            hour_val = hours[tick_idx]
            x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
            draw.line([(x, y0), (x, y1)], fill="#dddddd")
            if idx == len(panels) - 1:
                draw.text((x - 20, y1 + 8), f"{hour_val:.1f}", fill="black", font=font_tick)

        for point_idx in range(0, len(hours), step):
            hour_val = hours[point_idx]
            value = series[point_idx]
            x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
            y = y1 - (value / max_value) * (y1 - y0)
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color, outline=color)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate write stall metrics per minute.")
    parser.add_argument("--log", type=Path, default=Path("../rocksdb_log_phase_b.log"), help="Path to RocksDB LOG file.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("../results/write_stall_per_minute.csv"),
        help="Output CSV file.",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=Path("../write_stall_per_minute.png"),
        help="Output PNG visualization.",
    )
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"Log file not found: {args.log}")

    print(f"Parsing log: {args.log}")
    minute_data = parse_stall_data(args.log.read_text().splitlines())

    print(f"Writing CSV: {args.csv}")
    write_csv(args.csv, minute_data)

    print(f"Rendering PNG: {args.png}")
    render_png(args.png, minute_data)
    print("Done.")


if __name__ == "__main__":
    main()
