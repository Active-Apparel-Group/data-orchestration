#!/usr/bin/env powershell

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Available commands:" -ForegroundColor Green
    Write-Host "  build    - Build the Docker image"
    Write-Host "  up       - Start the containers"
    Write-Host "  down     - Stop the containers"
    Write-Host "  clean    - Stop containers and remove volumes"
    Write-Host "  rebuild  - Stop, rebuild, and start containers"
    Write-Host "  logs     - Show container logs"
    Write-Host "  help     - Show this help message"
}

function Invoke-Build {
    Write-Host "Scanning Python requirements..." -ForegroundColor Yellow
    python tools/update-requirements.py
    
    Write-Host "Building Kestra container..." -ForegroundColor Yellow
    docker compose build --no-cache kestra
}

function Invoke-Up {
    Write-Host "Starting containers..." -ForegroundColor Yellow
    docker compose up -d
}

function Invoke-Down {
    Write-Host "Stopping containers..." -ForegroundColor Yellow
    docker compose down
}

function Invoke-Clean {
    Write-Host "Cleaning up containers and volumes..." -ForegroundColor Yellow
    docker compose down -v
    docker system prune -f
}

function Invoke-Rebuild {
    Write-Host "Rebuilding everything..." -ForegroundColor Yellow
    Invoke-Down
    Invoke-Build
    Invoke-Up
}

function Show-Logs {
    Write-Host "Showing container logs..." -ForegroundColor Yellow
    docker compose logs -f
}

switch ($Command.ToLower()) {
    "build" { Invoke-Build }
    "up" { Invoke-Up }
    "down" { Invoke-Down }
    "clean" { Invoke-Clean }
    "rebuild" { Invoke-Rebuild }
    "logs" { Show-Logs }
    "help" { Show-Help }
    default { 
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help 
    }
}
