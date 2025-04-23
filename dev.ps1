$ErrorActionPreference = "Stop"

# Set-PSDebug -Trace 1# Turn on debugging
Set-PSDebug -Trace 0 # Turn off debugging

$username = $env:USERNAME

if ($args) {
  if ($args[0] -eq "--help") {
    Write-Host "Usage: dev.ps1 [--fix] [format]"
    Write-Host "--fix: Run ruff check --fix"
    Write-Host "format: Run ruff format"
    exit
  }
}

if ($args) {
  if ($args[0] -eq "--fix") {
    Write-Host "Running ruff check --fix..."
    uv run ruff check --fix
  }
  if ($args[0] -eq "format" -or $args[1] -eq "format") {
    Write-Host "Running ruff format..."
    uv run ruff format
  }
  exit
}


if (Test-Path ".venv") {
    if(-not ($env:VIRTUAL_ENV -eq ".venv")) {
        Write-Host "Activating existing virtual environment..."
        . .venv\Scripts\activate
    } else {
        Write-Host "Virtual environment already activated."
    }
} else {
    Write-Host "$username, Bro you do not have a virtual environment set up yet. so i have to create one and then install the dependencies... such a pain in ass"
    Write-Host "while i am Creating a virtual environment...,you understand this when ever you have to  run ./dev.sh to run the server"
    uv venv
    . .venv\Scripts\activate
    uv sync
}

# Run FastAPI in development mode
# python app/main.py
# python -m fastapi dev app/main.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload