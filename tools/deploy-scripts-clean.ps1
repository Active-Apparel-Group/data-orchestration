# Deploy Scripts to Kestra Namespace - SIMPLE VERSION
# Just uploads Python scripts with basic filtering

param(
    [string]$KestraUrl = "http://localhost:8080", 
    [string]$Namespace = "company.team"
)

Write-Host "Deploying Scripts to Kestra" -ForegroundColor Green
Write-Host "Target: $KestraUrl | Namespace: $Namespace" -ForegroundColor Cyan
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor Magenta

# Check scripts folder
if (-not (Test-Path "scripts")) {
    Write-Host "ERROR: No scripts/ folder found" -ForegroundColor Red
    exit 1
}

# Create filtered copy
$clean = "scripts_clean"
if (Test-Path $clean) { 
    Write-Host "Removing existing clean folder..." -ForegroundColor Yellow
    Remove-Item $clean -Recurse -Force 
    Start-Sleep -Seconds 1  # Ensure cleanup completes
}

Write-Host "Filtering out __pycache__ and __init__.py files..." -ForegroundColor Yellow
# Add /PURGE to ensure fresh copy
robocopy "scripts" $clean /E /PURGE /XD "__pycache__" /XF "__init__.py" "*.pyc" /NFL /NDL /NJH /NJS | Out-Null

# Show files
$sourceFiles = Get-ChildItem "scripts" -Recurse -File | Where-Object { $_.Extension -eq ".py" }
$cleanFiles = Get-ChildItem $clean -Recurse -File
Write-Host ""
Write-Host "Source .py files: $($sourceFiles.Count)" -ForegroundColor Yellow
Write-Host "Clean files: $($cleanFiles.Count)" -ForegroundColor Yellow
Write-Host "Files to upload:" -ForegroundColor Yellow
$cleanFiles | ForEach-Object { 
    $lastWrite = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "  $($_.Name) (Modified: $lastWrite)" -ForegroundColor Cyan 
}

Write-Host ""
Write-Host "Uploading to Kestra..." -ForegroundColor Yellow

# THE SIMPLE COMMAND THAT WORKS:
# Upload ONLY the scripts folder to namespace (preserving folder structure)
docker run --rm -v "${PWD}:/workspace" -w "/workspace" --network host `
    kestra/kestra:latest `
    namespace files update $Namespace $clean scripts `
    --server $KestraUrl

# Cleanup
Remove-Item $clean -Recurse -Force

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Scripts deployed!" -ForegroundColor Green
} else {
    Write-Host "FAILED: Deployment error" -ForegroundColor Red
}
