#!/usr/bin/env powershell

# Kestra Workflow Deployment Script
# This script deploys workflows to your Kestra instance

param(
    [Parameter(Position=0)]
    [string]$Action = "help",
    [string]$KestraUrl = "http://localhost:8080",
    [string]$Namespace = "company.team"
)

function Show-Help {
    Write-Host "Kestra Workflow Deployment Commands:" -ForegroundColor Green
    Write-Host "  deploy-all    - Deploy all workflow files to Kestra"
    Write-Host "  deploy-single - Deploy a specific workflow file"
    Write-Host "  list          - List all workflows in namespace"
    Write-Host "  delete        - Delete a specific workflow"
    Write-Host "  validate      - Validate workflow files"
    Write-Host "  help          - Show this help message"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\deploy-workflows.ps1 deploy-all"
    Write-Host "  .\deploy-workflows.ps1 deploy-single test-env-vars.yml"
    Write-Host "  .\deploy-workflows.ps1 list"
}

function Deploy-AllWorkflows {
    Write-Host "Deploying all workflows to namespace: $Namespace" -ForegroundColor Yellow
    
    # Look for workflow files in the workflows folder
    $workflowsPath = "workflows"
    if (-not (Test-Path $workflowsPath)) {
        Write-Host "ERROR: workflows/ folder not found. Make sure you're in the project root directory." -ForegroundColor Red
        return
    }
    
    $workflowFiles = Get-ChildItem -Path $workflowsPath -Filter "*.yml"
    
    if ($workflowFiles.Count -eq 0) {
        Write-Host "No workflow files found in workflows/ folder" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Found $($workflowFiles.Count) workflow files:" -ForegroundColor Cyan
    $workflowFiles | ForEach-Object { Write-Host "  $($_.Name)" -ForegroundColor Gray }
    Write-Host ""
    
    # First, get list of existing workflows
    $existingWorkflows = @{}
    try {
        $response = Invoke-WebRequest -Uri "$KestraUrl/api/v1/flows/search?namespace=$Namespace" -Method GET -Headers @{"Accept"="application/json"} -ErrorAction Stop
        $flows = $response.Content | ConvertFrom-Json
        if ($flows.results) {
            foreach ($flow in $flows.results) {
                $existingWorkflows[$flow.id] = $flow
            }
        }
        Write-Host "Found $($existingWorkflows.Count) existing workflows in namespace" -ForegroundColor Gray
    } catch {
        Write-Host "WARNING: Could not check existing workflows: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    foreach ($file in $workflowFiles) {
        Write-Host "Processing: $($file.Name)" -ForegroundColor Cyan
        
        try {
            $content = Get-Content $file.FullName -Raw
            
            # Extract workflow ID from content
            $workflowId = $null
            if ($content -match "id\s*:\s*(.+)") {
                $workflowId = $matches[1].Trim()
                Write-Host "  Workflow ID: $workflowId" -ForegroundColor Gray
            } else {
                Write-Host "  ERROR: No workflow ID found in file" -ForegroundColor Red
                continue
            }
            
            # Check if workflow already exists
            $isUpdate = $existingWorkflows.ContainsKey($workflowId)
            
            if ($isUpdate) {
                Write-Host "  Updating existing workflow..." -ForegroundColor Yellow
                try {
                    $response = Invoke-WebRequest -Uri "$KestraUrl/api/v1/flows/$Namespace/$workflowId" -Method PUT -ContentType "application/x-yaml" -Body $content -ErrorAction Stop
                    Write-Host "  SUCCESS: Updated workflow: $($file.Name)" -ForegroundColor Green
                } catch {
                    Write-Host "  ERROR: Failed to update: $($file.Name)" -ForegroundColor Red
                    Write-Host "    Details: $($_.Exception.Message)" -ForegroundColor Red
                    
                    # Try to get more detailed error info
                    if ($_.Exception.Response) {
                        try {
                            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
                            $errorDetails = $reader.ReadToEnd()
                            Write-Host "    Server response: $errorDetails" -ForegroundColor Red
                        } catch {
                            # Ignore if we can't read response
                        }
                    }
                }
            } else {
                Write-Host "  Creating new workflow..." -ForegroundColor Yellow
                try {
                    $response = Invoke-WebRequest -Uri "$KestraUrl/api/v1/flows" -Method POST -ContentType "application/x-yaml" -Body $content -ErrorAction Stop
                    Write-Host "  SUCCESS: Created new workflow: $($file.Name)" -ForegroundColor Green                } catch {
                    Write-Host "  ERROR: Failed to create: $($file.Name)" -ForegroundColor Red
                    Write-Host "    Details: $($_.Exception.Message)" -ForegroundColor Red
                    
                    # Try to get more detailed error info
                    if ($_.Exception.Response) {
                        try {
                            $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
                            $errorDetails = $reader.ReadToEnd()
                            Write-Host "    Server response: $errorDetails" -ForegroundColor Red
                        } catch {
                            # Ignore if we can't read response
                        }
                    }
                    
                    # Try validation endpoint for more specific error details
                    Write-Host "    Running validation check..." -ForegroundColor Yellow
                    try {
                        $validateResponse = Invoke-WebRequest -Uri "$KestraUrl/api/v1/flows/validate" -Method POST -ContentType "application/x-yaml" -Body $content -ErrorAction Stop
                        Write-Host "    Validation: PASSED (issue may be with creation endpoint)" -ForegroundColor Yellow
                    } catch {
                        Write-Host "    Validation: FAILED" -ForegroundColor Red
                        if ($_.Exception.Response) {
                            try {
                                $validateReader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
                                $validateError = $validateReader.ReadToEnd()
                                Write-Host "    Validation error details: $validateError" -ForegroundColor Red
                            } catch {
                                Write-Host "    Could not read validation error details" -ForegroundColor Red
                            }
                        }
                    }
                }
            }
            
        } catch {
            Write-Host "  ERROR: Failed to process file: $($file.Name)" -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        
        Write-Host ""
    }
}

function Deploy-SingleWorkflow {
    param([string]$FileName)
    
    if (-not $FileName) {
        Write-Host "Please specify a workflow file name" -ForegroundColor Red
        return
    }
    
    if (-not (Test-Path $FileName)) {
        Write-Host "File not found: $FileName" -ForegroundColor Red
        return
    }
    
    Write-Host "Deploying: $FileName to namespace: $Namespace" -ForegroundColor Yellow
    
    try {
        $content = Get-Content $FileName -Raw
        $response = Invoke-WebRequest -Uri "$KestraUrl/api/v1/flows" -Method POST -ContentType "application/x-yaml" -Body $content -ErrorAction Stop
        
        Write-Host "✅ Successfully deployed: $FileName" -ForegroundColor Green
        
        # Extract flow info from response if possible
        try {
            $flowInfo = $response.Content | ConvertFrom-Json
            Write-Host "   Flow ID: $($flowInfo.id)" -ForegroundColor Cyan
            Write-Host "   Revision: $($flowInfo.revision)" -ForegroundColor Cyan
        } catch {
            # If we can't parse response, that's ok
        }
        
    } catch {
        Write-Host "❌ Failed to deploy: $FileName" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        
        # Try to show response details if available
        if ($_.Exception.Response) {
            try {
                $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
                $responseText = $reader.ReadToEnd()
                Write-Host "   Details: $responseText" -ForegroundColor Red
            } catch {
                # Ignore if we can't read response
            }
        }
    }
}

function List-Workflows {
    Write-Host "Listing workflows in namespace: $Namespace" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "$KestraUrl/api/v1/flows/search?namespace=$Namespace" -Method GET -Headers @{"Accept"="application/json"} -ErrorAction Stop
        $flows = $response.Content | ConvertFrom-Json
        
        if ($flows.results -and $flows.results.Count -gt 0) {
            Write-Host "✅ Found $($flows.total) workflows:" -ForegroundColor Green
            foreach ($flow in $flows.results) {
                Write-Host "   $($flow.id) (rev: $($flow.revision))" -ForegroundColor Cyan
            }
        } else {
            Write-Host "No workflows found in namespace: $Namespace" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Failed to list workflows: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Validate-Workflows {
    Write-Host "Validating workflow files..." -ForegroundColor Yellow
    
    $workflowFiles = Get-ChildItem -Path "." -Filter "*.yml" | Where-Object { $_.Name -notlike "*docker-compose*" }
    
    foreach ($file in $workflowFiles) {
        Write-Host "Validating: $($file.Name)" -ForegroundColor Cyan
        
        $result = curl -X POST "$KestraUrl/api/v1/flows/validate" `
            -H "Content-Type: application/x-yaml" `
            --data-binary "@$($file.Name)" `
            -w "%{http_code}" -s -o response.json
        
        if ($result -eq "200") {
            Write-Host "✅ Valid: $($file.Name)" -ForegroundColor Green
        } else {
            Write-Host "❌ Invalid: $($file.Name)" -ForegroundColor Red
            if (Test-Path "response.json") {
                Get-Content "response.json" | Write-Host -ForegroundColor Red
            }
        }
    }
    
    # Cleanup
    if (Test-Path "response.json") { Remove-Item "response.json" }
}

function Delete-Workflow {
    param([string]$WorkflowId)
    
    if (-not $WorkflowId) {
        Write-Host "Please specify a workflow ID" -ForegroundColor Red
        return
    }
    
    Write-Host "Deleting workflow: $WorkflowId from namespace: $Namespace" -ForegroundColor Yellow
    
    $result = curl -X DELETE "$KestraUrl/api/v1/flows/$Namespace/$WorkflowId" `
        -w "%{http_code}" -s
    
    if ($result -eq "204") {
        Write-Host "✅ Successfully deleted: $WorkflowId" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to delete: $WorkflowId (HTTP: $result)" -ForegroundColor Red
    }
}

# Main script execution
switch ($Action.ToLower()) {
    "deploy-all" { Deploy-AllWorkflows }    "deploy-single" { 
        $fileName = Read-Host "Enter workflow file name (e.g., test-sql-with-variables.yml)"
        
        # Check if file exists in workflows folder
        $workflowPath = if (Test-Path "workflows\$fileName") {
            "workflows\$fileName"
        } elseif (Test-Path $fileName) {
            $fileName
        } else {
            Write-Host "❌ File not found: $fileName" -ForegroundColor Red
            Write-Host "   Looked in: workflows\$fileName and $fileName" -ForegroundColor Gray
            return
        }
        
        Deploy-SingleWorkflow -FileName $workflowPath 
    }
    "list" { List-Workflows }
    "validate" { Validate-Workflows }
    "delete" { 
        $workflowId = Read-Host "Enter workflow ID to delete"
        Delete-Workflow -WorkflowId $workflowId 
    }
    "help" { Show-Help }
    default { 
        Write-Host "Unknown command: $Action" -ForegroundColor Red
        Show-Help 
    }
}
