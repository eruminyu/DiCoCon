@echo off
chcp 65001 > nul
echo 백그라운드에서 실행 중인 Discord ConBot을 종료합니다...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*DiscordConBot*bot.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo 종료 완료!
pause
