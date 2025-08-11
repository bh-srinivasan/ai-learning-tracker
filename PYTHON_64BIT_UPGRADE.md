# Python 64-bit Upgrade for Windows

This directory contains PowerShell scripts to resolve the cryptography performance warning:

> "You are using cryptography on a 32-bit Python on a 64-bit Windows Operating System. Cryptography will be significantly faster if you switch to using a 64-bit Python."

## Files

- **`upgrade-python-64bit.ps1`** - Main upgrade script
- **`test-python-upgrade.ps1`** - Pre-upgrade system check script

## Quick Start

1. **Check current system state:**
   ```powershell
   .\test-python-upgrade.ps1
   ```

2. **Run the upgrade:**
   ```powershell
   .\upgrade-python-64bit.ps1
   ```

3. **Activate the new virtual environment:**
   ```powershell
   .\venv64\Scripts\activate
   ```

## Features

### Smart Detection
- ✅ Detects OS and Python architecture automatically
- ✅ Skips installation if 64-bit Python already exists
- ✅ Handles both user and admin installations
- ✅ Safe to re-run (idempotent)

### Robust Installation
- ✅ Downloads latest stable Python from python.org
- ✅ Silent installation with optimal settings
- ✅ Automatic PATH configuration
- ✅ No reboot required

### Virtual Environment Management
- ✅ Creates clean `venv64` virtual environment
- ✅ Automatically installs dependencies from `requirements.txt` or `pyproject.toml`
- ✅ Upgrades pip to latest version
- ✅ Preserves existing project structure

### Error Handling
- ✅ Comprehensive try/catch blocks
- ✅ Colored console output (success/warning/error)
- ✅ Detailed error messages
- ✅ Non-zero exit codes on failure

## Usage Examples

### Basic Usage
```powershell
# Check if upgrade is needed
.\test-python-upgrade.ps1

# Run upgrade
.\upgrade-python-64bit.ps1
```

### Advanced Options
```powershell
# Force reinstall even if 64-bit Python exists
.\upgrade-python-64bit.ps1 -Force

# Install specific Python version
.\upgrade-python-64bit.ps1 -PythonVersion "3.11.9"

# Combine options
.\upgrade-python-64bit.ps1 -Force -PythonVersion "3.12.0"
```

## Installation Behavior

### User Mode (Non-Admin)
- Installs Python to user profile directory
- Sets PATH for current user only
- Creates `venv64` in current directory

### Admin Mode (Elevated)
- Installs Python to `C:\Python` (system-wide)
- Sets PATH for all users
- Creates `venv64` in current directory

## Verification

After running the upgrade script, verify the installation:

```powershell
# Check Python architecture (should show 64bit)
python -c "import platform; print(platform.architecture()[0])"

# Test cryptography (should not show 32-bit warning)
python -c "import cryptography; print('Success')"

# Check virtual environment
.\venv64\Scripts\activate
python --version
pip --version
```

## Troubleshooting

### Script Execution Policy
If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Download Issues
- Ensure internet connectivity
- Check Windows Defender/antivirus settings
- Try running as administrator

### PATH Issues
- Close and reopen PowerShell after installation
- Check `where python` output
- Manually refresh PATH: `$env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")`

### Virtual Environment Issues
- Delete `venv64` folder and re-run script
- Ensure Python installation completed successfully
- Check Windows permissions

## Integration with Existing Projects

This script is designed to work with existing Python projects:

1. **Flask Applications** - Preserves your app structure and reinstalls dependencies
2. **Django Projects** - Maintains your project configuration
3. **Data Science Projects** - Reinstalls numpy, pandas, jupyter, etc.
4. **Any Python Project** - Works with `requirements.txt` or `pyproject.toml`

The script creates a new virtual environment but preserves your project files and automatically reinstalls dependencies, ensuring a smooth transition to 64-bit Python.

## Requirements

- Windows 10/11 (64-bit)
- PowerShell 5.1 or later
- Internet connectivity
- Administrator privileges (optional, for system-wide install)

## Safety Features

- ✅ Never modifies existing Python installations
- ✅ Creates new virtual environment (doesn't overwrite existing)
- ✅ Validates installation before proceeding
- ✅ Provides rollback information
- ✅ Safe to interrupt (no partial state corruption)
