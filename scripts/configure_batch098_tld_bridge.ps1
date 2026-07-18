param(
    [switch]$VerifyOnly,
    [string]$Repository = "GenghisDarb/controllergate-research"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$bundle = Join-Path $repoRoot "incoming_artifacts\ControllerGate_TLD_1-44_Historical_Architecture_Recovery_Source_Bundle_2026-07-17.zip"
$runtimeRoot = "C:\Dev\ControllerGate_Runtime\batch098_tld_bridge"
$workflow = "controllergate_batch098_tld_source_custody_bridge.yml"
$artifactName = "controllergate_batch098_exact_tld_source_bundle"

if (-not (Test-Path -LiteralPath $bundle -PathType Leaf)) {
    throw "BATCH098_TLD_SOURCE_BUNDLE_MISSING_EXACT"
}
python (Join-Path $repoRoot "scripts\verify_batch098_tld_source_bundle.py") --bundle $bundle
if ($LASTEXITCODE -ne 0) { throw "BATCH098_TLD_SOURCE_BUNDLE_IDENTITY_BLOCKED_EXACT" }
if ($VerifyOnly) {
    Write-Output "BATCH098_TLD_LOCAL_SOURCE_CUSTODY_PASS"
    exit 0
}

$secureUrl = Read-Host "Paste the time-limited HTTPS Dropbox direct-download/shared link" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureUrl)
try {
    $plainUrl = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $uri = [Uri]$plainUrl
    if ($uri.Scheme -ne "https") { throw "Only HTTPS source links are accepted" }
    $plainUrl | gh secret set CONTROLLERGATE_TLD_BUNDLE_URL --repo $Repository
    if ($LASTEXITCODE -ne 0) { throw "Failed to set protected Actions secret" }
} finally {
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    $plainUrl = $null
    $secureUrl.Dispose()
}

$started = [DateTime]::UtcNow
gh workflow run $workflow --repo $Repository --ref controllergate-v1.7-alpha-real-trace-pilot
if ($LASTEXITCODE -ne 0) { throw "Failed to dispatch one-time custody workflow" }
$run = $null
for ($attempt = 0; $attempt -lt 90; $attempt++) {
    Start-Sleep -Seconds 5
    $runs = gh run list --repo $Repository --workflow $workflow --event workflow_dispatch --limit 10 --json databaseId,status,conclusion,createdAt | ConvertFrom-Json
    $run = $runs | Where-Object { [DateTime]$_.createdAt -ge $started.AddMinutes(-1) } | Sort-Object { [DateTime]$_.createdAt } -Descending | Select-Object -First 1
    if ($run -and $run.status -eq "completed") { break }
}
if (-not $run -or $run.status -ne "completed" -or $run.conclusion -ne "success") {
    throw "BATCH098_TLD_SOURCE_CUSTODY_WORKFLOW_FAILED_OR_TIMED_OUT"
}

$artifactResponse = gh api "repos/$Repository/actions/runs/$($run.databaseId)/artifacts" | ConvertFrom-Json
$artifact = $artifactResponse.artifacts | Where-Object { $_.name -eq $artifactName -and -not $_.expired } | Select-Object -First 1
if (-not $artifact) { throw "BATCH098_TLD_SOURCE_CUSTODY_ARTIFACT_MISSING" }

$verificationRoot = Join-Path $runtimeRoot "verification-$($run.databaseId)"
New-Item -ItemType Directory -Path $verificationRoot -Force | Out-Null
gh run download $run.databaseId --repo $Repository --name $artifactName --dir $verificationRoot
if ($LASTEXITCODE -ne 0) { throw "Failed to download custody artifact" }
$inner = Get-ChildItem -LiteralPath $verificationRoot -Recurse -File -Filter "*.zip"
if ($inner.Count -ne 1) { throw "Custody artifact must contain exactly one raw ZIP" }
python (Join-Path $repoRoot "scripts\verify_batch098_tld_source_bundle.py") --bundle $inner[0].FullName
if ($LASTEXITCODE -ne 0) { throw "Downloaded custody artifact did not preserve exact source bytes" }

$record = [ordered]@{
    workflow_run_id = [int64]$run.databaseId
    artifact_id = [int64]$artifact.id
    artifact_size = [int64]$artifact.size_in_bytes
    raw_zip_size = 5389984
    raw_zip_sha256 = "c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b"
    expiry = $artifact.expires_at
}
$outputDir = Join-Path $repoRoot "outputs\post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
$record | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $outputDir "batch098_tld_bridge_record.json") -Encoding utf8

$resolvedVerificationRoot = (Resolve-Path -LiteralPath $verificationRoot).Path
if (-not $resolvedVerificationRoot.StartsWith($runtimeRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe verification cleanup path"
}
Remove-Item -LiteralPath $resolvedVerificationRoot -Recurse -Force
Write-Output ($record | ConvertTo-Json -Compress)
Write-Output "After the main Batch098 workflow acquires artifact $($artifact.id), revoke the Dropbox link and delete CONTROLLERGATE_TLD_BUNDLE_URL."
