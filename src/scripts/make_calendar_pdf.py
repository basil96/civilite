# -*- coding: utf-8 -*-
''' Client for creating a nicely formatted PDF calendar for a
    specified year or the current year (default).
'''
__version__ = '1.0.1'

# builtins
import calendar
import sys
from datetime import date, time, timedelta

# 3rd party
from reportlab.lib import colors
from reportlab.lib.pagesizes import inch, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# custom
from civilite.schedule import (EVENT_TYPES, EVT_FIXED, EVT_NEVER_ON,
                               EVT_SUNSET, createEvents, getCurrentSchedule)

THIS_YEAR = date.today().year
if len(sys.argv) > 1:
    THIS_YEAR = int(sys.argv[1])


def onFirstPage(canvas, _doc):
    ''' function object for setting up the default document
        this implementation does not use the doc parameter
    '''
    canvas.saveState()
    canvas.setTitle(f'House of Prayer - {THIS_YEAR} Parking Lot Lighting Schedule')
    canvas.setAuthor('AMV')
    canvas.setSubject(f'HoP parking lot lighting schedule for {THIS_YEAR}')
    canvas.setKeywords('')
    canvas.restoreState()


print(f'Creating the lighting control schedule for year {THIS_YEAR}')
# Occupancy schedule for parking lot lighting
MY_SCHEDULE = getCurrentSchedule()
SUNSET_EVENTS = createEvents(THIS_YEAR, MY_SCHEDULE)

print('Creating template..')
CALENDAR_FILE_NAME = f'lighting_calendar_{THIS_YEAR}.pdf'
CALENDAR_DOCUMENT = SimpleDocTemplate(CALENDAR_FILE_NAME,
                                      pagesize=letter,
                                      leftMargin=0.2*inch,
                                      rightMargin=0.2*inch,
                                      topMargin=0.2*inch,
                                      bottomMargin=0.2*inch)
print('Creating table...')
DOC_COLOR_BLUE = colors.HexColor('#99ccff')
DOC_COLOR_GREEN = colors.HexColor('#ccffcc')
DOC_COLOR_ORANGE = colors.HexColor('#ffcc99')
DOC_COLOR_GRAY_1 = colors.HexColor('#777777')
DOC_COLOR_GRAY_2 = colors.HexColor('#969696')
DOC_COLOR_GRAY_3 = colors.HexColor('#AF9E93')
# cGray3 = colors.HexColor('#677077')
EVENT_COLORS = {EVT_FIXED: DOC_COLOR_GREEN,
                EVT_SUNSET: DOC_COLOR_ORANGE,
                EVT_NEVER_ON: DOC_COLOR_GRAY_3}
CALENDAR_STYLE = [
    # global
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),   # all cells
    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),    # day columns
    ('ALIGN', (0, 0), (0, -1), 'LEFT'),       # month column
    ('ALIGN', (8, 0), (8, -1), 'CENTER'),     # sunset time column
    # header
    ('BACKGROUND', (0, 0), (7, 0), DOC_COLOR_GRAY_1),
    ('TEXTCOLOR', (0, 0), (7, 0), colors.white),
    ('BACKGROUND', (1, 0), (1, 0), DOC_COLOR_GRAY_2),
    ('BACKGROUND', (7, 0), (7, 0), DOC_COLOR_GRAY_2),
    ('BACKGROUND', (8, 0), (8, 0), DOC_COLOR_ORANGE),
]
DOCUMENT_ELEMENTS = []
START_DATE = date(THIS_YEAR, 1, 1)
DATA = [['MONTH', 'Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Sunset']]
CELL_DATE = START_DATE
NUM_PREFIX_COLUMNS = 1
NUM_SUFFIX_COLUMNS = 1
ROW_INDEX = 1
LAST_TIME = None
CURRENT_TIME = None
while CELL_DATE.year == START_DATE.year:
    COLUMN_ID = (CELL_DATE.weekday() + 1) % 7    # gives us Sunday first (Mon=0, Sun=6 in Python)
    COLUMN_INDEX = COLUMN_ID + NUM_PREFIX_COLUMNS
    ROW = [''] * (NUM_PREFIX_COLUMNS + COLUMN_ID)
    ROW[0] = ''
    for i in range(7 - COLUMN_ID):
        ROW.append('%02d' % CELL_DATE.day)
        info = SUNSET_EVENTS.get(CELL_DATE)
        if CELL_DATE.day == 1:
            ROW[0] = calendar.month_name[CELL_DATE.month]
            CALENDAR_STYLE.append(('BACKGROUND', (0, ROW_INDEX), (0, ROW_INDEX), DOC_COLOR_BLUE))
            CALENDAR_STYLE.append(('BOX', (COLUMN_INDEX, ROW_INDEX),
                                   (COLUMN_INDEX, ROW_INDEX), 1, DOC_COLOR_GRAY_2))
        if info is not None:
            sunsetTime, eventType, eventChanged = info
            if eventType is not None:
                CALENDAR_STYLE.append(('BACKGROUND', (COLUMN_INDEX, ROW_INDEX),
                                       (COLUMN_INDEX, ROW_INDEX), EVENT_COLORS[eventType]))
            else:
                CALENDAR_STYLE.append(('TEXTCOLOR', (COLUMN_INDEX, ROW_INDEX),
                                       (COLUMN_INDEX, ROW_INDEX), colors.lightslategray))
        CURRENT_TIME = sunsetTime
        if LAST_TIME is not None and (CURRENT_TIME.utcoffset() != LAST_TIME.utcoffset()):
            CALENDAR_STYLE.append(('BACKGROUND', (COLUMN_INDEX, ROW_INDEX),
                                   (COLUMN_INDEX, ROW_INDEX), colors.yellow))
        LAST_TIME = CURRENT_TIME
        COLUMN_INDEX += 1
        CELL_DATE += timedelta(days=1)
    ROW.append(CURRENT_TIME.time().strftime('%H:%M'))
    DATA.append(ROW)
    ROW_INDEX += 1
NUM_ROWS = len(DATA)

# sunset column formats
CALENDAR_STYLE.append(('LINEAFTER', (7, 0), (7, -1), 1, colors.black))
CALENDAR_STYLE.append(('GRID', (8, 0), (8, -1), 1, colors.black))

TABLE_1 = Table(DATA, [1.0*inch] + (len(DATA[0])-2)*[0.25*inch] + [None], len(DATA)*[0.19*inch])
TABLE_1.setStyle(TableStyle(CALENDAR_STYLE))

ROW_ADJUST = 21
SCHEDULE_DATA = [
    ['', '', THIS_YEAR, ''],
    ['', '', '', ''],
    ['', '', 'OCCUPANCY SCHEDULE\n(EVENINGS)', ''],
    ['', 'Weekday', 'Start time', 'End time']]
for i in range(7):
    weekDay = (i - 1) % 7   # list Sunday first, just like in calendar table
    evt = MY_SCHEDULE.events.get(weekDay)
    if evt is not None:
        SCHEDULE_DATA.append(['', calendar.day_name[weekDay],
                              time.strftime(evt.start, '%H:%M'),
                              time.strftime(evt.stop, '%H:%M')])
SCHEDULE_DATA = SCHEDULE_DATA + (NUM_ROWS-len(SCHEDULE_DATA)-ROW_ADJUST)*[['', '', '', '']]
SCHEDULE_DATA[12] = ['LEGEND', '']
SCHEDULE_DATA[13] = ['01', '%s event' % EVENT_TYPES[EVT_SUNSET]]
SCHEDULE_DATA[14] = ['01', '%s event' % EVENT_TYPES[EVT_FIXED]]
SCHEDULE_DATA[15] = ['01', '%s event' % EVENT_TYPES[EVT_NEVER_ON]]
SCHEDULE_DATA[16] = ['01', 'First day of month']
SCHEDULE_DATA[17] = ['01', 'DST change']
TABLE_2 = Table(SCHEDULE_DATA,
                [0.25*inch, 0.95*inch, 0.75*inch, 0.75*inch],
                [1.0*inch, 1.0*inch, 0.50*inch] +
                (NUM_ROWS-3-ROW_ADJUST)*[0.25*inch],
                TableStyle([
                    # global
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (2, 0), (2, 2), 'CENTER'),
                    ('ALIGN', (1, 3), (1, -1), 'LEFT'),
                    ('ALIGN', (2, 3), (-1, -1), 'CENTER'),
                    # year cell
                    ('FONT', (2, 0), (2, 0), 'Times-Bold', 64),
                    # header
                    ('BACKGROUND', (1, 3), (-1, 3), DOC_COLOR_GRAY_1),
                    ('TEXTCOLOR', (1, 3), (-1, 3), colors.white),
                    # grid
                    ('GRID', (1, 3), (-1, len(MY_SCHEDULE.events)+3), 1, colors.black),
                    # legend
                    ('ALIGN', (0, 12), (-1, -1), 'LEFT'),
                    ('ALIGN', (0, 13), (0, -1), 'CENTER'),
                    ('BACKGROUND', (0, 13), (0, 13), EVENT_COLORS[EVT_SUNSET]),
                    ('BACKGROUND', (0, 14), (0, 14), EVENT_COLORS[EVT_FIXED]),
                    ('BACKGROUND', (0, 15), (0, 15),
                     EVENT_COLORS[EVT_NEVER_ON]),
                    ('BOX', (0, 16), (0, 16), 1, DOC_COLOR_GRAY_2),
                    ('BACKGROUND', (0, 17), (0, 17), colors.yellow),
                ])
                )

TABLE_MAIN = Table([[TABLE_2, TABLE_1]])

DOCUMENT_ELEMENTS.append(TABLE_MAIN)
# write the document to disk
CALENDAR_DOCUMENT.build(DOCUMENT_ELEMENTS, onFirstPage=onFirstPage)
print(f'Calendar {CALENDAR_FILE_NAME} created.')
