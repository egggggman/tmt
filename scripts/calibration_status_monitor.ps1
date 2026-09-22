param(
    [Parameter(Mandatory = $true)]
    [string]$RunDirectory,
    [int]$RefreshSeconds = 30,
    [switch]$Once,
    [int]$HoldOpenMilliseconds = 0
)

$totalGames = 184320
$totalExecutions = 368640

function Read-Heartbeat {
    param([string]$Path)

    $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
    $stream = [System.IO.FileStream]::new(
        $Path,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::Read,
        $share
    )
    try {
        $reader = [System.IO.StreamReader]::new(
            $stream,
            [System.Text.Encoding]::UTF8,
            $true,
            1024,
            $true
        )
        try {
            $text = $reader.ReadToEnd()
        }
        finally {
            $reader.Dispose()
        }
        if ($HoldOpenMilliseconds -gt 0) {
            Start-Sleep -Milliseconds $HoldOpenMilliseconds
        }
        return ($text | ConvertFrom-Json)
    }
    finally {
        $stream.Dispose()
    }
}

do {
    Clear-Host
    try {
        $heartbeat = Read-Heartbeat (Join-Path $RunDirectory "RUN_HEARTBEAT.json")
        $games = [int64]$heartbeat.completed_member_count
        $executions = [int64]$heartbeat.returned_execution_count
        Write-Host ("Distinct games: {0:N0} / {1:N0} ({2:N4}%)" -f $games, $totalGames, (100 * $games / $totalGames))
        Write-Host ("Executions: {0:N0} / {1:N0} ({2:N4}%)" -f $executions, $totalExecutions, (100 * $executions / $totalExecutions))
        Write-Host ("Whole-roster blocks: {0:N0} / 2,048" -f ([math]::Floor($games / 90)))
        Write-Host ("Heartbeat phase: {0}" -f $heartbeat.phase)
        Write-Host ("Heartbeat UTC: {0}" -f $heartbeat.utc_timestamp)
        try {
            $start = [DateTimeOffset]::Parse($heartbeat.run_start_utc)
            $now = [DateTimeOffset]::Parse($heartbeat.utc_timestamp)
            $elapsed = ($now - $start).TotalSeconds
            if ($elapsed -gt 0 -and $games -gt 0) {
                $gamesPerSecond = $games / $elapsed
                $executionsPerSecond = $executions / $elapsed
                $remainingSeconds = ($totalGames - $games) / $gamesPerSecond
                Write-Host ("Elapsed: {0}; games/sec: {1:N3}; executions/sec: {2:N3}; ETA seconds: {3:N0}" -f ([TimeSpan]::FromSeconds($elapsed)), $gamesPerSecond, $executionsPerSecond, $remainingSeconds)
            }
            else {
                Write-Host "Elapsed/rates/ETA: insufficient completed work"
            }
        }
        catch {
            Write-Host "Elapsed/rates/ETA: unavailable; telemetry timestamps invalid or absent"
        }
    }
    catch {
        Write-Host "Heartbeat temporarily unavailable; no counters inferred."
    }
    if ($Once) { break }
    Start-Sleep -Seconds $RefreshSeconds
} while ($true)
