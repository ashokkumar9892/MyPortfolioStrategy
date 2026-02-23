$ProjectPath = "D:\Ashok\ETrade\Claude Ai\MyPortfolioStrategy"
$PythonExe = "C:\Users\dream\AppData\Local\Programs\Python\Python313\python.exe"
$TaskName = "MyPortfolioStrategyHourly"

$ScriptPath = Join-Path $ProjectPath "run_signals.py"
$Command = "`"$PythonExe`" `"$ScriptPath`""

schtasks /Create /TN $TaskName /TR $Command /SC HOURLY /F
Write-Host "Created task: $TaskName"
