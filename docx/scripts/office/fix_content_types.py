import zipfile, shutil, os, re

src = r"C:\Users\59620\Downloads\doc-converter_zh_template.docx"
tmp = src + ".tmp"

with zipfile.ZipFile(src, 'r') as zin:
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == '[Content_Types].xml':
                xml = data.decode('utf-8')
                # Add missing Default extensions if not present
                if 'Extension="png"' not in xml:
                    xml = xml.replace(
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n  <Default Extension="png" ContentType="image/png"/>'
                    )
                if 'Extension="jpg"' not in xml and 'Extension="jpeg"' not in xml:
                    xml = xml.replace(
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
                        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n  <Default Extension="jpg" ContentType="image/jpeg"/>'
                    )
                data = xml.encode('utf-8')
            zout.writestr(item, data)

shutil.move(tmp, src)
print("Fixed Content_Types.xml")