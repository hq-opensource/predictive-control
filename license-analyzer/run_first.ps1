python analyzer.py
Write-Host "Local analysis complete. Starting LLM validation..." -ForegroundColor Cyan
python llm_validator.py
Write-Host "Process complete. Check final_analysis.md and references.md" -ForegroundColor Green
