<#
.SYNOPSIS
Installs a freshly built Extend NSIS package and checks its native window on a Windows CI host.
.DESCRIPTION
Uses an isolated temporary install directory and an unrelated working directory. Does not set
up OBS, Docker, Python modules or accounts. Records installation timing, native window evidence
and a screenshot; this is not clean-workstation or physical capture acceptance.
.EXAMPLE
./scripts/testing/windows_installer.ps1 -App stream-extend
.EXAMPLE
Get-Help ./scripts/testing/windows_installer.ps1 -Full
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('stream-extend', 'creator-extend')]
    [string]$App
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:OS -ne 'Windows_NT') { throw 'Run this smoke test on Windows.' }

$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$evidence = Join-Path $repo "output/installer-smoke/$App"
New-Item -ItemType Directory -Force $evidence | Out-Null
$installers = @(Get-ChildItem (Join-Path $repo "apps/$App/src-tauri/target/release/bundle/nsis/*-setup.exe"))
if ($installers.Count -ne 1) { throw 'Expected exactly one freshly built installer.' }
$temporaryRoot = Join-Path ([IO.Path]::GetTempPath()) ("hcp-installer-" + [Guid]::NewGuid().ToString('N'))
$installDirectory = Join-Path $temporaryRoot 'installed app'
$workingDirectory = Join-Path $temporaryRoot 'unrelated working directory'
New-Item -ItemType Directory -Force $workingDirectory | Out-Null
$timer = [Diagnostics.Stopwatch]::StartNew()
$nativeProcess = $null
$report = [ordered]@{
    app = $App
    installer = $installers[0].Name
    installer_sha256 = (Get-FileHash $installers[0].FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    windows_version = [Environment]::OSVersion.VersionString
    install_exit_code = $null
    window_title = $null
    setup_text_observed = $false
    status = 'started'
    limitation = 'Hosted CI has developer tools and WebView2; not clean physical Windows acceptance.'
}
try {
    # NSIS requires /D to be the final argument, without quotes even when it contains spaces.
    $installerProcess = Start-Process -FilePath $installers[0].FullName -ArgumentList "/S /D=$installDirectory" -PassThru
    if (-not $installerProcess.WaitForExit(180000)) {
        $installerProcess.Kill()
        throw 'Installer did not finish within three minutes.'
    }
    $report.install_exit_code = $installerProcess.ExitCode
    if ($installerProcess.ExitCode -ne 0) { throw "Installer exited $($installerProcess.ExitCode)." }
    $report.install_seconds = [Math]::Round($timer.Elapsed.TotalSeconds, 2)
    $executable = Join-Path $installDirectory "$App.exe"
    if (-not (Test-Path $executable)) { throw "Installed application is missing: $executable" }
    $nativeProcess = Start-Process -FilePath $executable -WorkingDirectory $workingDirectory -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds(45)
    do {
        Start-Sleep -Milliseconds 500
        $nativeProcess.Refresh()
        if ($nativeProcess.HasExited) { throw "Application exited during startup: $($nativeProcess.ExitCode)" }
    } while ($nativeProcess.MainWindowHandle -eq 0 -and [DateTime]::UtcNow -lt $deadline)
    if ($nativeProcess.MainWindowHandle -eq 0) { throw 'Application did not open a native window.' }
    $report.window_title = $nativeProcess.MainWindowTitle
    $report.installer_to_window_seconds = [Math]::Round($timer.Elapsed.TotalSeconds, 2)
    $expectedTitle = if ($App -eq 'stream-extend') { 'Stream Extend' } else { 'Creator Extend' }
    if ($report.window_title -ne $expectedTitle) { throw 'Unexpected native window title.' }
    Start-Sleep -Seconds 5
    $nativeProcess.Refresh()
    if ($nativeProcess.HasExited) { throw 'Application exited after opening its window.' }

    # Accessibility evidence is best effort: runner desktop sessions vary. The report distinguishes
    # native-window proof from observing the actual setup content, never upgrades one into the other.
    try {
        Add-Type -AssemblyName UIAutomationClient
        $window = [Windows.Automation.AutomationElement]::FromHandle($nativeProcess.MainWindowHandle)
        $elements = $window.FindAll([Windows.Automation.TreeScope]::Descendants, [Windows.Automation.Condition]::TrueCondition)
        $names = @($elements | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
        $names | Set-Content (Join-Path $evidence 'accessibility.txt')
        $report.setup_text_observed = [bool]($names -match 'Module setup')
    } catch { $report.accessibility_error = $_.Exception.Message }
    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $bounds = [Windows.Forms.SystemInformation]::VirtualScreen
        $bitmap = New-Object Drawing.Bitmap($bounds.Width, $bounds.Height)
        $graphics = [Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($bounds.Location, [Drawing.Point]::Empty, $bounds.Size)
            $bitmap.Save((Join-Path $evidence 'desktop.png'), [Drawing.Imaging.ImageFormat]::Png)
        } finally { $graphics.Dispose(); $bitmap.Dispose() }
    } catch { $report.screenshot_error = $_.Exception.Message }
    $report.status = 'passed-native-window-smoke'
} catch {
    $report.status = 'failed'
    $report.error = $_.Exception.Message
    throw
} finally {
    $report | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $evidence 'report.json')
    if ($null -ne $nativeProcess -and -not $nativeProcess.HasExited) { $nativeProcess.Kill() }
}
