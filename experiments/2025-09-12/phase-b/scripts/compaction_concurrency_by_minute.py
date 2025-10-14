#!/usr/bin/env python3
"""
Estimate compaction concurrency by minute.

We read EVENT_LOG_v1 entries for `compaction_finished`, infer each job's
start time (time_micros - compaction_time_micros), and count how many jobs
are running in each minute bucket. Results are saved as CSV/PNG.
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable

from PIL import Image, ImageDraw, ImageFont


def parse_compaction_intervals(lines: Iterable[str]) -> Dict[int, int]:
    """
    Parse compaction events and return per-minute concurrency counts.

    Returns:
        minute_bucket -> max concurrent compaction jobs during that minute.
    """

    events = []
    start_time = None

    for line in lines:
        if '"event": "compaction_finished"' not in line:
            continue

        pos = line.find("{")
        if pos < 0:
            continue

        try:
            event = json.loads(line[pos:])
        except json.JSONDecodeError:
            continue

        if event.get("event") != "compaction_finished":
            continue

        time_micros = event.get("time_micros")
        duration_micros = event.get("compaction_time_micros")
        if time_micros is None or duration_micros is None:
            continue

        if start_time is None:
            start_time = time_micros

        end_rel = max(0, time_micros - start_time)
        start_rel = max(0, end_rel - duration_micros)

        events.append((start_rel, end_rel))

    if not events:
        return {}

    minute_concurrency = defaultdict(int)

    for start_rel, end_rel in events:
        start_minute = int(start_rel // 60_000_000)
        end_minute = int(end_rel // 60_000_000)

        for minute in range(start_minute, end_minute + 1):
            minute_concurrency[minute] += 1

    return minute_concurrency


def write_csv(output_csv: Path, minute_concurrency: Dict[int, int]) -> None:
    minutes = sorted(minute_concurrency.keys())

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["minute", "hour", "concurrent_compactions"])
        for minute in minutes:
            hour = minute / 60.0
            writer.writerow([minute, f"{hour:.4f}", minute_concurrency.get(minute, 0)])


def render_png(output_png: Path, minute_concurrency: Dict[int, int]) -> None:
    minutes = sorted(minute_concurrency.keys())
    if not minutes:
        raise SystemExit("No compaction events found; cannot render concurrency chart.")

    hours = [m / 60.0 for m in minutes]
    values = [minute_concurrency[m] for m in minutes]

    width, height = 1200, 500
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_tick = ImageFont.load_default()

    left_margin = 100
    right_margin = 80
    top_margin = 80
    bottom_margin = 60
    chart_width = width - left_margin - right_margin
    chart_height = height - top_margin - bottom_margin

    max_value = max(values) if values else 1
    if max_value <= 0:
        max_value = 1

    draw.rectangle([left_margin, top_margin, left_margin + chart_width, top_margin + chart_height], outline="black")
    draw.text((left_margin, top_margin - 25), "Concurrent Compaction Jobs per Minute", fill="black", font=font_title)
    draw.text((left_margin - 85, top_margin - 15), "Jobs", fill="black", font=font_tick)
    draw.text((left_margin + chart_width / 2 - 40, top_margin + chart_height + 30), "Time (hours)", fill="black", font=font_tick)

    num_y_ticks = 6
    for i in range(num_y_ticks):
        value = max_value * i / (num_y_ticks - 1)
        y = top_margin + chart_height - (value / max_value) * chart_height
        draw.line([(left_margin, y), (left_margin + chart_width, y)], fill="#dddddd")
        draw.text((left_margin - 60, y - 7), f"{value:.0f}", fill="black", font=font_tick)

    num_x_ticks = 8
    min_hour = hours[0]
    max_hour = hours[-1] if hours[-1] > min_hour else min_hour + 1.0
    for i in range(num_x_ticks):
        idx = round((len(hours) - 1) * i / (num_x_ticks - 1)) if len(hours) > 1 else 0
        hour_val = hours[idx]
        x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
        draw.line([(x, top_margin), (x, top_margin + chart_height)], fill="#dddddd")
        draw.text((x - 20, top_margin + chart_height + 10), f"{hour_val:.1f}", fill="black", font=font_tick)

    step = max(1, len(hours) // 4000)
    for idx in range(0, len(hours), step):
        hour_val = hours[idx]
        value = values[idx]
        x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
        y = top_margin + chart_height - (value / max_value) * chart_height
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill="#d62728", outline="#d62728")

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute compaction concurrency per minute.")
    parser.add_argument("--log", type=Path, default=Path("../rocksdb_log_phase_b.log"), help="Path to RocksDB LOG file.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("../results/compaction_concurrency_per_minute.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=Path("../compaction_concurrency_per_minute.png"),
        help="Output PNG path.",
    )
    args = parser.parse_args()

    if not args.log.exists():
        raise SystemExit(f"Log file not found: {args.log}")

    print(f"Parsing log: {args.log}")
    minute_concurrency = parse_compaction_intervals(args.log.read_text().splitlines())

    print(f"Writing CSV: {args.csv}")
    write_csv(args.csv, minute_concurrency)

    print(f"Rendering PNG: {args.png}")
    render_png(args.png, minute_concurrency)
    print("Done.")


if __name__ == "__main__":
    main()
