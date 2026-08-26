# Inicia o servidor OBS Controller API usando o ambiente virtual .venv

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Ambiente virtual nao encontrado em .venv. Criando..." -ForegroundColor Yellow
    python -m venv (Join-Path $RootDir ".venv")
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $RootDir "requirements.txt")
}

Set-Location $RootDir

Write-Host "Iniciando servidor..." -ForegroundColor Green
& $VenvPython (Join-Path $RootDir "main.py")
