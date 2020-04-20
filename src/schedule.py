# -*- coding: utf-8 -*-
''' Scheduling module for civilite '''
__version__ = '1.0.1'

# builtins
import sys
import calendar
from datetime import date, time, timedelta
# 3rd party
from astral import Observer, SunDirection
from astral.sun import twilight
import pytz

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

class ScheduleObserver(Observer):
    '''schedule implementation of astral.Observer to aggregate timezone'''
    tzinfo: pytz.tzinfo = pytz.utc
    def __init__(self, tzinfo = pytz.utc, **kwargs):
        self.tzinfo = tzinfo
        super().__init__(**kwargs)
    def get_civil_twilight(self, event_date):
        ''' wrapper function for twilight sunset start'''
        twilight_start_end = twilight(self, event_date, SunDirection.SETTING, self.tzinfo)
        return twilight_start_end[0]

def getEventType(schedule, event_date, observer):
    event = schedule.events.get(event_date.weekday())
    if event is None:
        return None
    result = EVT_SUNSET
    sunset_time = observer.get_civil_twilight(event_date).time()
    if event.start > sunset_time:
        result = EVT_FIXED
    elif sunset_time > event.stop:
        result = EVT_NEVER_ON
    return result


def createEvents(year, schedule):
    '''create events from a schedule object at a custom location'''
    # custom observer: Rochester_HoP,USA,43°09'N,77°23'W,US/Eastern,170
    observer = ScheduleObserver(latitude=43.1606355, longitude=-77.3883843, elevation=170, tzinfo=pytz.timezone("US/Eastern"))
    data = {}
    calDate = date(year, 1, 1)
    eventTypeChanged = False
    while calDate.year == year:
        thisEventType = getEventType(schedule, calDate, observer)
        if thisEventType is not None:
            lastWeekEventType = getEventType(schedule, calDate - timedelta(days=7), observer)
            if thisEventType != lastWeekEventType:
                eventTypeChanged = True
        data[calDate] = (observer.get_civil_twilight(calDate), thisEventType, eventTypeChanged)
        calDate += timedelta(days=1)
        eventTypeChanged = False

    with open('sunsets_%d.csv' % year, 'w') as fpOut:
        fpOut.write('"Weekday","Date","Sunset","Event Type","Event Change?"\n')
        for d, (s, e, evtChanged) in sorted(data.items()):
            fpOut.write('"%s",%s,%s,"%s",%s\n' % (calendar.day_abbr[d.weekday()], d,
                                                  (s.strftime('%H:%M:%S')), EVENT_TYPES.get(e, ''), '*' if evtChanged else ''))

    return data


def getCurrentSchedule():
    result = WeeklySchedule()
    result.AddEvent(calendar.SUNDAY, ScheduleEvent(time(16, 45), time(19, 0)))
    result.AddEvent(calendar.TUESDAY, ScheduleEvent(time(18, 30), time(22, 0)))
    result.AddEvent(calendar.WEDNESDAY, ScheduleEvent(time(18, 45), time(21, 0)))
    result.AddEvent(calendar.FRIDAY, ScheduleEvent(time(18, 45), time(21, 0)))
    return result


def outputSunsets(year):
    # Lot lighting schedule
    mySchedule = getCurrentSchedule()
    print('Occupancy schedule:')
    print(mySchedule)
    # run it
    createEvents(yr, mySchedule)


if __name__ == '__main__':
    yr = date.today().year
    if len(sys.argv) == 2:
        yr = int(sys.argv[1])
    outputSunsets(yr)
