# Simple Documentation Cleanup Script
# Only moves .md files to archive - keeps all mapping files in place

param([switch]$DryRun = $false)

Write-Host "🧹 Documentation Cleanup - Moving completed analysis files" -ForegroundColor Green
Write-Host "Dry Run: $DryRun" -ForegroundColor Yellow

# Create archive directory
$archiveDir = "docs\archive\customer-orders"
if (-not (Test-Path $archiveDir)) {
    if (-not $DryRun) {
        New-Item -Path $archiveDir -ItemType Directory -Force | Out-Null
        Write-Host "📁 Created archive directory: $archiveDir" -ForegroundColor Green
    } else {
        Write-Host "🔍 [DRY RUN] Would create directory: $archiveDir" -ForegroundColor Yellow
    }
}

# Documentation files to archive (completed analysis docs)
$docsToMove = @(
    "docs\MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md",
    "docs\ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md", 
    "docs\SCHEMA_VALIDATION_CRITICAL_ISSUES.md",
    "docs\SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md",
    "docs\YAML_MAPPING_FORMAT_DECISION.md"
)

$successCount = 0

foreach ($doc in $docsToMove) {
    if (Test-Path $doc) {
        $fileName = Split-Path -Leaf $doc
        $destination = Join-Path $archiveDir $fileName
        
        if (-not $DryRun) {
            try {
                Move-Item -Path $doc -Destination $destination -Force
                Write-Host "  ✅ Moved: $fileName -> archive/" -ForegroundColor Green
                $successCount++
            } catch {
                Write-Warning "❌ Failed to move $fileName : $_"
            }
        } else {
            Write-Host "  🔍 [DRY RUN] Would move: $fileName -> archive/" -ForegroundColor Yellow
            $successCount++
        }
    } else {
        Write-Host "  ⚠️ Not found: $doc" -ForegroundColor Gray
    }
}

Write-Host "`n📊 Moved $successCount documentation files to archive" -ForegroundColor Cyan
Write-Host "✅ All mapping files remain in original locations for Kestra compatibility" -ForegroundColor Green
