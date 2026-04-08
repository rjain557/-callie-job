# Setup Windows Task Scheduler for Daily Job Scan
# Run this script once in PowerShell as Administrator to create the scheduled task

$taskName = "CallieJobScan"
$description = "Daily job scan for Callie Wells - searches Indeed for new postings and emails digest"
$scriptPath = "C:\VSCode\callie-job\-callie-job\scripts\daily_job_scan.py"
$pythonPath = (Get-Command python).Source
$workingDir = "C:\VSCode\callie-job\-callie-job"
$logFile = "C:\VSCode\callie-job\-callie-job\tracking\scheduler-log.txt"

# Run daily at 7:00 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 7:00AM

# Action: run python script
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument $scriptPath `
    -WorkingDirectory $workingDir

# Settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Description $description `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -RunLevel Limited

Write-Host ""
Write-Host "Task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "Schedule: Daily at 7:00 AM"
Write-Host "Script: $scriptPath"
Write-Host ""
Write-Host "To verify: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "To run now: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "To remove:  Unregister-ScheduledTask -TaskName '$taskName'"
