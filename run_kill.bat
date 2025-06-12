@echo off
echo Stopping all Distributed File Storage System components...

:: Kill Python processes running from the project folder (adjust path if needed)
for /f "tokens=2 delims=," %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO CSV /NH') do (
    tasklist /FI "PID eq %%~i" | find /I "Distributed-File-Storage-System-master" >nul
    if not errorlevel 1 (
        echo Killing python.exe with PID %%~i
        taskkill /PID %%~i /F >nul 2>&1
    )
)

:: Close all CMD windows (be cautious with this)
taskkill /F /FI "WINDOWTITLE eq C:\Windows\system32\cmd.exe" >nul 2>&1

echo All servers, supernode, and client should be stopped.
pause
