$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$expectedRepositoryRoot = [IO.Path]::GetFullPath('C:\projects\tmt')
$scriptDirectory = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$root = [IO.Path]::GetFullPath((Join-Path $scriptDirectory '..\..'))
$scriptPath = [IO.Path]::GetFullPath($PSCommandPath)
$workingDirectory = [IO.Path]::GetFullPath((Get-Location).Path)
if (-not [string]::Equals($root, $expectedRepositoryRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Script-derived repository root is not approved: $root"
}
if (-not [string]::Equals($workingDirectory, $expectedRepositoryRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Caller working directory must be the approved repository root: $expectedRepositoryRoot"
}
if (-not $scriptPath.StartsWith($expectedRepositoryRoot.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Wrapper is outside the approved repository: $scriptPath"
}
$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path -LiteralPath $git -PathType Leaf)) { throw 'Qualified Git executable is missing' }
$gitTopLines = @(& $git -C $root rev-parse --show-toplevel 2>&1)
if ($LASTEXITCODE -ne 0 -or $gitTopLines.Count -ne 1 -or -not [string]::Equals(([string]$gitTopLines[0]).Trim(), $expectedRepositoryRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Git top-level does not identify the approved repository'
}
$originLines = @(& $git -C $root remote get-url origin 2>&1)
if ($LASTEXITCODE -ne 0 -or $originLines.Count -ne 1 -or (([string]$originLines[0]).Trim().TrimEnd('/') -replace '\.git$', '') -ne 'https://github.com/egggggman/tmt') {
    throw 'Git origin does not identify egggggman/tmt'
}
$projectPath = '.diag003-memory-independent-review\300-game-exploratory-r1'
$batchRoot = Join-Path $root $projectPath
$planPath = Join-Path $batchRoot 'explore300r1.schedule.json'
$manifestDir = Join-Path $batchRoot 'manifests'
$preflightDir = Join-Path $batchRoot 'preflight-r1'
$logDir = Join-Path $batchRoot 'execution-integrity-v2'
$python = Join-Path $root '.diag003-preparation\python-nuget-3.13.15\tools\python.exe'
$issuer = Join-Path $root '.diag003-memory-independent-review\correction\issue_diag003_authorization.py'
$supervisor = Join-Path $root '.diag003-memory-independent-review\correction\tools\stage002_diagnostic_supervisor.py'
$verifier = Join-Path $root '.diag003-memory-independent-review\verifier-trust-review\corrected\verify_completed_batch.py'
$integrityHelper = Join-Path $batchRoot 'batch_integrity_validation.integrity-v2.py'
$expectedPlanDigest = '9206c4267027473218f18e9482abcccb8a64dcfc62a7511d39b711a427a2179c'
$expectedPlanFileSha = '3f6c0a0ec56fc788ae14287d3333364cffa547e420fad92ee4272debabfc3166'
$expectedController = '25d8bbba9adbde68d92b98b552d9603f05db3015ceb562023a12a8d013e1495b'
$expectedIssuer = '47d4adee5c4ff36f0117375777ae76d8c34217e40d63812f505ad202bb702e23'
$expectedSupervisor = 'f23939f4bb656de73588ae9202437d093b38fc7cbaf4e92b7776cb542ee22b1d'
$expectedRuntime = '85b71d8c6ec1905935f74be0c9869aae198d00e98f39df699ec66f9c5a84cecd'
$expectedLock = '0c9863fb82c65e8c457b6903b13ab978e1012dc9252e9cca3e95807ef3ded11a'
$expectedIntegrityHelper = 'e342ac4ebca9103627a83028c0f6ca21c5be2bf916a955d54eb1fc815a7043ce'
# Candidate pin only; independent reviewer approval of this identity remains required.
$expectedVerifier = '5f4b3b87b37afc8c4f4a8d18f0740e2b5504751106d448d597d6b41bb660d603'
$outputRoot = 'G:\cardcade\diagnostics'
$authorizationRoot = 'C:\Users\cowabunga\AppData\Roaming\Cardcade\Stage002Diagnostic\batches'
$usedLedger = 'C:\Users\cowabunga\AppData\Roaming\Cardcade\Stage002Diagnostic\used-authorizations'

function Get-Sha256([string] $Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-ContainedFile([string] $Root, [string] $Relative) {
    if ([string]::IsNullOrWhiteSpace($Relative) -or $Relative.Split('\') -contains '..') {
        throw "Invalid artifact relative path: $Relative"
    }
    $full = [IO.Path]::GetFullPath((Join-Path $Root ($Relative -replace '/', '\')))
    $prefix = [IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact escaped assigned output: $Relative"
    }
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        throw "Recorded artifact is missing: $Relative"
    }
    $item = Get-Item -LiteralPath $full -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Recorded artifact is a reparse point: $Relative"
    }
    return $full
}

$pythonHash = Get-Sha256 $python
if ($pythonHash -ne $expectedRuntime) { throw "Qualified Python identity mismatch: $pythonHash" }
$helperHash = Get-Sha256 $integrityHelper
if ($helperHash -ne $expectedIntegrityHelper) { throw "Integrity helper identity mismatch: $helperHash" }
$integrityLines = @(& $python -P -s -B $integrityHelper --repo-root $root --working-directory $workingDirectory 2>&1)
$integrityCode = $LASTEXITCODE
if ($integrityCode -ne 0) {
    $integrityLines | ForEach-Object { Write-Error ([string]$_) }
    throw "Schedule/repository integrity preflight failed with exit $integrityCode"
}
try { $integrityReport = ($integrityLines -join "`n") | ConvertFrom-Json }
catch { throw 'Schedule/repository integrity preflight returned invalid JSON' }
if ($integrityReport.state -ne 'SCHEDULE_MANIFESTS_VERIFIED' -or $integrityReport.schedule_sha256 -ne $expectedPlanDigest -or $integrityReport.blocks_verified -ne 30 -or $integrityReport.games_verified -ne 300) {
    throw 'Schedule/repository integrity preflight report is incomplete or inconsistent'
}

if (Test-Path -LiteralPath $logDir) {
    throw "Execution evidence path already exists; refusing reuse: $logDir"
}
$scheduleBytes = [IO.File]::ReadAllBytes($planPath)
$scheduleFileSha = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($scheduleBytes)).Replace('-', '').ToLowerInvariant()
if ($scheduleFileSha -ne $expectedPlanFileSha) {
    throw "Approved schedule file hash mismatch: $scheduleFileSha"
}
$scheduleHashFile = (Get-Content -LiteralPath (Join-Path $batchRoot 'explore300r1.schedule.sha256') -Raw).Split(' ')[0]
if ($scheduleHashFile -ne $expectedPlanDigest) {
    throw "Approved canonical schedule digest mismatch: $scheduleHashFile"
}
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.blocks.Count -ne 30 -or $plan.games_total -ne 300 -or $plan.seed_range[0] -ne 10001 -or $plan.seed_range[1] -ne 10300) {
    throw 'Approved schedule dimensions or seed range changed'
}
if (-not (Test-Path -LiteralPath $preflightDir -PathType Container)) {
    throw 'Read-only issuer preflight evidence is missing'
}
New-Item -ItemType Directory -Path $logDir | Out-Null

$blockScorecards = @()
foreach ($block in $plan.blocks) {
    $batchId = [string]$block.batch_id
    $manifestPath = Join-Path $manifestDir ($batchId + '.manifest.json')
    $preflightLog = Join-Path $preflightDir ($batchId + '.manifest.log')
    $preflightExit = Join-Path $preflightDir ($batchId + '.manifest.exitcode')
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or -not (Test-Path -LiteralPath $preflightLog -PathType Leaf) -or (Get-Content -Raw $preflightExit).Trim() -ne '0') {
        throw "Block $batchId lacks a successful preserved read-only preflight"
    }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $preflight = Get-Content -LiteralPath $preflightLog -Raw | ConvertFrom-Json
    if ($manifest.games.Count -ne 10 -or $preflight.state -ne 'BATCH_PREFLIGHT_ONLY' -or $preflight.authorization_issued -ne $false) {
        throw "Block $batchId preflight or manifest state is invalid"
    }
    if ($preflight.batch_controller_sha256 -ne $expectedController -or $preflight.issuer_sha256 -ne $expectedIssuer -or $preflight.supervisor_sha256 -ne $expectedSupervisor -or $preflight.runtime.python_executable_sha256 -ne $expectedRuntime -or $preflight.runtime.uv_lock_sha256 -ne $expectedLock) {
        throw "Block $batchId preflight execution identity changed"
    }
    # The canonical digest is held in the adjacent sidecar, not in the strict manifest.
    $sidecar = Get-Content -LiteralPath (Join-Path $manifestDir ($batchId + '.manifest.sha256')) -Raw
    $sidecarDigest = $sidecar.Split("`n")[0].Split(' ')[0].Trim()
    if ($preflight.manifest_sha256 -ne $sidecarDigest) {
        throw "Block $batchId manifest differs from its preflight"
    }
    $statusPath = [string]$manifest.batch_status_path
    $statusLock = $statusPath + '.lock'
    $authDir = Join-Path $authorizationRoot $batchId
    if ((Test-Path -LiteralPath $statusPath) -or (Test-Path -LiteralPath $statusLock) -or (Test-Path -LiteralPath $authDir)) {
        throw "Block $batchId destination was occupied after preflight"
    }
    foreach ($game in $manifest.games) {
        if ((Test-Path -LiteralPath $game.output_destination) -or (Test-Path -LiteralPath $game.authorization_file)) {
            throw "Block $batchId game destination is occupied: $($game.run_id)"
        }
    }
    $issueLog = Join-Path $logDir ($batchId + '.issuer.log')
    $issueExit = Join-Path $logDir ($batchId + '.issuer.exitcode')
    if ((Test-Path $issueLog) -or (Test-Path $issueExit)) { throw "Refusing to repeat issuance for $batchId" }
    Write-Output "ISSUING $batchId"
    $issueLines = @(& $python -P -s -B $issuer --issue-batch --manifest $manifestPath 2>&1)
    $issueCode = $LASTEXITCODE
    $issueLines | Out-String | Set-Content -LiteralPath $issueLog -Encoding UTF8
    $issueCode | Set-Content -LiteralPath $issueExit -Encoding ASCII
    if ($issueCode -ne 0) { throw "Issuer failed for $batchId with exit $issueCode; execution stopped" }
    $issueRecord = ($issueLines -join "`n") | ConvertFrom-Json
    if ($issueRecord.state -ne 'ISSUED_NOT_LAUNCHED' -or $issueRecord.batch_id -ne $batchId -or $issueRecord.game_count -ne 10 -or $issueRecord.manifest_sha256 -ne $preflight.manifest_sha256 -or $issueRecord.authorization_paths.Count -ne 10) {
        throw "Issuer result for $batchId does not match the preflighted ten-entry contract"
    }

    $controllerLog = Join-Path $logDir ($batchId + '.controller.log')
    $controllerExit = Join-Path $logDir ($batchId + '.controller.exitcode')
    Write-Output "EXECUTING $batchId"
    $controllerLines = @(& $python -P -s -B $supervisor batch --manifest $manifestPath 2>&1)
    $controllerCode = $LASTEXITCODE
    $controllerLines | Out-String | Set-Content -LiteralPath $controllerLog -Encoding UTF8
    $controllerCode | Set-Content -LiteralPath $controllerExit -Encoding ASCII
    if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) {
        throw "Controller produced no durable block status for $batchId; stopping"
    }
    $status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
    if ($status.batch_id -ne $batchId -or $status.manifest_sha256 -ne $preflight.manifest_sha256 -or $status.games.Count -ne 10 -or $status.automatic_retries -ne 0 -or $status.next_index -ne 11) {
        throw "Block $batchId checkpoint is incomplete or inconsistent; stopping"
    }
    if ($status.state -notin @('COMPLETE', 'COMPLETE_WITH_GAME_FAILURES')) {
        throw "Block $batchId ended in mandatory stop state $($status.state)"
    }
    $returned = @($status.games | Where-Object state -eq 'RETURNED').Count
    $failed = @($status.games | Where-Object state -eq 'FAILED').Count
    if ($returned -ne $status.completed_games -or ($returned + $failed) -ne 10 -or ($failed -eq 0 -and $status.state -ne 'COMPLETE') -or ($failed -gt 0 -and $status.state -ne 'COMPLETE_WITH_GAME_FAILURES')) {
        throw "Block $batchId terminal game counts do not match its checkpoint"
    }

    $artifactCount = 0
    $outcomes = @()
    for ($i = 0; $i -lt 10; $i++) {
        $row = $manifest.games[$i]
        $record = $status.games[$i]
        if ($record.index -ne ($i + 1) -or $record.run_id -ne $row.run_id) { throw "Block $batchId row identity mismatch" }
        if ($record.state -notin @('RETURNED', 'FAILED')) { throw "Block $batchId has unsafe row state $($record.state)" }
        if ($record.state -eq 'RETURNED' -and $record.exit_code -ne 0) { throw "Block $batchId returned row has nonzero exit" }
        if ($record.state -eq 'FAILED' -and [string]::IsNullOrWhiteSpace([string]$record.failure_message)) { throw "Block $batchId failure lacks preserved diagnostic" }
        $output = [string]$row.output_destination
        foreach ($entry in $record.artifacts_sha256.PSObject.Properties) {
            $artifactPath = Assert-ContainedFile $output $entry.Name
            if ((Get-Sha256 $artifactPath) -ne ([string]$entry.Value).ToLowerInvariant()) { throw "Block $batchId artifact digest mismatch: $($row.run_id) $($entry.Name)" }
            $artifactCount++
        }
        if ($record.state -eq 'FAILED') {
            $failurePath = Join-Path $output 'failure.json'
            if (-not (Test-Path -LiteralPath $failurePath -PathType Leaf)) { throw "Block $batchId failure lacks failure.json" }
        } else {
            $result = Get-Content -LiteralPath (Join-Path $output 'result.json') -Raw | ConvertFrom-Json
            if ($result.run_id -ne $row.run_id -or $result.seed -ne $row.seed -or $result.completion_state -ne 'COMPLETE' -or $result.snapshot.winner -notin @($row.seats.deck_key)) {
                throw "Block $batchId returned result identity/completion mismatch: $($row.run_id)"
            }
        }
        $grant = Get-Content -LiteralPath $row.authorization_file -Raw | ConvertFrom-Json
        if (-not (Test-Path -LiteralPath (Join-Path $usedLedger ($grant.nonce + '.used')) -PathType Leaf)) {
            throw "Block $batchId consumed authorization record is missing: $($row.run_id)"
        }
        $outcomes += [pscustomobject]@{ run_id = $row.run_id; seed = $row.seed; pairing_id = $row.pairing_id; seats = @($row.seats.deck_key); state = $record.state; winner = if ($record.state -eq 'RETURNED') { $result.snapshot.winner } else { $null }; turn = if ($record.state -eq 'RETURNED') { $result.snapshot.turn } else { $null }; failure = if ($record.state -eq 'FAILED') { $record.failure_message } else { $null } }
    }
    if ($controllerCode -eq 0 -and $status.state -eq 'COMPLETE') {
        if (-not (Test-Path -LiteralPath $verifier -PathType Leaf)) { throw 'Pinned post-run verifier candidate is missing' }
        $verifierItem = Get-Item -LiteralPath $verifier -Force
        if (($verifierItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Pinned post-run verifier candidate is a reparse point' }
        $verifierHash = Get-Sha256 $verifier
        if ($verifierHash -ne $expectedVerifier) { throw "Post-run verifier identity mismatch: $verifierHash" }
        $verifyLines = @(& $python -P -s -B $verifier $manifestPath 2>&1)
        $verifyCode = $LASTEXITCODE
        $verifyLines | Out-String | Set-Content -LiteralPath (Join-Path $logDir ($batchId + '.verification.log')) -Encoding UTF8
        $verifyCode | Set-Content -LiteralPath (Join-Path $logDir ($batchId + '.verification.exitcode')) -Encoding ASCII
        if ($verifyCode -ne 0) { throw "Independent successful-block verifier failed for $batchId" }
    } elseif ($status.state -eq 'COMPLETE_WITH_GAME_FAILURES' -and $controllerCode -eq 1) {
        Write-Output "RECORDED_GAME_FAILURES $batchId returned=$returned failed=$failed; block evidence hashes and consumption markers verified"
    } else {
        throw "Controller exit/status combination is unsafe for $batchId (exit $controllerCode, state $($status.state))"
    }
    $score = [ordered]@{ block = $block.block; batch_id = $batchId; manifest_sha256 = $status.manifest_sha256; state = $status.state; attempts = 10; completed = $returned; failed = $failed; automatic_retries = 0; artifacts_verified = $artifactCount; games = $outcomes }
    $score | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $logDir ($batchId + '.scorecard.json')) -Encoding UTF8
    $blockScorecards += $score
    Write-Output "VERIFIED $batchId attempts=10 completed=$returned failed=$failed artifacts=$artifactCount state=$($status.state)"
}

$summary = [ordered]@{ schedule_digest = $expectedPlanDigest; blocks = 30; attempts = 300; completed = (($blockScorecards | ForEach-Object { $_.completed } | Measure-Object -Sum).Sum); failed = (($blockScorecards | ForEach-Object { $_.failed } | Measure-Object -Sum).Sum); automatic_retries = 0; state = 'ALL_BLOCKS_VERIFIED'; scorecards = $blockScorecards }
$summary | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $logDir 'batch-summary.json') -Encoding UTF8
Write-Output "ALL BLOCKS VERIFIED attempts=300 completed=$($summary.completed) failed=$($summary.failed)"
