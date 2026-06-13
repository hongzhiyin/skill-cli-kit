param(
    [string]$Version = $(if ($env:SKILLCLI_VERSION) { $env:SKILLCLI_VERSION } else { "latest" }),
    [string]$ReleaseBaseUrl = $env:SKILLCLI_RELEASE_BASE_URL,
    [string]$InstallRoot = $(if ($env:SKILLCLI_INSTALL_ROOT) { $env:SKILLCLI_INSTALL_ROOT } else { Join-Path $HOME ".local\share\skillcli" }),
    [string]$BinDir = $(if ($env:SKILLCLI_BIN_DIR) { $env:SKILLCLI_BIN_DIR } else { Join-Path $HOME ".local\bin" }),
    [switch]$SyncSkill,
    [switch]$NoSyncSkill
)

$ErrorActionPreference = "Stop"
$Repo = if ($env:SKILLCLI_RELEASE_REPO) { $env:SKILLCLI_RELEASE_REPO } else { "hongzhiyin/skill-cli-kit" }
$LogPrefix = if ($env:SKILLCLI_INSTALL_LOG_PREFIX) { $env:SKILLCLI_INSTALL_LOG_PREFIX } else { "[skillcli install]" }
if (-not $ReleaseBaseUrl) {
    if ($Version -eq "latest") {
        $ReleaseBaseUrl = "https://github.com/$Repo/releases/latest/download"
    } else {
        $ReleaseBaseUrl = "https://github.com/$Repo/releases/download/v$Version"
    }
}

function Write-SkillCliInstallLog {
    param([string]$Message)
    Write-Host "$LogPrefix $Message"
}

function Join-AssetUrl {
    param([string]$Name)
    return ($ReleaseBaseUrl.TrimEnd("/") + "/" + $Name)
}

function Receive-SkillCliAsset {
    param([string]$Url, [string]$Destination)
    if ($Url.StartsWith("file://")) {
        Copy-Item -LiteralPath $Url.Substring(7) -Destination $Destination -Force
    } elseif ($Url.StartsWith("http://") -or $Url.StartsWith("https://")) {
        $Headers = @{}
        if ($env:GITHUB_TOKEN) {
            $Headers["Authorization"] = "Bearer $env:GITHUB_TOKEN"
        }
        Invoke-WebRequest -Uri $Url -OutFile $Destination -Headers $Headers
    } else {
        Copy-Item -LiteralPath $Url -Destination $Destination -Force
    }
}

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("skillcli-install-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir | Out-Null
try {
    $ManifestPath = Join-Path $TempDir "manifest.json"
    Write-SkillCliInstallLog "download manifest: $(Join-AssetUrl 'manifest.json')"
    Receive-SkillCliAsset -Url (Join-AssetUrl "manifest.json") -Destination $ManifestPath
    $Manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
    if (-not $Manifest.version -or -not $Manifest.artifact -or -not $Manifest.sha256) {
        throw "manifest missing version, artifact, or sha256"
    }
    if ($Version -ne "latest" -and $Version -ne $Manifest.version) {
        throw "requested version $Version but manifest is $($Manifest.version)"
    }

    $ArtifactPath = Join-Path $TempDir $Manifest.artifact
    Write-SkillCliInstallLog "download artifact: $(Join-AssetUrl $Manifest.artifact)"
    Receive-SkillCliAsset -Url (Join-AssetUrl $Manifest.artifact) -Destination $ArtifactPath
    $ActualHash = (Get-FileHash -Algorithm SHA256 -Path $ArtifactPath).Hash.ToLowerInvariant()
    if ($ActualHash -ne $Manifest.sha256.ToLowerInvariant()) {
        throw "checksum mismatch for $($Manifest.artifact)"
    }

    $ReleasesDir = Join-Path $InstallRoot "releases"
    $TargetDir = Join-Path $ReleasesDir $Manifest.version
    $TmpRelease = Join-Path $ReleasesDir (".tmp-" + $Manifest.version + "-" + $PID)
    New-Item -ItemType Directory -Force -Path $ReleasesDir, $BinDir, $TmpRelease | Out-Null
    tar -xzf $ArtifactPath -C $TmpRelease --strip-components 1
    if (-not (Test-Path (Join-Path $TmpRelease "src\skill_cli_kit")) -or -not (Test-Path (Join-Path $TmpRelease "skill\SKILL.md"))) {
        throw "artifact does not look like a skill-cli-kit release"
    }
    if (Test-Path $TargetDir) {
        Remove-Item -Recurse -Force $TargetDir
    }
    Move-Item -Path $TmpRelease -Destination $TargetDir

    $Current = Join-Path $InstallRoot "current"
    if (Test-Path $Current) {
        Remove-Item -Recurse -Force $Current
    }
    New-Item -ItemType Junction -Path $Current -Target $TargetDir | Out-Null

    $Launcher = Join-Path $BinDir "skillcli.ps1"
    @"
`$env:SKILLCLI_PROJECT_DIR = '$Current'
`$env:PYTHONPATH = '$Current\src'
python -m skill_cli_kit.cli @args
exit `$LASTEXITCODE
"@ | Set-Content -Encoding UTF8 -Path $Launcher

    Write-SkillCliInstallLog "installed version $($Manifest.version) at $TargetDir"
    Write-SkillCliInstallLog "launcher: $Launcher"
    & $Launcher doctor
    if (-not $NoSyncSkill) {
        & $Launcher sync-skill --targets codex,agents --force
    }
} finally {
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir
    }
}
