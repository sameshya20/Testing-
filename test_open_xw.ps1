
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $wb = $excel.Workbooks.Open("D:\3rd uc\test_xlsxwriter.xlsx")
    Write-Host "Excel COM opened xlsxwriter file successfully!"
    $wb.Close($false)
} catch {
    Write-Host "Error: " $_.Exception.Message
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
