#Requires -Version 5.1
<#
.SYNOPSIS
    Install a chip fastfetch theme on Windows.

.DESCRIPTION
    Native Windows installer: PowerShell 5.1 or newer, no WSL / Git Bash / sh
    needed. bin/install.sh is for macOS and Linux (under Git Bash it simply
    forwards here).

    Writes <Dest>\config.jsonc plus the selected logo file(s), where <Dest>
    defaults to %APPDATA%\fastfetch -- one of the directories a plain
    "fastfetch" run searches (see: fastfetch --list-config-paths).

    Without -Chip the theme is picked from the host CPU. When a Python 3 is
    found the logo is regenerated for the exact model number
    ("CORE ULTRA 9 / 285H"); otherwise the closest pre-generated theme from
    chips/ is copied (generic wordmark, same palette and die artwork).

.PARAMETER Chip
    Chip id from chips/ (i7, ultra9, ryzen9, m2max, threadripper, ...).
    Omit to auto-detect from the CPU.

.PARAMETER Size
    full (default) or small.

.PARAMETER Dest
    Target fastfetch config directory. Defaults to $env:FASTFETCH_CONFIG_DIR,
    then %APPDATA%\fastfetch.

.PARAMETER Brand
    CPU brand string override, used for detection and the model wordmark.

.PARAMETER Python
    python.exe to use for the model-specific generator.

.PARAMETER List
    Print the available chips and exit.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\bin\install.ps1
.EXAMPLE
    .\bin\install.ps1 ryzen9 small
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)] [string] $Chip,
    [Parameter(Position = 1)] [string] $Size = 'full',
    [string] $Dest,
    [string] $Brand,
    [string] $Python,
    [switch] $List
)

$ErrorActionPreference = 'Stop'

$Root     = Split-Path -Parent $PSScriptRoot
$ChipsDir = Join-Path $Root 'chips'

# Ordered detection table: the first pattern whose chip folder exists wins.
# Keeps in sync with detect_chip() in bin/install.sh and CHIPS in tools/chips.py
# (specific tiers before general ones: "ryzen threadripper" is a Threadripper).
$ChipPatterns = @(
    @{ pattern = 'apple\s+m(\d)\s*ultra';              chip = 'm{0}ultra' },
    @{ pattern = 'apple\s+m(\d)\s*max';                chip = 'm{0}max' },
    @{ pattern = 'apple\s+m(\d)\s*pro';                chip = 'm{0}pro' },
    @{ pattern = 'apple\s+m(\d)\b';                    chip = 'm{0}' },
    @{ pattern = '(?:core\s+)?ultra\s+(9|7|5)\b';      chip = 'ultra{0}' },
    @{ pattern = 'xeon';                               chip = 'xeon' },
    @{ pattern = 'core\s*i(9|7|5|3)\b';                chip = 'i{0}' },
    @{ pattern = '\bi(9|7|5|3)-';                      chip = 'i{0}' },
    @{ pattern = 'threadripper';                       chip = 'threadripper' },
    @{ pattern = 'epyc';                               chip = 'epyc' },
    @{ pattern = 'ryzen\s*(9|7|5|3)\b';                chip = 'ryzen{0}' }
)

function Fail([string] $Message) {
    Write-Host "error: $Message"
    exit 1
}

function Show-DestHint {
    # A default config is only picked up automatically from the directories
    # fastfetch searches: %ProgramData%, %APPDATA%, %LOCALAPPDATA%, %USERPROFILE%.
    $ff = Get-Command fastfetch -CommandType Application -ErrorAction SilentlyContinue |
          Select-Object -First 1
    if (-not $ff) {
        Write-Host 'note: fastfetch is not on PATH -- winget install Fastfetch-cli.Fastfetch'
        return
    }
    $ErrorActionPreference = 'Continue'   # local to this function
    try {
        $paths = & $ff --list-config-paths 2> $null
        $want = ConvertTo-JsonPath $Dest
        $listed = @($paths | ForEach-Object { (ConvertTo-JsonPath ([string] $_).TrimEnd('/')) } |
                    Where-Object { $_ -eq $want })
        if ($listed.Count -eq 0) {
            Write-Host "note: fastfetch does not search $Dest -- run it as: fastfetch -c `"$ConfigDest`""
        }
    } catch { }
}

function Show-Chips {
    Write-Host 'available chips:'
    foreach ($dir in Get-ChildItem -LiteralPath $ChipsDir -Directory | Sort-Object Name) {
        Write-Host ('  ' + $dir.Name)
    }
}

function ConvertTo-JsonPath([string] $Path) {
    # A JSON string may not contain bare backslashes, and fastfetch accepts
    # forward slashes on Windows, so this is the only portable form.
    $Path -replace '\\', '/'
}

function Get-ConfigDir {
    # fastfetch on Windows searches, in order: %ProgramData%, %APPDATA%,
    # %LOCALAPPDATA% and %USERPROFILE%, each + "\fastfetch".
    if ($env:FASTFETCH_CONFIG_DIR) { return $env:FASTFETCH_CONFIG_DIR }
    if ($env:APPDATA)              { return (Join-Path $env:APPDATA 'fastfetch') }
    if ($env:LOCALAPPDATA)         { return (Join-Path $env:LOCALAPPDATA 'fastfetch') }
    return (Join-Path (Get-Location) 'fastfetch')
}

function Get-CpuBrand {
    if ($Brand) { return ([string] $Brand).Trim() }
    # wmic.exe was removed in Windows 11 24H2 and the WMI service can be
    # unavailable, so the registry (REG_SZ, one subkey per logical CPU) first.
    $reg = 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor'
    try {
        if (Test-Path -LiteralPath (Join-Path $reg '0')) {
            $value = (Get-ItemProperty -LiteralPath (Join-Path $reg '0') `
                                       -Name ProcessorNameString).ProcessorNameString
            if ($value) { return ([string] $value).Trim() }
        }
    } catch { }
    try {
        foreach ($cpu in (Get-ChildItem -LiteralPath $reg -ErrorAction Stop)) {
            $value = (Get-ItemProperty -LiteralPath $cpu.PSPath -Name ProcessorNameString `
                                       -ErrorAction SilentlyContinue).ProcessorNameString
            if ($value) { return ([string] $value).Trim() }
        }
    } catch { }
    try {
        $value = Get-CimInstance -ClassName Win32_Processor -ErrorAction Stop |
                 Select-Object -First 1 -ExpandProperty Name
        if ($value) { return ([string] $value).Trim() }
    } catch { }
    try {
        $value = Get-WmiObject -Class Win32_Processor -ErrorAction Stop |
                 Select-Object -First 1 -ExpandProperty Name
        if ($value) { return ([string] $value).Trim() }
    } catch { }
    return ''
}

function Resolve-ChipFromBrand([string] $BrandString) {
    $norm = ([string] $BrandString).ToLower()
    $norm = $norm -replace '\((r|tm)\)', ' '
    $norm = $norm -replace '[\u00ae\u2122]', ' '
    $norm = ($norm -replace '\s+', ' ').Trim()
    foreach ($entry in $ChipPatterns) {
        if ($norm -match $entry.pattern) {
            $candidate = $entry.chip -f $Matches[1]
            if (Test-Path -LiteralPath (Join-Path $ChipsDir $candidate)) {
                return $candidate
            }
        }
    }
    return ''
}

function Get-Python {
    # First interpreter that runs, as @{ exe = ...; prefix = @(...) }. The
    # Microsoft Store python.exe alias on PATH exits non-zero until Python is
    # really installed, which the version probe below catches.
    $candidates = @()
    if ($Python) {
        $candidates += @{ exe = $Python; prefix = @() }
    } else {
        foreach ($name in 'py', 'python', 'python3') {
            $cmd = Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue |
                   Select-Object -First 1
            if ($cmd) {
                $prefix = if ($name -eq 'py') { @('-3') } else { @() }
                $candidates += @{ exe = $cmd.Source; prefix = $prefix }
            }
        }
        $globs = @()
        if ($env:LOCALAPPDATA) { $globs += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\python.exe') }
        if ($env:ProgramFiles) { $globs += (Join-Path $env:ProgramFiles 'Python*\python.exe') }
        $globs += 'C:\Python*\python.exe'
        foreach ($glob in $globs) {
            foreach ($file in (Get-ChildItem -Path $glob -File -ErrorAction SilentlyContinue)) {
                $candidates += @{ exe = $file.FullName; prefix = @() }
            }
        }
    }
    $ErrorActionPreference = 'Continue'   # local: a probe must never be fatal
    foreach ($cand in $candidates) {
        # A real Python 3.8+ prints "3" and exits 0; that rejects the Microsoft
        # Store alias and anything else that merely happens to be named python.
        $probe = @($cand.prefix) + @('-c', 'import sys; print(sys.version_info[0]);' +
                                           ' sys.exit(0 if sys.version_info >= (3, 8) else 1)')
        try {
            $answer = @(& $cand.exe @probe 2> $null)   # no Select-Object: it would
            $first = if ($answer.Count) { [string] $answer[0] } else { '' }
            if ($LASTEXITCODE -eq 0 -and $first.Trim() -eq '3') { return $cand }
        } catch { }
    }
    return $null
}

# ---------------------------------------------------------------------------
# argument handling (same contract as bin/install.sh)
# ---------------------------------------------------------------------------
if (-not (Test-Path -LiteralPath $ChipsDir)) { Fail "chips folder not found: $ChipsDir" }

if ($Python -and -not (Test-Path -LiteralPath $Python)) { Fail "python not found: $Python" }

if ($List) { Show-Chips; exit 0 }

# Backward compatibility: install.ps1 small
if ($Chip -eq 'full' -or $Chip -eq 'small') {
    $Size = $Chip
    $Chip = ''
}
if ($Size -ne 'full' -and $Size -ne 'small') {
    Write-Host 'usage: bin/install.ps1 [chip] [full|small]'
    Show-Chips
    exit 1
}
if ($Chip) {
    if (-not (Test-Path -LiteralPath (Join-Path $ChipsDir $Chip))) {
        Write-Host "unknown chip: $Chip"
        Show-Chips
        exit 1
    }
}

if (-not $Dest) { $Dest = Get-ConfigDir }
if (-not [IO.Path]::IsPathRooted($Dest)) { $Dest = Join-Path (Get-Location) $Dest }

try {
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
} catch {
    Fail "cannot write to $Dest ($_)"
}

$ConfigDest = Join-Path $Dest 'config.jsonc'
if (Test-Path -LiteralPath $ConfigDest) {
    Copy-Item -LiteralPath $ConfigDest -Destination "$ConfigDest.bak" -Force
    Write-Host "kept the previous config in $ConfigDest.bak"
}

# ---------------------------------------------------------------------------
# preferred path: identify tier + exact model and generate a model-specific
# theme straight into the config dir (needs python3)
# ---------------------------------------------------------------------------
if (-not $Chip) {
    $brandString = Get-CpuBrand
    if ($brandString) { Write-Host "cpu: $brandString" }

    $py = Get-Python
    if ($py) {
        $genArgs = @($py.prefix) + @((Join-Path $Root 'tools\gen_logo.py'), '--auto',
                                     '--dest', $Dest, '--install-size', $Size)
        if ($brandString) { $genArgs += @('--brand', $brandString) }
        Write-Host ("generating a model-specific theme with " + $py.exe)
        & $py.exe @genArgs
        if ($LASTEXITCODE -eq 0) { Show-DestHint; exit 0 }
        Write-Host 'the generator failed; falling back to pre-generated themes'
    } else {
        Write-Host 'python3 not found: installing a pre-generated theme instead'
        Write-Host '  (the generic wordmark is used -- install Python and re-run'
        Write-Host '   for the logo with your exact model number)'
        Write-Host '  winget install Python.Python.3.12'
    }

    $Chip = Resolve-ChipFromBrand $brandString
    if (-not $Chip) {
        Write-Host 'could not detect this CPU; falling back to m4pro'
        $Chip = 'm4pro'
    } else {
        Write-Host "detected chip: $Chip"
    }
}

# ---------------------------------------------------------------------------
# copy the pre-generated theme
# ---------------------------------------------------------------------------
$ThemeDir = Join-Path $ChipsDir $Chip
$FullSrc  = Join-Path $ThemeDir ($Chip + '.txt')
$SmallSrc = Join-Path $ThemeDir ($Chip + '_small.txt')

if (-not (Test-Path -LiteralPath $FullSrc)) {
    Write-Host "unknown chip: $Chip"
    Show-Chips
    exit 1
}
if ($Size -eq 'small' -and -not (Test-Path -LiteralPath $SmallSrc)) {
    Fail "missing small theme: $SmallSrc"
}

$LogoSrc  = if ($Size -eq 'small') { $SmallSrc } else { $FullSrc }
$LogoDest = Join-Path $Dest ([IO.Path]::GetFileName($LogoSrc))

Copy-Item -LiteralPath $FullSrc -Destination (Join-Path $Dest ($Chip + '.txt')) -Force
$SmallInstalled = $false
if (Test-Path -LiteralPath $SmallSrc) {
    Copy-Item -LiteralPath $SmallSrc -Destination (Join-Path $Dest ($Chip + '_small.txt')) -Force
    $SmallInstalled = $true
}

# per-chip config (brand palette baked in) falls back to the shared template
$ConfigSrc = Join-Path $ThemeDir 'config.jsonc'
if (-not (Test-Path -LiteralPath $ConfigSrc)) {
    $ConfigSrc = Join-Path $Root 'templates\config.jsonc'
    Write-Host "no per-chip config for $Chip -- using the shared template"
}
$text = [IO.File]::ReadAllText($ConfigSrc, [Text.Encoding]::UTF8)
$text = $text.Replace('@LOGO@', (ConvertTo-JsonPath $LogoDest))
[IO.File]::WriteAllText($ConfigDest, $text, (New-Object Text.UTF8Encoding($false)))
if ($text -match '@[A-Z0-9]+@') {
    Write-Host "warning: unreplaced placeholder $($Matches[0]) in $ConfigDest"
}

Write-Host 'installed:'
Write-Host ("  $ConfigDest        (logo -> " + (ConvertTo-JsonPath $LogoDest) + ')')
Write-Host ('  ' + (Join-Path $Dest ($Chip + '.txt')))
if ($SmallInstalled) { Write-Host ('  ' + (Join-Path $Dest ($Chip + '_small.txt'))) }

Show-DestHint
Write-Host 'run:  fastfetch'