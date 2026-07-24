# evaluate.py - metrics for the timestomping detector
import pandas as pd
from pathlib import Path
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt

ROOT = Path(r"C:\ntfs-tamper-detect")
df = pd.read_csv(ROOT / "data" / "processed" / "features_corpus.csv")
out = ROOT / "results"; out.mkdir(exist_ok=True)

y_true = df["tampered"]
y_pred = df["si_fn_mismatch"]

tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
print(f"True negatives : {tn}")
print(f"False positives: {fp}")
print(f"False negatives: {fn}")
print(f"True positives : {tp}\n")

print(f"Accuracy            : {(tp+tn)/(tp+tn+fp+fn):.4f}")
print(f"Precision           : {tp/(tp+fp) if tp+fp else 0:.4f}")
print(f"Recall              : {tp/(tp+fn) if tp+fn else 0:.4f}")
print(f"False positive rate : {fp/(fp+tn) if fp+tn else 0:.4f}\n")
print(classification_report(y_true, y_pred, target_names=["benign","tampered"]))

fig, ax = plt.subplots(figsize=(4,4))
cm = confusion_matrix(y_true, y_pred)
ax.imshow(cm, cmap="Blues")
for i in range(2):
    for j in range(2):
        ax.text(j, i, cm[i,j], ha="center", va="center")
ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
ax.set_xticks([0,1], ["benign","tampered"]); ax.set_yticks([0,1], ["benign","tampered"])
ax.set_title("Timestomping detection (n=808)")
plt.tight_layout(); plt.savefig(out / "confusion_matrix.png", dpi=150)
print("Figure ->", out / "confusion_matrix.png")