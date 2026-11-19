"""Сборка отчёта report.odt в оформлении образца (template.odt).

Запуск:  python build_report.py
Использует results.json и plots/*.png (создаёт bloodProcessing.py), фото из photos/
(setup.jpg, work1.jpg, work2.jpg) и скрипты для раздела «Код программы».
Всё, чего нет, остаётся в отчёте ЖЁЛТОЙ пометкой [[...]] - её нужно заменить вручную.
Затем обновить оглавление:  "C:\\Program Files\\LibreOffice\\program\\python.exe" update_toc.py
"""
import json
import os
import re
import struct
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'template.odt')
OUT = os.path.join(HERE, 'report.odt')

AUTHORS = ['Богдан Разгулов', '[[ФИО остальных участников команды]]']
TITLE = 'Лабораторная работа «Визуализация пульсовой волны»'
CITY_YEAR = 'Долгопрудный, 2026'

# Откуда данные. Если сняли свои записи - поставьте OWN_DATA = True и опишите нагрузку.
OWN_DATA = False
LOAD_NOTE = '30 быстрых приседаний'

RES = None
if os.path.exists(os.path.join(HERE, 'results.json')):
    RES = json.load(open(os.path.join(HERE, 'results.json'), encoding='utf-8'))

pictures = {}
counter = {'fig': 0, 'tab': 0, 'img': 0}
table_styles = {}


# ---------------------------------------------------------------- разметка
def T(s):
    out = ''
    for part in re.split(r'(\[\[.*?\]\])', s):
        if part.startswith('[[') and part.endswith(']]'):
            out += '<text:span text:style-name="Thl">[%s]</text:span>' % escape(part[2:-2])
        else:
            out += escape(part)
    return out


def p(s):
    return '<text:p text:style-name="P13">%s</text:p>' % T(s)


def h1(s, numbered=True, page_break=False):
    if not numbered:
        st = 'P10' if page_break else 'Заголовок_20_1_20_без_20_номера'
    else:
        st = 'P12'
    return '<text:h text:style-name="%s" text:outline-level="1">%s</text:h>' % (st, T(s))


def h2(s):
    return '<text:h text:style-name="P14" text:outline-level="2">%s</text:h>' % T(s)


def ul(items):
    out = '<text:list text:style-name="L1">'
    for i, it in enumerate(items):
        st = 'P19' if i == len(items) - 1 else 'P18'
        out += '<text:list-item><text:p text:style-name="%s">%s</text:p></text:list-item>' % (st, T(it))
    return out + '</text:list>'


def formula(text, num):
    return '<text:p text:style-name="Pformula"><text:tab/>%s<text:tab/>(%d)</text:p>' % (T(text), num)


def code(path):
    src = open(path, encoding='utf-8').read().rstrip().split('\n')
    out = ''
    for line in src:
        e = escape(line.rstrip().replace('\t', '    '))
        e = re.sub(r'^( +)', lambda m: '<text:s text:c="%d"/>' % len(m.group(1)), e)
        e = re.sub(r'  +', lambda m: ' <text:s text:c="%d"/>' % (len(m.group(0)) - 1), e)
        out += '<text:p text:style-name="Pcode">%s</text:p>' % e
    return out + '<text:p text:style-name="P13"/>'


def img_size(path):
    with open(path, 'rb') as f:
        h = f.read(32)
        if h[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', h[16:24])
        f.seek(2)
        while True:
            m = f.read(4)
            if m[0] != 0xFF:
                return (4, 3)
            if m[1] in (0xC0, 0xC2):
                d = f.read(5)
                return struct.unpack('>HH', d[3:5])[::-1]
            f.seek(struct.unpack('>H', m[2:4])[0] - 2, 1)


def figure(path, caption, width_cm=14.0):
    counter['fig'] += 1
    n = counter['fig']
    cap = ('<text:p text:style-name="Pcap">Рисунок <text:sequence text:ref-name="refDrawing%d" '
           'text:name="Drawing" text:formula="ooow:Drawing+1" style:num-format="1">%d</text:sequence>'
           ' - %s</text:p>' % (n - 1, n, T(caption)))
    if path and os.path.exists(path):
        counter['img'] += 1
        ext = os.path.splitext(path)[1].lower()
        arc = 'Pictures/img%d%s' % (counter['img'], ext)
        pictures[arc] = path
        w, hh = img_size(path)
        mime = 'image/png' if ext == '.png' else 'image/jpeg'
        body_ = ('<text:p text:style-name="Pimg"><draw:frame draw:style-name="fr2" draw:name="Изображение%d" '
                 'text:anchor-type="as-char" svg:width="%.3fcm" svg:height="%.3fcm" draw:z-index="%d">'
                 '<draw:image xlink:href="%s" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad" '
                 'draw:mime-type="%s"/></draw:frame></text:p>' % (n, width_cm, width_cm * hh / w, n, arc, mime))
    else:
        body_ = '<text:p text:style-name="Pimg">%s</text:p>' % T(
            '[[Здесь будет фото: %s]]' % os.path.basename(path or 'фото'))
    return body_ + cap


def table(caption, header, rows, widths, left=False):
    counter['tab'] += 1
    n = counter['tab']
    out = ('<text:p text:style-name="Ptabcap">Таблица <text:sequence text:ref-name="refTable%d" '
           'text:name="Table" text:formula="ooow:Table+1" style:num-format="1">%d</text:sequence> - %s</text:p>'
           % (n - 1, n, T(caption)))
    out += '<table:table table:name="Таблица%d" table:style-name="Ttab%d">' % (n, n)
    for i in range(len(widths)):
        out += '<table:table-column table:style-name="Ttab%d.C%d"/>' % (n, i)
    for ri, row in enumerate([header] + rows):
        out += '<table:table-row>'
        for c in row:
            st = 'Tcellh' if ri == 0 else 'Tcell'
            pst = 'Ptabh' if ri == 0 else 'Ptab'
            out += ('<table:table-cell table:style-name="%s" office:value-type="string">'
                    '<text:p text:style-name="%s">%s</text:p></table:table-cell>' % (st, pst, T(str(c))))
        out += '</table:table-row>'
    out += '</table:table><text:p text:style-name="P13"/>'
    table_styles[n] = widths
    return out


def extra_styles():
    return (
        '<style:style style:name="Thl" style:family="text"><style:text-properties fo:background-color="#ffff00"/></style:style>'
        '<style:style style:name="Pcap" style:family="paragraph" style:parent-style-name="Text_20_body">'
        '<style:paragraph-properties fo:text-align="center" fo:margin-top="0cm" fo:margin-bottom="0.5cm" '
        'fo:text-indent="0cm" style:auto-text-indent="false"/></style:style>'
        '<style:style style:name="Ptabcap" style:family="paragraph" style:parent-style-name="Text_20_body">'
        '<style:paragraph-properties fo:text-align="start" fo:margin-top="0cm" fo:margin-bottom="0.2cm" '
        'fo:text-indent="0cm" style:auto-text-indent="false" fo:keep-with-next="always"/></style:style>'
        '<style:style style:name="Pimg" style:family="paragraph" style:parent-style-name="Text_20_body">'
        '<style:paragraph-properties fo:text-align="center" fo:margin-top="0cm" fo:margin-bottom="0.2cm" '
        'fo:text-indent="0cm" style:auto-text-indent="false" fo:keep-with-next="always"/></style:style>'
        '<style:style style:name="Pformula" style:family="paragraph" style:parent-style-name="Text_20_body">'
        '<style:paragraph-properties fo:text-align="center" fo:text-indent="0cm" style:auto-text-indent="false" '
        'fo:margin-top="0cm" fo:margin-bottom="0.3cm"><style:tab-stops>'
        '<style:tab-stop style:position="8.5cm" style:type="center"/>'
        '<style:tab-stop style:position="17cm" style:type="right"/></style:tab-stops></style:paragraph-properties></style:style>'
        '<style:style style:name="Pcode" style:family="paragraph" style:parent-style-name="Standard">'
        '<style:paragraph-properties fo:text-align="start" fo:margin-top="0cm" fo:margin-bottom="0cm" '
        'fo:line-height="100%" fo:text-indent="0cm" style:auto-text-indent="false"/>'
        '<style:text-properties style:font-name="Liberation Mono" fo:font-size="8pt"/></style:style>'
        '<style:style style:name="Ptab" style:family="paragraph" style:parent-style-name="Standard">'
        '<style:paragraph-properties fo:text-align="start" fo:text-indent="0cm" style:auto-text-indent="false"/>'
        '<style:text-properties fo:font-size="12pt"/></style:style>'
        '<style:style style:name="Ptabh" style:family="paragraph" style:parent-style-name="Standard">'
        '<style:paragraph-properties fo:text-align="center" fo:text-indent="0cm" style:auto-text-indent="false"/>'
        '<style:text-properties fo:font-size="12pt" fo:font-weight="bold"/></style:style>'
        '<style:style style:name="Tcell" style:family="table-cell"><style:table-cell-properties '
        'fo:padding="0.1cm" fo:border="0.5pt solid #000000"/></style:style>'
        '<style:style style:name="Tcellh" style:family="table-cell"><style:table-cell-properties '
        'fo:padding="0.1cm" fo:border="0.5pt solid #000000" fo:background-color="#e6e6e6"/></style:style>')


def table_style_xml():
    s = ''
    for n, widths in table_styles.items():
        s += ('<style:style style:name="Ttab%d" style:family="table"><style:table-properties '
              'style:width="%.2fcm" table:align="margins"/></style:style>' % (n, sum(widths)))
        for i, w in enumerate(widths):
            s += ('<style:style style:name="Ttab%d.C%d" style:family="table-column">'
                  '<style:table-column-properties style:column-width="%.2fcm"/></style:style>' % (n, i, w))
    return s


# ---------------------------------------------------------------- данные
def v(path, fmt='%s', ph='[[из данных]]'):
    if RES is None:
        return ph
    d = RES
    try:
        for k in path.split('.'):
            d = d[int(k)] if k.isdigit() else d[k]
        return fmt % d
    except (KeyError, TypeError, IndexError):
        return ph


def plot(name):
    return os.path.join(HERE, 'plots', name)


def photo(name):
    return os.path.join(HERE, 'photos', name)


def course(name):
    return os.path.join(HERE, 'pics_course', name)


def script(name):
    return os.path.join(HERE, name)


# ---------------------------------------------------------------- текст отчёта
def body():
    b = []
    b.append(h1('Введение', numbered=False, page_break=True))
    b.append(p('Артериальное давление и частота пульса - важнейшие показатели работы сердечно-сосудистой '
               'системы. Обычный тонометр показывает давление стрелкой, но если подключить к нему датчик '
               'давления, аналого-цифровой преобразователь (АЦП) и компьютер, то можно записать давление '
               'в манжете как функцию времени и увидеть пульсовую волну - небольшие колебания давления, '
               'вызванные ударами сердца. По такой записи находят артериальное давление и пульс.'))
    b.append(p('Работа выполняется командой за ограниченное время, поэтому задачи распределены по ролям: '
               'экспериментатор получает данные, программист их обрабатывает, руководитель пишет отчёт. '
               'Данная работа - научно-технический проект, в котором результат одной роли является входом '
               'для следующей.'))
    b.append(h1('Цели и задачи работы'))
    b.append(h2('Цели'))
    b.append(p('При помощи компьютера, АЦП, датчика давления и тонометра:'))
    b.append(ul(['визуализировать пульсовую волну',
                 'измерить артериальное давление и вычислить пульс в состоянии покоя и после физической нагрузки']))
    b.append(p('Определение скорости распространения пульсовой волны и жёсткости сосудов требует двух датчиков '
               'в разных точках артерии, а в установке датчик один. Поэтому эти величины рассмотрены в '
               'теории, но не измерялись.'))
    b.append(h2('Задачи'))
    b.append(ul(['написать скрипт записи показаний АЦП и убедиться, что АЦП отзывается на давление',
                 'откалибровать датчик по манометру тонометра при давлениях 40, 80, 120 и 160 мм рт. ст.',
                 'записать давление в манжете в состоянии покоя и после физической нагрузки',
                 'перевести отсчёты АЦП в мм рт. ст. и построить графики давления и пульсаций',
                 'определить систолическое и диастолическое давление и пульс по записям',
                 'сравнить результаты до и после нагрузки и оценить точность']))

    b.append(h1('Теория'))
    b.append(h2('Термины и определения'))
    b.append(table('Термины', ['Термин', 'Определение'], [
        ['Артериальное давление', 'давление крови в артериях; меняется в такт сердцу'],
        ['Систолическое давление', 'наибольшее давление в артерии за сердечный цикл, в момент сокращения сердца'],
        ['Диастолическое давление', 'наименьшее давление в артерии за сердечный цикл, в момент расслабления сердца'],
        ['Пульс', 'число сокращений сердца в минуту (ударов в минуту)'],
        ['Миллиметр ртутного столба', 'единица давления; 1 мм рт. ст. ≈ 133,3 Па, давление сверх атмосферного'],
        ['Пульсовая волна', 'колебание давления в манжете, вызванное ударом сердца'],
        ['Осциллометрический метод', 'определение артериального давления по колебаниям давления в манжете'],
        ['Калибровка датчика', 'нахождение зависимости давления от отсчёта АЦП по известным давлениям'],
        ['Шум квантования', 'ступенчатое искажение сигнала из-за конечной разрядности АЦП'],
    ], [5.2, 11.8]))
    b.append(h2('Физическая система'))
    b.append(p('Сердце работает как насос: сокращение (систола) выталкивает кровь в артерии, расслабление '
               '(диастола) позволяет сердцу наполниться. Упругие стенки артерий растягиваются при систоле и '
               'сжимаются при диастоле, поэтому давление в артерии не постоянно, а меняется между '
               'диастолическим и систолическим значениями. Запись «120/80» означает систолическое давление '
               '120 мм рт. ст. и диастолическое 80 мм рт. ст. У взрослого в покое пульс обычно 60 - 90 '
               'ударов в минуту. При физической нагрузке пульс растёт, систолическое давление повышается, '
               'а диастолическое меняется мало.'))
    b.append(p('Давление внутри артерии измерить нельзя, поэтому тонометр измеряет давление в манжете. Манжету '
               'надувают выше систолического давления: артерия пережата, колебаний нет. При медленном спуске '
               'давления в манжете оно опускается ниже систолического, на пике каждого удара артерия '
               'приоткрывается, порция крови толкает манжету изнутри, и в манжете появляются колебания '
               'давления - пульсовая волна. Их амплитуда растёт, достигает максимума около среднего давления '
               'в артерии и резко уменьшается, когда давление в манжете становится ниже диастолического. '
               'В этом состоит осциллометрический метод. В работе приняты правила: систолическое давление - '
               'давление в манжете в районе 5-й пульсовой волны после их появления; диастолическое - '
               'давление, при котором амплитуда пульсовых волн заметно уменьшается. Правила эмпирические, '
               'их точность около 5 - 10 мм рт. ст.'))
    b.append(p('Скорость пульсовой волны c в стенке артерии связана с жёсткостью сосуда формулой '
               'Моенса - Кортевега:'))
    b.append(formula('c = √( E·h / (2·ρ·R) )', 1))
    b.append(p('где E - модуль упругости стенки, h - толщина стенки, R - радиус сосуда, ρ - плотность крови. '
               'Более жёсткие сосуды проводят волну быстрее. Для измерения c нужно регистрировать волну в двух '
               'точках, поэтому в данной работе скорость не определялась.'))
    b.append(h2('Экспериментальная установка'))
    b.append(p('Механический тонометр состоит из манжеты, груши с клапаном и стрелочного манометра. Манометр '
               'показывает давление в мм рт. ст. и служит эталоном при калибровке. К воздушной магистрали '
               'через тройник подключён датчик давления: он выдаёт напряжение, растущее с давлением. Датчик '
               'и манометр соединены с одним объёмом воздуха, поэтому видят одно и то же давление.'))
    b.append(figure(course('tonometer.png'), 'Механический тонометр (иллюстрация из методических материалов курса)', 9.0))
    b.append(figure(course('sensor.png'), 'Датчик давления, подключённый через тройник (иллюстрация из '
                                          'методических материалов курса)', 9.0))
    b.append(p('Датчик подключается к плате get-adc, где его напряжение оцифровывает 10-битный АЦП MCP3021; '
               'отсчёты (от 0 до 1023) передаются на Raspberry Pi по шине I2C. Схема: рука в манжете - датчик '
               'давления - АЦП MCP3021 - I2C - Raspberry Pi; параллельно манометр тонометра служит эталоном '
               'для калибровки.'))
    b.append(figure(photo('setup.jpg'), 'Экспериментальная установка'))
    b.append(p('Чувствительность установки: по калибровке на один отсчёт АЦП приходится %s мм рт. ст., '
               'а пульсовая волна имеет размах около 0,5 - 1 мм рт. ст., то есть 1 - 2,5 отсчёта. Поэтому '
               'на записи давление меняется ступеньками (шум квантования), и запись нужно сглаживать.'
               % v('calibration.k', '%.2f')))

    b.append(h1('Программа и методика измерений'))
    b.append(h2('Подготовка'))
    b.append(ul(['создать на рабочем столе Raspberry Pi папку со своим именем и скопировать в неё драйвер '
                 'mcp3021_driver.py',
                 'вывести шину I2C на выводы командами raspi-gpio set 2 a0 и raspi-gpio set 3 a0',
                 'проверить, что отсчёты растут при сжатии груши и падают при открытии клапана']))
    b.append(h2('Программа эксперимента'))
    b.append(p('Скрипт bloodMeasure.py в цикле заданное число секунд читает АЦП, ничего не печатая и не '
               'пересчитывая, чтобы частота была выше тысячи отсчётов в секунду. После цикла он печатает '
               'число отсчётов и частоту и сохраняет отсчёты, длительность и дату в текстовый файл: '
               'несколько строк заголовка, пустая строка и столбец целых отсчётов АЦП.'))
    b.append(h2('Методика калибровки'))
    b.append(p('Эталон давления - стрелочный манометр тонометра. Манжету снимают с руки и кладут на стол: '
               'пульс помешал бы держать давление ровным. Клапан закрывают и накачивают давление 40 мм рт. ст. '
               'по стрелке, ждут пару секунд и записывают 10 секунд. Это повторяют для 80, 120 и 160 мм рт. ст. '
               'Давлений четыре, а не два, чтобы проверить линейность датчика и оценить погрешность калибровки. '
               'Погрешность стрелочного манометра обычно ±3 мм рт. ст.'))
    b.append(h2('Методика измерений'))
    b.append(p('Испытуемый сидит, рука расслаблена и лежит на столе на уровне сердца. Манжета надевается на '
               'плечо на 2 - 3 см выше локтевого сгиба. Запускается запись, манжета быстро накачивается до '
               '160 - 180 мм рт. ст., затем клапан приоткрывается так, чтобы давление падало на 2 - 3 мм рт. ст. '
               'в секунду. После этого клапан не трогают, испытуемый не двигается и не разговаривает. Когда '
               'давление опустилось ниже 50 мм рт. ст., клапан открывают полностью. Так записываются два '
               'измерения: в состоянии покоя (rest) и сразу после физической нагрузки (fitness), условия '
               'нагрузки: %s.' % LOAD_NOTE))
    if not OWN_DATA:
        b.append(p('Замечание о данных. Для обработки и оформления результатов в отчёте использованы записи с '
                   'установки курса из стартового набора (папка «Пример данных»): калибровка 40, 80, 120 и '
                   '160 мм рт. ст. по 10 с и записи rest и fitness. Собственные записи команды: '
                   '[[при наличии заменить и поставить OWN_DATA = True]].'))

    b.append(h1('Обработка данных'))
    b.append(h2('Выделение пульсовой волны'))
    b.append(p('Запись давления - сумма медленного тренда (давление спадает из-за выхода воздуха через клапан) '
               'и быстрых пульсаций амплитудой около 0,5 - 1 мм рт. ст. с частотой около 1 Гц. Если вычесть '
               'тренд, остаются пульсации, и каждая волна - заметный пик. Сначала отсчёты сглаживают скользящим '
               'средним по окну 50 мс: окно много короче периода пульса, но содержит около 90 отсчётов и убирает '
               'шум квантования. Тренд находят скользящим средним по окну 1,5 с - чуть длиннее периода пульса: '
               'более короткое окно оставляет пульсации в тренде, а слишком длинное не следует за спуском. '
               'Края записи на полокна искажены, поэтому первые 2,5 с в анализе амплитуд не используются.'))
    b.append(h2('Методика обработки данных'))
    b.append(ul(['калибровка: по среднему отсчёту АЦП в каждом из четырёх файлов прямая P = k·N + b '
                 'строится методом наименьших квадратов (numpy.polyfit)',
                 'давление: отсчёты переводятся в мм рт. ст. по прямой, время отсчёта - '
                 'numpy.linspace(0, длительность, число отсчётов)',
                 'пульс: пики пульсаций находятся scipy.signal.find_peaks (расстояние между пиками не менее '
                 '0,4 с, выраженность не менее 0,3 мм рт. ст.) на участке 10 - 30 с одинаково для обеих записей; '
                 'пульс = (N - 1)·60 / (t_N - t_1)',
                 'амплитуда волны: разность вершины волны и предыдущей впадины; сглаженная амплитуда - '
                 'медиана по семи соседним волнам, выбросы от движения руки (в 1,5 раза выше медианы) убираются',
                 'систолическое давление: давление в манжете в момент 5-й волны после начала спуска',
                 'диастолическое давление: давление в первый момент после максимума амплитуды, когда сглаженная '
                 'амплитуда становится ниже 0,8 от наибольшей (правило автоматических тонометров)']))
    b.append(formula('P = k·N + b,   пульс = (N − 1)·60 / (t_N − t_1)', 2))

    b.append(h1('Код программы'))
    b.append(h2('Скрипт измерения давления'))
    b.append(code(script('bloodMeasure.py')))
    b.append(h2('Скрипт обработки данных'))
    b.append(code(script('bloodProcessing.py')))
    b.append(h2('Драйвер АЦП'))
    b.append(code(script('mcp3021_driver.py')))

    b.append(h1('Эксперимент'))
    b.append(h2('Калибровка'))
    rows = [[pp, v('calibration.points.%d.n' % i, '%.1f')] for i, pp in enumerate((40, 80, 120, 160))]
    b.append(table('Средний отсчёт АЦП при заданном давлении', ['P, мм рт. ст.', 'Средний отсчёт N'],
                   rows, [6.0, 6.0]))
    if RES:
        c = RES['calibration']
        b.append(p('Прямая P = k·N + b: k = %.4f ± %.4f мм рт. ст. на отсчёт, b = %.2f ± %.2f мм рт. ст. '
                   'Наибольшее отклонение точки от прямой %.2f мм рт. ст., что меньше погрешности стрелочного '
                   'манометра (±3 мм рт. ст.), то есть датчик линеен.'
                   % (c['k'], c['dk'], c['b'], c['db'], c['maxdev'])))
    b.append(figure(plot('pressure-calibration.png'), 'Калибровочная прямая датчика давления', 12.5))
    b.append(h2('Графики давления'))
    b.append(p('Давление в манжете спускается ровно: %s мм рт. ст. в секунду в покое и %s после нагрузки. '
               'Мелкие зубцы на линии - пульсовые волны. Звёздочками отмечены систолическое и диастолическое '
               'давление.' % (v('rest.slope', '%.1f'), v('fitness.slope', '%.1f'))))
    b.append(figure(plot('rest-pressure.png'), 'Давление в манжете в состоянии покоя, отмечены систола и диастола'))
    b.append(figure(plot('fitness-pressure.png'), 'Давление в манжете после физической нагрузки, отмечены '
                                                  'систола и диастола'))
    b.append(h2('Графики пульса'))
    b.append(p('Каждый пик на графике пульсаций - один удар сердца. Высокие одиночные пики - удары, на которые '
               'наложилось движение руки; они тоже считаются.'))
    b.append(figure(plot('rest-pulse.png'), 'Пульсации давления в состоянии покоя'))
    b.append(figure(plot('fitness-pulse.png'), 'Пульсации давления после физической нагрузки'))
    b.append(p('По графикам амплитуды волн определялись систолическое и диастолическое давление.'))
    b.append(figure(plot('rest-amplitude.png'), 'Амплитуда пульсовых волн в состоянии покоя'))
    b.append(figure(plot('fitness-amplitude.png'), 'Амплитуда пульсовых волн после физической нагрузки'))

    b.append(h1('Результаты'))
    b.append(table('Давление и пульс до и после нагрузки',
                   ['Запись', 'Пульс, уд/мин', 'Давление, мм рт. ст.'],
                   [['В покое', v('rest.pulse'), '%s/%s' % (v('rest.sys'), v('rest.dia'))],
                    ['После нагрузки', v('fitness.pulse'), '%s/%s' % (v('fitness.sys'), v('fitness.dia'))]],
                   [6.0, 5.0, 6.0]))
    if RES:
        r, f = RES['rest'], RES['fitness']
        rise = 100.0 * (f['pulse'] - r['pulse']) / r['pulse']
        b.append(p('Пульс после нагрузки вырос с %d до %d уд/мин, примерно на %.0f %%. Это надёжный результат: '
                   'пики видны чётко, ошибка подсчёта - один удар на участке 20 с, то есть около 3 ударов в '
                   'минуту. Систолическое давление после нагрузки выше на %d мм рт. ст., диастолическое '
                   'изменилось на %+d мм рт. ст. - почти не изменилось, как и должно быть при нагрузке.'
                   % (r['pulse'], f['pulse'], rise, f['sys'] - r['sys'], f['dia'] - r['dia'])))

    b.append(h1('Итоги лабораторной работы', numbered=False))
    if RES:
        r, f, c = RES['rest'], RES['fitness'], RES['calibration']
        b.append(p('В работе по сигналу датчика давления в манжете визуализирована пульсовая волна. Датчик '
                   'откалиброван по манометру тонометра: P = %.4f·N %+.2f мм рт. ст., отклонения точек от прямой '
                   'не превышают %.1f мм рт. ст. Определены давление и пульс: в покое %d/%d мм рт. ст., '
                   '%d уд/мин; после нагрузки %d/%d мм рт. ст., %d уд/мин. Пульс после нагрузки выше, '
                   'потому что мышцам нужно больше кислорода и сердце бьётся чаще и сильнее.'
                   % (c['k'], c['b'], c['maxdev'], r['sys'], r['dia'], r['pulse'],
                      f['sys'], f['dia'], f['pulse'])))
        b.append(p('Точность давлений невелика: правила определения эмпирические, моменты систолы и диастолы '
                   'зависят от выбора критерия, а погрешность манометра при калибровке составляет ±3 мм рт. ст., '
                   'поэтому ошибка порядка 5 - 10 мм рт. ст. Влияют также движение руки и скорость спуска '
                   'давления. В записях пульсовые волны видны с самого начала спуска, поэтому момент их появления '
                   'определить нельзя и систолическое давление может быть завышено; надёжнее сравнивать '
                   'давления до и после нагрузки между собой, чем судить об их абсолютных значениях. '
                   'Скорость пульсовой волны и жёсткость сосудов не определялись: для этого нужен второй '
                   'датчик. Работа - учебное измерение, а не диагностика, и медицинских выводов из неё делать нельзя.'))
    else:
        b.append(p('[[Вывод будет написан после обработки данных.]]'))
    return ''.join(b)


# ---------------------------------------------------------------- сборка
def title_page():
    x = ('<text:p text:style-name="P1">Московский физико-технический институт '
         '(национальный исследовательский университет)</text:p>')
    x += '<text:p text:style-name="P2"/>' * 3
    x += '<text:p text:style-name="P3">%s</text:p>' % T(TITLE)
    x += '<text:p text:style-name="P3"/>' * 2
    x += '<text:p text:style-name="P4">Выполнили:</text:p>'
    for au in AUTHORS:
        x += '<text:p text:style-name="P4">%s</text:p>' % T(au)
    x += '<text:p text:style-name="P3"/>'
    x += '<text:p text:style-name="P3">%s</text:p>' % T(CITY_YEAR)
    return x


def main():
    z = zipfile.ZipFile(TEMPLATE)
    c = z.read('content.xml').decode('utf8')
    head = c[:c.index('<office:text')]
    toc = c[c.index('<text:table-of-content '):c.index('</text:index-title>') + len('</text:index-title>')]
    toc += '</text:index-body></text:table-of-content>'
    seq = c[c.index('<text:sequence-decls>'):c.index('</text:sequence-decls>') + len('</text:sequence-decls>')]
    bd = body()
    head = head.replace('</office:automatic-styles>', extra_styles() + table_style_xml() + '</office:automatic-styles>')
    content = (head + '<office:text text:use-soft-page-breaks="true">' + seq + title_page() + toc
               + '<text:p text:style-name="P9"/>' + bd + '</office:text></office:body></office:document-content>')
    man = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.4">',
           '<manifest:file-entry manifest:full-path="/" manifest:version="1.4" '
           'manifest:media-type="application/vnd.oasis.opendocument.text"/>']
    for n in ('styles.xml', 'settings.xml', 'meta.xml', 'content.xml'):
        man.append('<manifest:file-entry manifest:full-path="%s" manifest:media-type="text/xml"/>' % n)
    for arc in pictures:
        mt = 'image/png' if arc.endswith('.png') else 'image/jpeg'
        man.append('<manifest:file-entry manifest:full-path="%s" manifest:media-type="%s"/>' % (arc, mt))
    man.append('</manifest:manifest>')
    with zipfile.ZipFile(OUT, 'w') as o:
        o.writestr(zipfile.ZipInfo('mimetype'), z.read('mimetype'), compress_type=zipfile.ZIP_STORED)
        for n in ('styles.xml', 'settings.xml', 'meta.xml'):
            o.writestr(n, z.read(n), compress_type=zipfile.ZIP_DEFLATED)
        o.writestr('content.xml', content.encode('utf8'), compress_type=zipfile.ZIP_DEFLATED)
        for arc, src in pictures.items():
            o.write(src, arc, compress_type=zipfile.ZIP_DEFLATED)
        o.writestr('META-INF/manifest.xml', '\n'.join(man).encode('utf8'), compress_type=zipfile.ZIP_DEFLATED)
    print('Готово:', OUT)


if __name__ == '__main__':
    main()
