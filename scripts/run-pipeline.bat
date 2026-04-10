@echo off
REM Daily Job Pipeline for Callie Wells
REM Runs at 7:00 AM via Windows Task Scheduler
REM Logs output to tracking/pipeline-output.log

set LOGFILE=C:\VSCode\callie-job\-callie-job\tracking\pipeline-output.log

echo. >> "%LOGFILE%"
echo ============================================ >> "%LOGFILE%"
echo Pipeline started: %DATE% %TIME% >> "%LOGFILE%"
echo ============================================ >> "%LOGFILE%"

"C:\Users\rjain\AppData\Local\Programs\Python\Python312\python.exe" "C:\VSCode\callie-job\-callie-job\scripts\daily_job_scan.py" >> "%LOGFILE%" 2>&1

echo Pipeline finished: %DATE% %TIME% >> "%LOGFILE%"
