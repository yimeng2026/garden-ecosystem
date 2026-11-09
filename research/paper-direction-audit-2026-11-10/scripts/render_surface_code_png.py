"""Render the stored real benchmark as PNG for visual inspection and Word."""
from pathlib import Path
import json
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
payload = json.loads((ROOT / "surface-code-threshold" / "results.json").read_text(encoding="utf-8"))
colors = {3: "#2563a6", 5: "#2e8b70", 7: "#b36a22", 9: "#9c4f76"}
fig, ax = plt.subplots(figsize=(10, 6), dpi=160)
for distance in payload["protocol"]["distances"]:
    group = sorted((p for p in payload["points"] if p["distance"] == distance), key=lambda p: p["p"])
    xs = [p["p"] for p in group]
    rates = [p["rate"] for p in group]
    lower = [max(p["rate"] - p["wilson95_low"], 0) for p in group]
    upper = [max(p["wilson95_high"] - p["rate"], 0) for p in group]
    ax.errorbar(xs, rates, yerr=[lower, upper], marker="o", markersize=4,
                capsize=3, linewidth=1.8, color=colors[distance], label=f"d={distance}")
ax.set_yscale("log")
ax.set_xlabel("Physical error probability p")
ax.set_ylabel("Logical error rate per shot")
ax.set_title("Surface-code circuit-level Monte Carlo (MWPM)")
ax.grid(True, which="both", alpha=0.25)
ax.legend()
fig.tight_layout()
output = ROOT / "surface-code-threshold" / "threshold.png"
fig.savefig(output, bbox_inches="tight")
plt.close(fig)
print(f"wrote {output} ({output.stat().st_size} bytes)")
