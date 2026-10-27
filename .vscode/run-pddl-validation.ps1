$validator = 'C:\Users\Tanvi\.copilot\session-state\67491160-0083-4e79-aabb-cf4d2e6c02f7\files\val-win64\extract\bin\Val-20211204.1-win64\bin\Validate.exe'
$pddl = Join-Path $PSScriptRoot '..\PDDL'
$partAB = Join-Path $pddl 'PartA&B'
$partC = Join-Path $pddl 'PartC'

$missions = @(
    @{
        Name = 'Mission 1'
        Domain = Join-Path $partAB 'domain.pddl'
        Problem = Join-Path $partAB 'mission1.pddl'
        Plan = Join-Path $partAB 'mission1.pddl.soln'
    },
    @{
        Name = 'Mission 2'
        Domain = Join-Path $partAB 'domain.pddl'
        Problem = Join-Path $partAB 'mission2.pddl'
        Plan = Join-Path $partAB 'mission2.pddl.soln'
    },
    @{
        Name = 'Mission 3'
        Domain = Join-Path $partC 'domain-ext.pddl'
        Problem = Join-Path $partC 'mission3.pddl'
        Plan = Join-Path $partC 'mission3.pddl.soln'
    }
)

foreach ($mission in $missions) {
    Write-Output "=== $($mission.Name) ==="
    & $validator $mission.Domain $mission.Problem $mission.Plan
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
