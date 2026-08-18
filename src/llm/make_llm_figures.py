import json
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LLM = Path(r"C:\ntfs-tamper-detect\data\llm")
RES = Path(r"C:\ntfs-tamper-detect\results")
key = pd.read_csv(LLM / "bundle_key.csv")
truth = dict(zip(key["file_id"], key["true_label"]))
POS = {"LIKELY_TIMESTOMPING", "SUSPICIOUS"}

def counts(fname, expc=False):
    rows = []
    for line in open(LLM / fname, encoding="utf-8"):
        r = json.loads(line)
        if expc and r["experiment"] != "C":
            continue
        p = 1 if (r.get("parsed") or {}).get("classification") in POS else 0
        rows.append((p, truth.get(r["file_id"])))
    tp = sum(1 for p,t in rows if p==1 and t==1)
    tn = sum(1 for p,t in rows if p==0 and t==0)
    fp = sum(1 for p,t in rows if p==1 and t==0)
    fn = sum(1 for p,t in rows if p==0 and t==1)
    return [[tn, fp], [fn, tp]]

# rules arm on the same 150 files
scored = pd.concat([pd.read_csv(rf"C:\ntfs-tamper-detect\data\processed\scored_files_{e}.csv")
                    for e in "ABC"], ignore_index=True)
s = dict(zip(scored["FileName"], scored["tamper_score"]))
bund = [json.loads(l) for l in open(LLM / "bundles.jsonl", encoding="utf-8")]
rr = [(1 if s.get(b["orig_name"], 0) >= 1 else 0, truth[b["file_id"]]) for b in bund]
rules = [[sum(1 for p,t in rr if p==0 and t==0), sum(1 for p,t in rr if p==1 and t==0)],
         [sum(1 for p,t in rr if p==0 and t==1), sum(1 for p,t in rr if p==1 and t==1)]]

panels = [("Static rules", rules),
          ("LLM alone", counts("responses_llm.jsonl")),
          ("Hybrid", counts("responses_hybrid.jsonl"))]

fig, axes = plt.subplots(1, 3, figsize=(11, 3.8))
for ax, (title, cm) in zip(axes, panels):
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=max(max(r) for r in cm))
    for i in range(2):
        for j in range(2):
            ax.text(j, i, cm[i][j], ha="center", va="center", fontsize=20,
                    color="white" if cm[i][j] > max(max(r) for r in cm)*0.5 else "black")
    ax.set_xticks([0,1]); ax.set_xticklabels(["benign", "tampered"])
    ax.set_yticks([0,1]); ax.set_yticklabels(["benign", "tampered"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title(title, fontsize=11)
plt.suptitle("Triage arms on the same 150 files (75 tampered / 75 benign)", fontsize=10)
plt.tight_layout()
plt.savefig(RES / "llm_confusion_matrices.png", dpi=150)

# Exp C only, two model tiers
fig, ax = plt.subplots(figsize=(6, 3.4))
labels = ["Rules", "Lite model", "Reasoning model"]
recall = [1.00, 0.12, 1.00]
fpr    = [0.00, 0.22, 1.00]
x = range(len(labels))
ax.bar([i-0.2 for i in x], recall, 0.4, label="recall")
ax.bar([i+0.2 for i in x], fpr, 0.4, label="false positive rate")
ax.set_xticks(list(x)); ax.set_xticklabels(labels)
ax.set_ylim(0, 1.1); ax.legend(fontsize=8)
ax.set_title("Experiment C (clock rollback): both models fail, oppositely", fontsize=10)
plt.tight_layout()
plt.savefig(RES / "llm_expC_tiers.png", dpi=150)

print("Saved -> llm_confusion_matrices.png")
print("Saved -> llm_expC_tiers.png")
