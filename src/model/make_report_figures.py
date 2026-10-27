"""
make_report_figures.py - figures for Chapters 3 and 4.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

RES = Path(r"C:\ntfs-tamper-detect\results")

# ---------- FIGURE 1: Experiment C timeline ----------
# What the system clock believed, against real elapsed time.
fig, ax = plt.subplots(figsize=(7.5, 3.6))
t  = [0, 1.0, 1.0, 5.8, 5.8, 7.0]
yr = [2026, 2026, 2023, 2023, 2026, 2026]
ax.plot(t, yr, linewidth=2.5, color="#2b6cb0")
ax.axvspan(1.0, 5.8, alpha=0.15, color="#c53030")
ax.annotate("clock set back\n1,096 days", xy=(1.0, 2024.5), xytext=(1.6, 2025.2),
            fontsize=9, arrowprops=dict(arrowstyle="->", color="#c53030"))
ax.annotate("200 files written here\n4.8 second window", xy=(3.4, 2023),
            xytext=(2.4, 2023.4), fontsize=9, ha="center")
ax.annotate("clock restored", xy=(5.8, 2024.5), xytext=(6.0, 2025.2),
            fontsize=9, arrowprops=dict(arrowstyle="->", color="#2f855a"))
ax.set_xlabel("real elapsed time (seconds)")
ax.set_ylabel("year the system clock reported")
ax.set_ylim(2022.5, 2026.5)
ax.set_yticks([2023, 2024, 2025, 2026])
ax.set_title("Experiment C: every timestamp honestly recorded from a lying clock",
             fontsize=10)
plt.tight_layout()
plt.savefig(RES / "expC_timeline.png", dpi=150)
print("Saved -> expC_timeline.png")

# ---------- FIGURE 2: sequence signal, failed vs working ----------
fig, ax = plt.subplots(figsize=(6.5, 3.6))
exps = ["Exp A", "Exp B", "Exp C"]
median = [1.00, 1.00, 0.005]
runmax = [1.00, 1.00, 1.00]
x = range(len(exps))
b1 = ax.bar([i - 0.2 for i in x], median, 0.4,
            label="neighbourhood median (first attempt)", color="#c53030")
b2 = ax.bar([i + 0.2 for i in x], runmax, 0.4,
            label="running maximum (final)", color="#2f855a")
for b in list(b1) + list(b2):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.02,
            f"{b.get_height():.2f}", ha="center", fontsize=9)
ax.set_xticks(list(x)); ax.set_xticklabels(exps)
ax.set_ylim(0, 1.15); ax.set_ylabel("recall")
ax.legend(fontsize=8, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.12), frameon=False)
ax.set_title("USN sequence signal: the first implementation was self-referential",
             fontsize=10, pad=12)
plt.tight_layout()
plt.savefig(RES / "seq_signal_versions.png", dpi=150)
print("Saved -> seq_signal_versions.png")

# ---------- FIGURE 3: MFT record structure ----------
fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.axis("off")
ax.add_patch(mpatches.Rectangle((0.02, 0.05), 0.96, 0.88, fill=False,
                                edgecolor="#2d3748", linewidth=2))
ax.text(0.5, 0.96, "MFT file record", ha="center", fontsize=11, weight="bold")

fields = ["Created", "Modified", "MFT changed", "Accessed"]

ax.add_patch(mpatches.Rectangle((0.06, 0.12), 0.41, 0.72,
                                facecolor="#fed7d7", edgecolor="#c53030"))
ax.text(0.265, 0.78, "$STANDARD_INFORMATION", ha="center", fontsize=9.5,
        weight="bold", family="monospace")
ax.text(0.265, 0.72, "writable from user space", ha="center", fontsize=8.5,
        style="italic", color="#c53030")
for i, f in enumerate(fields):
    ax.text(0.265, 0.60 - i * 0.11, f, ha="center", fontsize=9)

ax.add_patch(mpatches.Rectangle((0.53, 0.12), 0.41, 0.72,
                                facecolor="#c6f6d5", edgecolor="#2f855a"))
ax.text(0.735, 0.78, "$FILE_NAME", ha="center", fontsize=9.5,
        weight="bold", family="monospace")
ax.text(0.735, 0.72, "kernel-managed only", ha="center", fontsize=8.5,
        style="italic", color="#2f855a")
for i, f in enumerate(fields):
    ax.text(0.735, 0.60 - i * 0.11, f, ha="center", fontsize=9)

ax.text(0.5, 0.02,
        "Timestomping tools reach the left half. The mismatch is the evidence.",
        ha="center", fontsize=9)
plt.tight_layout()
plt.savefig(RES / "mft_record_structure.png", dpi=150)
print("Saved -> mft_record_structure.png")

