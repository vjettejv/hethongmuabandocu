# Script to package the KienTrucPM project excluding heavy/unnecessary folders
$sourceDir = "d:\workspacecuachjp\KienTrucPM"
$zipFile = "d:\workspacecuachjp\KienTrucPM_Export.zip"

Write-Host "Cleaning up old zip..."
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

Write-Host "Creating zip file (this might take a few minutes)..."
Write-Host "Excluding node_modules to save space..."

# Get all files and folders EXCEPT node_modules and .git
$itemsToZip = Get-ChildItem -Path $sourceDir -Recurse | Where-Object {
    $_.FullName -notmatch "\\node_modules\\" -and
    $_.FullName -notmatch "\\\.git\\" -and
    $_.Name -ne "node_modules" -and
    $_.Name -ne ".git" -and
    $_.FullName -ne $zipFile
}

Compress-Archive -Path $itemsToZip.FullName -DestinationPath $zipFile -Force

Write-Host "Done! Your project is packaged at: $zipFile"
Write-Host "You can now send this ZIP file to others."
