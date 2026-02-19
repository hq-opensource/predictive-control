Write-Host "Starting GitHub link extraction..." -ForegroundColor Cyan
python llm_link_extractor.py
Write-Host "Process complete. Check final_analysis_with_links.md" -ForegroundColor Green
