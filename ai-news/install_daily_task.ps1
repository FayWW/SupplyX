$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $PSCommandPath
$runner = Join-Path $scriptDir 'run_daily_news.bat'
$taskName = 'DailyNewsBriefingAI'

if (-not (Test-Path -LiteralPath $runner)) {
    throw "News task runner was not found: $runner"
}

$action = New-ScheduledTaskAction -Execute $env:ComSpec -Argument ('/d /c ""{0}""' -f $runner)
$trigger = New-ScheduledTaskTrigger -Daily -At 9:55AM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force -ErrorAction Stop | Out-Null
Write-Host "Task '$taskName' now runs daily at 09:55."