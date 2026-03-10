# PowerShell Deployment Script for Vultr
# Run this from PowerShell on Windows

$SERVER_IP = "139.84.133.1"
$SERVER_USER = "root"
$APP_DIR = "/root/ytz-automation"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "YTZ Automation - Vultr Deployment" -ForegroundColor Cyan
Write-Host "Server: $SERVER_IP" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we have the necessary files
$requiredFiles = @("main.py", "requirements.txt", "src", "frontend", "deploy")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Missing required files/directories:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

# Create deployment directory
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$deployDir = "deploy_package_$timestamp"

Write-Host "Step 1: Creating deployment package..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $deployDir -Force | Out-Null

# Copy files
Write-Host "  - Copying backend files..." -ForegroundColor Gray
Copy-Item -Path "src" -Destination "$deployDir\src" -Recurse -Force
Copy-Item -Path "main.py" -Destination "$deployDir\" -Force
Copy-Item -Path "requirements.txt" -Destination "$deployDir\" -Force

if (Test-Path ".env") {
    Copy-Item -Path ".env" -Destination "$deployDir\" -Force
    Write-Host "  - Copied .env file" -ForegroundColor Green
}

if (Test-Path "secrets") {
    Copy-Item -Path "secrets" -Destination "$deployDir\secrets" -Recurse -Force
    Write-Host "  - Copied secrets directory" -ForegroundColor Green
}

Write-Host "  - Copying frontend files..." -ForegroundColor Gray
Copy-Item -Path "frontend" -Destination "$deployDir\frontend" -Recurse -Force

Write-Host "  - Copying deployment scripts..." -ForegroundColor Gray
Copy-Item -Path "deploy" -Destination "$deployDir\deploy" -Recurse -Force

Write-Host "  ✅ Deployment package created: $deployDir" -ForegroundColor Green

# Instructions for upload
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Upload the package to Vultr server:" -ForegroundColor Yellow
Write-Host "   scp -r $deployDir ${SERVER_USER}@${SERVER_IP}:$APP_DIR" -ForegroundColor White
Write-Host ""
Write-Host "2. SSH into the server and run setup:" -ForegroundColor Yellow
Write-Host "   ssh ${SERVER_USER}@${SERVER_IP}" -ForegroundColor White
Write-Host "   cd $APP_DIR" -ForegroundColor White
Write-Host "   bash deploy/vultr-setup.sh" -ForegroundColor White
Write-Host ""
Write-Host "OR use WinSCP/FileZilla to upload the '$deployDir' folder" -ForegroundColor Cyan
Write-Host ""

# Try to use SCP if available
Write-Host "Attempting to upload via SCP..." -ForegroundColor Yellow
try {
    $scpCommand = "scp -r $deployDir ${SERVER_USER}@${SERVER_IP}:$APP_DIR"
    Write-Host "Running: $scpCommand" -ForegroundColor Gray
    
    # Note: This requires SSH client to be installed on Windows
    # Available by default on Windows 10/11
    Invoke-Expression $scpCommand
    
    Write-Host "✅ Files uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now running setup on server..." -ForegroundColor Yellow
    
    $sshCommand = "ssh ${SERVER_USER}@${SERVER_IP} 'cd $APP_DIR && bash deploy/vultr-setup.sh'"
    Invoke-Expression $sshCommand
    
} catch {
    Write-Host "⚠️  Automatic upload failed. Please upload manually." -ForegroundColor Yellow
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual upload instructions above ⬆️" -ForegroundColor Cyan
}
