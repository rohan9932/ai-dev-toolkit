[CmdletBinding()]
param(
    [string]$Destination, [string]$Preset, [string]$Style, [string]$Team,
    [string]$Brief, [string]$Audience, [string]$Database, [string[]]$Integrations,
    [string[]]$AddSkill, [string[]]$RemoveSkill, [string]$Config,
    [string]$Name, [string]$ProjectsRoot, [string[]]$Capabilities, [string]$Harness,
    [switch]$NonInteractive, [switch]$DryRun, [switch]$Yes, [switch]$List, [switch]$AllowScreened
)
$ErrorActionPreference='Stop'
$pythonCommand = Get-Command python -ErrorAction Stop
$arguments = @((Join-Path $PSScriptRoot 'init-project.py'))
$mapping = @{ Destination='destination'; Preset='preset'; Style='style'; Team='team'; Brief='brief'; Audience='audience'; Database='database'; Config='config'; Integrations='integrations'; AddSkill='add-skills'; RemoveSkill='remove-skills' }
$mapping.Name='name'; $mapping.ProjectsRoot='projects-root'; $mapping.Capabilities='capabilities'
$mapping.Harness='harness'
foreach ($key in $mapping.Keys) {
    if ($PSBoundParameters.ContainsKey($key)) {
        $arguments += ('--'+$mapping[$key])
        $arguments += ($PSBoundParameters[$key] -join ',')
    }
}
foreach ($pair in @(@('NonInteractive','noninteractive'),@('DryRun','dry-run'),@('Yes','yes'),@('List','list'),@('AllowScreened','allow-screened'))) {
    if ($PSBoundParameters[$pair[0]]) { $arguments += '--'+$pair[1] }
}
& $pythonCommand.Source @arguments
if ($LASTEXITCODE -ne 0) { throw "Project initialization failed (exit $LASTEXITCODE)." }
