
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $wb = $excel.Workbooks.Open("C:\Users\HP\Downloads\Test_Suite_US-101_US-103.xlsx")
    Write-Host "Excel COM opened file successfully!"
    $wb.Close($false)
} catch {
    Write-Host "Excel COM Exception: " $($_.Exception.Message)
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
