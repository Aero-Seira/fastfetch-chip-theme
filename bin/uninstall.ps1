#Requires -Version 5.1
<#
.SYNOPSIS
    Remove the files installed by bin\install.ps1 (Windows).

.DESCRIPTION
    Deletes <Dest>\config.jsonc and every chip logo this repository has ever
    installed there. <Dest> defaults to %APPDATA%\fastfetch (override with
    -Dest or $env:FASTFETCH_CONFIG_DIR). A config.jsonc.bak written by the
    installer is left alone.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\bin\uninstall.ps1
#>
[CmdletBinding()]
param(
    [string] $Dest
)

$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$ChipsDir = Join-Path $Root 'chips'

if (-not $Dest) {
    if ($env:FASTFETCH_CONFIG_DIR) {
        $Dest = $env:FASTFETCH_CONFIG_DIR
    } elseif ($env:APPDATA) {
        $Dest = (Join-Path $env:APPDATA 'fastfetch')
    } elseif ($env:LOCALAPPDATA) {
        $Dest = (Join-Path $env:LOCALAPPDATA 'fastfetch')
    } else {
        $Dest = (Join-Path (Get-Location) 'fastfetch')
    }
}
if (-not [IO.Path]::IsPathRooted($Dest)) { $Dest = Join-Path (Get-Location) $Dest }

if (-not (Test-Path -LiteralPath $Dest)) {
    Write-Host "nothing to remove: $Dest does not exist"
    exit 0
}

$removed = 0
$config = Join-Path $Dest 'config.jsonc'
if (Test-Path -LiteralPath $config) {
    Remove-Item -LiteralPath $config -Force
    Write-Host "removed $config"
    $removed = $removed + 1
    if (Test-Path -LiteralPath "$config.bak") {
        Write-Host "kept $config.bak (restore it with Copy-Item if you want it back)"
    }
}

if (Test-Path -LiteralPath $ChipsDir) {
    foreach ($theme in (Get-ChildItem -LiteralPath $ChipsDir -Recurse -Filter '*.txt')) {
        $target = Join-Path $Dest $theme.Name
        if (Test-Path -LiteralPath $target) {
            Remove-Item -LiteralPath $target -Force
            Write-Host "removed $target"
            $removed = $removed + 1
        }
    }
}

if ($removed -eq 0) {
    Write-Host "no managed chip theme files in $Dest"
} else {
    Write-Host "removed $removed managed file(s) from $Dest"
}