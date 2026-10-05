$downloads = Join-Path $env:USERPROFILE "Downloads"
$latestDownload = Get-ChildItem -Path $downloads -Filter "Test_Suite_*.xlsx" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestDownload) {
    $path = $latestDownload.FullName
} else {
    $path = "D:\3rd uc\backend\real_export.xlsx"
}

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    Write-Host "Opening $path in Microsoft Excel..."
    $wb = $excel.Workbooks.Open($path)
    Write-Host "SUCCESS: Opened $(Split-Path $path -Leaf) in Microsoft Excel!"
    Write-Host "Sheet count: $($wb.Sheets.Count)"
    foreach ($sh in $wb.Sheets) {
        Write-Host "Sheet: $($sh.Name), Rows: $($sh.UsedRange.Rows.Count), Cols: $($sh.UsedRange.Columns.Count)"
    }
    $wb.Close($false)
    $excel.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
} catch {
    Write-Host "FAILED to open in Excel: $($_.Exception.Message)"
}
