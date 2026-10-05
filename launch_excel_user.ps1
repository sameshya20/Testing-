$path = "$env:USERPROFILE\Downloads\Test_Suite_US-002 (1).xlsx"
if (-not (Test-Path $path)) {
    $path = "$env:USERPROFILE\Downloads\Test_Suite_US-002.xlsx"
}

Write-Host "Opening $path in Microsoft Excel on screen..."
Unblock-File -Path $path -ErrorAction SilentlyContinue

$excel = New-Object -ComObject Excel.Application
$excel.Visible = $true
$excel.DisplayAlerts = $true
$wb = $excel.Workbooks.Open($path)
Write-Host "Successfully opened in Microsoft Excel!"
Write-Host "Workbook: $($wb.Name)"
Write-Host "Sheets count: $($wb.Sheets.Count)"
foreach ($sh in $wb.Sheets) {
    Write-Host " - Sheet: $($sh.Name) | Rows: $($sh.UsedRange.Rows.Count)"
}
# Release COM reference without closing so the user can view it in Excel!
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
