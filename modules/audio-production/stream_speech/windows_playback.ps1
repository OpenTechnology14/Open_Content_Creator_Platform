$ErrorActionPreference = 'Stop'
$request = [Console]::In.ReadToEnd() | ConvertFrom-Json
$player = New-Object System.Media.SoundPlayer([string]$request.path)
$player.PlaySync()
$player.Dispose()
