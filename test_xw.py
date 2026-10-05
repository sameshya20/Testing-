import io
import xlsxwriter
import subprocess

out = io.BytesIO()
wb = xlsxwriter.Workbook(out, {'in_memory': True})
ws = wb.add_worksheet('Positive')

header_format = wb.add_format({
    'bold': True,
    'font_name': 'Calibri',
    'font_size': 11,
    'font_color': '#FFFFFF',
    'bg_color': '#1E293B',
    'align': 'center',
    'valign': 'vcenter',
    'border': 1,
    'border_color': '#E2E8F0',
    'text_wrap': True
})

ws.write_row(0, 0, ['Test Case ID', 'User Story', 'Acceptance Criteria'], header_format)
ws.freeze_panes(1, 0)
ws.autofilter(0, 0, 10, 2)
wb.close()
out.seek(0)

with open('test_xlsxwriter.xlsx', 'wb') as f:
    f.write(out.getvalue())

print("Created test_xlsxwriter.xlsx, size:", len(out.getvalue()))

ps_script = '''
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $wb = $excel.Workbooks.Open("D:\\3rd uc\\test_xlsxwriter.xlsx")
    Write-Host "Excel COM opened xlsxwriter file successfully!"
    $wb.Close($false)
} catch {
    Write-Host "Error: " $_.Exception.Message
} finally {
    $excel.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
}
'''
with open("test_open_xw.ps1", "w") as f:
    f.write(ps_script)

res = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "test_open_xw.ps1"], capture_output=True, text=True)
print(res.stdout)
