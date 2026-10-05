$excel = New-Object -ComObject Excel.Application
$excel.DisplayAlerts = $false
try {
    $wb = $excel.Workbooks.Open("C:\Users\HP\Downloads\Test_Suite_US-001_US-102 (1).xlsx")
    Write-Host "Sheets count:" $wb.Sheets.Count
    foreach ($sh in $wb.Sheets) {
        Write-Host "Sheet: $($sh.Name) | Rows: $($sh.UsedRange.Rows.Count) | Cols: $($sh.UsedRange.Columns.Count)"
    }
    $wb.Close($false)
} catch {
    Write-Host "COM Open error: $($_.Exception.Message)"
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
