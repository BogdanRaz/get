# Визуализация пульсовой волны (лр5)

Источник методики: https://github.com/lalina0404-hub/get-labs (папка «Лабораторная работа 5»).

| Роль | Файл | Что делает |
| --- | --- | --- |
| экспериментатор | `bloodMeasure.py` (+ `mcp3021_driver.py`) | на Raspberry Pi: `python3 bloodMeasure.py "40 mmHg" 10`, `rest 90`, `fitness 90` -> `data/<имя>.txt` |
| программист | `bloodProcessing.py` | `python bloodProcessing.py` -> `plots/*.png`, `results.json`, печатает пульс и давление |
| руководитель | `build_report.py` | `python build_report.py`, затем `update_toc.py` -> `report.odt` |

В `data/` сейчас лежат записи с установки курса из стартового набора (Пример данных), не собственные.
Свои записи положить туда же с теми же именами, в `build_report.py` поставить `OWN_DATA = True`
и указать нагрузку в `LOAD_NOTE`, затем пересобрать отчёт.

Жёлтые пометки в `report.odt` - места для ручного заполнения (ФИО команды, фото установки в `photos/`: `setup.jpg`).
Обновить оглавление: `"C:\Program Files\LibreOffice\program\python.exe" update_toc.py`.
