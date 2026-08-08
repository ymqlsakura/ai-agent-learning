param(
    [string]$VideoRoot = 'D:\video',
    [string]$BenchmarkRoot = 'D:\video\_worktrees\motion-design-benchmark'
)

$ErrorActionPreference = 'Stop'
$checks = [System.Collections.Generic.List[object]]::new()

function Add-Check {
    param([string]$Name, [bool]$Pass, [string]$Detail)
    $checks.Add([PSCustomObject]@{ Check = $Name; Pass = $Pass; Detail = $Detail })
}

$runtimeRoot = Join-Path $VideoRoot '.codex\skills'
$skillNames = @(
    'remotion-best-practices',
    'remotion-captions',
    'remotion-create',
    'remotion-docs',
    'remotion-interactivity',
    'remotion-maps',
    'remotion-markup',
    'remotion-multimedia',
    'remotion-render',
    'remotion-saas',
    'remotion-studio',
    'remotion-upgrade',
    'video-shotcraft',
    'benchmark-remotion-motion-design'
)

foreach ($name in $skillNames) {
    $skillFile = Join-Path (Join-Path $runtimeRoot $name) 'SKILL.md'
    Add-Check -Name "skill:$name" -Pass (Test-Path -LiteralPath $skillFile) -Detail $skillFile
}

$shotcraftRoot = Join-Path $runtimeRoot 'video-shotcraft'
if (Test-Path -LiteralPath (Join-Path $shotcraftRoot '.git')) {
    $shotcraftCommit = (git -C $shotcraftRoot rev-parse HEAD).Trim()
    Add-Check -Name 'pin:video-shotcraft' -Pass ($shotcraftCommit -eq '0022ec45d28800cecb5b16624a3179093c93f4e9') -Detail $shotcraftCommit
} else {
    Add-Check -Name 'pin:video-shotcraft' -Pass $false -Detail 'Git metadata missing'
}

$referencePins = @{
    'remotion-agent-skills' = '7809e7935bc2e18f4b86526fa6022e6aadd8fe8b'
    'prompt-to-motion-graphics' = '341afb0d9aa9d837cb58b9c802d89ac105a42a6c'
    'rve-remotion-templates' = '6209b724798e48ff395f8df1a6fa2d26082372b5'
    'remotion-scenes' = '02c7a84241da7010b5f59c420b0110aafd1d6f0d'
    'curvable-motion' = '48aa412b5f4a15d5a31fe02f6e7e43e654ca091a'
    'remotion-playground' = 'fe10b866da07c5799b226d7ff9598c1dc35d7159'
}
foreach ($name in $referencePins.Keys) {
    $repo = Join-Path $VideoRoot ".cache\motion-design\$name"
    if (Test-Path -LiteralPath (Join-Path $repo '.git')) {
        $actual = (git -C $repo rev-parse HEAD).Trim()
        Add-Check -Name "pin:$name" -Pass ($actual -eq $referencePins[$name]) -Detail $actual
    } else {
        Add-Check -Name "pin:$name" -Pass $false -Detail 'Repository missing'
    }
}

$packageFile = Join-Path $BenchmarkRoot 'package.json'
if (Test-Path -LiteralPath $packageFile) {
    $package = Get-Content -Raw $packageFile | ConvertFrom-Json
    $requiredPackages = @(
        'remotion',
        '@remotion/transitions',
        '@remotion/effects',
        '@remotion/lottie',
        '@remotion/three',
        '@remotion/shapes',
        '@remotion/paths',
        '@remotion/sfx'
    )
    foreach ($name in $requiredPackages) {
        $value = $package.dependencies.PSObject.Properties[$name].Value
        Add-Check -Name "package:$name" -Pass (-not [string]::IsNullOrWhiteSpace($value)) -Detail ([string]$value)
    }
    Add-Check -Name 'package:remotion-version' -Pass ($package.dependencies.remotion -eq '4.0.506') -Detail ([string]$package.dependencies.remotion)
} else {
    Add-Check -Name 'benchmark-package' -Pass $false -Detail $packageFile
}

$checks | Format-Table -AutoSize
if ($checks.Where({ -not $_.Pass }).Count -gt 0) {
    exit 1
}
exit 0
