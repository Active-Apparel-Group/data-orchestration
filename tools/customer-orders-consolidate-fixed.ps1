# Customer Orders File Consolidation Script
# Handles file moves and dependency updates for the customer-orders pipeline

param(
    [string]$Phase = "all",
    [switch]$DryRun = $false
)

Write-Host "🚀 Customer Orders File Consolidation" -ForegroundColor Green
Write-Host "Phase: $Phase | Dry Run: $DryRun" -ForegroundColor Yellow

# File movements to execute
$FileMoves = @{
    "Phase1" = @(
        @{ Source = "sql\mappings\orders-unified-mapping.yaml"; Dest = "sql\mappings\legacy\orders-unified-mapping.yaml" },
        @{ Source = "sql\mappings\orders-unified-delta-sync-v3-mapping.yaml"; Dest = "sql\mappings\legacy\orders-unified-delta-sync-v3-mapping.yaml" },
        @{ Source = "sql\mappings\orders_unified_comprehensive_pipeline.yaml"; Dest = "sql\mappings\legacy\orders_unified_comprehensive_pipeline.yaml" },
        @{ Source = "sql\mappings\orders-monday-master.json"; Dest = "sql\mappings\legacy\orders-monday-master.json" },
        @{ Source = "sql\mappings\orders-monday-subitems.json"; Dest = "sql\mappings\legacy\orders-monday-subitems.json" },
        @{ Source = "utils\data_mapping.yaml"; Dest = "sql\mappings\legacy\data_mapping.yaml" }
    )
    "Phase2" = @(
        @{ Source = "docs\mapping\orders_unified_monday_mapping.yaml"; Action = "DELETE" },
        @{ Source = "docs\mapping\field_mapping_matrix.yaml"; Dest = "sql\mappings\legacy\field_mapping_matrix.yaml" },
        @{ Source = "docs\mapping\monday_column_ids.json"; Action = "DELETE" },
        @{ Source = "docs\mapping\customer_mapping.yaml"; Dest = "sql\mappings\legacy\customer_mapping.yaml" },
        @{ Source = "docs\mapping\mapping_fields.yaml"; Dest = "sql\mappings\legacy\mapping_fields.yaml" }
    )
    "Phase3" = @(
        @{ Source = "sql\mappings\orders-unified-comprehensive-mapping.yaml"; Dest = "sql\mappings\customer-orders-master-mapping.yaml" },
        @{ Source = "sql\mappings\simple-orders-mapping.yaml"; Dest = "sql\mappings\customer-orders-simple-mapping.yaml" },
        @{ Source = "sql\mappings\monday-column-ids.json"; Dest = "sql\mappings\customer-orders-monday-columns.json" }
    )
}

function Test-FileExists {
    param([string]$Path)
    return Test-Path -Path $Path
}

function Move-FileWithBackup {
    param(
        [string]$Source,
        [string]$Destination,
        [switch]$DryRun
    )
    
    if (-not (Test-FileExists $Source)) {
        Write-Warning "⚠️ Source file not found: $Source"
        return $false
    }
    
    # Create destination directory
    $destDir = Split-Path -Path $Destination -Parent
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
        try {
            Move-Item -Path $Source -Destination $Destination -Force
            Write-Host "  ✅ Moved: $Source → $Destination" -ForegroundColor Green
            return $true
        } catch {
            Write-Error "❌ Failed to move $Source to $Destination : $_"
            return $false
        }
    } else {
        Write-Host "  🔍 [DRY RUN] Would move: $Source → $Destination" -ForegroundColor Yellow
        return $true
    }
}

function Remove-FileWithBackup {
    param(
        [string]$FilePath,
        [switch]$DryRun
    )
    
    if (-not (Test-FileExists $FilePath)) {
        Write-Warning "⚠️ File not found: $FilePath"
        return $false
    }
    
    if (-not $DryRun) {
        try {
            Remove-Item -Path $FilePath -Force
            Write-Host "  🗑️ Deleted: $FilePath" -ForegroundColor Green
            return $true
        } catch {
            Write-Error "❌ Failed to delete $FilePath : $_"
            return $false
        }
    } else {
        Write-Host "  🔍 [DRY RUN] Would delete: $FilePath" -ForegroundColor Yellow
        return $true
    }
}

function Update-FileReferences {
    param(
        [string]$FilePath,
        [string]$OldPattern,
        [string]$NewPattern,
        [switch]$DryRun
    )
    
    if (-not (Test-FileExists $FilePath)) {
        return $false
    }
    
    try {
        $content = Get-Content -Path $FilePath -Raw -ErrorAction SilentlyContinue
        if (-not $content) { 
            return $false 
        }
        
        if ($content -match $OldPattern) {
            $newContent = $content -replace $OldPattern, $NewPattern
            
            if (-not $DryRun) {
                Set-Content -Path $FilePath -Value $newContent -NoNewline
                Write-Host "  ✅ Updated references in: $(Split-Path -Leaf $FilePath)" -ForegroundColor Green
            } else {
                Write-Host "  🔍 [DRY RUN] Would update references in: $(Split-Path -Leaf $FilePath)" -ForegroundColor Yellow
            }
            return $true
        }
    } catch {
        Write-Warning "⚠️ Could not process file: $FilePath"
    }
    
    return $false
}

function Start-ConsolidationPhase {
    param(
        [string]$PhaseName,
        [switch]$DryRun
    )
    
    Write-Host "`n🎯 Executing Phase: $PhaseName" -ForegroundColor Magenta
    
    if (-not $FileMoves.ContainsKey($PhaseName)) {
        Write-Warning "⚠️ Phase $PhaseName not found"
        return
    }
    
    $moves = $FileMoves[$PhaseName]
    $successCount = 0
    
    foreach ($move in $moves) {
        $source = $move.Source
        $destination = $move.Dest
        $action = $move.Action
        
        if ($action -eq "DELETE") {
            if (Remove-FileWithBackup -FilePath $source -DryRun:$DryRun) {
                $successCount++
            }
        } else {
            if (Move-FileWithBackup -Source $source -Destination $destination -DryRun:$DryRun) {
                $successCount++
                
                # Update dependencies for specific files
                if ($source -eq "utils\data_mapping.yaml") {
                    Write-Host "🔗 Updating references to data_mapping.yaml" -ForegroundColor Blue
                    
                    # Update Python files
                    $pythonFiles = Get-ChildItem -Path "scripts", "utils", "dev" -Filter "*.py" -Recurse -ErrorAction SilentlyContinue
                    foreach ($file in $pythonFiles) {
                        Update-FileReferences -FilePath $file.FullName -OldPattern "utils[/\\]data_mapping\.yaml" -NewPattern "sql/mappings/legacy/data_mapping.yaml" -DryRun:$DryRun
                        Update-FileReferences -FilePath $file.FullName -OldPattern '"data_mapping\.yaml"' -NewPattern '"legacy/data_mapping.yaml"' -DryRun:$DryRun
                    }
                }
                
                if ($source -eq "sql\mappings\simple-orders-mapping.yaml") {
                    Write-Host "🔗 Updating references to simple-orders-mapping.yaml" -ForegroundColor Blue
                    
                    # Update all files
                    $allFiles = Get-ChildItem -Path "." -Include "*.py", "*.yml", "*.yaml", "*.md" -Recurse -ErrorAction SilentlyContinue
                    foreach ($file in $allFiles) {
                        Update-FileReferences -FilePath $file.FullName -OldPattern "simple-orders-mapping\.yaml" -NewPattern "customer-orders-simple-mapping.yaml" -DryRun:$DryRun
                    }
                }
            }
        }
    }
    
    Write-Host "📊 Phase $PhaseName completed: $successCount/$($moves.Count) operations successful" -ForegroundColor Cyan
}

# Main execution
try {
    if ($Phase -eq "all" -or $Phase -eq "1") {
        Start-ConsolidationPhase -PhaseName "Phase1" -DryRun:$DryRun
    }
    
    if ($Phase -eq "all" -or $Phase -eq "2") {
        Start-ConsolidationPhase -PhaseName "Phase2" -DryRun:$DryRun
    }
    
    if ($Phase -eq "all" -or $Phase -eq "3") {
        Start-ConsolidationPhase -PhaseName "Phase3" -DryRun:$DryRun
    }
    
    Write-Host "`n🎉 Customer Orders consolidation completed!" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the application to ensure all references work" -ForegroundColor Yellow
    Write-Host "  2. Update the FILE_MOVEMENT_TRACKER.md with completed items" -ForegroundColor Yellow
    Write-Host "  3. Commit the changes to git" -ForegroundColor Yellow
    
} catch {
    Write-Error "❌ Consolidation failed: $_"
    exit 1
}
