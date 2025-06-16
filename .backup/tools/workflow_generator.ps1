# 🏗️ KESTRA WORKFLOW GENERATOR - PowerShell Version
# Automatically creates standardized Kestra workflow structure

param(
    [string]$BasePath = (Get-Location).Path
)

# Function to display colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to prompt for workflow details
function Get-WorkflowDetails {
    Write-ColorOutput "🏗️ === KESTRA WORKFLOW GENERATOR ===" "Cyan"
    Write-ColorOutput "⏰ $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "Gray"
    Write-ColorOutput "📁 Base Path: $BasePath" "Gray"
    Write-Host

    # Get workflow name
    do {
        $workflowName = Read-Host "🏷️  Enter workflow name (kebab-case, e.g., 'user-data-sync')"
        if ($workflowName -and $workflowName.Contains('-') -and $workflowName -eq $workflowName.ToLower()) {
            break
        }
        Write-ColorOutput "❌ Please use kebab-case format (lowercase with hyphens)" "Red"
    } while ($true)

    # Get description
    $description = Read-Host "📝 Enter workflow description"
    if (-not $description) {
        $description = "Workflow for $workflowName"
    }

    # Get namespace
    $namespace = Read-Host "🏷️  Enter namespace (default: company.team)"
    if (-not $namespace) {
        $namespace = "company.team"
    }

    # Database usage
    $usesDatabase = Read-Host "🗄️  Does this workflow use database? (y/n, default: y)"
    $usesDatabase = $usesDatabase -ne 'n'

    # SQL queries
    $usesSqlFiles = $false
    if ($usesDatabase) {
        $sqlInput = Read-Host "📄 Does this workflow use SQL files? (y/n, default: n)"
        $usesSqlFiles = $sqlInput -eq 'y'
    }

    return @{
        WorkflowName = $workflowName
        ScriptName = $workflowName.Replace('-', '_')
        Description = $description
        Namespace = $namespace
        UsesDatabase = $usesDatabase
        UsesSqlFiles = $usesSqlFiles
    }
}

# Function to create folder structure
function New-WorkflowFolders {
    param($Config)
    
    $folders = @(
        "$BasePath\workflows",
        "$BasePath\scripts\$($Config.ScriptName)",
        "$BasePath\docs\workflows\$($Config.ScriptName)"
    )
    
    if ($Config.UsesSqlFiles) {
        $folders += "$BasePath\queries"
    }
    
    foreach ($folder in $folders) {
        if (-not (Test-Path $folder)) {
            New-Item -ItemType Directory -Path $folder -Force | Out-Null
            Write-ColorOutput "📁 Created folder: $folder" "Green"
        } else {
            Write-ColorOutput "📁 Folder exists: $folder" "Yellow"
        }
    }
}

# Function to generate workflow YAML
function New-WorkflowYaml {
    param($Config)
    
    $dbVariables = ""
    $dbEnvVars = ""
    $includeQueries = ""
    
    if ($Config.UsesDatabase) {
        $dbVariables = @"

# Database Configuration Variables
variables:
  db_host: "{{ envs.db_orders_host }}"
  db_port: "{{ envs.db_orders_port }}"
  db_database: "{{ envs.db_orders_database }}"
  db_username: "{{ envs.db_orders_username }}"
  db_password: "{{ envs.db_orders_password }}"
  db_encrypt: "{{ envs.db_orders_encrypt }}"
  db_trust_cert: "{{ envs.db_orders_trustservercertificate }}"
"@
        
        $dbEnvVars = @"
        env:
          # Database environment variables passed to container
          DB_ORDERS_HOST: "{{ vars.db_host }}"
          DB_ORDERS_PORT: "{{ vars.db_port }}"
          DB_ORDERS_DATABASE: "{{ vars.db_database }}"
          DB_ORDERS_USERNAME: "{{ vars.db_username }}"
          DB_ORDERS_PASSWORD: "{{ vars.db_password }}"
          DB_ORDERS_ENCRYPT: "{{ vars.db_encrypt }}"
          DB_ORDERS_TRUSTSERVERCERTIFICATE: "{{ vars.db_trust_cert }}"
"@
    }
      if ($Config.UsesSqlFiles) {
        $includeQueries = "`n        - queries/$($Config.ScriptName)_*.sql"
    }
    
    $yamlContent = @"
id: $($Config.WorkflowName)
namespace: $($Config.Namespace)
description: "$($Config.Description)"$dbVariables

tasks:
  - id: setup_and_log
    type: io.kestra.plugin.core.log.Log
    message: |
      🚀 Starting Workflow: {{ flow.id }}
      📅 Timestamp: {{ now() }}
      🏷️  Namespace: {{ flow.namespace }}
      📝 Description: $($Config.Description)
      📁 Script Location: scripts/$($Config.ScriptName)/
      
  - id: execute_main_workflow
    type: io.kestra.plugin.core.flow.WorkingDirectory
    description: "Execute $($Config.WorkflowName) main script with environment configuration"
    namespaceFiles:
      enabled: true
      include:
        - scripts/$($Config.ScriptName)/**$includeQueries
    tasks:
      - id: run_main_script
        type: io.kestra.plugin.scripts.python.Commands
        taskRunner:
          type: io.kestra.plugin.scripts.runner.docker.Docker
          pullPolicy: NEVER
        containerImage: my-custom-kestra:latest
        description: "Execute main workflow logic for $($Config.WorkflowName)"
        namespaceFiles:
          enabled: true
$dbEnvVars        commands:
          - echo "🚀 === $($Config.Description) Starting ==="
          - echo "📄 Executing main script..."
          - python scripts/$($Config.ScriptName)/main.py
          - echo "✅ === $($Config.Description) Completed ==="
          
  - id: completion_log
    type: io.kestra.plugin.core.log.Log
    message: |
      ✅ Workflow completed successfully!
      🎯 Workflow: $($Config.WorkflowName)
      📊 Results: Check task outputs above for detailed execution results
      ⏰ Completed at: {{ now() }}
"@
    
    return $yamlContent
}

# Function to run the generator
function Invoke-WorkflowGenerator {
    try {
        # Get workflow details
        $config = Get-WorkflowDetails
        
        Write-Host
        Write-ColorOutput "🔧 Creating workflow structure for '$($config.WorkflowName)'..." "Cyan"
        
        # Create folders
        New-WorkflowFolders -Config $config
        
        # Create workflow YAML
        $yamlPath = "$BasePath\workflows\$($config.WorkflowName).yml"
        $yamlContent = New-WorkflowYaml -Config $config
        Set-Content -Path $yamlPath -Value $yamlContent -Encoding UTF8
        Write-ColorOutput "📄 Created workflow: $yamlPath" "Green"
        
        # Create main Python script (simplified version)
        $scriptPath = "$BasePath\scripts\$($config.ScriptName)\main.py"
        $scriptContent = @"
import os
import sys
from datetime import datetime

def main():
    """
    Main workflow function for $($config.WorkflowName).
    
    Description: $($config.Description)
    """
    
    print(f"🚀 === $($config.Description) ===")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Workflow: $($config.WorkflowName)")
    print(f"🏷️  Namespace: $($config.Namespace)")
    print()
    
    try:
        # TODO: Add your workflow logic here
        print("🔧 Implementing workflow logic...")
        print("📊 Processing data...")
        
        # Placeholder for actual implementation
        print("⚠️  This is a template - implement your specific logic here!")
        
        print()
        print("✅ Workflow completed successfully!")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        print(f"⏰ Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
"@
        
        Set-Content -Path $scriptPath -Value $scriptContent -Encoding UTF8
        Write-ColorOutput "🐍 Created script: $scriptPath" "Green"
        
        # Create README
        $readmePath = "$BasePath\scripts\$($config.ScriptName)\README.md"        $readmeContent = @"
# $($config.WorkflowName.Replace('-', ' ')) Script

## 📝 Overview
$($config.Description)

**Workflow**: $($config.WorkflowName)
**Namespace**: $($config.Namespace)
**Script Folder**: scripts/$($config.ScptName)/

## 🚀 Usage
The script is executed automatically by the Kestra workflow $($config.WorkflowName).yml.

## 🛠️ Development
1. Modify ``main.py`` to implement your specific logic
2. Test the script independently before deploying to Kestra

---

**Generated by Kestra Workflow Generator on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')**
"@
        
        Set-Content -Path $readmePath -Value $readmeContent -Encoding UTF8
        Write-ColorOutput "📚 Created README: $readmePath" "Green"
        
        # Summary
        Write-Host
        Write-ColorOutput "✅ === WORKFLOW GENERATION COMPLETE ===" "Green"
        Write-ColorOutput "🏷️  Workflow: $($config.WorkflowName)" "White"
        Write-ColorOutput "📝 Description: $($config.Description)" "White"
        Write-ColorOutput "🏷️  Namespace: $($config.Namespace)" "White"
        Write-ColorOutput "📁 Script Folder: scripts/$($config.ScriptName)/" "White"
        
        Write-Host
        Write-ColorOutput "🎯 Next Steps:" "Yellow"
        Write-ColorOutput "   1. Review and customize the generated files" "White"
        Write-ColorOutput "   2. Implement your workflow logic in scripts/$($config.ScriptName)/main.py" "White"
        Write-ColorOutput "   3. Test the script independently before deploying to Kestra" "White"
        
        Write-Host
        Write-ColorOutput "🚀 Ready to start developing your workflow!" "Green"
        
    } catch {
        Write-ColorOutput "❌ Error generating workflow: $_" "Red"
        exit 1
    }
}

# Run the generator
Invoke-WorkflowGenerator
