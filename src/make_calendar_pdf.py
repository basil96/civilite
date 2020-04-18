# -*- coding: utf-8 -*-
# Client for creating a nicely formatted PDF calendar for a specified year or the current year (default).

# builtins
import calendar
from datetime import date, time, timedelta
import sys
# 3rd party
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
# custom
from schedule import WeeklySchedule, ScheduleEvent, createEvents, getCurrentSchedule, EVENT_TYPES, EVT_FIXED, EVT_SUNSET, EVT_NEVER_ON

thisYear = date.today().year
if len(sys.argv) > 1:
    thisYear = int(sys.argv[1])


def OnFirstPage(canvas, doc):
    canvas.saveState()
    canvas.setTitle('House of Prayer - {} Parking Lot Lighting Schedule'.format(thisYear))
    canvas.setAuthor('AMV')
    canvas.setSubject('HoP parking lot lighting schedule for {}'.format(thisYear))
    canvas.setKeywords('')
    canvas.restoreState()


print('Creating the lighting control schedule for year {}'.format(thisYear))
# Occupancy schedule for parking lot lighting
mySchedule = getCurrentSchedule()
sunsetEvents = createEvents(thisYear, mySchedule)

print('Creating template..')
calFileName = 'lighting_calendar_{}.pdf'.format(thisYear)
doc = SimpleDocTemplate(calFileName,
                        pagesize=letter,
                        leftMargin=0.2*inch,
                        rightMargin=0.2*inch,
                        topMargin=0.2*inch,
                        bottomMargin=0.2*inch)
print('Creating table...')
cBlue = colors.HexColor('#99ccff')
cGreen = colors.HexColor('#ccffcc')
cOrange = colors.HexColor('#ffcc99')
cGray1 = colors.HexColor('#777777')
cGray2 = colors.HexColor('#969696')
cGray3 = colors.HexColor('#AF9E93')
# cGray3 = colors.HexColor('#677077')
EVENT_COLORS = {EVT_FIXED: cGreen, EVT_SUNSET: cOrange, EVT_NEVER_ON: cGray3}
CALENDAR_STYLE = [
    # global
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),   # all cells
    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),    # day columns
    ('ALIGN', (0, 0), (0, -1), 'LEFT'),       # month column
    ('ALIGN', (8, 0), (8, -1), 'CENTER'),     # sunset time column
    # header
    ('BACKGROUND', (0, 0), (7, 0), cGray1),
    ('TEXTCOLOR', (0, 0), (7, 0), colors.white),
    ('BACKGROUND', (1, 0), (1, 0), cGray2),
    ('BACKGROUND', (7, 0), (7, 0), cGray2),
    ('BACKGROUND', (8, 0), (8, 0), cOrange),
]
elements = []
startDate = date(thisYear, 1, 1)
data = [['MONTH', 'Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Sunset']]
cellDate = startDate
numPrefixCols = 1
numSuffixCols = 1
ri = 1
lastTime = None
currTime = None
while cellDate.year == startDate.year:
    colId = (cellDate.weekday() + 1) % 7    # gives us Sunday first (Mon=0, Sun=6 in Python)
    ci = colId + numPrefixCols
    row = [''] * (numPrefixCols + colId)
    row[0] = ''
    for i in range(7 - colId):
        row.append('%02d' % cellDate.day)
        info = sunsetEvents.get(cellDate)
        if cellDate.day == 1:
            row[0] = calendar.month_name[cellDate.month]
            CALENDAR_STYLE.append(('BACKGROUND', (0, ri), (0, ri), cBlue))
            CALENDAR_STYLE.append(('BOX', (ci, ri), (ci, ri), 1, cGray2))
        if info is not None:
            sunsetTime, eventType, eventChanged = info
            if eventType is not None:
                CALENDAR_STYLE.append(('BACKGROUND', (ci, ri), (ci, ri), EVENT_COLORS[eventType]))
            else:
                CALENDAR_STYLE.append(('TEXTCOLOR', (ci, ri), (ci, ri), colors.lightslategray))
        currTime = sunsetTime
        if lastTime is not None and (currTime.utcoffset() != lastTime.utcoffset()):
            CALENDAR_STYLE.append(('BACKGROUND', (ci, ri), (ci, ri), colors.yellow))
        lastTime = currTime
        ci += 1
        cellDate += timedelta(days=1)
    row.append(currTime.time().strftime('%H:%M'))
    data.append(row)
    ri += 1

# sunset column formats
CALENDAR_STYLE.append(('LINEAFTER', (7, 0), (7, -1), 1, colors.black))
CALENDAR_STYLE.append(('GRID', (8, 0), (8, -1), 1, colors.black))

t1 = Table(data, [1.0*inch] + (len(data[0])-2)*[0.25*inch] + [None], len(data)*[0.19*inch])
t1.setStyle(TableStyle(CALENDAR_STYLE))

rowAdjust = 21
schedData = [
    ['', '', thisYear, ''],
    ['', '', '', ''],
    ['', '', 'OCCUPANCY SCHEDULE\n(EVENINGS)', ''],
    ['', 'Weekday', 'Start time', 'End time']]
for i in range(7):
    weekDay = (i - 1) % 7   # list Sunday first, just like in calendar table
    evt = mySchedule.events.get(weekDay)
    if evt is not None:
        schedData.append(['', calendar.day_name[weekDay], time.strftime(evt.start, '%H:%M'), time.strftime(evt.stop, '%H:%M')])
schedData = schedData + (t1._nrows-len(schedData)-rowAdjust)*[['', '', '', '']]
schedData[12] = ['LEGEND', '']
schedData[13] = ['01', '%s event' % EVENT_TYPES[EVT_SUNSET]]
schedData[14] = ['01', '%s event' % EVENT_TYPES[EVT_FIXED]]
schedData[15] = ['01', '%s event' % EVENT_TYPES[EVT_NEVER_ON]]
schedData[16] = ['01', 'First day of month']
schedData[17] = ['01', 'DST change']
t2 = Table(schedData,
           [0.25*inch, 0.95*inch, 0.75*inch, 0.75*inch],
           [1.0*inch, 1.0*inch, 0.50*inch] + (t1._nrows-3-rowAdjust)*[0.25*inch],
           TableStyle([
               # global
               ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
               ('ALIGN', (2, 0), (2, 2), 'CENTER'),
               ('ALIGN', (1, 3), (1, -1), 'LEFT'),
               ('ALIGN', (2, 3), (-1, -1), 'CENTER'),
               # year cell
               ('FONT', (2, 0), (2, 0), 'Times-Bold', 64),
               # header
               ('BACKGROUND', (1, 3), (-1, 3), cGray1),
               ('TEXTCOLOR', (1, 3), (-1, 3), colors.white),
               # grid
               ('GRID', (1, 3), (-1, len(mySchedule.events)+3), 1, colors.black),
               # legend
               ('ALIGN', (0, 12), (-1, -1), 'LEFT'),
               ('ALIGN', (0, 13), (0, -1), 'CENTER'),
               ('BACKGROUND', (0, 13), (0, 13), EVENT_COLORS[EVT_SUNSET]),
               ('BACKGROUND', (0, 14), (0, 14), EVENT_COLORS[EVT_FIXED]),
               ('BACKGROUND', (0, 15), (0, 15), EVENT_COLORS[EVT_NEVER_ON]),
               ('BOX', (0, 16), (0, 16), 1, cGray2),
               ('BACKGROUND', (0, 17), (0, 17), colors.yellow),
           ])
           )

tMain = Table([[t2, t1]])

elements.append(tMain)
# write the document to disk
doc.build(elements, onFirstPage=OnFirstPage)
print('Calendar {} created.'.format(calFileName))
