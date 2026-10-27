# run_all.ps1 - reproduces the full pipeline end to end.
# Detection stages only. The LLM stages cost money and hit the API, so they are
# listed at the bottom, commented out - uncomment deliberately, not by accident.

$ErrorActionPreference = "Stop"
Set-Location C:\ntfs-tamper-detect

Write-Host "`n=== 1. USN sequence signal (all experiments) ===" -ForegroundColor Cyan
python src\features\add_usn_sequence_signal.py

Write-Host "`n=== 2. Scoring each experiment ===" -ForegroundColor Cyan
python src\model\confidence_score.py --exp A
python src\model\confidence_score.py --exp B
python src\model\confidence_score.py --exp C

Write-Host "`n=== 3. Unified evaluation (1,308 files) ===" -ForegroundColor Cyan
python src\model\evaluate_unified.py

Write-Host "`n=== 4. Figures ===" -ForegroundColor Cyan
python src\llm\make_llm_figures.py
python src\llm\make_final_figures.py

Write-Host "`nDetection pipeline complete. Results in .\results\" -ForegroundColor Green
Write-Host "Key files: unified_evaluation.md, arm_comparison.md, forensic_report.md`n"

# ---- LLM STAGES - COST MONEY, uncomment only when you mean it ----
# cd src\llm
# python run_llm_triage.py --arm llm
# python run_llm_triage.py --arm hybrid
# python run_llm_triage.py --arm ablation
# python compare_arms.py
# python compare_expC.py
# python unified_report.py
# cd ..\..
