import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

RES = Path(r"C:\ntfs-tamper-detect\results")

# ---- Figure 1: Experiment C across every configuration ----
labels = ["Static\nrules", "Lite model\nvolume-wide", "Reasoning\nvolume-wide",
          "Lite model\n+ JOIN"]
recall = [1.00, 0.12, 1.00, 1.00]
fpr    = [0.00, 0.22, 1.00, 0.00]

fig, ax = plt.subplots(figsize=(7.5, 3.8))
x = range(len(labels))
b1 = ax.bar([i - 0.2 for i in x], recall, 0.4, label="recall", color="#2b6cb0")
b2 = ax.bar([i + 0.2 for i in x], fpr, 0.4, label="false positive rate",
            color="#dd6b20")
for b in list(b1) + list(b2):
    h = b.get_height()
    ax.text(b.get_x() + b.get_width() / 2, h + 0.02, f"{h:.2f}",
            ha="center", fontsize=8)
ax.set_xticks(list(x))
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylim(0, 1.15)
ax.legend(fontsize=8, loc="upper center", ncol=2, framealpha=0.9,
          bbox_to_anchor=(0.5, 1.02))
ax.set_title("Experiment C: supplying the interval test fixes the LLM entirely",
             fontsize=10)
plt.tight_layout()
plt.savefig(RES / "llm_expC_tiers.png", dpi=150)
print("Saved -> llm_expC_tiers.png  (now includes the JOIN result)")

# ---- Figure 2: classify vs explain ----
q = pd.read_csv(RES / "report_quality.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.6))
tasks = ["CLASSIFY\n(Exp C recall)", "EXPLAIN\n(faithfulness)",
         "EXPLAIN\n(completeness)"]
vals = [0.12, q["faithful"].mean(), q["completeness"].mean()]
cols = ["#c53030", "#2f855a", "#2f855a"]
bars = ax.bar(tasks, vals, color=cols, width=0.55)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
            ha="center", fontsize=11)
ax.set_ylim(0, 1.15)
ax.set_title(f"Same model, two jobs  (n={len(q)} reports)", fontsize=10)
ax.set_ylabel("score")
plt.tight_layout()
plt.savefig(RES / "llm_classify_vs_explain.png", dpi=150)
print("Saved -> llm_classify_vs_explain.png")

