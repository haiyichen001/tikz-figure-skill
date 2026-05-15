$ErrorActionPreference = "Stop"

$Dest = "$env:USERPROFILE\.claude\skills\tikz-figure-skill"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== tikz-figure-skill installer ==="
Write-Host "Destination: $Dest"

New-Item -ItemType Directory -Force -Path "$Dest\references" | Out-Null
New-Item -ItemType Directory -Force -Path "$Dest\scripts" | Out-Null

Copy-Item "$ScriptDir\SKILL.md" $Dest -Force
Copy-Item "$ScriptDir\references\*" "$Dest\references" -Force
Copy-Item "$ScriptDir\scripts\*" "$Dest\scripts" -Force

$count = (Get-ChildItem $Dest -Recurse -File | Measure-Object).Count
Write-Host "Files installed: $count"
Write-Host ""

# Run env check if Python available
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    Write-Host "=== Environment check ==="
    & python "$Dest\scripts\check-env.py"
} else {
    Write-Host "Python not found — skipping environment check"
}

Write-Host ""
Write-Host "Done. Restart Claude Code to use /tikz-figure-skill"
