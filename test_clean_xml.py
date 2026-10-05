import openpyxl
import io
import zipfile

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Test"
ws.append(["Col1", "Col2"])
ws.append(["Val1", "Val2"])

buf = io.BytesIO()
wb.save(buf)
wb.close()
buf.seek(0)

with zipfile.ZipFile(buf, 'r') as z:
    print(z.read('xl/worksheets/sheet1.xml').decode('utf-8'))
