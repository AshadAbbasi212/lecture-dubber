# Clones candidate model repos into third_party/ (shallow).
# Clone only models needed for local offline inference; many dependencies can be
# pip-installed directly. Reference models are documented in docs/MODEL_CHOICES.md.
# Run from the project root: powershell -ExecutionPolicy Bypass -File scripts\fetch_repos.ps1

$repos = @(
    @{ name = "faster-whisper"; url = "https://github.com/SYSTRAN/faster-whisper" },
    @{ name = "whisperX";       url = "https://github.com/m-bain/whisperX" },
    @{ name = "demucs";         url = "https://github.com/facebookresearch/demucs" },
    @{ name = "MuseTalk";       url = "https://github.com/TMElyralab/MuseTalk" },
    @{ name = "LatentSync";     url = "https://github.com/bytedance/LatentSync" },
    @{ name = "OpenVoice";      url = "https://github.com/myshell-ai/OpenVoice" },
    @{ name = "chatterbox";     url = "https://github.com/resemble-ai/chatterbox" },
    @{ name = "yt-dlp";         url = "https://github.com/yt-dlp/yt-dlp" },
    # Reference only (non-commercial / research licenses, verify before any use):
    @{ name = "F5-TTS";         url = "https://github.com/SWivid/F5-TTS" },
    @{ name = "Wav2Lip";        url = "https://github.com/Rudrabha/Wav2Lip" }
)

New-Item -ItemType Directory -Force -Path "third_party" | Out-Null
foreach ($r in $repos) {
    $dest = Join-Path "third_party" $r.name
    if (Test-Path $dest) {
        Write-Host "skip   $($r.name) (already cloned)"
    } else {
        Write-Host "clone  $($r.name)"
        git clone --depth 1 $r.url $dest
    }
}
Write-Host "`nDone. Verify each repo's LICENSE and model-card terms before use."
