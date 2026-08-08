param(
    [string]$VideoRoot = 'D:\video',
    [string]$ShotcraftRoot = ''
)

$ErrorActionPreference = 'Stop'

$skillRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($ShotcraftRoot)) {
    $ShotcraftRoot = Join-Path $env:USERPROFILE '.agents\skills\video-shotcraft'
}

$runtimeRoot = Join-Path $VideoRoot '.codex\skills'
$cacheRoot = Join-Path $VideoRoot '.cache\motion-design'
New-Item -ItemType Directory -Force -Path $runtimeRoot, $cacheRoot | Out-Null

function Ensure-Junction {
    param([string]$Name, [string]$Target)

    if (-not (Test-Path -LiteralPath $Target)) {
        throw "Missing skill source for $Name at $Target"
    }

    $link = Join-Path $runtimeRoot $Name
    if (Test-Path -LiteralPath $link) {
        $item = Get-Item -LiteralPath $link
        $resolvedTarget = [string]$item.Target
        if ($resolvedTarget -ne $Target) {
            throw "Existing path $link points to $resolvedTarget instead of $Target"
        }
        Write-Output "OK $Name"
        return
    }

    New-Item -ItemType Junction -Path $link -Target $Target | Out-Null
    Write-Output "LINKED $Name"
}

$referenceRepos = @(
    @{
        Name = 'remotion-agent-skills'
        Url = 'https://github.com/remotion-dev/skills.git'
        Commit = '7809e7935bc2e18f4b86526fa6022e6aadd8fe8b'
    },
    @{
        Name = 'prompt-to-motion-graphics'
        Url = 'https://github.com/remotion-dev/template-prompt-to-motion-graphics-saas.git'
        Commit = '341afb0d9aa9d837cb58b9c802d89ac105a42a6c'
    },
    @{
        Name = 'rve-remotion-templates'
        Url = 'https://github.com/reactvideoeditor/remotion-templates.git'
        Commit = '6209b724798e48ff395f8df1a6fa2d26082372b5'
    },
    @{
        Name = 'remotion-scenes'
        Url = 'https://github.com/lifeprompt-team/remotion-scenes.git'
        Commit = '02c7a84241da7010b5f59c420b0110aafd1d6f0d'
    },
    @{
        Name = 'curvable-motion'
        Url = 'https://github.com/Curvable/motion.git'
        Commit = '48aa412b5f4a15d5a31fe02f6e7e43e654ca091a'
    },
    @{
        Name = 'remotion-playground'
        Url = 'https://github.com/jessai2026/remotion-playground.git'
        Commit = 'fe10b866da07c5799b226d7ff9598c1dc35d7159'
    }
)

foreach ($repo in $referenceRepos) {
    $path = Join-Path $cacheRoot $repo.Name
    if (-not (Test-Path -LiteralPath $path)) {
        git clone --filter=blob:none $repo.Url $path
        git -C $path checkout $repo.Commit
    }
    $actual = (git -C $path rev-parse HEAD).Trim()
    if ($actual -ne $repo.Commit) {
        throw "$($repo.Name) is at $actual instead of pinned commit $($repo.Commit)"
    }
    Write-Output "PINNED $($repo.Name) $actual"
}

$officialSkills = @(
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
    'remotion-upgrade'
)
$officialRoot = Join-Path $cacheRoot 'remotion-agent-skills\skills'
foreach ($name in $officialSkills) {
    Ensure-Junction -Name $name -Target (Join-Path $officialRoot $name)
}
Ensure-Junction -Name 'video-shotcraft' -Target $ShotcraftRoot
Ensure-Junction -Name 'benchmark-remotion-motion-design' -Target $skillRoot

$optionalTransitions = Join-Path $env:USERPROFILE '.agents\skills\remotion-transitions'
if (Test-Path -LiteralPath $optionalTransitions) {
    Ensure-Junction -Name 'remotion-transitions' -Target $optionalTransitions
}

Write-Output 'Remotion Codex plugin is managed by the Codex Plugin Manager and must be verified in the app.'
