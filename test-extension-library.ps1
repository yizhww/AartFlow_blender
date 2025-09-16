# AartFlow Extension Library Test Script
param(
    [string]$BaseUrl = "https://yizhww.github.io/AartFlow_blender"
)

Write-Host "Testing AartFlow Extension Library Accessibility" -ForegroundColor Green
Write-Host "Base URL: $BaseUrl" -ForegroundColor Cyan

# Test index.json file
Write-Host "`nTesting index.json..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/index.json" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "SUCCESS: index.json accessible" -ForegroundColor Green
        
        # Validate JSON format
        try {
            $jsonContent = $response.Content | ConvertFrom-Json
            Write-Host "SUCCESS: JSON format valid" -ForegroundColor Green
            Write-Host "Extension Library Info:" -ForegroundColor Cyan
            Write-Host "  - Name: $($jsonContent.data[0].name)" -ForegroundColor White
            Write-Host "  - Version: $($jsonContent.data[0].version)" -ForegroundColor White
        } catch {
            Write-Host "ERROR: JSON format invalid" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "ERROR: index.json not accessible - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`nTest completed!" -ForegroundColor Green
