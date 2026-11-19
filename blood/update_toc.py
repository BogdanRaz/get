"""Обновляет оглавление (и номера рисунков) в report.odt через LibreOffice.

Запуск (интерпретатором из LibreOffice):
  "C:\\Program Files\\LibreOffice\\program\\python.exe" update_toc.py
Опционально: второй аргумент - путь для PDF-копии.
"""
import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue

here = os.path.dirname(os.path.abspath(__file__))
doc_path = os.path.join(here, 'report.odt')


def pv(n, v):
    p = PropertyValue()
    p.Name, p.Value = n, v
    return p


soffice = r'C:\Program Files\LibreOffice\program\soffice.exe'
proc = subprocess.Popen([soffice, '--headless', '--norestore',
                         '--accept=socket,host=localhost,port=2002;urp;'])
ctx = None
for _ in range(60):
    try:
        local = uno.getComponentContext()
        res = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
        ctx = res.resolve('uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext')
        break
    except Exception:
        time.sleep(1)
desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(doc_path), '_blank', 0, (pv('Hidden', True),))
idx = doc.getDocumentIndexes()
for i in range(idx.getCount()):
    idx.getByIndex(i).update()
doc.getTextFields().refresh()
doc.store()
if len(sys.argv) > 1:
    doc.storeToURL(uno.systemPathToFileUrl(sys.argv[1]),
                   (pv('FilterName', 'writer_pdf_Export'),))
doc.close(True)
try:
    desktop.terminate()
except Exception:
    pass
proc.wait(timeout=30)
print('Оглавление обновлено')
