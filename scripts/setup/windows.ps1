<#
.SYNOPSIS
Bootstraps Open Content Creator Platform on Windows and scans local capture hardware.

.DESCRIPTION
Installs Python 3.12 when needed, optionally installs OBS Studio and FFmpeg with winget,
installs only the selected platform modules, runs readiness checks, and writes a capture report.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -InstallDesktopApps

.EXAMPLE
powershell -ExecutionPolicy Bypass -File scripts/setup/windows.ps1 -Preset custom -Modules soundboard,audio-production
#>
[CmdletBinding()]
param(
    [ValidateSet("stream", "creator", "custom")]
    [string]$Preset = "stream",
    [string[]]$Modules = @(),
    [switch]$InstallDesktopApps,
    [switch]$PlanOnly,
    [switch]$SkipCaptureScan
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($env:OS -ne "Windows_NT") {
    throw "This bootstrap is for Windows. Use the desktop setup panel or Python setup CLI on macOS."
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
Set-Location $RepoRoot

function Install-WingetPackage {
    param([Parameter(Mandatory = $true)][string]$Id)
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Windows Package Manager (winget) is required. Install or update App Installer, then retry."
    }
    Write-Host "Installing $Id with winget..."
    $wingetPath = $winget.Source
    & $wingetPath install --id $Id --exact --source winget --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget could not install $Id (exit $LASTEXITCODE)."
    }
}

function Find-Python312 {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $launcherPath = $launcher.Source
        & $launcherPath -3.12 -I -c "import sys; assert sys.version_info >= (3, 11)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Executable = $launcherPath; Prefix = @("-3.12") }
        }
    }
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs/Python/Python312/python.exe"),
        (Join-Path $env:ProgramFiles "Python312/python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            & $candidate -I -c "import sys; assert sys.version_info >= (3, 11)"
            if ($LASTEXITCODE -eq 0) {
                return @{ Executable = $candidate; Prefix = @() }
            }
        }
    }
    return $null
}

function Invoke-SetupPython {
    param(
        [Parameter(Mandatory = $true)][hashtable]$Python,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $pythonPath = $Python.Executable
    $allArguments = @($Python.Prefix) + $Arguments
    & $pythonPath @allArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python setup command failed (exit $LASTEXITCODE)."
    }
}

$python = Find-Python312
if (-not $python) {
    if ($PlanOnly) {
        throw "Python 3.12 is required for a setup plan. Rerun without -PlanOnly to install it automatically."
    }
    Install-WingetPackage -Id "Python.Python.3.12"
    $python = Find-Python312
    if (-not $python) {
        throw "Python 3.12 was installed but is not visible yet. Reopen PowerShell and rerun setup."
    }
}

if ($InstallDesktopApps -and -not $PlanOnly) {
    if (-not (Test-Path "$env:ProgramFiles/obs-studio/bin/64bit/obs64.exe")) {
        Install-WingetPackage -Id "OBSProject.OBSStudio"
    }
    if (-not (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue)) {
        Install-WingetPackage -Id "Gyan.FFmpeg"
    }
}

$selection = switch ($Preset) {
    "stream" { @("ai-agents", "audio-production", "automation-control", "content-creation", "creator-experience", "soundboard", "broadcast-graphics") }
    "creator" { @("content-creation", "image-editing", "asset-pipeline", "model-registry") }
    "custom" {
        if ($Modules.Count -eq 0) { throw "-Preset custom requires one or more -Modules values." }
        $Modules
    }
}

$action = if ($PlanOnly) { "plan" } else { "install" }
Invoke-SetupPython -Python $python -Arguments (@("scripts/setup/modules.py", $action, "--modules") + $selection)

if (-not $PlanOnly) {
    Invoke-SetupPython -Python $python -Arguments (@("scripts/setup/modules.py", "doctor", "--modules") + $selection)
    if (-not $SkipCaptureScan) {
        $report = Join-Path $RepoRoot "output/module-setup/windows-capture-report.json"
        Invoke-SetupPython -Python $python -Arguments @("scripts/setup/capture_devices.py", "--output", $report)
        Write-Host "Capture report: $report"
    }
    Write-Host "Setup finished. Open Stream Extend, review Module setup, then make a local OBS recording before streaming."
}
