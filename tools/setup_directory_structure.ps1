#!/usr/bin/env powershell
<#
.SYNOPSIS
    Setup Directory Structure for Monday.com Board Extraction Refactor
    
.DESCRIPTION
    Creates the new directory structure for the unified board extraction system.
    Handles existing folders gracefully and shows what will be created/moved.
    
.EXAMPLE
    .\setup_directory_structure.ps1 -WhatIf
    .\setup_directory_structure.ps1 -Execute
#>

param(
    [switch]$Execute,
    [switch]$WhatIf
)

# Default to WhatIf mode if no switches provided
if (-not $Execute -and -not $WhatIf) {
    $WhatIf = $true
}

# Get repository root
$RepoRoot = $PSScriptRoot
Write-Host "🚀 Monday.com Board Extraction - Directory Setup" -ForegroundColor Cyan
Write-Host "📁 Repository Root: $RepoRoot" -ForegroundColor Gray
Write-Host ""

# Define directory structure
$DirectoryStructure = @{
    # Root level directories
    "configs" = @{
        "path" = "configs"
        "description" = "Board metadata and configurations"
        "subdirs" = @("boards")
    }
    "workflows" = @{
        "path" = "workflows" 
        "description" = "Kestra workflow definitions"
        "subdirs" = @()
    }
    
    # Under pipelines/ (already exists)
    "pipelines_scripts" = @{
        "path" = "pipelines\scripts"
        "description" = "ELT pipeline scripts"
        "subdirs" = @()
    }
    "pipelines_codegen" = @{
        "path" = "pipelines\codegen"
        "description" = "Code generation utilities"
        "subdirs" = @("templates")
    }
    "pipelines_utils" = @{
        "path" = "pipelines\utils"
        "description" = "Shared utilities (copied from root utils/)"
        "subdirs" = @()
    }
}

# Files to create
$FilesToCreate = @{
    "configs\registry.json" = @{
        "description" = "Master board registry"
        "content" = '{
  "boards": {},
  "metadata": {
    "version": "1.0",
    "created_at": "' + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ') + '",
    "updated_at": "' + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ') + '"
  }
}'
    }
    "configs\boards\.gitkeep" = @{
        "description" = "Placeholder for boards directory"
        "content" = "# Board configuration files will be stored here"
    }
    "pipelines\codegen\templates\.gitkeep" = @{
        "description" = "Placeholder for templates directory"
        "content" = "# Jinja2 templates for code generation"
    }
}

# Files to move/copy
$FilesToMove = @{
    "dev\monday-boards-dynamic\universal_board_extractor.py" = "pipelines\codegen\universal_board_extractor.py"
    "dev\monday-boards-dynamic\templates" = "pipelines\codegen\templates"
    "dev\monday-boards-dynamic\core\script_template_generator.py" = "pipelines\codegen\script_template_generator.py"
    "dev\monday-boards-dynamic\metadata\board_registry.json" = "configs\registry.json"
}

# Utils files to copy (not move - keep originals)
$UtilsToCopy = @(
    "db_helper.py"
    "logger_helper.py" 
    "staging_helper.py"
    "config.yaml"
)

Write-Host "📋 PLANNED DIRECTORY STRUCTURE:" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Yellow

function Show-DirectoryPlan {
    param($Structure, $Indent = "")
    
    foreach ($key in $Structure.Keys | Sort-Object) {
        $item = $Structure[$key]
        $fullPath = Join-Path $RepoRoot $item.path
        $exists = Test-Path $fullPath
        $status = if ($exists) { "EXISTS" } else { "CREATE" }
        
        Write-Host "$Indent$status $($item.path) - $($item.description)" -ForegroundColor $(if ($exists) { "Green" } else { "White" })
        
        # Show subdirectories
        foreach ($subdir in $item.subdirs) {
            $subPath = Join-Path $fullPath $subdir
            $subExists = Test-Path $subPath
            $subStatus = if ($subExists) { "EXISTS" } else { "CREATE" }
            Write-Host "$Indent  $subStatus $($item.path)\$subdir" -ForegroundColor $(if ($subExists) { "Green" } else { "Gray" })
        }
    }
}

Show-DirectoryPlan $DirectoryStructure

Write-Host ""
Write-Host "📄 FILES TO CREATE:" -ForegroundColor Yellow
Write-Host "===================" -ForegroundColor Yellow

foreach ($file in $FilesToCreate.Keys) {
    $fullPath = Join-Path $RepoRoot $file
    $exists = Test-Path $fullPath
    $status = if ($exists) { "EXISTS" } else { "CREATE" }
    Write-Host "$status $file - $($FilesToCreate[$file].description)" -ForegroundColor $(if ($exists) { "Yellow" } else { "White" })
}

Write-Host ""
Write-Host "📦 FILES TO MOVE:" -ForegroundColor Yellow
Write-Host "=================" -ForegroundColor Yellow

foreach ($source in $FilesToMove.Keys) {
    $sourcePath = Join-Path $RepoRoot $source
    $destPath = Join-Path $RepoRoot $FilesToMove[$source]
    $sourceExists = Test-Path $sourcePath
    $destExists = Test-Path $destPath
    
    if ($sourceExists) {
        if ($destExists) {
            Write-Host "CONFLICT $source -> $($FilesToMove[$source]) (destination exists)" -ForegroundColor Red
        } else {
            Write-Host "MOVE $source -> $($FilesToMove[$source])" -ForegroundColor White
        }
    } else {
        Write-Host "MISSING $source (source not found)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📋 UTILS TO COPY:" -ForegroundColor Yellow
Write-Host "=================" -ForegroundColor Yellow

foreach ($util in $UtilsToCopy) {
    $sourcePath = Join-Path $RepoRoot "utils\$util"
    $destPath = Join-Path $RepoRoot "pipelines\utils\$util"
    $sourceExists = Test-Path $sourcePath
    $destExists = Test-Path $destPath
    
    if ($sourceExists) {
        if ($destExists) {
            Write-Host "EXISTS utils\$util -> pipelines\utils\$util (will overwrite)" -ForegroundColor Yellow
        } else {
            Write-Host "COPY utils\$util -> pipelines\utils\$util" -ForegroundColor White
        }
    } else {
        Write-Host "MISSING utils\$util (source not found)" -ForegroundColor Red
    }
}

Write-Host ""

if ($WhatIf -and -not $Execute) {
    Write-Host "PREVIEW MODE - No changes made" -ForegroundColor Cyan
    Write-Host "   Run with -Execute to apply changes" -ForegroundColor Gray
    Write-Host "   Example: .\setup_directory_structure.ps1 -Execute" -ForegroundColor Gray
    return
}

if (-not $Execute) {
    $confirm = Read-Host "Execute these changes? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Cancelled by user" -ForegroundColor Red
        return
    }
}

Write-Host "🔧 EXECUTING CHANGES..." -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# Create directories
foreach ($key in $DirectoryStructure.Keys) {
    $item = $DirectoryStructure[$key]
    $fullPath = Join-Path $RepoRoot $item.path
    
    if (-not (Test-Path $fullPath)) {
        try {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "Created directory: $($item.path)" -ForegroundColor Green
        } catch {
            Write-Host "Failed to create directory: $($item.path) - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Directory exists: $($item.path)" -ForegroundColor Gray
    }
    
    # Create subdirectories
    foreach ($subdir in $item.subdirs) {
        $subPath = Join-Path $fullPath $subdir
        if (-not (Test-Path $subPath)) {
            try {
                New-Item -ItemType Directory -Path $subPath -Force | Out-Null
                Write-Host "Created subdirectory: $($item.path)\$subdir" -ForegroundColor Green
            } catch {
                Write-Host "Failed to create subdirectory: $($item.path)\$subdir - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# Create files
foreach ($file in $FilesToCreate.Keys) {
    $fullPath = Join-Path $RepoRoot $file
    $directory = Split-Path $fullPath -Parent
    
    # Ensure directory exists
    if (-not (Test-Path $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    
    if (-not (Test-Path $fullPath)) {
        try {
            $FilesToCreate[$file].content | Out-File -FilePath $fullPath -Encoding UTF8
            Write-Host "Created file: $file" -ForegroundColor Green
        } catch {
            Write-Host "Failed to create file: $file - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "File exists: $file (skipped)" -ForegroundColor Yellow
    }
}

# Move files
foreach ($source in $FilesToMove.Keys) {
    $sourcePath = Join-Path $RepoRoot $source
    $destPath = Join-Path $RepoRoot $FilesToMove[$source]
    $destDirectory = Split-Path $destPath -Parent
    
    if (Test-Path $sourcePath) {
        # Ensure destination directory exists
        if (-not (Test-Path $destDirectory)) {
            New-Item -ItemType Directory -Path $destDirectory -Force | Out-Null
        }
        
        if (-not (Test-Path $destPath)) {
            try {
                if (Test-Path $sourcePath -PathType Container) {
                    # Moving a directory
                    Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
                    Write-Host "Copied directory: $source -> $($FilesToMove[$source])" -ForegroundColor Green
                } else {
                    # Moving a file
                    Copy-Item -Path $sourcePath -Destination $destPath -Force
                    Write-Host "Copied file: $source -> $($FilesToMove[$source])" -ForegroundColor Green
                }
            } catch {
                Write-Host "Failed to copy: $source -> $($FilesToMove[$source]) - $($_.Exception.Message)" -ForegroundColor Red
            }
        } else {
            Write-Host "Destination exists: $($FilesToMove[$source]) (skipped)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Source not found: $source" -ForegroundColor Red
    }
}

# Copy utils
$utilsDestDir = Join-Path $RepoRoot "pipelines\utils"
if (-not (Test-Path $utilsDestDir)) {
    New-Item -ItemType Directory -Path $utilsDestDir -Force | Out-Null
}

foreach ($util in $UtilsToCopy) {
    $sourcePath = Join-Path $RepoRoot "utils\$util"
    $destPath = Join-Path $RepoRoot "pipelines\utils\$util"
    
    if (Test-Path $sourcePath) {
        try {
            Copy-Item -Path $sourcePath -Destination $destPath -Force
            Write-Host "Copied utility: utils\$util -> pipelines\utils\$util" -ForegroundColor Green
        } catch {
            Write-Host "Failed to copy utility: utils\$util - $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "Utility not found: utils\$util" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Review created directories and files" -ForegroundColor Gray
Write-Host "2. Implement load_boards.py in pipelines\scripts\" -ForegroundColor Gray
Write-Host "3. Test with existing board configurations" -ForegroundColor Gray
Write-Host ""
Write-Host "New structure ready for unified board extraction!" -ForegroundColor Cyan
