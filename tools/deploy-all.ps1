#!/usr/bin/env powershell

# KESTRA COMPLETE DEPLOYMENT SCRIPT v2.0
# Calls existing deployment scripts in the correct order

param(
    [Parameter(Position=0)]
    [string]$Action = "deploy-all",
    [string]$KestraUrl = "http://localhost:8080",
    [string]$Namespace = "company.team"
)

function Show-Help {
    Write-Host "KESTRA COMPLETE DEPLOYMENT SCRIPT v2.0" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Green
    Write-Host ""
    Write-Host "COMMANDS:" -ForegroundColor Yellow
    Write-Host "  deploy-all      - Deploy both scripts and workflows (DEFAULT)"
    Write-Host "  scripts-only    - Deploy only scripts"
    Write-Host "  workflows-only  - Deploy only workflows"
    Write-Host "  list            - List deployed workflows"
    Write-Host "  help            - Show this help"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Cyan
    Write-Host "  .\deploy-all.ps1                    # Deploy everything"
    Write-Host "  .\deploy-all.ps1 scripts-only       # Deploy only scripts"
    Write-Host "  .\deploy-all.ps1 workflows-only     # Deploy only workflows"
    Write-Host ""
}

function Deploy-Scripts {
    Write-Host "[STEP] Deploying Scripts..." -ForegroundColor Magenta
    Write-Host ""
    
    try {
        & "$PSScriptRoot\deploy-scripts-clean.ps1" -KestraUrl $KestraUrl -Namespace $Namespace
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[SUCCESS] Scripts deployment completed successfully!" -ForegroundColor Green
            return $true
        } else {
            Write-Host "[ERROR] Scripts deployment failed!" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "[ERROR] Error running script deployment: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Deploy-Workflows {
    Write-Host "[STEP] Deploying Workflows..." -ForegroundColor Magenta
    Write-Host ""
    
    try {
        & "$PSScriptRoot\deploy-workflows.ps1" "deploy-all" -KestraUrl $KestraUrl -Namespace $Namespace
        
        Write-Host "[SUCCESS] Workflow deployment completed!" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[ERROR] Error running workflow deployment: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function List-Workflows {
    Write-Host "[INFO] Listing Deployed Workflows..." -ForegroundColor Magenta
    Write-Host ""
    
    try {
        & "$PSScriptRoot\deploy-workflows.ps1" "list" -KestraUrl $KestraUrl -Namespace $Namespace
        return $true
    } catch {
        Write-Host "[ERROR] Error listing workflows: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Deploy-All {
    Write-Host "KESTRA COMPLETE DEPLOYMENT" -ForegroundColor Green
    Write-Host "=" * 40 -ForegroundColor Green
    Write-Host "Target: $KestraUrl" -ForegroundColor Cyan
    Write-Host "Namespace: $Namespace" -ForegroundColor Cyan
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""
    
    $scriptsSuccess = Deploy-Scripts
    Write-Host ""
    
    $workflowsSuccess = Deploy-Workflows
    Write-Host ""
    
    # Summary
    Write-Host "DEPLOYMENT SUMMARY" -ForegroundColor Green
    Write-Host "=" * 30 -ForegroundColor Green
    
    if ($scriptsSuccess -and $workflowsSuccess) {
        Write-Host "[SUCCESS] All deployments completed successfully!" -ForegroundColor Green
        Write-Host "Kestra UI: $KestraUrl" -ForegroundColor Cyan
        Write-Host "Namespace: $Namespace" -ForegroundColor Cyan
    } elseif ($scriptsSuccess -and -not $workflowsSuccess) {
        Write-Host "[WARNING] Scripts deployed, but some workflows failed" -ForegroundColor Yellow
    } elseif (-not $scriptsSuccess -and $workflowsSuccess) {
        Write-Host "[WARNING] Workflows deployed, but scripts failed" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Both scripts and workflows deployment had issues" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Check Kestra UI at $KestraUrl" -ForegroundColor Gray
    Write-Host "   2. Review any failed workflows above" -ForegroundColor Gray
    Write-Host "   3. Test your workflows in the Kestra interface" -ForegroundColor Gray
    
    return $scriptsSuccess -and $workflowsSuccess
}

# Main script execution
Write-Host "KESTRA DEPLOYMENT TOOL v2.0" -ForegroundColor Green
Write-Host ""

switch ($Action.ToLower()) {
    "deploy-all" { 
        Deploy-All
    }
    "scripts-only" { 
        Deploy-Scripts
    }
    "workflows-only" { 
        Deploy-Workflows
    }
    "list" { 
        List-Workflows
    }
    "help" { 
        Show-Help 
    }
    default { 
        if ($Action -and $Action -ne "help") {
            Write-Host "[ERROR] Unknown command: $Action" -ForegroundColor Red
            Write-Host ""
        }
        Show-Help
    }
}

Write-Host ""
Write-Host "Deployment script completed" -ForegroundColor Green
