param(
    [string]$RuntimeRoot = "C:\Dev\ControllerGate_Runtime\batch098_hybrid_private",
    [string]$OutputDir = "outputs\post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure",
    [string]$PublicDecisionEvidenceArtifactId,
    [string]$PublicTruthBlindExecutionArtifactId,
    [switch]$LocalWindowsDiagnosticFallback
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$allowedRuntime = [IO.Path]::GetFullPath("C:\Dev\ControllerGate_Runtime")
if (-not $runtime.StartsWith($allowedRuntime, [StringComparison]::OrdinalIgnoreCase)) {
    throw "BATCH098_LOCAL_RUNTIME_ROOT_FORBIDDEN"
}
if ($runtime.Equals($repo, [StringComparison]::OrdinalIgnoreCase) -or $runtime.StartsWith(($repo.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw "BATCH098_LOCAL_RUNTIME_INSIDE_REPOSITORY"
}

$bundle = Join-Path $repo "incoming_artifacts\batch098_tld_reconstructed\ControllerGate_TLD_1-44_Direct_Source_Custody_Bundle.zip"
$requirements = Join-Path $repo "configs\tld_1_44_direct_source_requirement_registry_v1.jsonl"
$opaquePlan = Join-Path $repo "configs\batch098_opaque_probe_plan_registry_v1.jsonl"
$LegacyIsolatedStageRunner = "scripts\run_batch098_local_stage.py" # historical diagnostic reference; never used for hybrid candidate execution
$output = Join-Path $repo $OutputDir
New-Item -ItemType Directory -Force -Path $runtime,$output | Out-Null

if ($LocalWindowsDiagnosticFallback) {
    if ($PublicDecisionEvidenceArtifactId -or $PublicTruthBlindExecutionArtifactId) {
        throw "BATCH098_HYBRID_AND_LOCAL_DIAGNOSTIC_MODES_CONFLICT"
    }
    $providers = [ordered]@{}
    if ($env:CG_PYTHON_37 -and (Test-Path $env:CG_PYTHON_37)) { $providers["3.7"] = $env:CG_PYTHON_37 }
    if ($env:CG_PYTHON_311 -and (Test-Path $env:CG_PYTHON_311)) { $providers["3.11"] = $env:CG_PYTHON_311 }
    if (Get-Command python -ErrorAction SilentlyContinue) { $providers["default"] = (Get-Command python).Source }
    $diagnostic = [ordered]@{
        status = "LOCAL_WINDOWS_DIAGNOSTIC_NONPARITY"
        providers = $providers
        historical_scoring = "FORBIDDEN"
        provider_parity = "NOT_ESTABLISHED"
        source_ownership = "FORBIDDEN"
        repair_authority = "FORBIDDEN"
        count_mutation = "FORBIDDEN"
        release_decision = "FORBIDDEN"
        local_candidate_materialization_count = 0
        local_candidate_probe_execution_count = 0
    }
    $diagnostic | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $output "local_windows_diagnostic_nonparity.json") -Encoding utf8NoBOM
    Write-Output "LOCAL_WINDOWS_DIAGNOSTIC_NONPARITY"
    exit 0
}

if (-not $PublicDecisionEvidenceArtifactId) { throw "BATCH098_PUBLIC_DECISION_TIME_EVIDENCE_REQUIRED" }
if (-not $PublicTruthBlindExecutionArtifactId) { throw "BATCH098_PUBLIC_TRUTH_BLIND_EXECUTION_REQUIRED" }
if (-not (Test-Path $bundle)) { throw "BATCH098_PRIVATE_TLD_BUNDLE_REQUIRED" }
if (-not (Test-Path $requirements)) { throw "BATCH098_PRIVATE_TLD_REQUIREMENT_REGISTRY_REQUIRED" }
if (-not (Test-Path $opaquePlan)) { throw "BATCH098_PRIVATE_TLD_OPAQUE_PLAN_REQUIRED" }

function Download-ActionsArtifact {
    param([string]$ArtifactId,[string]$Destination)
    $token = (& gh auth token).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $token) { throw "BATCH098_GITHUB_AUTH_REQUIRED" }
    $ownerRepo = (& gh repo view --json nameWithOwner --jq .nameWithOwner).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $ownerRepo) { throw "BATCH098_GITHUB_REPOSITORY_IDENTITY_REQUIRED" }
    $headers = @{Authorization = "Bearer $token"; Accept = "application/vnd.github+json"; "X-GitHub-Api-Version" = "2022-11-28"}
    Invoke-WebRequest -Uri "https://api.github.com/repos/$ownerRepo/actions/artifacts/$ArtifactId/zip" -Headers $headers -OutFile $Destination
}

$decisionZip = Join-Path $runtime "public_decision_time_evidence.zip"
$truthBlindZip = Join-Path $runtime "public_truth_blind_execution_evidence.zip"
$decisionRoot = Join-Path $runtime "public_decision_time_evidence"
$truthBlindRoot = Join-Path $runtime "public_truth_blind_execution_evidence"
foreach ($path in @($decisionRoot,$truthBlindRoot)) {
    if (Test-Path $path) { Remove-Item -LiteralPath $path -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $path | Out-Null
}
Download-ActionsArtifact -ArtifactId $PublicDecisionEvidenceArtifactId -Destination $decisionZip
Download-ActionsArtifact -ArtifactId $PublicTruthBlindExecutionArtifactId -Destination $truthBlindZip
Expand-Archive -LiteralPath $decisionZip -DestinationPath $decisionRoot
Expand-Archive -LiteralPath $truthBlindZip -DestinationPath $truthBlindRoot

& python (Join-Path $repo "scripts\verify_batch098_public_artifact.py") --artifact-root $decisionRoot --kind decision --output (Join-Path $runtime "public_decision_verification.json")
if ($LASTEXITCODE -ne 0) { throw "BATCH098_PUBLIC_DECISION_TIME_EVIDENCE_REQUIRED" }
& python (Join-Path $repo "scripts\verify_batch098_public_artifact.py") --artifact-root $truthBlindRoot --kind truth-blind --output (Join-Path $runtime "public_truth_blind_verification.json")
if ($LASTEXITCODE -ne 0) { throw "BATCH098_PUBLIC_TRUTH_BLIND_EXECUTION_REQUIRED" }

$artifact = Join-Path $repo "incoming_artifacts\batch098_tld_verification\post_v2_37_hardening_batch098_hybrid_public_provider_private_tld_artifacts.zip"
$artifactReport = Join-Path $output "batch098_hybrid_private_artifact_identity.json"
$finalOutput = Join-Path $runtime "final_compact_evidence"
if (Test-Path $finalOutput) { Remove-Item -LiteralPath $finalOutput -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Split-Path $artifact),$finalOutput | Out-Null
& python (Join-Path $repo "scripts\finalize_batch098_hybrid_private_run.py") `
    --public-decision-artifact $decisionRoot `
    --public-truth-blind-artifact $truthBlindRoot `
    --tld-bundle $bundle `
    --requirement-registry $requirements `
    --opaque-plan-registry $opaquePlan `
    --output-dir $finalOutput `
    --artifact $artifact `
    --artifact-report $artifactReport
if ($LASTEXITCODE -ne 0) { throw "BATCH098_PRIVATE_FINALIZATION_REQUIRED" }

Write-Output "HYBRID_PUBLIC_PROVIDER_PRIVATE_TLD_PROTECTED_RUN"
Write-Output "public_provider_execution=PASS_EXACT_FROZEN_LINUX_PARITY"
Write-Output "private_TLD_custody=PASS_LOCAL_DIRECT_SOURCE_REPRODUCIBLE"
Write-Output "GitHub_raw_TLD_custody=NOT_APPLICABLE_PRIVATE_DIRECT_SOURCE_MODE"
Write-Output "local_candidate_materialization_count=0"
Write-Output "local_candidate_probe_execution_count=0"
Write-Output "artifact=$artifact"
