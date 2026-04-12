# ─────────────────────────────────────────
#  AetherAI — Commande personnalisée
#  Ajoute "launch AetherAI" et "AetherAI launch" au terminal
# ─────────────────────────────────────────

function global:launch ([string]$target) {
    if ($target -eq "AetherAI") {
        Set-Location C:\AetherAI
        & C:\AetherAI\venv\Scripts\python.exe C:\AetherAI\aether.py
    } else {
        Write-Host "Commande inconnue : launch $target" -ForegroundColor Red
    }
}

function global:AetherAI ([string]$action) {
    if ($action -eq "launch") {
        Set-Location C:\AetherAI
        & C:\AetherAI\venv\Scripts\python.exe C:\AetherAI\aether.py
    } else {
        Write-Host "Commande inconnue : AetherAI $action" -ForegroundColor Red
    }
}

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host "Commandes AetherAI chargees : 'launch AetherAI' ou 'AetherAI launch'" -ForegroundColor Magenta

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function global:launch ([string]$target) {
    if ($target -eq "AetherAI") {
        Set-Location C:\AetherAI
        & C:\AetherAI\venv\Scripts\python.exe C:\AetherAI\aether.py
    } elseif ($target -eq "AetherTUI") {
        Set-Location C:\AetherAI
        & C:\AetherAI\venv\Scripts\python.exe C:\AetherAI\aether_tui.py
    } else {
        Write-Host "Commande inconnue : launch $target" -ForegroundColor Red
    }
}

function global:AetherAI ([string]$action) {
    if ($action -eq "launch") {
        Set-Location C:\AetherAI
        & C:\AetherAI\venv\Scripts\python.exe C:\AetherAI\aether.py
    } elseif ($action -eq "tui") {
        Set-Location C:\AetherAI
        & C:\AetherAI\venv\Scripts\python.exe C:\AetherAI\aether_tui.py
    } else {
        Write-Host "Commande inconnue : AetherAI $action" -ForegroundColor Red
    }
}

Write-Host "Commandes AetherAI chargees :" -ForegroundColor Magenta
Write-Host "  launch AetherAI  -> terminal classique" -ForegroundColor Cyan
Write-Host "  launch AetherTUI -> interface TUI" -ForegroundColor Cyan
Write-Host "  AetherAI launch  -> terminal classique" -ForegroundColor Cyan
Write-Host "  AetherAI tui     -> interface TUI" -ForegroundColor Cyan
