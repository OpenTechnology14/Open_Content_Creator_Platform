# Invoked by render_reply.py with this fixed source as -Command; input is JSON data on stdin.
# No execution-policy changes, scripts downloaded at runtime, audio playback or network calls.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$request = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName System.Speech
$speaker = [System.Speech.Synthesis.SpeechSynthesizer]::new()
try {
    if ($request.voice) { $speaker.SelectVoice([string]$request.voice) }
    $format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(
        22050,
        [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono
    )
    $speaker.SetOutputToWaveFile([string]$request.output, $format)
    $speaker.Speak([string]$request.text)
} finally {
    $speaker.Dispose()
}
