"""Cross-platform utilities for the Agent Starter Pack CLI.

This module provides platform-specific functionality to ensure compatibility
across Windows, macOS, and Linux systems.
"""

import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path


def get_platform_info() -> tuple[str, str, str]:
    """Get detailed platform information.

    Returns:
        Tuple of (system, architecture, version)
    """
    return (platform.system(), platform.machine(), platform.version())


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def get_shell_command(command: str) -> list[str]:
    """Get platform-appropriate shell command.

    Args:
        command: The command to execute

    Returns:
        List of command parts for subprocess
    """
    if is_windows():
        return ["cmd", "/c", command]
    else:
        return ["sh", "-c", command]


def get_npm_install_command(frontend_dir: str) -> str:
    """Get platform-appropriate npm install command.

    Args:
        frontend_dir: Directory containing the frontend package.json

    Returns:
        Platform-appropriate npm install command
    """
    if is_windows():
        # Windows has issues with --prefix, use cd instead
        return f"cd {frontend_dir} && npm install"
    else:
        # Unix-like systems can use --prefix
        return f"npm --prefix {frontend_dir} install"


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    return shutil.which(command) is not None


def get_make_command() -> str | None:
    """Get the make command if available, with fallback suggestions.

    Returns:
        Make command if available, None otherwise
    """
    # Check for standard make commands
    make_commands = ["make", "gmake", "mingw32-make"]

    for cmd in make_commands:
        if check_command_exists(cmd):
            return cmd

    return None


def suggest_make_installation() -> str:
    """Provide platform-specific instructions for installing make.

    Returns:
        Installation instructions as a string
    """
    if is_windows():
        return """
Make is not available. To install make on Windows, use one of these options:

1. Using Chocolatey:
   choco install make

2. Using Winget:
   winget install GnuWin32.Make

3. Using Scoop:
   scoop install make

4. Using Visual Studio Build Tools (includes nmake):
   - Install Visual Studio Build Tools
   - Use 'nmake' instead of 'make'

5. Using WSL (Windows Subsystem for Linux):
   wsl --install
   # Then use make within WSL
"""
    elif is_macos():
        return """
Make is not available. To install make on macOS:

1. Install Xcode Command Line Tools:
   xcode-select --install

2. Using Homebrew:
   brew install make
"""
    else:  # Linux
        return """
Make is not available. To install make on Linux:

1. Ubuntu/Debian:
   sudo apt update && sudo apt install build-essential

2. CentOS/RHEL/Fedora:
   sudo yum install make
   # or
   sudo dnf install make

3. Arch Linux:
   sudo pacman -S make
"""


def run_cross_platform_command(
    command: str,
    cwd: Path | None = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command in a cross-platform way.

    Args:
        command: Command to run
        cwd: Working directory
        capture_output: Whether to capture output
        check: Whether to check return code

    Returns:
        CompletedProcess object

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
    """
    shell_cmd = get_shell_command(command)

    try:
        result = subprocess.run(
            shell_cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check,
            encoding="utf-8",
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}")
        logging.error(f"Error: {e.stderr if e.stderr else str(e)}")
        raise


def ensure_utf8_encoding() -> None:
    """Ensure UTF-8 encoding is used for file operations.

    This is particularly important on Windows where the default encoding
    might not be UTF-8.
    """
    if is_windows():
        # Set environment variables for UTF-8 on Windows
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        # For Python 3.7+ on Windows, this helps with console output
        if hasattr(os, "add_dll_directory"):
            os.environ.setdefault("PYTHONUTF8", "1")


def get_python_executable() -> str:
    """Get the current Python executable path.

    Returns:
        Path to the Python executable
    """
    import sys

    return sys.executable


def get_uv_command() -> str | None:
    """Get the uv command if available.

    Returns:
        Path to uv executable or None if not found
    """
    return shutil.which("uv")


def suggest_uv_installation() -> str:
    """Provide platform-specific instructions for installing uv.

    Returns:
        Installation instructions as a string
    """
    if is_windows():
        return """
uv is not available. To install uv on Windows:

1. Using PowerShell:
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

2. Using pip:
   pip install uv

3. Using Scoop:
   scoop install uv

4. Using Chocolatey:
   choco install uv
"""
    else:
        return """
uv is not available. To install uv:

1. Using the install script:
   curl -LsSf https://astral.sh/uv/install.sh | sh

2. Using pip:
   pip install uv

3. Using Homebrew (macOS):
   brew install uv

4. Using your package manager (Linux):
   # Check your distribution's package repository
"""


def create_platform_specific_scripts(project_path: Path) -> None:
    """Create platform-specific build scripts alongside Makefile.

    Args:
        project_path: Path to the project directory
    """
    # Create a batch file for Windows
    batch_content = """@echo off
REM Windows batch script for Agent Starter Pack

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if "%1"=="install" goto install
if "%1"=="playground" goto playground
if "%1"=="test" goto test
if "%1"=="lint" goto lint
goto help

:install
echo Installing dependencies...
uv sync --dev --extra jupyter --extra streamlit
if exist "frontend" (
    cd frontend && npm install && cd ..
)
goto end

:playground
echo Starting playground...
uv run streamlit run app/main.py
goto end

:test
echo Running tests...
uv run pytest tests/
goto end

:lint
echo Running linters...
uv run ruff check .
uv run mypy .
goto end

:help
echo Available commands:
echo   install    - Install dependencies
echo   playground - Start the development playground
echo   test       - Run tests
echo   lint       - Run linters
echo.
echo Usage: build.bat [command]
goto end

:end
"""

    # Create PowerShell script for Windows
    powershell_content = """# PowerShell script for Agent Starter Pack

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

switch ($Command) {
    "install" {
        Write-Host "Installing dependencies..." -ForegroundColor Green
        uv sync --dev --extra jupyter --extra streamlit
        if (Test-Path "frontend") {
            Set-Location frontend
            npm install
            Set-Location ..
        }
    }
    "playground" {
        Write-Host "Starting playground..." -ForegroundColor Green
        uv run streamlit run app/main.py
    }
    "test" {
        Write-Host "Running tests..." -ForegroundColor Green
        uv run pytest tests/
    }
    "lint" {
        Write-Host "Running linters..." -ForegroundColor Green
        uv run ruff check .
        uv run mypy .
    }
    default {
        Write-Host "Available commands:" -ForegroundColor Yellow
        Write-Host "  install    - Install dependencies"
        Write-Host "  playground - Start the development playground"
        Write-Host "  test       - Run tests"
        Write-Host "  lint       - Run linters"
        Write-Host ""
        Write-Host "Usage: ./build.ps1 [command]"
    }
}
"""

    try:
        # Write batch file
        batch_file = project_path / "build.bat"
        with open(batch_file, "w", encoding="utf-8") as f:
            f.write(batch_content)

        # Write PowerShell script
        ps_file = project_path / "build.ps1"
        with open(ps_file, "w", encoding="utf-8") as f:
            f.write(powershell_content)

        logging.info("Created platform-specific build scripts")

    except Exception as e:
        logging.warning(f"Failed to create platform-specific scripts: {e}")
