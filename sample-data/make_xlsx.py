"""
Run this once to generate polaris-findings-demo.xlsx
Usage: python sample-data/make_xlsx.py
"""
import zipfile, io, os

rows = [
    ['Application','Project','Issue Type','Severity','Test Type','CWE ID','Location','Link'],
    ['MyApp','backend','SQL Injection','High','SAST','CWE-89','src/db/UserRepo.java:45','https://polaris.example.com/1'],
    ['MyApp','backend','Use of Hard-coded Credentials','Critical','SAST','CWE-798','src/config/AppConfig.java:12','https://polaris.example.com/2'],
    ['MyApp','frontend','Cross-site Scripting','High','SAST','CWE-79','src/views/ProfileView.js:87','https://polaris.example.com/3'],
    ['MyApp','infra','Path Traversal','High','SAST','CWE-22','src/api/FileController.java:33','https://polaris.example.com/4'],
    ['MyApp','backend','NULL Pointer Dereference','Medium','SAST','CWE-476','src/service/OrderService.java:61','https://polaris.example.com/5'],
    ['MyApp','backend','XXE Injection','High','SAST','CWE-611','src/parser/XmlParser.java:19','https://polaris.example.com/6'],
    ['MyApp','backend','Missing Authorization Check','High','SAST','CWE-862','src/api/AdminController.java:77','https://polaris.example.com/7'],
    ['MyApp','deps','Deserialization of Untrusted Data','Critical','SCA','CWE-502','pom.xml (commons-collections 3.1)','https://polaris.example.com/8'],
    ['MyApp','backend','Use of Broken Cryptographic Algorithm','Medium','SAST','CWE-327','src/util/CryptoUtil.java:24','https://polaris.example.com/9'],
    ['MyApp','infra','Server-Side Request Forgery','Critical','SAST','CWE-918','src/api/HttpClient.java:55','https://polaris.example.com/10'],
    ['MyApp','backend','SQL Injection','High','SAST','CWE-89','src/db/ProductRepo.java:112','https://polaris.example.com/11'],
    ['MyApp','frontend','Cross-site Scripting','Medium','SAST','CWE-79','src/components/SearchBar.js:34','https://polaris.example.com/12'],
    ['MyApp','backend','Improper Resource Shutdown','Medium','SAST','CWE-404','src/db/ConnectionPool.java:88','https://polaris.example.com/13'],
    ['MyApp','backend','Integer Overflow','High','SAST','CWE-190','src/util/MathHelper.java:17','https://polaris.example.com/14'],
    ['MyApp','backend','Exposure of Sensitive Information','Medium','SAST','CWE-200','src/api/ErrorHandler.java:55','https://polaris.example.com/15'],
]

def xml_cell(col_idx, row_idx, value):
    col_letter = chr(ord('A') + col_idx)
    cell_ref = f'{col_letter}{row_idx}'
    safe = str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return f'<c r="{cell_ref}" t="inlineStr"><is><t>{safe}</t></is></c>'

sheet_rows = ''
for ri, row in enumerate(rows, 1):
    cells = ''.join(xml_cell(ci, ri, v) for ci, v in enumerate(row))
    sheet_rows += f'<row r="{ri}">{cells}</row>'

sheet_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData>{sheet_rows}</sheetData>
</worksheet>'''

workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Findings" sheetId="1" r:id="rId1"/></sheets>
</workbook>'''

workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''

rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', content_types)
    z.writestr('_rels/.rels', rels)
    z.writestr('xl/workbook.xml', workbook_xml)
    z.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
    z.writestr('xl/worksheets/sheet1.xml', sheet_xml)

out = os.path.join(os.path.dirname(__file__), 'polaris-findings-demo.xlsx')
with open(out, 'wb') as f:
    f.write(buf.getvalue())

print(f'Created: {out}')
print(f'Findings: {len(rows)-1}  |  File size: {len(buf.getvalue())} bytes')
