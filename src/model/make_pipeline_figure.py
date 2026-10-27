"""
make_pipeline_figure.py - Figure 4.1, the four-stage architecture.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

RES = Path(r"C:\ntfs-tamper-detect\results")

fig, ax = plt.subplots(figsize=(11, 4.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

stages = [
    ("1. EXTRACTION", "#bee3f8", "#2b6cb0",
     ["MFTECmd", "  -> $MFT", "  -> USN Journal", "", "Get-WinEvent", "  -> Event Log"],
     "raw artefacts to CSV"),
    ("2. FEATURE DERIVATION", "#c6f6d5", "#2f855a",
     ["build_features_*.py", "add_usn_sequence", "   _signal.py", "", "one row per file", "5 binary indicators"],
     "artefacts to signals"),
    ("3. SCORING", "#feebc8", "#c05621",
     ["confidence_score.py", "", "5 weighted rules", "+ corroboration", "   bonus", "", "score 0-100 + reason"],
     "signals to verdict"),
    ("4. REPORTING", "#e9d8fd", "#6b46c1",
     ["evaluate_unified.py", "  -> metrics", "", "unified_report.py", "  -> per-file reports", "  -> incident summary"],
     "verdict to output"),
]

w, gap, x0, ytop, h = 20.0, 4.5, 4.0, 82.0, 58.0

for i, (title, fill, edge, lines, sub) in enumerate(stages):
    x = x0 + i * (w + gap)
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, ytop - h), w, h, boxstyle="round,pad=0.6",
        facecolor=fill, edgecolor=edge, linewidth=1.8))
    ax.text(x + w / 2, ytop - 5, title, ha="center", fontsize=9.5,
            weight="bold", color=edge)
    for j, ln in enumerate(lines):
        ax.text(x + 2.0, ytop - 14 - j * 6.2, ln, ha="left", fontsize=8,
                family="monospace" if ln.strip().endswith(".py") or ln.strip().startswith("->")
                or "MFTECmd" in ln or "Get-WinEvent" in ln else "sans-serif")
    ax.text(x + w / 2, ytop - h - 5, sub, ha="center", fontsize=8,
            style="italic", color="#4a5568")

    if i < len(stages) - 1:
        ax.annotate("", xy=(x + w + gap - 0.5, ytop - h / 2),
                    xytext=(x + w + 0.5, ytop - h / 2),
                    arrowprops=dict(arrowstyle="-|>", linewidth=2, color="#4a5568"))

ax.text(50, 8,
        "Extraction runs once. Stages 2 to 4 re-run in seconds without "
        "re-parsing a 231 MB Master File Table.",
        ha="center", fontsize=8.5, color="#4a5568")

plt.tight_layout()
plt.savefig(RES / "pipeline_architecture.png", dpi=150, bbox_inches="tight")
print("Saved ->", RES / "pipeline_architecture.png")

