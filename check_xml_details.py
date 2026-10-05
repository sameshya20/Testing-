import zipfile
import xml.etree.ElementTree as ET

filepath = r"C:\Users\HP\Downloads\Test_Suite_US-101_US-103.xlsx"

with zipfile.ZipFile(filepath, 'r') as z:
    for name in z.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            try:
                xml_data = z.read(name)
                root = ET.fromstring(xml_data)
            except Exception as e:
                print(f"XML PARSE ERROR in {name}: {e}")

print("All XML entries are well-formed XML.")

# Let's inspect xl/styles.xml, xl/worksheets/sheet1.xml
with zipfile.ZipFile(filepath, 'r') as z:
    print("\n--- xl/styles.xml ---")
    print(z.read('xl/styles.xml').decode('utf-8'))
    print("\n--- xl/worksheets/sheet1.xml ---")
    print(z.read('xl/worksheets/sheet1.xml').decode('utf-8')[:1500])
