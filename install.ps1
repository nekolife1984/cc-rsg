<#
.SYNOPSIS
  cc-rsg installer — interactive skill installer for coding agents

.DESCRIPTION
  Installs the cc-rsg skill to one or more coding agents:
  Claude Code, Codex CLI, OpenCode, GitHub Copilot, Cursor, Other.

.PARAMETER DryRun
  Print what would be done without making any changes.

.EXAMPLE
  .\install.ps1           interactive mode
  .\install.ps1 -DryRun   dry-run mode
#>

param([switch]$DryRun)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillSrc = Join-Path $ScriptDir "skills\cc-rsg"

if (-not (Test-Path $SkillSrc)) {
  Write-Host "Error: skills/cc-rsg/ not found alongside this script."
  Write-Host "Run this script from the root of the cc-rsg repository."
  exit 1
}

# ── Agent list ─────────────────────────────────────────────────────────
$AgentNames = @()
$AgentKeys  = @()

function Add-Agent($name, $key) {
  $script:AgentNames += $name
  $script:AgentKeys  += $key
}

Write-Host ""
Write-Host "cc-rsg installer v0.1.0"
Write-Host "========================="
Write-Host ""

Add-Agent "Claude Code" "claude"
Add-Agent "Codex CLI" "codex"
Add-Agent "OpenCode" "opencode"
Add-Agent "GitHub Copilot" "copilot"
Add-Agent "Cursor" "cursor"
Add-Agent "Other (.agents/skills/)" "other"

# ── Helper: install paths ─────────────────────────────────────────────
function Get-UserPath($key) {
  switch ($key) {
    "claude"   { return "$HOME\.claude\skills\cc-rsg" }
    "codex"    { return "$HOME\.codex\skills\cc-rsg" }
    "opencode" { return "$HOME\.opencode\skills\cc-rsg" }
    "copilot"  { return "$HOME\.copilot\skills\cc-rsg" }
    "cursor"   { return "$HOME\.cursor\skills\cc-rsg" }
    "other"    { return "$HOME\.agents\skills\cc-rsg" }
  }
}

function Get-ProjPath($key) {
  switch ($key) {
    "claude"   { return ".claude\skills\cc-rsg" }
    "codex"    { return ".codex\skills\cc-rsg" }
    "opencode" { return ".opencode\skills\cc-rsg" }
    "copilot"  { return ".github\skills\cc-rsg" }
    "cursor"   { return ".cursor\skills\cc-rsg" }
    "other"    { return ".agents\skills\cc-rsg" }
  }
}

# ── Helper: install ───────────────────────────────────────────────────
function Install-Skill($dest, $label) {
  if (-not $dest) { return }

  if ($DryRun) {
    Write-Host "  ⏺  $dest ($label)"
    return
  }

  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  Copy-Item -Recurse -Force "$SkillSrc\*" $dest
  Write-Host "  ✅ $dest ($label)"
}

# ── Select level ──────────────────────────────────────────────────────
Write-Host "Select install level:"
Write-Host "  1) User level (available for all projects)"
Write-Host "  2) Project level (this directory only)"
Write-Host "  3) Both"
$levelChoice = Read-Host "> "
Write-Host ""

$installUser = $true
$installProj = $false
if ($levelChoice -eq "2") { $installUser = $false; $installProj = $true }
if ($levelChoice -eq "3") { $installUser = $true;  $installProj = $true }

# ── Select agents ─────────────────────────────────────────────────────
Write-Host "Available agents:"
for (\$i = 0; \$i -lt \$AgentNames.Count; \$i++) {
  Write-Host ("  " + (\$i+1) + ") " + \$AgentNames[\$i])
}
Write-Host ""
Write-Host "Select agents to install (comma separated, e.g. 1,3,6):"
\$agentSel = Read-Host "> "
Write-Host ""

\$selectedIndices = @()
\$selNums = \$agentSel -split ',' | ForEach-Object { \$_.Trim() }
foreach (\$n in \$selNums) {
  \$idx = [int]\$n - 1
  if (\$idx -ge 0 -and \$idx -lt \$AgentNames.Count) {
    \$selectedIndices += \$idx
  }
}

# ── Install ───────────────────────────────────────────────────────────
Write-Host "Installing cc-rsg to:"
Write-Host ""

$installed = 0
foreach ($idx in $selectedIndices) {
  $key = $AgentKeys[$idx]
  $label = $AgentNames[$idx]

  if ($installUser) {
    $dest = Get-UserPath $key
    Install-Skill $dest $label
    $installed++
  }

  if ($installProj) {
    $dest = Get-ProjPath $key
    if ($dest) {
      Install-Skill $dest $label
      $installed++
    }
  }
}

Write-Host ""
if ($DryRun) {
  Write-Host "Dry-run complete. No changes were made."
} else {
  Write-Host "Done. cc-rsg is now installed."
}
Write-Host ""
