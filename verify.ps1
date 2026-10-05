param([string]$FilePath)
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $wb = $excel.Workbooks.Open($FilePath)
    Write-Host "SUCCESS: Opened $FilePath, Sheets: $($wb.Sheets.Count)"
    $wb.Close($false)
    exit 0
} catch {
    Write-Host "FAILED: $($_.Exception.Message)"
    exit 1
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
