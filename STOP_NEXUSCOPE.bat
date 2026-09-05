@echo off
title Stop NEXUSCOPE
echo Stopping NEXUSCOPE processes...
taskkill /FI "WINDOWTITLE eq NEXUSCOPE Backend*" /T /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq NEXUSCOPE Frontend*" /T /F >nul 2>nul
echo Done.
pause
