# -*- coding: utf-8 -*-
# Scheduling module for civilite

import sys
import calendar
from astral import Astral
from datetime import date, time, timedelta


class ScheduleEvent:
    def __init__(self, start=None, stop=None):
        self.start = start
        self.stop = stop


class WeeklySchedule:
    def __init__(self):
        self.events = {}

    def __str__(self):
        s = [('Weekday', 'Start time', 'End time')]
        for wd in range(7):
            if wd in self.events:
                s += [(calendar.day_abbr[wd], str(self.events[wd].start), str(self.events[wd].stop))]
        return '\n'.join(['\t'.join(ss) for ss in s])

    def AddEvent(self, weekday, event):
        self.events[weekday] = event


# Event definitions for describing tasks on the Intermatic astro time clock
EVT_FIXED = 1
EVT_SUNSET = 2
EVT_NEVER_ON = 3
EVENT_TYPES = {EVT_FIXED: 'FIXED', EVT_SUNSET: 'SUNSET', EVT_NEVER_ON: 'NEVER-ON'}


def getEventType(schedule, date, city):
    event = schedule.events.get(date.weekday())
    if event is None:
        return None
    result = EVT_SUNSET
    sunsetTime = city.sunset(date).time()
    if event.start > sunsetTime:
        result = EVT_FIXED
    elif sunsetTime > event.stop:
        result = EVT_NEVER_ON
    return result


def createEvents(year, schedule):
    a = Astral()
    a.solar_depression = 'civil'
    # city = a['Buffalo']     # close enuff, about 5 minutes behind ROC in sunset times
    # city = a['Rochester']     # custom addition: Rochester,USA,43°10'N,77°36'W,US/Eastern,153
    city = a['Rochester_HoP']     # custom addition: Rochester_HoP,USA,43°09'N,77°23'W,US/Eastern,170

    data = {}
    calDate = date(year, 1, 1)
    eventTypeChanged = False
    while calDate.year == year:
        thisEventType = getEventType(schedule, calDate, city)
        if thisEventType is not None:
            lastWeekEventType = getEventType(schedule, calDate - timedelta(days=7), city)
            if thisEventType != lastWeekEventType:
                eventTypeChanged = True
        data[calDate] = (city.sunset(calDate), thisEventType, eventTypeChanged)
        calDate += timedelta(days=1)
        eventTypeChanged = False

    with open('sunsets_%d.csv' % year, 'w') as fpOut:
        fpOut.write('"Weekday","Date","Sunset","Event Type","Event Change?"\n')
        for d, (s, e, evtChanged) in sorted(data.items()):
            fpOut.write('"%s",%s,%s,"%s",%s\n' % (calendar.day_abbr[d.weekday()], d,
                                                  s.time(), EVENT_TYPES.get(e, ''), '*' if evtChanged else ''))

    return data


def getCurrentSchedule():
    '''Current HoP weekly schedule'''
    result = WeeklySchedule()
    result.AddEvent(calendar.SUNDAY, ScheduleEvent(time(16, 45), time(19, 0)))
    result.AddEvent(calendar.TUESDAY, ScheduleEvent(time(18, 30), time(22, 0)))
    result.AddEvent(calendar.WEDNESDAY, ScheduleEvent(time(18, 45), time(21, 0)))
    result.AddEvent(calendar.FRIDAY, ScheduleEvent(time(18, 45), time(21, 0)))
    return result


def outputSunsets(year):
    '''output the schedule and then create astrological events as necessary
    for safe lighting
    '''
    # Get Lot lighting schedule
    mySchedule = getCurrentSchedule()
    print('Occupancy schedule:')
    print(mySchedule)
    # run it
    createEvents(year, mySchedule)


if __name__ == '__main__':
    YEAR = date.today().year
    if len(sys.argv) == 2:
        YEAR = int(sys.argv[1])
    outputSunsets(YEAR)
