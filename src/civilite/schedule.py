# -*- coding: utf-8 -*-
''' Scheduling module for civilite '''
__version__ = '1.0.1'

# Builtins
import sys
import calendar
from datetime import date, time, datetime, timedelta
from typing import Dict, Tuple, Optional
# 3rd party
from astral import Observer, SunDirection
from astral.sun import twilight
import pytz


# Event definitions for describing tasks on the Intermatic astro time clock
# Assumptions:
#   * Events never occur during sunrise. TODO: sunrises should be considered in the future.
#   * Events occasionally end after sunset.
#
# "Fixed" event: when an event starts after sunset,
#   the ON and OFF times for lights must be explicitly fixed by user.
EVT_FIXED = 1
# "Sunset" event: when a sunset occurs during an event,
#   the ON time is programmed according to the clock's sunset time for that day
#   and the OFF time is programmed explicitly.
EVT_SUNSET = 2
# "Never on" event: when an event ends before sunset, lights do not need to be ON at all.
EVT_NEVER_ON = 3
EVENT_TYPES = {EVT_FIXED: 'FIXED', EVT_SUNSET: 'SUNSET', EVT_NEVER_ON: 'NEVER-ON'}


class ScheduleEvent:
    '''An event in a building's occupancy schedule.
        Defined by endpoints that must lie within one day.
        If an event spans multiple days, one event for each day must be created
        to ensure continuity.
    '''

    def __init__(self, start: time, stop: time) -> None:
        '''Create a new event whose duration spans from start to stop times, inclusive.'''
        self.start = start
        self.stop = stop


class WeeklySchedule:
    '''A collection of events that repeat every week.'''

    def __init__(self) -> None:
        self.events = {}

    def __str__(self) -> str:
        result = [('Weekday', 'Start time', 'End time')]
        for weekday in range(7):
            if weekday in self.events:
                result += [(
                    calendar.day_abbr[weekday],
                    str(self.events[weekday].start),
                    str(self.events[weekday].stop)
                )]
        return '\n'.join(['\t'.join(ss) for ss in result])

    def addEvent(self, weekday: int, event: ScheduleEvent) -> None:
        '''Add a new event to this schedule.'''
        self.events[weekday] = event


class ScheduleObserver(Observer):
    '''Schedule implementation of astral.Observer to aggregate timezone'''

    def __init__(self, tzinfo: pytz.tzinfo = pytz.utc, **kwargs) -> None:
        '''Create an observer in a given time zone.'''
        self.tzinfo = tzinfo
        super().__init__(**kwargs)

    def getCivilTwilight(self, event_date: date = None) -> datetime:
        '''Return the start of civil sunset on a given date.
        Defaults to today's date if not given.'''
        twilight_start_end = twilight(self, event_date, SunDirection.SETTING, self.tzinfo)
        return twilight_start_end[0]


def getEventType(schedule: WeeklySchedule, event_date: date, observer: Observer) -> Optional[int]:
    '''Return the type of event for manually programming an Intermatic astronomical time clock.
    The event type primarily depends on whether a sunset occurs during the event.
    '''
    event = schedule.events.get(event_date.weekday())
    if event is None:
        return None
    result = EVT_SUNSET
    sunset_time = observer.getCivilTwilight(event_date).time()
    if event.start > sunset_time:
        result = EVT_FIXED
    elif sunset_time > event.stop:
        result = EVT_NEVER_ON
    return result


def createEvents(year: int, schedule: WeeklySchedule) -> Dict[date, Tuple[datetime, int, bool]]:
    '''Create events from a Schedule object at a custom location for the entire given year.

    Outputs the schedule to a CSV file.

    Returns:
        A dictionary defined as follows:
            keys: dates of the year
            values: tuple of (sunset datetime, event type, "event type changed" flag)

    The "event type changed" flag indicates that a change in the clock's
    manual programming is needed for the event that week.
    '''
    # Custom observer: Rochester_HoP,USA,43°09'N,77°23'W,US/Eastern,170
    # Note: elevation (in meters) is just a guess based on ROC airport. We may adjust it.
    observer = ScheduleObserver(latitude=43.1606355, longitude=-77.3883843, elevation=170,
                                tzinfo=pytz.timezone("US/Eastern"))
    data = {}
    calendar_date = date(year, 1, 1)
    event_type_changed = False
    while calendar_date.year == year:
        curr_event_type = getEventType(schedule, calendar_date, observer)
        if curr_event_type is not None:
            prev_week_event_type = getEventType(schedule,
                                                calendar_date - timedelta(days=7),
                                                observer)
            if curr_event_type != prev_week_event_type:
                event_type_changed = True
        data[calendar_date] = (observer.getCivilTwilight(calendar_date),
                               curr_event_type,
                               event_type_changed)
        calendar_date += timedelta(days=1)
        event_type_changed = False
    csv_name = f'sunsets_{year}.csv'
    with open(csv_name, 'w') as out_file:
        out_file.write('"Weekday","Date","Sunset","Event Type","Event Change?"\n')
        for evt_date, (sunset_time, evt_type, evt_changed) in sorted(data.items()):
            out_file.write(
                f'"{calendar.day_abbr[evt_date.weekday()]}",'
                f'{evt_date},'
                f'{sunset_time.strftime("%H:%M:%S")},'
                f'"{EVENT_TYPES.get(evt_type, "")}",'
                f'{"*" if evt_changed else ""}\n'
            )
    print(f'Schedule {csv_name} created.')
    return data


def getCurrentSchedule() -> WeeklySchedule:
    '''Current HoP weekly schedule.'''
    result = WeeklySchedule()
    result.addEvent(calendar.SUNDAY, ScheduleEvent(time(16, 45), time(19, 0)))
    result.addEvent(calendar.TUESDAY, ScheduleEvent(time(18, 30), time(22, 0)))
    result.addEvent(calendar.WEDNESDAY, ScheduleEvent(time(18, 45), time(21, 0)))
    result.addEvent(calendar.FRIDAY, ScheduleEvent(time(18, 45), time(21, 0)))
    return result


def outputSunsets(year: int) -> None:
    '''Create astronomical events as necessary for safe lighting
    and output the schedule to a file.'''
    # Get Lot lighting schedule
    hop_schedule = getCurrentSchedule()
    print('Occupancy schedule:')
    print(hop_schedule)
    # Save it
    createEvents(year, hop_schedule)


if __name__ == '__main__':
    # Default usage: create a CSV file of the current year's schedule
    YEAR = date.today().year
    if len(sys.argv) == 2:
        YEAR = int(sys.argv[1])
    outputSunsets(YEAR)
