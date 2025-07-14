# Customer Orders File Consolidation Script
# Purpose: Automate file movements with validation and progress tracking
# Usage: powershell -File tools/consolidate-customer-orders-files.ps1

param(
    [string]$Phase = "all",  # Which phase to run: 1, 2, 3, 4, or "all"
    [switch]$DryRun = $false,  # If true, show what would happen without doing it
    [switch]$Rollback = $false  # If true, rollback changes
)

# Set working directory to project root
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "🚀 Customer Orders File Consolidation Script" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Phase: $Phase | Dry Run: $DryRun | Rollback: $Rollback" -ForegroundColor Gray
Write-Host ""

# Progress tracking
$Results = @{
    Phase1 = @()
    Phase2 = @()  
    Phase3 = @()
    Phase4 = @()
    Errors = @()
}

function Log-Action {
    param([string]$Action, [string]$Status, [string]$Details = "")
    $timestamp = Get-Date -Format "HH:mm:ss"
    $color = switch($Status) {
        "SUCCESS" { "Green" }
        "ERROR" { "Red" }
        "INFO" { "Cyan" }
        "WARNING" { "Yellow" }
        default { "White" }
    }
    Write-Host "[$timestamp] $Status : $Action $Details" -ForegroundColor $color
}

function Test-FileExists {
    param([string]$Path)
    return Test-Path $Path -PathType Leaf
}

function Move-FileWithValidation {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Description,
        [switch]$Force = $false
    )
    
    try {
        if (-not (Test-FileExists $Source)) {
            Log-Action "SKIP: $Description" "WARNING" "- Source file not found: $Source"
            return $false
        }
        
        # Create destination directory if needed
        $destDir = Split-Path -Parent $Destination
        if (-not (Test-Path $destDir)) {
            if (-not $DryRun) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                Log-Action "CREATE DIR: $destDir" "INFO"
            } else {
                Log-Action "WOULD CREATE DIR: $destDir" "INFO"
            }
        }
        
        if ($DryRun) {
            Log-Action "WOULD MOVE: $Description" "INFO" "- $Source → $Destination"
            return $true
        } else {
            Move-Item $Source $Destination -Force:$Force
            if (Test-FileExists $Destination) {
                Log-Action "MOVE: $Description" "SUCCESS" "- $Source → $Destination"
                return $true
            } else {
                Log-Action "MOVE: $Description" "ERROR" "- Destination file not found after move"
                return $false
            }
        }
    }
    catch {
        Log-Action "MOVE: $Description" "ERROR" "- $($_.Exception.Message)"
        $Results.Errors += "Failed to move $Source : $($_.Exception.Message)"
        return $false
    }
}

function Remove-FileWithValidation {
    param([string]$Path, [string]$Description)
    
    try {
        if (-not (Test-FileExists $Path)) {
            Log-Action "SKIP: $Description" "WARNING" "- File not found: $Path"
            return $false
        }
        
        if ($DryRun) {
            Log-Action "WOULD DELETE: $Description" "INFO" "- $Path"
            return $true
        } else {
            Remove-Item $Path -Force
            if (-not (Test-FileExists $Path)) {
                Log-Action "DELETE: $Description" "SUCCESS" "- $Path"
                return $true
            } else {
                Log-Action "DELETE: $Description" "ERROR" "- File still exists after delete"
                return $false
            }
        }
    }
    catch {
        Log-Action "DELETE: $Description" "ERROR" "- $($_.Exception.Message)"
        $Results.Errors += "Failed to delete $Path : $($_.Exception.Message)"
        return $false
    }
}

function Rename-FileWithValidation {
    param([string]$OldPath, [string]$NewName, [string]$Description)
    
    try {
        if (-not (Test-FileExists $OldPath)) {
            Log-Action "SKIP: $Description" "WARNING" "- Source file not found: $OldPath"
            return $false
        }
        
        $newPath = Join-Path (Split-Path -Parent $OldPath) $NewName
        
        if ($DryRun) {
            Log-Action "WOULD RENAME: $Description" "INFO" "- $OldPath → $NewName"
            return $true
        } else {
            Rename-Item $OldPath $NewName -Force
            if (Test-FileExists $newPath) {
                Log-Action "RENAME: $Description" "SUCCESS" "- $OldPath → $NewName"
                return $true
            } else {
                Log-Action "RENAME: $Description" "ERROR" "- New file not found after rename"
                return $false
            }
        }
    }
    catch {
        Log-Action "RENAME: $Description" "ERROR" "- $($_.Exception.Message)"
        $Results.Errors += "Failed to rename $OldPath : $($_.Exception.Message)"
        return $false
    }
}

# Phase 1: Archive Legacy Mapping Files
function Invoke-Phase1 {
    Write-Host "`n📦 Phase 1: Archive Legacy Mapping Files" -ForegroundColor Yellow
    
    $moves = @(
        @{ Source = "sql\mappings\orders-unified-mapping.yaml"; Dest = "sql\mappings\legacy\orders-unified-mapping.yaml"; Desc = "Archive legacy orders-unified-mapping.yaml" }
        @{ Source = "sql\mappings\orders-unified-delta-sync-v3-mapping.yaml"; Dest = "sql\mappings\legacy\orders-unified-delta-sync-v3-mapping.yaml"; Desc = "Archive legacy delta-sync-v3 mapping" }
        @{ Source = "sql\mappings\orders_unified_comprehensive_pipeline.yaml"; Dest = "sql\mappings\legacy\orders_unified_comprehensive_pipeline.yaml"; Desc = "Archive legacy comprehensive pipeline" }
        @{ Source = "sql\mappings\orders-monday-master.json"; Dest = "sql\mappings\legacy\orders-monday-master.json"; Desc = "Archive legacy Monday master JSON" }
        @{ Source = "sql\mappings\orders-monday-subitems.json"; Dest = "sql\mappings\legacy\orders-monday-subitems.json"; Desc = "Archive legacy Monday subitems JSON" }
        @{ Source = "utils\data_mapping.yaml"; Dest = "sql\mappings\legacy\data_mapping.yaml"; Desc = "Move utils data_mapping to archive" }
    )
    
    foreach ($move in $moves) {
        $success = Move-FileWithValidation -Source $move.Source -Destination $move.Dest -Description $move.Desc -Force
        $Results.Phase1 += @{ File = $move.Source; Success = $success; Description = $move.Desc }
    }
}

# Phase 2: Remove Duplicate Documentation Files  
function Invoke-Phase2 {
    Write-Host "`n🗑️ Phase 2: Remove Duplicate Documentation Files" -ForegroundColor Yellow
    
    # Files to delete (duplicates)
    $deletes = @(
        @{ Path = "docs\mapping\orders_unified_monday_mapping.yaml"; Desc = "Delete duplicate orders_unified_monday_mapping.yaml" }
        @{ Path = "docs\mapping\monday_column_ids.json"; Desc = "Delete duplicate monday_column_ids.json" }
    )
    
    foreach ($delete in $deletes) {
        $success = Remove-FileWithValidation -Path $delete.Path -Description $delete.Desc
        $Results.Phase2 += @{ File = $delete.Path; Success = $success; Description = $delete.Desc; Action = "DELETE" }
    }
    
    # Files to archive (fragments)
    $moves = @(
        @{ Source = "docs\mapping\field_mapping_matrix.yaml"; Dest = "sql\mappings\legacy\field_mapping_matrix.yaml"; Desc = "Archive field_mapping_matrix fragment" }
        @{ Source = "docs\mapping\customer_mapping.yaml"; Dest = "sql\mappings\legacy\customer_mapping.yaml"; Desc = "Archive incomplete customer_mapping" }
        @{ Source = "docs\mapping\mapping_fields.yaml"; Dest = "sql\mappings\legacy\mapping_fields.yaml"; Desc = "Archive mapping_fields fragment" }
    )
    
    foreach ($move in $moves) {
        $success = Move-FileWithValidation -Source $move.Source -Destination $move.Dest -Description $move.Desc -Force
        $Results.Phase2 += @{ File = $move.Source; Success = $success; Description = $move.Desc; Action = "MOVE" }
    }
}

# Phase 3: Rename Production Files
function Invoke-Phase3 {
    Write-Host "`n✏️ Phase 3: Rename Production Files" -ForegroundColor Yellow
    
    $renames = @(
        @{ Path = "sql\mappings\orders-unified-comprehensive-mapping.yaml"; NewName = "customer-orders-master-mapping.yaml"; Desc = "Rename to customer-orders-master-mapping.yaml" }
        @{ Path = "sql\mappings\simple-orders-mapping.yaml"; NewName = "customer-orders-simple-mapping.yaml"; Desc = "Rename to customer-orders-simple-mapping.yaml" }
        @{ Path = "sql\mappings\monday-column-ids.json"; NewName = "customer-orders-monday-columns.json"; Desc = "Rename to customer-orders-monday-columns.json" }
    )
    
    foreach ($rename in $renames) {
        $success = Rename-FileWithValidation -OldPath $rename.Path -NewName $rename.NewName -Description $rename.Desc
        $Results.Phase3 += @{ File = $rename.Path; Success = $success; Description = $rename.Desc; NewName = $rename.NewName }
    }
}

# Phase 4: Archive Documentation
function Invoke-Phase4 {
    Write-Host "`n📚 Phase 4: Archive Documentation" -ForegroundColor Yellow
    
    $moves = @(
        @{ Source = "docs\MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md"; Dest = "docs\archive\customer-orders\MAPPING_ANALYSIS_COMPREHENSIVE_REPORT.md"; Desc = "Archive comprehensive mapping analysis" }
        @{ Source = "docs\ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md"; Dest = "docs\archive\customer-orders\ORDERS_UNIFIED_BACKWARD_MAPPING_COMPREHENSIVE.md"; Desc = "Archive backward mapping analysis" }
        @{ Source = "docs\SCHEMA_VALIDATION_CRITICAL_ISSUES.md"; Dest = "docs\archive\customer-orders\SCHEMA_VALIDATION_CRITICAL_ISSUES.md"; Desc = "Archive schema validation issues" }
        @{ Source = "docs\SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md"; Dest = "docs\archive\customer-orders\SCHEMA_VALIDATION_IMPLEMENTATION_PLAN.md"; Desc = "Archive schema validation plan" }
        @{ Source = "docs\YAML_MAPPING_FORMAT_DECISION.md"; Dest = "docs\archive\customer-orders\YAML_MAPPING_FORMAT_DECISION.md"; Desc = "Archive YAML format decision" }
    )
    
    foreach ($move in $moves) {
        $success = Move-FileWithValidation -Source $move.Source -Destination $move.Dest -Description $move.Desc -Force
        $Results.Phase4 += @{ File = $move.Source; Success = $success; Description = $move.Desc }
    }
}

# Execute phases based on parameter
if ($Rollback) {
    Write-Host "🔄 ROLLBACK MODE - Reverting changes using Git" -ForegroundColor Red
    git checkout HEAD -- sql/mappings/ docs/mapping/ utils/data_mapping.yaml docs/
    Log-Action "Git rollback completed" "INFO"
    exit 0
}

switch ($Phase) {
    "1" { Invoke-Phase1 }
    "2" { Invoke-Phase2 }
    "3" { Invoke-Phase3 }
    "4" { Invoke-Phase4 }
    "all" { 
        Invoke-Phase1
        Invoke-Phase2  
        Invoke-Phase3
        Invoke-Phase4
    }
    default {
        Write-Host "❌ Invalid phase: $Phase. Use 1, 2, 3, 4, or 'all'" -ForegroundColor Red
        exit 1
    }
}

# Generate summary report
Write-Host "`n📊 CONSOLIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

$totalFiles = 0
$successFiles = 0

@("Phase1", "Phase2", "Phase3", "Phase4") | ForEach-Object {
    $phase = $_
    $phaseResults = $Results.$phase
    $total = $phaseResults.Count
    $successful = ($phaseResults | Where-Object { $_.Success }).Count
    
    if ($total -gt 0) {
        $percentage = [math]::Round(($successful / $total) * 100, 1)
        Write-Host "$phase : $successful/$total files ($percentage%)" -ForegroundColor $(if ($successful -eq $total) { "Green" } else { "Yellow" })
        
        $totalFiles += $total
        $successFiles += $successful
    }
}

$overallPercentage = if ($totalFiles -gt 0) { [math]::Round(($successFiles / $totalFiles) * 100, 1) } else { 0 }
Write-Host "OVERALL: $successFiles/$totalFiles files ($overallPercentage%)" -ForegroundColor $(if ($successFiles -eq $totalFiles) { "Green" } else { "Red" })

if ($Results.Errors.Count -gt 0) {
    Write-Host "`n❌ ERRORS ENCOUNTERED:" -ForegroundColor Red
    $Results.Errors | ForEach-Object { Write-Host "  • $_" -ForegroundColor Red }
}

Write-Host "`n✅ Next Steps:" -ForegroundColor Green
Write-Host "  1. Update FILE_MOVEMENT_TRACKER.md with completed items" -ForegroundColor Gray
Write-Host "  2. Test dev/customer-orders/ scripts still work" -ForegroundColor Gray  
Write-Host "  3. Update any hardcoded file paths in code" -ForegroundColor Gray
Write-Host "  4. Run VS Code tasks to verify no broken references" -ForegroundColor Gray
