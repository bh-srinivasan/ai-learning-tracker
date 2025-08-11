#Requires -Version 5.1
<#
.SYNOPSIS
    Upgrades Python to 64-bit on Windows systems to resolve cryptography performance warnings.

.DESCRIPTION
    This script detects the current Python architecture and upgrades to 64-bit Python if needed.
    It handles both user and admin installs, creates a clean virtual environment, and reinstalls
    dependencies from requirements.txt or pyproject.toml.

.EXAMPLE
    .\upgrade-python-64bit.ps1
    
.NOTES
    Safe to re-run. Skips installation if 64-bit Python is already installed.
    Does not require reboot.
#>

param(
    [switch]$Force,  # Force reinstall even if 64-bit Python exists
    [string]$PythonVersion = "latest"  # Specific version or "latest"
)

# Color output functions
function Write-Header { param($Text) Write-Host "`n=== $Text ===" -ForegroundColor Cyan }
function Write-Success { param($Text) Write-Host "[SUCCESS] $Text" -ForegroundColor Green }
function Write-Warning { param($Text) Write-Host "[WARNING] $Text" -ForegroundColor Yellow }
function Write-Error { param($Text) Write-Host "[ERROR] $Text" -ForegroundColor Red }
function Write-Info { param($Text) Write-Host "[INFO] $Text" -ForegroundColor Blue }

# Global variables for tracking
$script:OSArch = ""
$script:OldPythonArch = ""
$script:NewPythonPath = ""
$script:VenvPath = ""
$script:IsElevated = $false

function Test-IsElevated {
    try {
        $principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
        return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    catch {
        return $false
    }
}

function Get-OSArchitecture {
    try {
        $arch = (Get-WmiObject -Class Win32_Processor | Select-Object -First 1).Architecture
        switch ($arch) {
            0 { return "x86" }
            5 { return "ARM" }
            6 { return "IA64" }
            9 { return "x64" }
            12 { return "ARM64" }
            default { return "Unknown" }
        }
    }
    catch {
        # Fallback method
        if ($env:PROCESSOR_ARCHITECTURE -eq "AMD64" -or $env:PROCESSOR_ARCHITEW6432 -eq "AMD64") {
            return "x64"
        }
        elseif ($env:PROCESSOR_ARCHITECTURE -eq "ARM64" -or $env:PROCESSOR_ARCHITEW6432 -eq "ARM64") {
            return "ARM64"
        }
        else {
            return "x86"
        }
    }
}

function Get-PythonArchitecture {
    try {
        $pythonCheck = python -c "import platform; print(platform.architecture()[0])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $pythonCheck) {
            return $pythonCheck.Trim()
        }
        return $null
    }
    catch {
        return $null
    }
}

function Get-LatestPythonVersion {
    try {
        Write-Info "Fetching latest Python version from python.org..."
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/python/cpython/releases/latest" -TimeoutSec 30
        $version = $response.tag_name -replace '^v', ''
        Write-Success "Latest Python version: $version"
        return $version
    }
    catch {
        Write-Warning "Could not fetch latest version, using fallback: 3.11.9"
        return "3.11.9"
    }
}

function Get-PythonInstaller {
    param(
        [string]$Version,
        [string]$Architecture = "amd64"
    )
    
    try {
        Write-Info "Downloading Python $Version ($Architecture)..."
        
        # Construct download URL
        $filename = "python-$Version-$Architecture.exe"
        $url = "https://www.python.org/ftp/python/$Version/$filename"
        $downloadPath = Join-Path $env:TEMP $filename
        
        # Remove existing file if present
        if (Test-Path $downloadPath) {
            Remove-Item $downloadPath -Force
        }
        
        # Download with progress
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($url, $downloadPath)
        $webClient.Dispose()
        
        if (Test-Path $downloadPath) {
            $size = [math]::Round((Get-Item $downloadPath).Length / 1MB, 2)
            Write-Success "Downloaded $filename ($size MB)"
            return $downloadPath
        }
        else {
            throw "Download failed - file not found at $downloadPath"
        }
    }
    catch {
        Write-Error "Failed to download Python: $($_.Exception.Message)"
        throw
    }
}

function Invoke-PythonInstaller {
    param(
        [string]$InstallerPath,
        [bool]$AllUsers = $false
    )
    
    try {
        Write-Info "Installing Python ($(if($AllUsers){'All Users'}else{'Current User'}))..."
        
        # Prepare installer arguments
        $installArgs = @(
            "/quiet"
            "PrependPath=1"
            "Include_test=0"
            "SimpleInstall=1"
            "Include_launcher=0"  # Avoid launcher conflicts
        )
        
        if ($AllUsers) {
            $installArgs += "InstallAllUsers=1"
            $installArgs += "DefaultAllUsersTargetDir=C:\Python"
        }
        else {
            $installArgs += "InstallAllUsers=0"
        }
        
        # Run installer
        $process = Start-Process -FilePath $InstallerPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-Success "Python installation completed successfully"
            
            # Clean up installer
            Remove-Item $InstallerPath -Force -ErrorAction SilentlyContinue
            
            # Refresh PATH in current session
            $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
            
            return $true
        }
        else {
            throw "Installer failed with exit code: $($process.ExitCode)"
        }
    }
    catch {
        Write-Error "Failed to install Python: $($_.Exception.Message)"
        throw
    }
}

function Test-PythonInstallation {
    try {
        Write-Info "Verifying Python installation..."
        
        # Wait a moment for PATH to update
        Start-Sleep -Seconds 2
        
        # Test python command
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Python command not found in PATH"
        }
        
        # Test architecture
        $archCheck = python -c "import platform; print(platform.architecture()[0], platform.python_version())" 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Python architecture check failed"
        }
        
        $pythonPath = where.exe python 2>$null | Select-Object -First 1
        $script:NewPythonPath = $pythonPath
        
        Write-Success "Python verification successful:"
        Write-Host "  Version: $pythonVersion" -ForegroundColor White
        Write-Host "  Architecture: $archCheck" -ForegroundColor White
        Write-Host "  Path: $pythonPath" -ForegroundColor White
        
        return $archCheck.Contains("64bit")
    }
    catch {
        Write-Error "Python verification failed: $($_.Exception.Message)"
        return $false
    }
}

function New-PythonVirtualEnvironment {
    param(
        [string]$VenvName = "venv64"
    )
    
    try {
        Write-Header "Creating Virtual Environment"
        
        $venvPath = Join-Path (Get-Location) $VenvName
        $script:VenvPath = $venvPath
        
        # Remove existing venv if present
        if (Test-Path $venvPath) {
            Write-Info "Removing existing virtual environment..."
            Remove-Item $venvPath -Recurse -Force
        }
        
        # Create new virtual environment
        Write-Info "Creating virtual environment: $VenvName"
        
        # Use cmd to run python venv (sometimes PowerShell has issues with Start-Process)
        $venvCommand = "python -m venv `"$venvPath`""
        $result = cmd /c $venvCommand
        
        # Check if the virtual environment was created successfully
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        if (-not (Test-Path $activateScript)) {
            throw "Virtual environment creation failed - Activate.ps1 not found at $activateScript"
        }
        
        # Activate virtual environment and upgrade pip
        Write-Info "Activating virtual environment..."
        & $activateScript
        
        Write-Info "Upgrading pip..."
        python -m pip install --upgrade pip --quiet
        
        Write-Success "Virtual environment created and activated"
        return $true
    }
    catch {
        Write-Error "Failed to create virtual environment: $($_.Exception.Message)"
        throw
    }
}

function Install-PythonDependencies {
    try {
        Write-Header "Installing Dependencies"
        
        $requirementsFile = "requirements.txt"
        $pyprojectFile = "pyproject.toml"
        
        if (Test-Path $requirementsFile) {
            Write-Info "Found requirements.txt - installing dependencies..."
            $process = Start-Process -FilePath "python" -ArgumentList "-m", "pip", "install", "-r", $requirementsFile -Wait -PassThru -NoNewWindow
            
            if ($process.ExitCode -eq 0) {
                Write-Success "Dependencies installed from requirements.txt"
            }
            else {
                Write-Warning "Some dependencies may have failed to install (exit code: $($process.ExitCode))"
            }
        }
        elseif (Test-Path $pyprojectFile) {
            Write-Info "Found pyproject.toml - attempting to install..."
            
            # Try with current directory install
            $process = Start-Process -FilePath "python" -ArgumentList "-m", "pip", "install", "." -Wait -PassThru -NoNewWindow
            
            if ($process.ExitCode -eq 0) {
                Write-Success "Dependencies installed from pyproject.toml"
            }
            else {
                Write-Warning "Failed to install from pyproject.toml (exit code: $($process.ExitCode))"
            }
        }
        else {
            Write-Info "No requirements.txt or pyproject.toml found - skipping dependency installation"
        }
    }
    catch {
        Write-Warning "Error during dependency installation: $($_.Exception.Message)"
    }
}

function Write-FinalSummary {
    Write-Header "Installation Summary"
    
    try {
        # Get current Python info
        $pythonVersion = python --version 2>$null
        $pipVersion = python -m pip --version 2>$null
        $pythonPath = where.exe python 2>$null | Select-Object -First 1
        
        Write-Host "System Information:" -ForegroundColor Cyan
        Write-Host "  OS Architecture: $script:OSArch" -ForegroundColor White
        if ($script:OldPythonArch) {
            Write-Host "  Previous Python: $script:OldPythonArch" -ForegroundColor White
        }
        Write-Host "  Current Python: $pythonVersion" -ForegroundColor White
        Write-Host "  Python Path: $pythonPath" -ForegroundColor White
        Write-Host "  Pip Version: $pipVersion" -ForegroundColor White
        
        if ($script:VenvPath) {
            Write-Host "  Virtual Environment: $script:VenvPath" -ForegroundColor White
            Write-Host "" -ForegroundColor White
            Write-Host "To activate virtual environment later:" -ForegroundColor Yellow
            Write-Host "  .\venv64\Scripts\activate" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Success "Python upgrade completed successfully!"
        Write-Info "The cryptography performance warning should now be resolved."
    }
    catch {
        Write-Warning "Could not gather final system information: $($_.Exception.Message)"
    }
}

# Main execution
try {
    Write-Header "Python 64-bit Upgrade Script"
    
    # Detect system architecture
    $script:OSArch = Get-OSArchitecture
    $script:IsElevated = Test-IsElevated
    
    Write-Info "OS Architecture: $script:OSArch"
    Write-Info "Running as: $(if($script:IsElevated){'Administrator'}else{'User'})"
    
    if ($script:OSArch -ne "x64") {
        Write-Error "This script requires a 64-bit Windows system"
        exit 1
    }
    
    # Check current Python
    $script:OldPythonArch = Get-PythonArchitecture
    
    if ($script:OldPythonArch) {
        Write-Info "Current Python Architecture: $script:OldPythonArch"
        
        if ($script:OldPythonArch -eq "64bit" -and -not $Force) {
            Write-Success "64-bit Python is already installed"
            
            # Still create/update virtual environment
            New-PythonVirtualEnvironment
            Install-PythonDependencies
            Write-FinalSummary
            exit 0
        }
    }
    else {
        Write-Info "Python not found in PATH"
    }
    
    # Determine Python version to install
    $versionToInstall = if ($PythonVersion -eq "latest") { 
        Get-LatestPythonVersion 
    } else { 
        $PythonVersion 
    }
    
    # Download and install Python
    Write-Header "Installing 64-bit Python"
    
    $installerPath = Get-PythonInstaller -Version $versionToInstall -Architecture "amd64"
    Invoke-PythonInstaller -InstallerPath $installerPath -AllUsers $script:IsElevated
    
    # Verify installation
    if (-not (Test-PythonInstallation)) {
        Write-Error "Python installation verification failed"
        exit 1
    }
    
    # Create virtual environment and install dependencies
    New-PythonVirtualEnvironment
    Install-PythonDependencies
    
    # Final summary
    Write-FinalSummary
    
    Write-Success "All operations completed successfully!"
    exit 0
}
catch {
    Write-Error "Script execution failed: $($_.Exception.Message)"
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}
finally {
    # Cleanup any temporary files
    Get-ChildItem $env:TEMP -Filter "python-*.exe" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
}
