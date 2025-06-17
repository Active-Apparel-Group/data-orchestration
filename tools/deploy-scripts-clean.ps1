# Deploy Scripts to Kestra Namespace - SIMPLE VERSION
# Just uploads Python scripts with basic filtering

param(
    [string]$KestraUrl = "http://localhost:8080", 
    [string]$Namespace = "company.team"
)

Write-Host "Deploying Scripts to Kestra" -ForegroundColor Green
Write-Host "Target: $KestraUrl | Namespace: $Namespace" -ForegroundColor Cyan
Write-Host "Working Directory: $(Get-Location)" -ForegroundColor Magenta

# Check scripts and utils folders
if (-not (Test-Path "scripts")) {
    Write-Host "ERROR: No scripts/ folder found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "utils")) {
    Write-Host "ERROR: No utils/ folder found" -ForegroundColor Red
    exit 1
}

# Create filtered copy for scripts
$clean = "scripts_clean"
if (Test-Path $clean) { 
    Write-Host "Removing existing clean scripts folder..." -ForegroundColor Yellow
    Remove-Item $clean -Recurse -Force 
    Start-Sleep -Seconds 1  # Ensure cleanup completes
}

# Create filtered copy for utils
$utilsClean = "utils_clean"
if (Test-Path $utilsClean) { 
    Write-Host "Removing existing clean utils folder..." -ForegroundColor Yellow
    Remove-Item $utilsClean -Recurse -Force 
    Start-Sleep -Seconds 1  # Ensure cleanup completes
}

Write-Host "Filtering out __pycache__ and __init__.py files from scripts..." -ForegroundColor Yellow
# Add /PURGE to ensure fresh copy
robocopy "scripts" $clean /E /PURGE /XD "__pycache__" /XF "__init__.py" "*.pyc" /NFL /NDL /NJH /NJS | Out-Null

Write-Host "Filtering out __pycache__ and __init__.py files from utils..." -ForegroundColor Yellow
# Add /PURGE to ensure fresh copy
robocopy "utils" $utilsClean /E /PURGE /XD "__pycache__" /XF "__init__.py" "*.pyc" /NFL /NDL /NJH /NJS | Out-Null

# Show files
$sourceFiles = Get-ChildItem "scripts" -Recurse -File | Where-Object { $_.Extension -eq ".py" }
$cleanFiles = Get-ChildItem $clean -Recurse -File
$utilsFiles = Get-ChildItem "utils" -Recurse -File | Where-Object { $_.Extension -in @(".py", ".yaml") }
$utilsCleanFiles = Get-ChildItem $utilsClean -Recurse -File
Write-Host ""
Write-Host "Source .py files in scripts: $($sourceFiles.Count)" -ForegroundColor Yellow
Write-Host "Clean scripts files: $($cleanFiles.Count)" -ForegroundColor Yellow
Write-Host "Source files in utils: $($utilsFiles.Count)" -ForegroundColor Yellow
Write-Host "Clean utils files: $($utilsCleanFiles.Count)" -ForegroundColor Yellow
Write-Host "Scripts files to upload:" -ForegroundColor Yellow
$cleanFiles | ForEach-Object { 
    $lastWrite = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "  scripts/$($_.Name) (Modified: $lastWrite)" -ForegroundColor Cyan 
}
Write-Host "Utils files to upload:" -ForegroundColor Yellow
$utilsCleanFiles | ForEach-Object { 
    $lastWrite = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "  utils/$($_.Name) (Modified: $lastWrite)" -ForegroundColor Cyan 
}

Write-Host ""
Write-Host "Uploading scripts to Kestra..." -ForegroundColor Yellow

# Upload scripts folder to namespace (preserving folder structure)
docker run --rm -v "${PWD}:/workspace" -w "/workspace" --network host `
    kestra/kestra:latest `
    namespace files update $Namespace $clean scripts `
    --server $KestraUrl

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Scripts deployment error" -ForegroundColor Red
    exit 1
}

Write-Host "Uploading utils to Kestra..." -ForegroundColor Yellow

# Upload utils folder to namespace (preserving folder structure)
docker run --rm -v "${PWD}:/workspace" -w "/workspace" --network host `
    kestra/kestra:latest `
    namespace files update $Namespace $utilsClean utils `
    --server $KestraUrl

# Cleanup
Remove-Item $clean -Recurse -Force
Remove-Item $utilsClean -Recurse -Force

if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: Scripts and utils deployed successfully!" -ForegroundColor Green
    Write-Host "  ✅ Scripts folder uploaded to Kestra namespace" -ForegroundColor Green
    Write-Host "  ✅ Utils folder uploaded to Kestra namespace" -ForegroundColor Green
} else {
    Write-Host "FAILED: Utils deployment error" -ForegroundColor Red
}
