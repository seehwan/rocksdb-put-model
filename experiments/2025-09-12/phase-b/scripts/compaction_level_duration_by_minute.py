#!/usr/bin/env python3
"""
Aggregate RocksDB compaction durations by level and minute.

Reads EVENT_LOG_v1 entries (`compaction_finished`) from `rocksdb_log_phase_b.log`,
groups them by minute (relative to the first compaction event), and records how
much wall-clock time each level spent compacting. Outputs both a CSV summary
and a dot-plot PNG for quick inspection.
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Tuple

from PIL import Image, ImageDraw, ImageFont


def parse_compaction_durations(lines: Iterable[str]) -> Dict[int, Dict[str, float]]:
    """
    Parse the log lines and return a mapping:
        minute -> { level_name -> total_compaction_seconds }
    """

    minute_level_seconds: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    start_time_micros = None

    for line in lines:
        if '"event": "compaction_finished"' not in line:
            continue

        json_start = line.find("{")
        if json_start < 0:
            continue

        try:
            event = json.loads(line[json_start:])
        except json.JSONDecodeError:
            continue

        if event.get("event") != "compaction_finished":
            continue

        time_micros = event.get("time_micros")
        duration_micros = event.get("compaction_time_micros")
        output_level = event.get("output_level")

        if time_micros is None or duration_micros is None or output_level is None:
            continue

        if start_time_micros is None:
            start_time_micros = time_micros

        rel_micros = max(0, time_micros - start_time_micros)
        minute_bucket = int(rel_micros // 60_000_000)

        seconds = duration_micros / 1_000_000.0
        level = f"L{int(output_level)}"
        minute_level_seconds[minute_bucket][level] += seconds

    return minute_level_seconds


def write_csv(output_csv: Path, minute_level_seconds: Dict[int, Dict[str, float]]) -> None:
    minutes = sorted(minute_level_seconds.keys())
    levels = sorted({lvl for data in minute_level_seconds.values() for lvl in data.keys()}, key=lambda x: int(x[1:]))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["minute", "hour", "level", "seconds"])

        for minute in minutes:
            hour = minute / 60.0
            level_map = minute_level_seconds[minute]
            for level in levels:
                seconds = level_map.get(level, 0.0)
                writer.writerow([minute, f"{hour:.4f}", level, f"{seconds:.6f}"])


def render_png(output_png: Path, minute_level_seconds: Dict[int, Dict[str, float]]) -> None:
    minutes = sorted(minute_level_seconds.keys())
    if not minutes:
        raise SystemExit("No compaction events found — cannot render PNG.")

    levels = sorted({lvl for data in minute_level_seconds.values() for lvl in data.keys()}, key=lambda x: int(x[1:]))
    hours = [m / 60.0 for m in minutes]

    series = {
        level: [minute_level_seconds[m].get(level, 0.0) for m in minutes] for level in levels
    }

    width, height = 1200, 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font_title = ImageFont.load_default()
    font_tick = ImageFont.load_default()

    left_margin = 100
    right_margin = 200
    top_margin = 80
    bottom_margin = 80
    chart_width = width - left_margin - right_margin
    chart_height = height - top_margin - bottom_margin

    max_value = max((max(vals) for vals in series.values()), default=1.0)
    if max_value <= 0:
        max_value = 1.0

    draw.rectangle([left_margin, top_margin, left_margin + chart_width, top_margin + chart_height], outline="black")
    draw.text((left_margin, top_margin - 25), "Compaction Time per Minute by Level (Seconds)", fill="black", font=font_title)
    draw.text((left_margin - 80, top_margin - 15), "Seconds", fill="black", font=font_tick)
    draw.text((left_margin + chart_width / 2 - 40, top_margin + chart_height + 35), "Time (hours)", fill="black", font=font_tick)

    num_y_ticks = 6
    for i in range(num_y_ticks):
        value = max_value * i / (num_y_ticks - 1)
        y = top_margin + chart_height - (value / max_value) * chart_height
        draw.line([(left_margin, y), (left_margin + chart_width, y)], fill="#dddddd")
        draw.text((left_margin - 60, y - 7), f"{value:.1f}", fill="black", font=font_tick)

    num_x_ticks = 8
    min_hour = hours[0]
    max_hour = hours[-1] if hours[-1] > min_hour else min_hour + 1.0
    for i in range(num_x_ticks):
        idx = round((len(hours) - 1) * i / (num_x_ticks - 1)) if len(hours) > 1 else 0
        hour_val = hours[idx]
        x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
        draw.line([(x, top_margin), (x, top_margin + chart_height)], fill="#dddddd")
        draw.text((x - 20, top_margin + chart_height + 10), f"{hour_val:.1f}", fill="black", font=font_tick)

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
    color_map = {level: tuple(int(color[i : i + 2], 16) for i in (1, 3, 5)) for level, color in zip(levels, palette)}

    step = max(1, len(hours) // 4000)
    for level in levels:
        color = color_map.get(level, (0, 0, 0))
        for idx in range(0, len(hours), step):
            hour_val = hours[idx]
            value = series[level][idx]
            x = left_margin + (hour_val - min_hour) / (max_hour - min_hour) * chart_width
            y = top_margin + chart_height - (value / max_value) * chart_height
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=color, outline=color)

    legend_x = left_margin + chart_width + 20
    legend_y = top_margin + 10
    for level in levels:
        color = color_map.get(level, (0, 0, 0))
        draw.rectangle([legend_x, legend_y, legend_x + 15, legend_y + 15], fill=color, outline=color)
        draw.text((legend_x + 20, legend_y), level, fill="black", font=font_tick)
        legend_y += 20

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate compaction durations per level and minute.")
    parser.add_argument("--log", type=Path, default=Path("../rocksdb_log_phase_b.log"), help="Path to RocksDB LOG file.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("../results/compaction_level_duration_per_minute.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--png",
        type=Path,
        default=Path("../compaction_level_duration_per_minute.png"),
        help="Output PNG path.",
    )

    args = parser.parse_args()
    if not args.log.exists():
        raise SystemExit(f"Log file not found: {args.log}")

    print(f"Parsing log: {args.log}")
    minute_level_seconds = parse_compaction_durations(args.log.read_text().splitlines())

    print(f"Writing CSV: {args.csv}")
    write_csv(args.csv, minute_level_seconds)

    print(f"Rendering PNG: {args.png}")
    render_png(args.png, minute_level_seconds)
    print("Done.")


if __name__ == "__main__":
    main()
