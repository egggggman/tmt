param(
    [string]$Checkpoint = 'G:\cardcade\calibration-runs\BAD_GUYS_CRONIES_0_2_DURABLE_001\checkpoint.json',
    [string]$ExpectedScheduleDigest = '4da440bc83b9790876d1020ae83cf2147c4e60a67feba8bb7181421e196b303e',
    [int]$HoldOpenMilliseconds = 0
)

$ErrorActionPreference = 'Stop'
$count = $null
$identity = 'NO_CHECKPOINT'
$modified = $null
$file = Get-Item -LiteralPath $Checkpoint -ErrorAction SilentlyContinue
if ($file) {
    $modified = $file.LastWriteTimeUtc.ToString('o')
    $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
    $stream = [System.IO.FileStream]::new(
        $Checkpoint, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share
    )
    try {
        if ($stream.Length -lt 256) { throw 'Checkpoint too small' }
        $head = New-Object byte[] 256
        $tail = New-Object byte[] 256
        $readHead = $stream.Read($head, 0, $head.Length)
        [void]$stream.Seek(-256, [System.IO.SeekOrigin]::End)
        $readTail = $stream.Read($tail, 0, $tail.Length)
        $headText = [System.Text.Encoding]::UTF8.GetString($head, 0, $readHead)
        $tailText = [System.Text.Encoding]::UTF8.GetString($tail, 0, $readTail)
        if ($headText -notmatch '"completed_games":\s*(\d+)') { throw 'Count header missing' }
        $count = [int]$Matches[1]
        if ($tailText -notmatch '"schedule_digest":\s*"([0-9a-f]{64})"') { throw 'Schedule digest missing' }
        if ($Matches[1] -cne $ExpectedScheduleDigest) { throw 'Schedule digest mismatch' }
        if ($tailText -notmatch '"schedule_games":\s*900') { throw 'Schedule size mismatch' }
        if ($count -lt 0 -or $count -gt 900) { throw 'Count out of range' }
        $identity = 'HEADER_AND_TAIL_MATCH; RECORDS_NOT_AUDITED'
        if ($HoldOpenMilliseconds -gt 0) {
            Write-Output 'MONITOR_READ_HANDLE_OPEN'
            Start-Sleep -Milliseconds $HoldOpenMilliseconds
        }
    }
    catch {
        $count = $null
        $identity = "UNAVAILABLE: $($_.Exception.Message)"
    }
    finally {
        $stream.Dispose()
    }
}

try {
    $writers = @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^python(w)?\.exe$' -and
        $_.CommandLine -match 'run_bad_guys_initial_calibration\.py' -and
        $_.CommandLine -match '--checkpoint'
    } | Select-Object ProcessId, CommandLine)
    $processStatus = if ($writers.Count) { ($writers.ProcessId -join ',') } else { 'none' }
}
catch {
    $processStatus = 'UNKNOWN: process enumeration denied'
}

[pscustomobject]@{
    Checkpoint = $Checkpoint
    CheckpointModifiedUtc = $modified
    ReportedCompletedGames = $count
    IdentityCheck = $identity
    CalibrationProcessIds = $processStatus
    LockPresent = Test-Path -LiteralPath "$Checkpoint.lock"
}
