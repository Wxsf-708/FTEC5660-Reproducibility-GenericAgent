# FTEC5660 Reproducibility - one-command experiment runner
#
# The ONLY modification studied in this report is the sampling temperature.
#   baseline     :  .\experiments\run_experiment.ps1 -Label baseline -Temperature 1.0
#   modification :  .\experiments\run_experiment.ps1 -Label temp0
#                   (default temperature is 0.0 after the modification commit)
#
# All other settings (tasks, repeats, grader, model, prompts) are held fixed.
param(
    [double]$Temperature = 1.0,
    [string]$Label       = "baseline",
    [int]$Repeats        = 5
)

$ErrorActionPreference = "Stop"
& .\.venv\Scripts\python.exe scripts\run_benchmark.py `
    --label $Label `
    --tasks teb_01,teb_02,teb_06,teb_07,teb_08 `
    --repeats $Repeats `
    --temperature $Temperature
