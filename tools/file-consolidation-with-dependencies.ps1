# File Consolidation with Dependency Updates
# Comprehensive PowerShell automation for customer-orders consolidation
# Handles both file movements AND dependency updates

param(
    [string]$Phase = "all",
    [switch]$DryRun = $false,
    [switch]$ValidateOnly = $false
)

Write-Host "🚀 Customer Orders File Consolidation with Dependency Updates" -ForegroundColor Green
Write-Host "Phase: $Phase | Dry Run: $DryRun | Validate Only: $ValidateOnly" -ForegroundColor Yellow

# Dependency mapping for file movements
$DependencyMap = @{
    # When we move these files, we need to update these references
    'sql/mappings/orders-unified-mapping.yaml' = @(
        'scripts/customer_master_schedule/*.py',
        'scripts/monday-boards/*.py',
        'tests/customer_master_schedule_tests/*.py',
        'docs/mapping/*.md',
        'workflows/*.yml'
    )
    'sql/mappings/simple-orders-mapping.yaml' = @(
        'utils/simple_mapper.py',
        'utils/mapping_helper.py',
        'scripts/order_sync_v2.py',
        'dev/customer-orders/*.py'
    )
    'utils/data_mapping.yaml' = @(
        'scripts/customer_master_schedule/add_order.py',
        'scripts/customer_master_schedule/add_bulk_orders.py',
        'utils/mapping_helper.py',
        'tests/debug/*.py'
    )
    'docs/mapping/' = @(
        'docs/CUSTOMER_ORDERS_PIPELINE_HANDOVER.md',
        'docs/plans/*.md',
        'docs/design/*.md',
        'README.md',
        'tasks/ops/*.yml'
    )
}

# Pattern-based reference updates
$ReferencePatterns = @{
    # Python file references
    "from sql\.mappings\..*import" = "# ❌ MOVED: Use utils/ imports instead"
    "sql/mappings/orders-unified-mapping\.yaml" = "sql/mappings/legacy/orders-unified-mapping.yaml"
    "sql/mappings/simple-orders-mapping\.yaml" = "sql/mappings/customer-orders-simple-mapping.yaml"
    "utils/data_mapping\.yaml" = "sql/mappings/legacy/data_mapping.yaml"
    
    # Documentation references
    "docs/mapping/" = "sql/mappings/ or docs/archive/customer-orders/"
    "orders_unified" = "customer-orders"
    "orders-unified" = "customer-orders"
    
    # VS Code task references
    '"sql/mappings/orders-unified-mapping\.yaml"' = '"sql/mappings/legacy/orders-unified-mapping.yaml"'
    '"utils/data_mapping\.yaml"' = '"sql/mappings/legacy/data_mapping.yaml"'
}

function Test-FileExists {
    param([string]$FilePath)
    return Test-Path -Path $FilePath -PathType Leaf
}

function Update-FileReferences {
    param(
        [string]$FilePath,
        [hashtable]$Patterns,
        [switch]$DryRun
    )
    
    if (-not (Test-FileExists $FilePath)) {
        Write-Warning "⚠️ File not found: $FilePath"
        return $false
    }
    
    $content = Get-Content -Path $FilePath -Raw
    $originalContent = $content
    $updateCount = 0
    
    foreach ($pattern in $Patterns.Keys) {
        $replacement = $Patterns[$pattern]
        if ($content -match $pattern) {
            $content = $content -replace $pattern, $replacement
            $updateCount++
            Write-Host "  ✅ Updated pattern '$pattern' → '$replacement'" -ForegroundColor Green
        }
    }
    
    if ($updateCount -gt 0 -and -not $DryRun) {
        Set-Content -Path $FilePath -Value $content -NoNewline
        Write-Host "  📝 Updated $updateCount references in: $FilePath" -ForegroundColor Cyan
    } elseif ($updateCount -gt 0) {
        Write-Host "  🔍 [DRY RUN] Would update $updateCount references in: $FilePath" -ForegroundColor Yellow
    }
    
    return $updateCount -gt 0
}

function Update-VSCodeTasks {
    param([switch]$DryRun)
    
    $tasksFile = ".vscode/tasks.json"
    if (-not (Test-FileExists $tasksFile)) {
        Write-Warning "⚠️ VS Code tasks.json not found"
        return
    }
    
    Write-Host "🔧 Updating VS Code tasks..." -ForegroundColor Blue
    
    # Load and update tasks.json
    $tasks = Get-Content -Path $tasksFile | ConvertFrom-Json
    $updateCount = 0
    
    foreach ($task in $tasks.tasks) {
        if ($task.args -contains "sql/mappings/orders-unified-mapping.yaml") {
            $task.args = $task.args -replace "sql/mappings/orders-unified-mapping\.yaml", "sql/mappings/legacy/orders-unified-mapping.yaml"
            $updateCount++
        }
        if ($task.args -contains "utils/data_mapping.yaml") {
            $task.args = $task.args -replace "utils/data_mapping\.yaml", "sql/mappings/legacy/data_mapping.yaml"
            $updateCount++
        }
    }
    
    if ($updateCount -gt 0 -and -not $DryRun) {
        $tasks | ConvertTo-Json -Depth 10 | Set-Content -Path $tasksFile
        Write-Host "  ✅ Updated $updateCount VS Code task references" -ForegroundColor Green
    } elseif ($updateCount -gt 0) {
        Write-Host "  🔍 [DRY RUN] Would update $updateCount VS Code task references" -ForegroundColor Yellow
    }
}

function Update-AllDependencies {
    param(
        [string]$MovedFile,
        [string]$NewLocation,
        [switch]$DryRun
    )
    
    Write-Host "🔗 Updating dependencies for: $MovedFile → $NewLocation" -ForegroundColor Blue
    
    if ($DependencyMap.ContainsKey($MovedFile)) {
        $dependentFiles = $DependencyMap[$MovedFile]
        
        foreach ($pattern in $dependentFiles) {
            $files = Get-ChildItem -Path $pattern -Recurse -ErrorAction SilentlyContinue
            
            foreach ($file in $files) {
                Update-FileReferences -FilePath $file.FullName -Patterns $ReferencePatterns -DryRun:$DryRun
            }
        }
    }
    
    # Update VS Code tasks
    Update-VSCodeTasks -DryRun:$DryRun
}

function Move-FileWithDependencies {
    param(
        [string]$SourcePath,
        [string]$DestinationPath,
        [switch]$DryRun
    )
    
    if (-not (Test-FileExists $SourcePath)) {
        Write-Warning "⚠️ Source file not found: $SourcePath"
        return $false
    }
    
    # Create destination directory if needed
    $destDir = Split-Path -Path $DestinationPath -Parent
    if (-not (Test-Path -Path $destDir)) {
        if (-not $DryRun) {
            New-Item -Path $destDir -ItemType Directory -Force | Out-Null
            Write-Host "  📁 Created directory: $destDir" -ForegroundColor Green
        } else {
            Write-Host "  🔍 [DRY RUN] Would create directory: $destDir" -ForegroundColor Yellow
        }
    }
    
    # Move the file
    if (-not $DryRun) {
        Move-Item -Path $SourcePath -Destination $DestinationPath -Force
        Write-Host "  ✅ Moved: $SourcePath → $DestinationPath" -ForegroundColor Green
    } else {
        Write-Host "  🔍 [DRY RUN] Would move: $SourcePath → $DestinationPath" -ForegroundColor Yellow
    }
    
    # Update all dependencies
    Update-AllDependencies -MovedFile $SourcePath -NewLocation $DestinationPath -DryRun:$DryRun
    
    return $true
}

function Execute-Phase1 {
    param([switch]$DryRun)
    
    Write-Host "📦 Phase 1: Legacy Mapping Files" -ForegroundColor Magenta
    
    $phase1Files = @(
        @{ Source = "sql/mappings/orders-unified-mapping.yaml"; Dest = "sql/mappings/legacy/orders-unified-mapping.yaml" },
        @{ Source = "sql/mappings/orders-unified-delta-sync-v3-mapping.yaml"; Dest = "sql/mappings/legacy/orders-unified-delta-sync-v3-mapping.yaml" },
        @{ Source = "sql/mappings/orders_unified_comprehensive_pipeline.yaml"; Dest = "sql/mappings/legacy/orders_unified_comprehensive_pipeline.yaml" },
        @{ Source = "sql/mappings/orders-monday-master.json"; Dest = "sql/mappings/legacy/orders-monday-master.json" },
        @{ Source = "sql/mappings/orders-monday-subitems.json"; Dest = "sql/mappings/legacy/orders-monday-subitems.json" },
        @{ Source = "utils/data_mapping.yaml"; Dest = "sql/mappings/legacy/data_mapping.yaml" }
    )
    
    foreach ($fileMove in $phase1Files) {
        Move-FileWithDependencies -SourcePath $fileMove.Source -DestinationPath $fileMove.Dest -DryRun:$DryRun
    }
}

function Execute-Phase2 {
    param([switch]$DryRun)
    
    Write-Host "🗑️ Phase 2: Remove Duplicate Files" -ForegroundColor Magenta
    
    $duplicateFiles = @(
        "docs/mapping/orders_unified_monday_mapping.yaml",
        "docs/mapping/monday_column_ids.json"
    )
    
    $archiveFiles = @(
        @{ Source = "docs/mapping/field_mapping_matrix.yaml"; Dest = "sql/mappings/legacy/field_mapping_matrix.yaml" },
        @{ Source = "docs/mapping/customer_mapping.yaml"; Dest = "sql/mappings/legacy/customer_mapping.yaml" },
        @{ Source = "docs/mapping/mapping_fields.yaml"; Dest = "sql/mappings/legacy/mapping_fields.yaml" }
    )
    
    # Remove duplicates
    foreach ($file in $duplicateFiles) {
        if (Test-FileExists $file) {
            if (-not $DryRun) {
                Remove-Item -Path $file -Force
                Write-Host "  🗑️ Removed duplicate: $file" -ForegroundColor Red
            } else {
                Write-Host "  🔍 [DRY RUN] Would remove: $file" -ForegroundColor Yellow
            }
        }
    }
    
    # Archive fragments
    foreach ($fileMove in $archiveFiles) {
        Move-FileWithDependencies -SourcePath $fileMove.Source -DestinationPath $fileMove.Dest -DryRun:$DryRun
    }
}

function Execute-Phase3 {
    param([switch]$DryRun)
    
    Write-Host "📝 Phase 3: Rename Production Files" -ForegroundColor Magenta
    
    $renameFiles = @(
        @{ Source = "sql/mappings/orders-unified-comprehensive-mapping.yaml"; Dest = "sql/mappings/customer-orders-master-mapping.yaml" },
        @{ Source = "sql/mappings/simple-orders-mapping.yaml"; Dest = "sql/mappings/customer-orders-simple-mapping.yaml" },
        @{ Source = "sql/mappings/monday-column-ids.json"; Dest = "sql/mappings/customer-orders-monday-columns.json" }
    )
    
    foreach ($fileMove in $renameFiles) {
        Move-FileWithDependencies -SourcePath $fileMove.Source -DestinationPath $fileMove.Dest -DryRun:$DryRun
    }
}

function Validate-Consolidation {
    Write-Host "🔍 Validating consolidation results..." -ForegroundColor Blue
    
    $issues = @()
    
    # Check for broken imports
    $pythonFiles = Get-ChildItem -Path "*.py" -Recurse
    foreach ($file in $pythonFiles) {
        $content = Get-Content -Path $file.FullName -Raw
        if ($content -match "from sql\.mappings\..*import") {
            $issues += "❌ Broken import in: $($file.FullName)"
        }
    }
    
    # Check for missing files
    $requiredFiles = @(
        "sql/mappings/customer-orders-master-mapping.yaml",
        "sql/mappings/customer-orders-simple-mapping.yaml",
        "sql/mappings/customer-orders-monday-columns.json"
    )
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-FileExists $file)) {
            $issues += "❌ Missing required file: $file"
        }
    }
    
    if ($issues.Count -eq 0) {
        Write-Host "✅ All validation checks passed!" -ForegroundColor Green
        return $true
    } else {
        Write-Host "❌ Validation issues found:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "  $issue" -ForegroundColor Red
        }
        return $false
    }
}

# Main execution
try {
    if ($ValidateOnly) {
        Validate-Consolidation
        exit
    }
    
    switch ($Phase.ToLower()) {
        "1" { Execute-Phase1 -DryRun:$DryRun }
        "2" { Execute-Phase2 -DryRun:$DryRun }
        "3" { Execute-Phase3 -DryRun:$DryRun }
        "all" {
            Execute-Phase1 -DryRun:$DryRun
            Execute-Phase2 -DryRun:$DryRun
            Execute-Phase3 -DryRun:$DryRun
        }
        default {
            Write-Error "Invalid phase. Use: 1, 2, 3, or all"
            exit 1
        }
    }
    
    if (-not $DryRun) {
        Write-Host "🎯 Running final validation..." -ForegroundColor Blue
        Validate-Consolidation
    }
    
    Write-Host "🚀 File consolidation completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Error "❌ Consolidation failed: $($_.Exception.Message)"
    exit 1
}
