param(
    [string]$SourceRoot = "incoming_artifacts\batch098_tld_direct_sources",
    [string]$RuntimeRoot = "C:\Dev\ControllerGate_Runtime\batch098_tld_direct_local",
    [string]$OutputDir = "outputs\post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$source = (Resolve-Path (Join-Path $repo $SourceRoot)).Path
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
$allowedRuntime = [IO.Path]::GetFullPath("C:\Dev\ControllerGate_Runtime")
if (-not $runtime.StartsWith($allowedRuntime, [StringComparison]::OrdinalIgnoreCase)) {
    throw "BATCH098_LOCAL_RUNTIME_ROOT_FORBIDDEN"
}
if ($runtime.Equals($repo, [StringComparison]::OrdinalIgnoreCase) -or $runtime.StartsWith(($repo.TrimEnd('\') + '\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw "BATCH098_LOCAL_RUNTIME_INSIDE_REPOSITORY"
}
$output = Join-Path $repo $OutputDir
$bundle = Join-Path $repo "incoming_artifacts\batch098_tld_reconstructed\ControllerGate_TLD_1-44_Direct_Source_Custody_Bundle.zip"
$requirements = Join-Path $repo "configs\tld_1_44_direct_source_requirement_registry_v1.jsonl"
$receipts = Join-Path $runtime "evidence\local_stage_process_receipts.jsonl"
$wheelRoot = Join-Path $runtime "tooling\wheel"
$venv = Join-Path $runtime "tooling\venv"
$tooling = Join-Path $runtime "tooling\scripts"
New-Item -ItemType Directory -Force -Path $runtime,$output,$wheelRoot,$tooling,(Split-Path $bundle) | Out-Null
if (Test-Path $receipts) { throw "BATCH098_LOCAL_RUNTIME_ALREADY_CONTAINS_RECEIPTS" }

function Write-Utf8NoBom {
    param([string]$Path,[string]$Content)
    $encoding = New-Object System.Text.UTF8Encoding($false)
    $normalized = (($Content -replace "`r`n", "`n") -replace "`r", "`n").TrimEnd() + "`n"
    [System.IO.File]::WriteAllText($Path, $normalized, $encoding)
}

function Invoke-IsolatedStage {
    param([string]$Name,[string]$Role,[string]$InputPath,[string]$OutputPath,[string[]]$Command)
    $args = @((Join-Path $repo "scripts\run_batch098_local_stage.py"),"--stage",$Name,"--role",$Role,"--receipts",$receipts)
    if ($InputPath) { $args += @("--input",$InputPath) }
    if ($OutputPath) { $args += @("--output",$OutputPath) }
    $args += "--"; $args += $Command
    & python @args
    if ($LASTEXITCODE -ne 0) { throw "BATCH098_LOCAL_STAGE_BLOCKED_EXACT:$Name" }
}

$builderManifest = Join-Path $output "tld_direct_bundle_builder_manifest_v1.json"
$builderReport = Join-Path $output "tld_direct_bundle_builder_report_v1.json"
Invoke-IsolatedStage "direct-source-bundle-build" "custody" $source $bundle @("python",(Join-Path $repo "scripts\build_batch098_tld_bundle_from_direct_sources.py"),"--source-root",$source,"--output-bundle",$bundle,"--output-manifest",$builderManifest,"--output-report",$builderReport)
Invoke-IsolatedStage "direct-source-inventory" "verifier" $source $output @("python",(Join-Path $repo "scripts\audit_batch098_tld_direct_source_inventory.py"),"--source-root",$source,"--output-dir",$output)
Invoke-IsolatedStage "direct-source-requirement-compilation" "producer" $source $requirements @("python",(Join-Path $repo "scripts\compile_batch098_tld_requirements_from_sources.py"),"--source-root",$source,"--output-registry",$requirements,"--output-report",(Join-Path $output "tld_direct_requirement_compilation_v1.json"),"--special-output-dir",$output)
Invoke-IsolatedStage "direct-source-independent-rebuild" "verifier" $source $bundle @("python",(Join-Path $repo "scripts\verify_batch098_tld_bundle_reproducibility.py"),"--source-root",$source,"--output-bundle",$bundle,"--output-dir",$output,"--requirement-registry",$requirements,"--inventory-output-dir",$output)
Invoke-IsolatedStage "controllergate-wheel-build" "custody" $repo $wheelRoot @("python","-m","pip","wheel",$repo,"--no-deps","--wheel-dir",$wheelRoot)
$wheel = Get-ChildItem -LiteralPath $wheelRoot -Filter "controllergate-*.whl" | Select-Object -First 1
if (-not $wheel) { throw "BATCH098_LOCAL_WHEEL_MISSING" }
Invoke-IsolatedStage "installed-environment-create" "custody" $wheelRoot $venv @("python","-m","venv",$venv)
$venvPython = Join-Path $venv "Scripts\python.exe"
$controllergate = Join-Path $venv "Scripts\controllergate.exe"
Invoke-IsolatedStage "installed-wheel-install" "custody" $wheel.FullName $venv @($venvPython,"-m","pip","install","--no-deps",$wheel.FullName)
Copy-Item -LiteralPath (Join-Path $repo "scripts\batch098_workflow_stage.py") -Destination (Join-Path $tooling "batch098_workflow_stage.py")

$providers = [ordered]@{"3.13"=(Get-Command python).Source}
if ($env:CG_PYTHON_37 -and (Test-Path $env:CG_PYTHON_37)) { $providers["3.7"]=$env:CG_PYTHON_37 }
if ($env:CG_PYTHON_311 -and (Test-Path $env:CG_PYTHON_311)) { $providers["3.11"]=$env:CG_PYTHON_311 }
$providerMap = Join-Path $runtime "tooling\provider_map.json"
Write-Utf8NoBom -Path $providerMap -Content ($providers | ConvertTo-Json)
$missing = @("3.7","3.11","3.13") | Where-Object { -not $providers.Contains($_) }
$independence = Join-Path $output "local_execution_independence_audit_v1.json"
if ($missing.Count -gt 0) {
    & python (Join-Path $repo "scripts\audit_batch098_local_process_separation.py") --receipts $receipts --wheel $wheel.FullName --installed-origin "outside_repository_site_packages/controllergate" --output $independence --minimum-processes 20
    $audit = Get-Content $independence -Raw | ConvertFrom-Json
    $audit | Add-Member -NotePropertyName exact_blocker -NotePropertyValue "BATCH098_LOCAL_PROVIDER_INTERPRETER_PARITY_BLOCKED_EXACT" -Force
    $audit | Add-Member -NotePropertyName missing_provider_series -NotePropertyValue $missing -Force
    $audit | Add-Member -NotePropertyName tld_source_custody -NotePropertyValue "PASS_LOCAL_DIRECT_SOURCE_REPRODUCIBLE" -Force
    $audit | Add-Member -NotePropertyName github_raw_tld_custody -NotePropertyValue "NOT_APPLICABLE_PRIVATE_DIRECT_SOURCE_MODE" -Force
    $audit | Add-Member -NotePropertyName github_scientific_workflow -NotePropertyValue "NOT_RUN_PRIVATE_SOURCE_MODE" -Force
    Write-Utf8NoBom -Path $independence -Content ($audit | ConvertTo-Json -Depth 8)
    Write-Output "BATCH098_TLD_DIRECT_SOURCE_CUSTODY_PASS_LOCAL_EXACT"
    Write-Output "BATCH098_LOCAL_PROVIDER_INTERPRETER_PARITY_BLOCKED_EXACT missing=$($missing -join ',')"
    exit 2
}

$artifact = Join-Path $repo "incoming_artifacts\batch098_tld_verification\post_v2_37_hardening_batch098_local_protected_source_artifacts.zip"
$artifactReport = Join-Path $output "batch098_local_protected_source_artifact_identity.json"
& $venvPython (Join-Path $repo "scripts\run_batch098_local_scientific.py") --controllergate $controllergate --workflow-stage (Join-Path $tooling "batch098_workflow_stage.py") --provider-map $providerMap --contracts (Join-Path $repo "configs\candidate_execution_contracts_v2.jsonl") --bundle $bundle --requirements $requirements --runtime-root $runtime --forbidden-repo-root $repo --artifact $artifact --artifact-report $artifactReport
$scientificExit = $LASTEXITCODE
& python (Join-Path $repo "scripts\audit_batch098_local_process_separation.py") --receipts $receipts --wheel $wheel.FullName --installed-origin "outside_repository_site_packages/controllergate" --output $independence --minimum-processes 20
$auditExit = $LASTEXITCODE
if ($scientificExit -ne 0 -or $auditExit -ne 0) { throw "BATCH098_LOCAL_SCIENTIFIC_RUN_BLOCKED_EXACT" }
Write-Output "BATCH098_TLD_DIRECT_SOURCE_CUSTODY_PASS_LOCAL_EXACT"
Write-Output "BATCH098_LOCAL_PROTECTED_SOURCE_RUN_PASS"
