import zipfile

with zipfile.ZipFile(r"C:\Users\HP\Downloads\Test_Suite_US-101_US-103.xlsx", 'r') as z:
    for info in z.infolist():
        print(f"{info.filename}: compress_type={info.compress_type}, file_size={info.file_size}, compress_size={info.compress_size}")
