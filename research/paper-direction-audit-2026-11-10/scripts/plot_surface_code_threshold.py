"""Render the real benchmark points as a standalone static SVG."""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

AUDIT_DIR = Path(__file__).resolve().parents[1]
RESULTS = AUDIT_DIR / "surface-code-threshold" / "results.json"
OUTPUT = AUDIT_DIR / "surface-code-threshold" / "threshold.svg"
COLORS = {3: "#2563a6", 5: "#2e8b70", 7: "#b36a22", 9: "#9c4f76"}


def render_svg(points: list[dict]) -> str:
    visible = [point for point in points if point["rate"] > 0]
    if not visible:
        raise ValueError("no nonzero logical error rates to plot")
    width, height = 1000, 600
    left, right, top, bottom = 90, 235, 60, 85
    plot_width = width - left - right
    plot_height = height - top - bottom
    probabilities = sorted({point["p"] for point in visible})
    logs = [math.log10(value) for point in visible
            for value in (point["rate"], point["wilson95_low"], point["wilson95_high"]) if value > 0]
    x_min, x_max = min(probabilities), max(probabilities)
    y_min, y_max = min(logs), max(logs)
    if x_min == x_max:
        x_min, x_max = x_min - 0.001, x_max + 0.001
    if y_min == y_max:
        y_min, y_max = y_min - 0.5, y_max + 0.5
    y_min -= 0.08
    y_max += 0.08
    x = lambda value: left + (value - x_min) / (x_max - x_min) * plot_width
    y = lambda value: top + (y_max - math.log10(value)) / (y_max - y_min) * plot_height
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfcfa"/>',
        '<style>text{font-family:Arial,"Microsoft YaHei",sans-serif;fill:#253640} .axis{stroke:#52636b;stroke-width:1.2} .grid{stroke:#dce4e2;stroke-width:1} .series{fill:none;stroke-width:2.2} .point{stroke:#fff;stroke-width:1}</style>',
        '<text x="500" y="30" text-anchor="middle" font-size="21" font-weight="700">Surface-code circuit-level Monte Carlo (MWPM)</text>',
        f'<line class="axis" x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}"/>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
    ]
    for exponent in range(math.ceil(y_min), math.floor(y_max) + 1):
        value = 10 ** exponent
        yy = y(value)
        lines.extend([
            f'<line class="grid" x1="{left}" y1="{yy:.3f}" x2="{left + plot_width}" y2="{yy:.3f}"/>',
            f'<text x="{left - 10}" y="{yy + 4:.3f}" text-anchor="end" font-size="12">1e{exponent}</text>',
        ])
    for probability in probabilities:
        xx = x(probability)
        lines.extend([
            f'<line class="grid" x1="{xx:.3f}" y1="{top}" x2="{xx:.3f}" y2="{top + plot_height}"/>',
            f'<text x="{xx:.3f}" y="{top + plot_height + 23}" text-anchor="middle" font-size="12">{probability:.3f}</text>',
        ])
    for distance in sorted({point["distance"] for point in visible}):
        group = sorted((point for point in visible if point["distance"] == distance), key=lambda item: item["p"])
        color = COLORS.get(distance, "#555555")
        coordinates = " ".join(f"{x(point['p']):.3f},{y(point['rate']):.3f}" for point in group)
        lines.append(f'<polyline class="series" points="{coordinates}" stroke="{color}"/>')
        for point in group:
            xx, yy = x(point["p"]), y(point["rate"])
            low = max(point["wilson95_low"], 1e-12)
            high = max(point["wilson95_high"], 1e-12)
            lines.extend([
                f'<line x1="{xx:.3f}" y1="{y(low):.3f}" x2="{xx:.3f}" y2="{y(high):.3f}" stroke="{color}" stroke-width="1.2"/>',
                f'<circle class="point" cx="{xx:.3f}" cy="{yy:.3f}" r="4" fill="{color}"/>',
            ])
        lines.append(f'<text x="{left + plot_width + 18}" y="{top + 22 + 25 * sorted(set(p["distance"] for p in visible)).index(distance)}" font-size="13" fill="{color}">d={distance}</text>')
    lines.extend([
        f'<text x="{left + plot_width / 2}" y="{height - 22}" text-anchor="middle" font-size="14">Physical error probability p</text>',
        f'<text x="20" y="{top + plot_height / 2}" text-anchor="middle" font-size="14" transform="rotate(-90 20 {top + plot_height / 2})">Logical error rate per shot</text>',
        '</svg>',
    ])
    return "\n".join(lines)


def main() -> int:
    payload = json.loads(RESULTS.read_text(encoding="utf-8"))
    OUTPUT.write_text(render_svg(payload["points"]), encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
