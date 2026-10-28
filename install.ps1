$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'dist\LayoutFixer.exe'
if (-not (Test-Path -LiteralPath $source)) {
    throw 'First run build.bat. Expected dist\LayoutFixer.exe'
}
$destination = Join-Path $env:LOCALAPPDATA 'LayoutFixer'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -LiteralPath $source -Destination (Join-Path $destination 'LayoutFixer.exe') -Force
$shell = New-Object -ComObject WScript.Shell
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Layout Fixer.lnk'
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $destination 'LayoutFixer.exe'
$shortcut.WorkingDirectory = $destination
$shortcut.Save()
Write-Host 'Installed. Start Layout Fixer using the desktop shortcut.'
